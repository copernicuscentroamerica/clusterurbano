#!/usr/bin/env python3
"""
Exportador público de seguimiento operativo desde GitHub Issues y GitHub Projects v2
(scripts/export_progress.py).

Reglas críticas:
- Identificador único global: owner/repo#numero.
- Consulta tanto los Issues de cada repositorio canónico (y del hub) como los campos
  del tablero regional GitHub Project v2 (Status, Prioridad, Iteración, Fecha objetivo)
  mediante GraphQL cuando hay token o acceso disponible.
- Excluye cierres 'not_planned' de los contadores de tareas completadas.
- Estados desconocidos se mapean a 'Sin clasificar' (sin perder la tarjeta ni asignarla por defecto al primer proyecto).
- Sin credenciales o en modo --offline mantiene 'not_initialized' o el último snapshot válido.
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

from site_common import make_format_checker

ROOT = Path(__file__).resolve().parent.parent
HTTP_TIMEOUT = 15

VALID_WORKFLOW_STATUSES = {"Por hacer", "En curso", "En revisión", "Terminado", "Sin clasificar"}
BOARD_STATUS_ALIASES = {
    "todo": "Por hacer",
    "to do": "Por hacer",
    "por hacer": "Por hacer",
    "por iniciar": "Por hacer",
    "backlog": "Por hacer",
    "in progress": "En curso",
    "en curso": "En curso",
    "en progreso": "En curso",
    "in review": "En revisión",
    "en revisión": "En revisión",
    "en revision": "En revisión",
    "review": "En revisión",
    "done": "Terminado",
    "terminado": "Terminado",
    "completado": "Terminado",
}
PRIORITY_ALIASES = {
    "alta": "Alta",
    "high": "Alta",
    "must": "Alta",
    "p0": "Alta",
    "p1": "Alta",
    "media": "Media",
    "medium": "Media",
    "should": "Media",
    "p2": "Media",
    "baja": "Baja",
    "low": "Baja",
    "could": "Baja",
    "p3": "Baja",
}
HTTPS_URL_RE = re.compile(r"https://[^\s)>\"]+")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_issue_form_body(body: str | None) -> dict[str, str | None]:
    """
    Normalizador explícito de respuestas Markdown generadas por GitHub Issue Forms.
    Lee encabezados '### Etiqueta' y devuelve valores limpios; ignora '_No response_'.
    """
    if not body:
        return {}
    sections: dict[str, str | None] = {}
    current_heading: str | None = None
    buf: list[str] = []

    def _flush() -> None:
        if current_heading is None:
            return
        val = "\n".join(buf).strip()
        if not val or val == "_No response_":
            sections[current_heading] = None
        else:
            sections[current_heading] = val

    for line in body.replace("\r\n", "\n").split("\n"):
        if line.startswith("### "):
            _flush()
            current_heading = line[4:].strip()
            buf = []
        else:
            buf.append(line)
    _flush()
    return sections


def fetch_project_v2_board_metadata(
    owner: str,
    project_number: int,
    token: str | None,
) -> dict[str, dict[str, str | None]]:
    """
    Consulta mediante GitHub GraphQL API los ítems del Project v2 regional
    y devuelve un mapa { "owner/repo#number": { "status", "priority", "iteration", "due_date" } }.
    Si no hay token o la consulta falla, retorna {} de forma segura y continúa con Issues/etiquetas.
    """
    if not token:
        return {}

    query = """
    query($owner: String!, $number: Int!, $cursor: String) {
      user(login: $owner) {
        projectV2(number: $number) {
          items(first: 100, after: $cursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              content {
                ... on Issue {
                  number
                  repository {
                    nameWithOwner
                  }
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldIterationValue {
                    title
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldTextValue {
                    text
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    board_map: dict[str, dict[str, str | None]] = {}
    cursor: str | None = None
    for _ in range(10):
        payload = json.dumps(
            {"query": query, "variables": {"owner": owner, "number": project_number, "cursor": cursor}}
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=payload,
            headers={
                "User-Agent": "CopernicusUrbanoProgressExporter/1.1",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            break

        items_obj = (
            data.get("data", {})
            .get("user", {})
            .get("projectV2", {})
            .get("items")
        )
        if not items_obj:
            break

        for node in items_obj.get("nodes") or []:
            if not node:
                continue
            content = node.get("content") or {}
            repo_slug = (content.get("repository") or {}).get("nameWithOwner")
            issue_num = content.get("number")
            if not repo_slug or not issue_num:
                continue
            task_key = f"{repo_slug}#{issue_num}"
            meta: dict[str, str | None] = {
                "status": None,
                "priority": None,
                "iteration": None,
                "due_date": None,
            }
            for fv in (node.get("fieldValues") or {}).get("nodes") or []:
                if not fv:
                    continue
                fname = ((fv.get("field") or {}).get("name") or "").strip().lower()
                val_str = fv.get("name") or fv.get("title") or fv.get("date") or fv.get("text")
                if not fname or not val_str:
                    continue
                if fname in ("status", "estado", "columna"):
                    norm_st = BOARD_STATUS_ALIASES.get(str(val_str).strip().lower(), str(val_str).strip())
                    meta["status"] = norm_st
                elif fname in ("priority", "prioridad"):
                    norm_pr = PRIORITY_ALIASES.get(str(val_str).strip().lower(), str(val_str).strip())
                    meta["priority"] = norm_pr
                elif fname in ("iteration", "iteración", "iteracion", "sprint"):
                    meta["iteration"] = str(val_str).strip()
                elif fname in ("target date", "due date", "fecha", "fecha objetivo", "fecha límite"):
                    meta["due_date"] = str(val_str).strip()
            board_map[task_key] = meta

        page_info = items_obj.get("pageInfo") or {}
        if page_info.get("hasNextPage") and page_info.get("endCursor"):
            cursor = page_info["endCursor"]
        else:
            break

    return board_map


def normalize_task_record(
    *,
    issue: dict[str, Any],
    repo_slug: str,
    project_id: str,
    board_status: str | None = None,
    board_priority: str | None = None,
    board_iteration: str | None = None,
    board_due_date: str | None = None,
) -> dict[str, Any]:
    num = int(issue["number"])
    state_raw = str(issue.get("state", "OPEN")).upper()
    issue_state = "CLOSED" if state_raw == "CLOSED" else "OPEN"

    reason_raw = (issue.get("state_reason") or "").lower()
    completion_reason: str | None = None
    if issue_state == "CLOSED":
        if reason_raw == "not_planned":
            completion_reason = "not_planned"
        elif reason_raw == "completed" or not reason_raw:
            completion_reason = "completed"
    elif reason_raw == "reopened":
        completion_reason = "reopened"

    labels = [
        (lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)).lower()
        for lbl in issue.get("labels", [])
    ]
    blocked = any("bloquead" in l or l == "blocked" for l in labels)

    # Precedencia transparente entre cierre de Issue, etiquetas de flujo y columna de GitHub Project:
    if issue_state == "CLOSED":
        wf_status = "Terminado" if completion_reason == "completed" else "Sin clasificar"
    elif board_status in ("En revisión", "En curso", "Terminado"):
        wf_status = board_status
    elif any("revision" in l or "revisión" in l for l in labels):
        wf_status = "En revisión"
    elif any("curso" in l or "progreso" in l for l in labels):
        wf_status = "En curso"
    elif board_status in VALID_WORKFLOW_STATUSES:
        wf_status = board_status
    elif any("tipo:tarea" in l for l in labels):
        wf_status = "Por hacer"
    else:
        wf_status = "Sin clasificar"

    parsed_form = parse_issue_form_body(issue.get("body"))
    evidence_urls: list[str] = []
    for k, v in parsed_form.items():
        if v and ("evidencia" in k.lower() or "enlace" in k.lower()):
            for u in HTTPS_URL_RE.findall(v):
                if u not in evidence_urls:
                    evidence_urls.append(u)

    # Fecha objetivo: usa fecha confirmada en el tablero Project v2 (formato ISO YYYY-MM-DD)
    due_date: str | None = None
    if board_due_date and re.match(r"^\d{4}-\d{2}-\d{2}$", board_due_date):
        due_date = board_due_date

    # Prioridad: usa campo del tablero Project v2 o etiqueta/formulario normalizado
    priority: str | None = None
    if board_priority in ("Alta", "Media", "Baja"):
        priority = board_priority
    else:
        for l in labels:
            if l.startswith("prioridad:"):
                cand = PRIORITY_ALIASES.get(l.split(":", 1)[1].strip(), "")
                if cand in ("Alta", "Media", "Baja"):
                    priority = cand
                    break
        if not priority:
            for k, v in parsed_form.items():
                if v and "prioridad" in k.lower():
                    cand = PRIORITY_ALIASES.get(v.strip().lower(), "")
                    if cand in ("Alta", "Media", "Baja"):
                        priority = cand
                        break

    # Iteración: usa campo del tablero Project v2 o sección Sprint/Iteración en el cuerpo
    iteration = board_iteration
    if not iteration:
        for k, v in parsed_form.items():
            if v and ("sprint" in k.lower() or "iteraci" in k.lower()):
                iteration = v.strip()[:60]
                break

    assignees = [a["login"] for a in issue.get("assignees", []) if isinstance(a, dict) and a.get("login")]

    updated_at = issue.get("updated_at") or utc_now_iso()
    return {
        "task_id": f"{repo_slug}#{num}",
        "project_id": project_id,
        "repository": repo_slug,
        "issue_number": num,
        "issue_url": issue["html_url"],
        "title": issue["title"].strip() or f"Issue #{num}",
        "workflow_status": wf_status,
        "issue_state": issue_state,
        "completion_reason": completion_reason,
        "blocked": blocked,
        "assignees": assignees,
        "priority": priority,
        "iteration": iteration,
        "due_date": due_date,
        "evidence_urls": evidence_urls,
        "source_updated_at": updated_at,
    }


def compute_metrics(tasks: list[dict[str, Any]]) -> dict[str, int]:
    open_tasks = 0
    completed_tasks = 0
    in_review_tasks = 0
    blocked_tasks = 0
    for t in tasks:
        if t["issue_state"] == "OPEN":
            open_tasks += 1
        elif t["issue_state"] == "CLOSED" and t["completion_reason"] == "completed":
            completed_tasks += 1
        if t["workflow_status"] == "En revisión" and t["issue_state"] == "OPEN":
            in_review_tasks += 1
        if t["blocked"] and t["issue_state"] == "OPEN":
            blocked_tasks += 1
    return {
        "open_tasks": open_tasks,
        "completed_tasks": completed_tasks,
        "in_review_tasks": in_review_tasks,
        "blocked_tasks": blocked_tasks,
    }


def fetch_paginated_repo_issues(repo_slug: str, token: str | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while page <= 20:
        url = f"https://api.github.com/repos/{repo_slug}/issues?state=all&per_page=100&page={page}"
        headers = {
            "User-Agent": "CopernicusUrbanoProgressExporter/1.1",
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            batch = json.loads(resp.read().decode("utf-8"))
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if "pull_request" not in item:
                issues.append(item)
        if len(batch) < 100:
            break
        page += 1
    return issues


def load_previous_progress_snapshot(out_path: Path, previous_url: str | None) -> dict[str, dict[str, Any]]:
    prev_by_proj: dict[str, dict[str, Any]] = {}
    if previous_url and previous_url.startswith("https://"):
        try:
            req = urllib.request.Request(
                previous_url,
                headers={"User-Agent": "CopernicusUrbanoProgressExporter/1.1", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                remote_doc = json.loads(resp.read().decode("utf-8"))
                for p in remote_doc.get("projects", []):
                    if p.get("project_id"):
                        prev_by_proj[p["project_id"]] = p
        except Exception:
            pass

    if not prev_by_proj and out_path.exists():
        try:
            prev_doc = json.loads(out_path.read_text(encoding="utf-8"))
            for p in prev_doc.get("projects", []):
                if p.get("project_id"):
                    prev_by_proj[p["project_id"]] = p
        except Exception:
            pass
    return prev_by_proj


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta snapshot público de seguimiento desde Issues y GitHub Projects v2.")
    parser.add_argument("--offline", action="store_true", help="Conserva snapshot local o inicial sin consultar red.")
    parser.add_argument("--output", type=str, default="data/seguimiento.json", help="Archivo JSON de salida.")
    parser.add_argument("--previous-snapshot", type=str, default=None, help="URL HTTPS opcional del último snapshot publicado.")
    args = parser.parse_args()

    checker = make_format_checker()
    schema = json.loads((ROOT / "schemas" / "progress-snapshot.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=checker)

    registry = json.loads((ROOT / "data" / "projects.registry.json").read_text(encoding="utf-8"))
    out_path = ROOT / args.output
    initial_path = ROOT / "data" / "seguimiento.initial.json"

    if args.offline:
        if out_path.exists():
            snap = json.loads(out_path.read_text(encoding="utf-8"))
        else:
            snap = json.loads(initial_path.read_text(encoding="utf-8"))
        validator.validate(snap)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] Seguimiento resuelto en modo offline (overall_state='{snap['overall_state']}').")
        return 0

    token = os.environ.get("GH_PROJECTS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    prev_url = args.previous_snapshot or os.environ.get("PREVIOUS_PROGRESS_SNAPSHOT_URL")
    prev_by_proj = load_previous_progress_snapshot(out_path, prev_url)

    # Consultar metadatos del tablero GitHub Project v2 regional si está configurado
    board_cfg_path = ROOT / "data" / "project_board.config.json"
    board_cfg = json.loads(board_cfg_path.read_text(encoding="utf-8")) if board_cfg_path.exists() else {}
    board_number = int(board_cfg.get("project_number") or 1)
    hub_repo = registry.get("hub", {}).get("repository") or "copernicuscentroamerica/clusterurbano"
    board_owner = hub_repo.split("/")[0] if "/" in hub_repo else "copernicuscentroamerica"
    board_meta_by_task = fetch_project_v2_board_metadata(board_owner, board_number, token)

    now_iso = utc_now_iso()
    proj_entries: list[dict[str, Any]] = []
    ok_count = 0
    canonical_count = 0

    # También consultar Issues del hub clasificadas por project_id en el formulario
    hub_issues_by_proj: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    valid_pids = {p["id"] for p in registry["projects"]}
    if hub_repo:
        try:
            for iss in fetch_paginated_repo_issues(hub_repo, token):
                parsed = parse_issue_form_body(iss.get("body"))
                chosen_pid = (parsed.get("Proyecto") or "").strip()
                if chosen_pid in valid_pids:
                    hub_issues_by_proj.setdefault(chosen_pid, []).append((hub_repo, iss))
        except Exception:
            pass

    for entry in registry["projects"]:
        pid = entry["id"]
        repo_slug = entry.get("repository")
        if entry.get("source_mode") != "canonical" or not repo_slug:
            proj_entries.append(
                {
                    "project_id": pid,
                    "sync_state": "not_initialized",
                    "last_success_at": None,
                    "source_updated_at": None,
                    "error_code": None,
                    "metrics": {
                        "open_tasks": None,
                        "completed_tasks": None,
                        "in_review_tasks": None,
                        "blocked_tasks": None,
                    },
                    "tasks": [],
                }
            )
            continue

        canonical_count += 1
        try:
            raw_issues = fetch_paginated_repo_issues(repo_slug, token)
            seen_task_ids: set[str] = set()
            tasks: list[dict[str, Any]] = []
            latest_upd: str | None = None

            combined = [(repo_slug, i) for i in raw_issues] + hub_issues_by_proj.get(pid, [])
            for r_slug, iss in combined:
                t_key = f"{r_slug}#{int(iss['number'])}"
                b_meta = board_meta_by_task.get(t_key, {})
                norm = normalize_task_record(
                    issue=iss,
                    repo_slug=r_slug,
                    project_id=pid,
                    board_status=b_meta.get("status"),
                    board_priority=b_meta.get("priority"),
                    board_iteration=b_meta.get("iteration"),
                    board_due_date=b_meta.get("due_date"),
                )
                if norm["task_id"] in seen_task_ids:
                    continue
                seen_task_ids.add(norm["task_id"])
                tasks.append(norm)
                if latest_upd is None or norm["source_updated_at"] > latest_upd:
                    latest_upd = norm["source_updated_at"]

            tasks.sort(key=lambda x: x["task_id"])
            proj_entries.append(
                {
                    "project_id": pid,
                    "sync_state": "ok",
                    "last_success_at": now_iso,
                    "source_updated_at": latest_upd,
                    "error_code": None,
                    "metrics": compute_metrics(tasks),
                    "tasks": tasks,
                }
            )
            ok_count += 1
        except urllib.error.HTTPError as he:
            err_code = "AUTH_REQUIRED" if he.code == 401 else ("RATE_LIMIT" if he.code in (403, 429) else "SOURCE_UNAVAILABLE")
            if pid in prev_by_proj and prev_by_proj[pid].get("sync_state") in ("ok", "stale"):
                stale = dict(prev_by_proj[pid])
                stale["sync_state"] = "stale"
                stale["error_code"] = err_code
                proj_entries.append(stale)
            else:
                proj_entries.append(
                    {
                        "project_id": pid,
                        "sync_state": "unavailable",
                        "last_success_at": None,
                        "source_updated_at": None,
                        "error_code": err_code,
                        "metrics": {"open_tasks": None, "completed_tasks": None, "in_review_tasks": None, "blocked_tasks": None},
                        "tasks": [],
                    }
                )
        except Exception:
            proj_entries.append(
                {
                    "project_id": pid,
                    "sync_state": "unavailable",
                    "last_success_at": None,
                    "source_updated_at": None,
                    "error_code": "SOURCE_UNAVAILABLE",
                    "metrics": {"open_tasks": None, "completed_tasks": None, "in_review_tasks": None, "blocked_tasks": None},
                    "tasks": [],
                }
            )

    if canonical_count == 0:
        overall = "not_initialized"
        gen_at = None
    elif ok_count == len(proj_entries):
        overall = "ok"
        gen_at = now_iso
    elif ok_count > 0:
        overall = "partial"
        gen_at = now_iso
    else:
        overall = "unavailable"
        gen_at = now_iso

    snapshot = {
        "schema_version": "1.0.0",
        "generated_at": gen_at,
        "source_system": "github",
        "overall_state": overall,
        "projects": proj_entries,
    }
    validator.validate(snapshot)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[OK] Seguimiento exportado (overall_state='{overall}', ok={ok_count}/{len(proj_entries)}, "
        f"items_project_v2={len(board_meta_by_task)})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
