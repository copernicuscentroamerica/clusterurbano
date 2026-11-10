#!/usr/bin/env python3
"""
Validador oficial de fuentes (--source) y artefacto estático (--site)
para el repositorio central del Portal Comunitario (clusterurbano).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html.parser
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from site_common import make_format_checker, resolve_json_pointer

ROOT = Path(__file__).resolve().parent.parent
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

EXPECTED_IDS = [
    "pa-panama-oeste",
    "sv-amss",
    "cr-la-carpio",
    "sv-la-union",
    "gt-bethania",
    "do-santiago",
    "gt-salud-metropolitana",
    "hn-distrito-central",
]


class LinkCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "a" and "href" in attr_map:
            self.links.append(("href", attr_map["href"]))
        elif tag.lower() in ("link", "script", "img", "iframe"):
            for key in ("href", "src"):
                if key in attr_map and attr_map[key]:
                    self.links.append((key, attr_map[key]))


def check_no_private_data(text: str, label: str, errors: list[str]) -> None:
    found = EMAIL_RE.findall(text)
    if found:
        errors.append(f"[{label}] Contiene correos personales no autorizados: {found}")


def validate_source() -> list[str]:
    errors: list[str] = []

    if (ROOT / "project.json").exists():
        errors.append("Configuración ambigua: el repositorio del hub no debe contener un project.json de iniciativa en la raíz.")
        return errors

    reg_path = ROOT / "data" / "projects.registry.json"
    if not reg_path.exists():
        errors.append("Falta data/projects.registry.json en el hub.")
        return errors

    checker = make_format_checker()

    # 1. Validar los 4 esquemas oficiales + esquemas derivados contra Draft 2020-12
    schema_names = [
        "project.schema.json",
        "registry.schema.json",
        "atlas-product.schema.json",
        "progress-snapshot.schema.json",
        "catalog-snapshot.schema.json",
        "atlas-snapshot.schema.json",
    ]
    loaded_schemas: dict[str, Any] = {}
    for sname in schema_names:
        sp = ROOT / "schemas" / sname
        if not sp.exists():
            errors.append(f"Falta esquema requerido: schemas/{sname}")
            continue
        sobj = json.loads(sp.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(sobj)
        loaded_schemas[sname] = sobj

    if errors:
        return errors

    reg_val = Draft202012Validator(loaded_schemas["registry.schema.json"], format_checker=checker)
    proj_val = Draft202012Validator(loaded_schemas["project.schema.json"], format_checker=checker)
    atlas_val = Draft202012Validator(loaded_schemas["atlas-product.schema.json"], format_checker=checker)
    prog_val = Draft202012Validator(loaded_schemas["progress-snapshot.schema.json"], format_checker=checker)

    # 2. Validar registro de proyectos
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    for verr in reg_val.iter_errors(registry):
        errors.append(f"[projects.registry.json] {verr.message}")

    reg_ids = [p["id"] for p in registry.get("projects", [])]
    if reg_ids != EXPECTED_IDS:
        errors.append(f"Los IDs del registro {reg_ids} no coinciden exactamente con los ocho IDs obligatorios {EXPECTED_IDS}.")

    # 3. Validar las 8 semillas bootstrap y sus productos Atlas
    all_groups: set[int] = set()
    for entry in registry.get("projects", []):
        pid = entry["id"]
        bm_path = ROOT / entry["bootstrap_manifest"]
        bc_path = ROOT / entry["bootstrap_content"]
        if not bm_path.exists() or not bc_path.exists():
            errors.append(f"Faltan semillas bootstrap para {pid}.")
            continue
        raw_m = bm_path.read_text(encoding="utf-8")
        raw_c = bc_path.read_text(encoding="utf-8")
        check_no_private_data(raw_m, str(bm_path.relative_to(ROOT)), errors)
        check_no_private_data(raw_c, str(bc_path.relative_to(ROOT)), errors)
        if "../fuentes/" in raw_c or "](fuentes/" in raw_c:
            errors.append(f"[{bc_path.relative_to(ROOT)}] Enlace relativo prohibido hacia fuentes/.")

        manifest = json.loads(raw_m)
        if manifest.get("id") != pid:
            errors.append(f"[{bm_path.name}] id='{manifest.get('id')}' != '{pid}'.")
        for verr in proj_val.iter_errors(manifest):
            errors.append(f"[{bm_path.name}] {verr.message}")

        for g in manifest.get("source_groups", []):
            all_groups.add(g)
        if pid == "pa-panama-oeste" and sorted(manifest.get("source_groups", [])) != [1, 9]:
            errors.append("Panamá Oeste debe consolidar exactamente los grupos de origen 1 y 9.")

        src_ids = {s["id"] for s in manifest.get("provenance", {}).get("sources", [])}
        for st in manifest.get("provenance", {}).get("statements", []):
            try:
                resolve_json_pointer(manifest, st.get("pointer", ""))
            except Exception as exc:
                errors.append(f"[{bm_path.name} provenance] {exc}")
            for sid in st.get("source_ids", []):
                if sid not in src_ids:
                    errors.append(f"[{bm_path.name} provenance] source_id '{sid}' inexistente.")

        ba_path = ROOT / "bootstrap" / "atlas" / f"{pid}.json"
        if not ba_path.exists():
            errors.append(f"Falta contribución inicial al Atlas en bootstrap/atlas/{pid}.json")
        else:
            ap = json.loads(ba_path.read_text(encoding="utf-8"))
            if ap.get("project_id") != pid:
                errors.append(f"[bootstrap/atlas/{pid}.json] project_id != '{pid}'.")
            for verr in atlas_val.iter_errors(ap):
                errors.append(f"[bootstrap/atlas/{pid}.json] {verr.message}")

    if sorted(all_groups) != [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        errors.append(f"Los grupos fuente cubiertos {sorted(all_groups)} no representan los 9 grupos originales (1..9).")

    # 4. Validar agenda oficial A01
    agenda_path = ROOT / "data" / "events.agenda.json"
    if not agenda_path.exists():
        errors.append("Falta data/events.agenda.json")
    else:
        agenda = json.loads(agenda_path.read_text(encoding="utf-8"))
        prev_start_by_day: dict[str, dt.datetime] = {}
        for ev in agenda.get("scheduled_activities", []):
            t0 = dt.datetime.fromisoformat(ev["start"])
            t1 = dt.datetime.fromisoformat(ev["end"])
            if t1 <= t0:
                errors.append(f"[events.agenda.json] Actividad '{ev['id']}' termina antes o igual que su inicio.")
            if ev.get("utc_offset") != "-06:00" or not ev["start"].endswith("-06:00"):
                errors.append(f"[events.agenda.json] Actividad '{ev['id']}' debe conservar hora de El Salvador (-06:00).")
            day_k = ev["day_date"]
            if day_k in prev_start_by_day and t0 < prev_start_by_day[day_k]:
                errors.append(f"[events.agenda.json] Orden cronológico alterado en '{ev['id']}'.")
            prev_start_by_day[day_k] = t0

    # 5. Validar seguimiento inicial/actual
    for seg_file in ("seguimiento.initial.json", "seguimiento.json"):
        sf = ROOT / "data" / seg_file
        if sf.exists():
            sobj = json.loads(sf.read_text(encoding="utf-8"))
            for verr in prog_val.iter_errors(sobj):
                errors.append(f"[data/{seg_file}] {verr.message}")

    # 6. Validar snapshots derivados si existen
    cat_snap_file = ROOT / "data" / "projects.snapshot.json"
    if cat_snap_file.exists():
        cat_val = Draft202012Validator(loaded_schemas["catalog-snapshot.schema.json"], format_checker=checker)
        for verr in cat_val.iter_errors(json.loads(cat_snap_file.read_text(encoding="utf-8"))):
            errors.append(f"[projects.snapshot.json] {verr.message}")

    atlas_snap_file = ROOT / "data" / "atlas.snapshot.json"
    if atlas_snap_file.exists():
        as_val = Draft202012Validator(loaded_schemas["atlas-snapshot.schema.json"], format_checker=checker)
        for verr in as_val.iter_errors(json.loads(atlas_snap_file.read_text(encoding="utf-8"))):
            errors.append(f"[atlas.snapshot.json] {verr.message}")

    if (ROOT / "fuentes").exists():
        errors.append("La carpeta privada 'fuentes/' no debe incluirse en el repositorio público del hub.")

    return errors


def resolve_internal_target(site_dir: Path, base_path: str, current_html: Path, ref: str) -> Path | None:
    parsed = urllib.parse.urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        return None
    path_part = parsed.path
    if not path_part:
        return current_html
    norm_base = base_path if base_path.endswith("/") else base_path + "/"
    if path_part.startswith("/"):
        if norm_base != "/" and path_part.startswith(norm_base):
            rel = path_part[len(norm_base) :]
        elif norm_base == "/":
            rel = path_part.lstrip("/")
        else:
            return site_dir / "__FUERA_DE_BASE_PATH__" / path_part.lstrip("/")
        target = site_dir / rel
    else:
        target = (current_html.parent / path_part).resolve()

    if target.is_dir() or str(path_part).endswith("/"):
        return target / "index.html"
    return target


def validate_site(site_dir: Path) -> list[str]:
    errors: list[str] = []
    if not site_dir.exists():
        return [f"No existe el directorio construido: {site_dir}"]

    required_routes = [
        "index.html",
        "404.html",
        "proyectos/index.html",
        "ejercicio/index.html",
        "seguimiento/index.html",
        "atlas/index.html",
        "comunidad/index.html",
        "recursos/index.html",
        "agenda/index.html",
        "agenda/jornada-copernicus-2026.ics",
        "data/projects.snapshot.json",
        "data/atlas.snapshot.json",
        "data/seguimiento.json",
        "data/build-meta.json",
        "assets/css/styles.css",
        "assets/js/ui.js",
        "assets/js/geovisor.js",
        "assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb",
        "assets/descargas/scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx",
    ]
    for pid in EXPECTED_IDS:
        required_routes.append(f"proyectos/{pid}/index.html")

    for rel in required_routes:
        if not (site_dir / rel).exists():
            errors.append(f"[site] Falta ruta o artefacto requerido: {rel}")

    if (site_dir / "CNAME").exists():
        errors.append("[site] No debe generarse CNAME heredado.")
    if (site_dir / "fuentes").exists():
        errors.append("[site] No debe publicarse la carpeta privada fuentes/.")

    if errors:
        return errors

    build_meta = json.loads((site_dir / "data" / "build-meta.json").read_text(encoding="utf-8"))
    base_path = build_meta.get("base_path", "/")

    for hf in sorted(site_dir.rglob("*.html")):
        txt = hf.read_text(encoding="utf-8")
        check_no_private_data(txt, str(hf.relative_to(site_dir)), errors)
        col = LinkCollector()
        col.feed(txt)
        for attr_kind, href in col.links:
            h = href.strip()
            if h == "#":
                errors.append(f"[{hf.relative_to(site_dir)}] Enlace vacío prohibido href='#'.")
                continue
            if h.lower().startswith(("javascript:", "data:", "vbscript:")):
                errors.append(f"[{hf.relative_to(site_dir)}] Esquema ejecutable prohibido: {h}")
                continue
            if "fuentes/" in h.lower():
                errors.append(f"[{hf.relative_to(site_dir)}] Enlace hacia carpeta privada fuentes/: {h}")
                continue
            if h.startswith("http://"):
                errors.append(f"[{hf.relative_to(site_dir)}] Recurso sin HTTPS: {h}")
                continue
            if h.startswith("https://") or h.startswith("#"):
                continue

            target = resolve_internal_target(site_dir, base_path, hf, h)
            if target is not None and not target.exists():
                errors.append(f"[{hf.relative_to(site_dir)}] Enlace interno roto ({attr_kind}='{h}') -> {target}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida fuentes y sitio construido del portal clusterurbano.")
    parser.add_argument("--source", action="store_true", help="Valida esquemas, registro, semillas y snapshots.")
    parser.add_argument("--site", type=str, default=None, help="Directorio del sitio generado a validar.")
    args = parser.parse_args()

    if not args.source and not args.site:
        parser.error("Indica --source y/o --site <directorio>.")

    all_errors: list[str] = []
    if args.source:
        errs = validate_source()
        if errs:
            all_errors.extend(errs)
        else:
            print("[OK] Validación de fuentes del hub (--source) superada sin errores.")

    if args.site:
        errs = validate_site(ROOT / args.site)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"[OK] Validación del sitio del hub (--site {args.site}) superada sin errores.")

    if all_errors:
        print("Se encontraron errores de validación en el hub:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
