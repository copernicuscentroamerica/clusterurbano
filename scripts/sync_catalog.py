#!/usr/bin/env python3
"""
Sincronizador del catálogo regional y del Atlas Urbano Regional (scripts/sync_catalog.py).
Soporta:
  --offline : usa semillas bootstrap/ para entradas bootstrap y conserva snapshots canónicos locales válidos.
  --online [--previous-snapshot URL] : consulta únicamente repositorios canónicos registrados en un SHA fijo,
                                       valida contra JSON Schema Draft 2020-12 y conserva versiones previas
                                       marcadas como 'stale' ante cualquier fallo parcial.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from site_common import make_format_checker, resolve_json_pointer

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 2 * 1024 * 1024  # Límite de seguridad 2 MB por archivo consultado
HTTP_TIMEOUT = 15
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_http_get(url: str, accept: str = "application/json") -> tuple[int, bytes]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Solo se admiten consultas HTTPS válidas.")
    headers = {
        "User-Agent": "CopernicusUrbanoHubSync/1.0",
        "Accept": accept,
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and parsed.netloc in ("api.github.com", "raw.githubusercontent.com"):
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        status = getattr(resp, "status", 200)
        body = resp.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError(f"Respuesta excede tamaño máximo permitido ({MAX_BYTES} bytes).")
        return status, body


def sanitize_error_code(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (401, 403):
            return f"HTTP_{exc.code}_AUTH_OR_RATE_LIMIT"
        return f"HTTP_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "NETWORK_UNAVAILABLE"
    return type(exc).__name__


def validate_project_manifest(
    manifest: dict[str, Any],
    expected_id: str,
    proj_validator: Draft202012Validator,
) -> None:
    if manifest.get("id") != expected_id:
        raise ValueError(f"ID del manifiesto ('{manifest.get('id')}') no coincide con el registro ('{expected_id}').")
    errs = list(proj_validator.iter_errors(manifest))
    if errs:
        raise ValueError(f"Esquema inválido en {expected_id}: {errs[0].message}")
    sources_defined = {s["id"] for s in manifest.get("provenance", {}).get("sources", [])}
    for st in manifest.get("provenance", {}).get("statements", []):
        resolve_json_pointer(manifest, st.get("pointer", ""))
        for sid in st.get("source_ids", []):
            if sid not in sources_defined:
                raise ValueError(f"source_id '{sid}' no definido en provenance.sources.")
    if EMAIL_RE.search(json.dumps(manifest, ensure_ascii=False)):
        raise ValueError("El manifiesto contiene posibles correos electrónicos no autorizados.")


def validate_atlas_product(
    product: dict[str, Any],
    expected_project_id: str,
    atlas_validator: Draft202012Validator,
) -> None:
    if product.get("project_id") != expected_project_id:
        raise ValueError(f"Producto Atlas tiene project_id='{product.get('project_id')}' != '{expected_project_id}'.")
    errs = list(atlas_validator.iter_errors(product))
    if errs:
        raise ValueError(f"Producto Atlas inválido: {errs[0].message}")
    sources_defined = {s["id"] for s in product.get("provenance", {}).get("sources", [])}
    for st in product.get("provenance", {}).get("statements", []):
        resolve_json_pointer(product, st.get("pointer", ""))
        for sid in st.get("source_ids", []):
            if sid not in sources_defined:
                raise ValueError(f"source_id '{sid}' no definido en producto Atlas.")


def load_previous_snapshots(previous_url: str | None) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    prev_projects: dict[str, dict[str, Any]] = {}
    prev_atlas_by_proj: dict[str, list[dict[str, Any]]] = {}

    # 1. Intentar snapshot remoto previo si fue configurado
    if previous_url:
        try:
            _, raw = safe_http_get(previous_url)
            remote_snap = json.loads(raw.decode("utf-8"))
            for item in remote_snap.get("projects", []):
                pid = item.get("project", {}).get("id")
                if pid:
                    prev_projects[pid] = item
        except Exception as exc:
            print(f"[AVISO] No se pudo recuperar snapshot remoto previo ({sanitize_error_code(exc)}); se usará copia local si existe.")

    # 2. Respaldo local en data/projects.snapshot.json y data/atlas.snapshot.json
    local_cat = ROOT / "data" / "projects.snapshot.json"
    if not prev_projects and local_cat.exists():
        try:
            snap = json.loads(local_cat.read_text(encoding="utf-8"))
            for item in snap.get("projects", []):
                pid = item.get("project", {}).get("id")
                if pid:
                    prev_projects[pid] = item
        except Exception:
            pass

    local_atlas = ROOT / "data" / "atlas.snapshot.json"
    if local_atlas.exists():
        try:
            asnap = json.loads(local_atlas.read_text(encoding="utf-8"))
            for prod in asnap.get("products", []):
                pid = prod.get("project_id")
                if pid:
                    prev_atlas_by_proj.setdefault(pid, []).append(prod)
        except Exception:
            pass

    return prev_projects, prev_atlas_by_proj


def load_bootstrap_entry(
    entry: dict[str, Any],
    proj_validator: Draft202012Validator,
    atlas_validator: Draft202012Validator,
    geovisor_map: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pid = entry["id"]
    m_path = ROOT / entry["bootstrap_manifest"]
    c_path = ROOT / entry["bootstrap_content"]
    manifest = json.loads(m_path.read_text(encoding="utf-8"))
    content_md = c_path.read_text(encoding="utf-8")
    if EMAIL_RE.search(content_md) or "../fuentes/" in content_md:
        raise ValueError(f"Contenido bootstrap inválido en {pid}.")
    validate_project_manifest(manifest, pid, proj_validator)

    atlas_list: list[dict[str, Any]] = []
    boot_atlas = ROOT / "bootstrap" / "atlas" / f"{pid}.json"
    if boot_atlas.exists():
        ap = json.loads(boot_atlas.read_text(encoding="utf-8"))
        validate_atlas_product(ap, pid, atlas_validator)
        atlas_list.append(ap)

    cat_item = {
        "project": manifest,
        "content_markdown": content_md,
        "source_repository": None,
        "source_commit": None,
        "fetched_at": utc_now_iso(),
        "content_updated_at": manifest["governance"].get("content_updated_at"),
        "sync_state": "bootstrap",
        "source_mode": entry["source_mode"],
        "geovisor_summary": geovisor_map.get(pid),
    }
    return cat_item, atlas_list


def fetch_canonical_online(
    entry: dict[str, Any],
    proj_validator: Draft202012Validator,
    atlas_validator: Draft202012Validator,
    geovisor_map: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pid = entry["id"]
    repo_slug = entry["repository"]
    branch = entry["default_branch"]
    if not repo_slug or not branch:
        raise ValueError("Entrada canonical sin repository o default_branch.")

    # 1. Resolver SHA concreto de la rama
    commit_api = f"https://api.github.com/repos/{repo_slug}/commits/{urllib.parse.quote(branch, safe='')}"
    _, commit_raw = safe_http_get(commit_api, accept="application/vnd.github+json")
    commit_info = json.loads(commit_raw.decode("utf-8"))
    sha = commit_info.get("sha")
    if not sha or not re.match(r"^[0-9a-f]{40}$", sha):
        raise ValueError("No se obtuvo un SHA de commit válido.")

    # 2. Descargar project.json y content/project.md desde ese mismo SHA
    raw_base = f"https://raw.githubusercontent.com/{repo_slug}/{sha}"
    _, m_bytes = safe_http_get(f"{raw_base}/{entry['manifest_path']}", accept="text/plain")
    _, c_bytes = safe_http_get(f"{raw_base}/{entry['content_path']}", accept="text/plain")

    manifest = json.loads(m_bytes.decode("utf-8"))
    content_md = c_bytes.decode("utf-8")
    if EMAIL_RE.search(content_md) or "../fuentes/" in content_md:
        raise ValueError("Contenido remoto contiene correos o enlaces relativos prohibidos.")
    validate_project_manifest(manifest, pid, proj_validator)

    # 3. Consultar productos en atlas/products/ en ese mismo SHA
    atlas_list: list[dict[str, Any]] = []
    try:
        _, dir_bytes = safe_http_get(
            f"https://api.github.com/repos/{repo_slug}/contents/atlas/products?ref={sha}",
            accept="application/vnd.github+json",
        )
        listing = json.loads(dir_bytes.decode("utf-8"))
        if isinstance(listing, list):
            for f_entry in sorted(listing, key=lambda x: x.get("name", "")):
                fname = f_entry.get("name", "")
                if fname.endswith(".json"):
                    _, p_bytes = safe_http_get(f"{raw_base}/atlas/products/{urllib.parse.quote(fname)}", accept="text/plain")
                    p_obj = json.loads(p_bytes.decode("utf-8"))
                    validate_atlas_product(p_obj, pid, atlas_validator)
                    atlas_list.append(p_obj)
    except urllib.error.HTTPError as he:
        if he.code != 404:
            raise

    cat_item = {
        "project": manifest,
        "content_markdown": content_md,
        "source_repository": repo_slug,
        "source_commit": sha,
        "fetched_at": utc_now_iso(),
        "content_updated_at": manifest["governance"].get("content_updated_at"),
        "sync_state": "ok",
        "source_mode": "canonical",
        "geovisor_summary": geovisor_map.get(pid),
    }
    return cat_item, atlas_list


def run_sync(*, online: bool, previous_snapshot_url: str | None = None, registry_path: Path | None = None) -> int:
    checker = make_format_checker()
    reg_schema = json.loads((ROOT / "schemas" / "registry.schema.json").read_text(encoding="utf-8"))
    proj_schema = json.loads((ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
    atlas_schema = json.loads((ROOT / "schemas" / "atlas-product.schema.json").read_text(encoding="utf-8"))

    reg_validator = Draft202012Validator(reg_schema, format_checker=checker)
    proj_validator = Draft202012Validator(proj_schema, format_checker=checker)
    atlas_validator = Draft202012Validator(atlas_schema, format_checker=checker)

    reg_file = registry_path or (ROOT / "data" / "projects.registry.json")
    registry = json.loads(reg_file.read_text(encoding="utf-8"))
    reg_validator.validate(registry)

    seen_ids: set[str] = set()
    for p in registry["projects"]:
        pid = p["id"]
        if pid in seen_ids:
            raise ValueError(f"ID duplicado en projects.registry.json: {pid}")
        seen_ids.add(pid)

    geovisor_map: dict[str, Any] = {}
    geo_summary_file = ROOT / "bootstrap" / "geovisor_index.json"
    if geo_summary_file.exists():
        geovisor_map = json.loads(geo_summary_file.read_text(encoding="utf-8"))

    prev_projects, prev_atlas_by_proj = load_previous_snapshots(previous_snapshot_url if online else None)

    out_projects: list[dict[str, Any]] = []
    out_atlas_products: list[dict[str, Any]] = []
    atlas_sources_status: list[dict[str, Any]] = []

    for entry in registry["projects"]:
        if not entry.get("enabled", True):
            continue
        pid = entry["id"]
        smode = entry["source_mode"]

        if smode == "bootstrap":
            item, prods = load_bootstrap_entry(entry, proj_validator, atlas_validator, geovisor_map)
            out_projects.append(item)
            out_atlas_products.extend(prods)
            atlas_sources_status.append(
                {"project_id": pid, "source_mode": "bootstrap", "sync_state": "bootstrap", "error_code": None}
            )
            continue

        # smode == "canonical"
        if not online:
            if pid in prev_projects and prev_projects[pid].get("source_repository"):
                cached = dict(prev_projects[pid])
                cached["source_mode"] = "canonical"
                validate_project_manifest(cached["project"], pid, proj_validator)
                out_projects.append(cached)
                out_atlas_products.extend(prev_atlas_by_proj.get(pid, []))
                atlas_sources_status.append(
                    {"project_id": pid, "source_mode": "canonical", "sync_state": cached.get("sync_state", "ok"), "error_code": None}
                )
            else:
                # Recuperación bootstrap explícita sin alterar projects.registry.json
                item, prods = load_bootstrap_entry(entry, proj_validator, atlas_validator, geovisor_map)
                item["sync_state"] = "stale"
                item["source_mode"] = "canonical"
                out_projects.append(item)
                out_atlas_products.extend(prods)
                atlas_sources_status.append(
                    {"project_id": pid, "source_mode": "canonical", "sync_state": "stale", "error_code": "OFFLINE_BOOTSTRAP_FALLBACK"}
                )
        else:
            try:
                item, prods = fetch_canonical_online(entry, proj_validator, atlas_validator, geovisor_map)
                out_projects.append(item)
                out_atlas_products.extend(prods)
                atlas_sources_status.append(
                    {"project_id": pid, "source_mode": "canonical", "sync_state": "ok", "error_code": None}
                )
                print(f"[OK] Sincronizado remoto canónico: {pid} ({item['source_repository']}@{item['source_commit'][:7]})")
            except Exception as exc:
                err_code = sanitize_error_code(exc)
                print(f"[AVISO] Fallo al consultar {pid} ({err_code}); se preserva última versión válida.", file=sys.stderr)
                if pid in prev_projects:
                    stale_item = dict(prev_projects[pid])
                    stale_item["sync_state"] = "stale"
                    stale_item["source_mode"] = "canonical"
                    out_projects.append(stale_item)
                    out_atlas_products.extend(prev_atlas_by_proj.get(pid, []))
                    atlas_sources_status.append(
                        {"project_id": pid, "source_mode": "canonical", "sync_state": "stale", "error_code": err_code}
                    )
                else:
                    fallback_item, prods = load_bootstrap_entry(entry, proj_validator, atlas_validator, geovisor_map)
                    fallback_item["sync_state"] = "unavailable"
                    fallback_item["source_mode"] = "canonical"
                    out_projects.append(fallback_item)
                    out_atlas_products.extend(prods)
                    atlas_sources_status.append(
                        {"project_id": pid, "source_mode": "canonical", "sync_state": "unavailable", "error_code": err_code}
                    )

    now_iso = utc_now_iso()
    catalog_snapshot = {
        "schema_version": "1.0.0",
        "generated_at": now_iso,
        "projects": out_projects,
    }
    atlas_snapshot = {
        "schema_version": "1.0.0",
        "generated_at": now_iso,
        "sources": atlas_sources_status,
        "products": out_atlas_products,
    }

    (ROOT / "data" / "projects.snapshot.json").write_text(
        json.dumps(catalog_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "data" / "atlas.snapshot.json").write_text(
        json.dumps(atlas_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    mode_lbl = "ONLINE" if online else "OFFLINE"
    print(f"[OK] Catálogo ({len(out_projects)} iniciativas) y Atlas ({len(out_atlas_products)} productos) resueltos en modo {mode_lbl}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza el catálogo de iniciativas y productos del Atlas.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--offline", action="store_true", help="Resuelve únicamente desde bootstrap/snapshots locales sin red.")
    group.add_argument("--online", action="store_true", help="Consulta repositorios canónicos registrados en GitHub.")
    parser.add_argument("--previous-snapshot", type=str, default=None, help="URL HTTPS opcional del último snapshot publicado.")
    args = parser.parse_args()

    prev_url = args.previous_snapshot or os.environ.get("PREVIOUS_CATALOG_SNAPSHOT_URL")
    return run_sync(online=args.online, previous_snapshot_url=prev_url)


if __name__ == "__main__":
    sys.exit(main())
