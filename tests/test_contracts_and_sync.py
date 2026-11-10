#!/usr/bin/env python3
"""
Suite de pruebas automatizadas de contratos (JSON Schema Draft 2020-12),
reglas de sincronización tolerante a fallos, saneamiento HTML y seguimiento.
Cubre las 14 condiciones P0 de 04_MODELO_DE_DATOS_Y_CONTRATOS.md y 03_GITHUB_PAGES_Y_AUTOMATIZACION.md.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from jsonschema import Draft202012Validator, ValidationError
from markdown_lite import render_markdown
from site_common import make_format_checker
from export_progress import compute_metrics, normalize_task_record
import sync_catalog


class ContractAndSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = make_format_checker()
        cls.schemas = {}
        for name in (
            "project.schema.json",
            "registry.schema.json",
            "atlas-product.schema.json",
            "progress-snapshot.schema.json",
            "catalog-snapshot.schema.json",
            "atlas-snapshot.schema.json",
        ):
            obj = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(obj)
            cls.schemas[name] = obj

        cls.proj_val = Draft202012Validator(cls.schemas["project.schema.json"], format_checker=cls.checker)
        cls.reg_val = Draft202012Validator(cls.schemas["registry.schema.json"], format_checker=cls.checker)
        cls.atlas_val = Draft202012Validator(cls.schemas["atlas-product.schema.json"], format_checker=cls.checker)
        cls.prog_val = Draft202012Validator(cls.schemas["progress-snapshot.schema.json"], format_checker=cls.checker)

    def test_01_metaschemas_and_fixtures_valid(self) -> None:
        p_fix = json.loads((ROOT / "tests" / "fixtures" / "project.fixture.json").read_text(encoding="utf-8"))
        a_fix = json.loads((ROOT / "tests" / "fixtures" / "atlas-product.fixture.json").read_text(encoding="utf-8"))
        self.proj_val.validate(p_fix)
        self.atlas_val.validate(a_fix)

    def test_02_eight_real_seeds_and_panama_consolidation(self) -> None:
        reg = json.loads((ROOT / "data" / "projects.registry.json").read_text(encoding="utf-8"))
        self.reg_val.validate(reg)
        ids = [p["id"] for p in reg["projects"]]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(set(ids)), 8)
        for p in reg["projects"]:
            manifest = json.loads((ROOT / p["bootstrap_manifest"]).read_text(encoding="utf-8"))
            self.proj_val.validate(manifest)
            self.assertEqual(manifest["id"], p["id"])
            if p["id"] == "pa-panama-oeste":
                self.assertEqual(sorted(manifest["source_groups"]), [1, 9])

    def test_03_swapped_id_rejected(self) -> None:
        manifest = json.loads((ROOT / "bootstrap" / "projects" / "pa-panama-oeste.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            sync_catalog.validate_project_manifest(manifest, "sv-amss", self.proj_val)

    def test_04_validated_review_without_evidence_rejected(self) -> None:
        bad = json.loads((ROOT / "tests" / "fixtures" / "project.fixture.json").read_text(encoding="utf-8"))
        bad["status"]["technical_review"]["state"] = "validado"
        bad["status"]["technical_review"]["evidence_url"] = None
        with self.assertRaises(ValidationError):
            self.proj_val.validate(bad)

    def test_05_demo_disponible_without_url_rejected(self) -> None:
        bad = json.loads((ROOT / "tests" / "fixtures" / "project.fixture.json").read_text(encoding="utf-8"))
        bad["status"]["demo"] = "disponible"
        bad["links"]["demo"] = None
        with self.assertRaises(ValidationError):
            self.proj_val.validate(bad)

    def test_06_published_atlas_without_outputs_or_governance_rejected(self) -> None:
        bad = json.loads((ROOT / "tests" / "fixtures" / "atlas-product.fixture.json").read_text(encoding="utf-8"))
        bad["publication_status"] = "publicado"
        with self.assertRaises(ValidationError):
            self.atlas_val.validate(bad)

    def test_07_canonical_registry_without_repo_rejected(self) -> None:
        reg = json.loads((ROOT / "data" / "projects.registry.json").read_text(encoding="utf-8"))
        bad = copy.deepcopy(reg)
        bad["projects"][0]["source_mode"] = "canonical"
        bad["projects"][0]["repository"] = None
        with self.assertRaises(ValidationError):
            self.reg_val.validate(bad)

    def test_08_format_checker_enforces_iso_dates_and_https_uris(self) -> None:
        bad = json.loads((ROOT / "tests" / "fixtures" / "project.fixture.json").read_text(encoding="utf-8"))
        bad["governance"]["content_updated_at"] = "09-11-2026"
        with self.assertRaises(ValidationError):
            self.proj_val.validate(bad)

        bad2 = json.loads((ROOT / "tests" / "fixtures" / "project.fixture.json").read_text(encoding="utf-8"))
        bad2["links"]["website"] = "http://inseguro.ejemplo.org"
        with self.assertRaises(ValidationError):
            self.proj_val.validate(bad2)

    def test_09_uninitialized_progress_uses_null_metrics(self) -> None:
        init_prog = json.loads((ROOT / "data" / "seguimiento.initial.json").read_text(encoding="utf-8"))
        self.prog_val.validate(init_prog)
        self.assertEqual(init_prog["overall_state"], "not_initialized")
        for p in init_prog["projects"]:
            self.assertIsNone(p["metrics"]["open_tasks"])
            self.assertIsNone(p["metrics"]["completed_tasks"])

    def test_10_cancelled_not_planned_issue_excluded_from_completed(self) -> None:
        cancelled_issue = {
            "number": 12,
            "html_url": "https://github.com/copernicuscentroamerica/urbano-sv-amss/issues/12",
            "title": "Tarea descartada",
            "state": "CLOSED",
            "state_reason": "not_planned",
            "labels": [{"name": "tipo:tarea"}],
            "assignees": [],
            "updated_at": "2026-11-10T15:00:00Z",
            "body": "",
        }
        done_issue = {
            "number": 13,
            "html_url": "https://github.com/copernicuscentroamerica/urbano-sv-amss/issues/13",
            "title": "Tarea completada",
            "state": "CLOSED",
            "state_reason": "completed",
            "labels": [{"name": "tipo:tarea"}],
            "assignees": [{"login": "participante1"}],
            "updated_at": "2026-11-10T16:00:00Z",
            "body": "### Evidencia\nhttps://github.com/copernicuscentroamerica/urbano-sv-amss/pull/1",
        }
        t_cancel = normalize_task_record(issue=cancelled_issue, repo_slug="copernicuscentroamerica/urbano-sv-amss", project_id="sv-amss")
        t_done = normalize_task_record(issue=done_issue, repo_slug="copernicuscentroamerica/urbano-sv-amss", project_id="sv-amss")
        self.assertEqual(t_cancel["workflow_status"], "Sin clasificar")
        self.assertEqual(t_done["workflow_status"], "Terminado")
        metrics = compute_metrics([t_cancel, t_done])
        self.assertEqual(metrics["completed_tasks"], 1)
        self.assertEqual(metrics["open_tasks"], 0)

    def test_11_xss_and_unsafe_links_escaped_in_markdown(self) -> None:
        malicious = "<script>alert(1)</script> [click](javascript:alert(2)) [priv](../fuentes/S02.md)"
        rendered = render_markdown(malicious)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn('href="javascript:', rendered)
        self.assertNotIn('href="../fuentes/', rendered)

    def test_12_sync_failure_preserves_previous_valid_snapshot_as_stale(self) -> None:
        reg = json.loads((ROOT / "data" / "projects.registry.json").read_text(encoding="utf-8"))
        test_reg = copy.deepcopy(reg)
        test_reg["projects"][0]["source_mode"] = "canonical"
        test_reg["projects"][0]["repository"] = "copernicuscentroamerica/urbano-pa-panama-oeste"
        test_reg["projects"][0]["default_branch"] = "main"

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump(test_reg, tf, ensure_ascii=False)
            tmp_reg_path = Path(tf.name)

        try:
            # Simular fallo de red al consultar el repositorio remoto de Panamá Oeste:
            # debe conservar la ficha previa del snapshot local marcada como 'stale' y mantener intactas las otras 7.
            orig_snap = (ROOT / "data" / "projects.snapshot.json").read_text(encoding="utf-8")
            orig_atlas = (ROOT / "data" / "atlas.snapshot.json").read_text(encoding="utf-8")
            try:
                with mock.patch.object(sync_catalog, "safe_http_get", side_effect=OSError("Simulated network failure")):
                    rc = sync_catalog.run_sync(online=True, registry_path=tmp_reg_path)
                    self.assertEqual(rc, 0)
                updated_snap = json.loads((ROOT / "data" / "projects.snapshot.json").read_text(encoding="utf-8"))
                self.assertEqual(len(updated_snap["projects"]), 8)
                pa_entry = [x for x in updated_snap["projects"] if x["project"]["id"] == "pa-panama-oeste"][0]
                self.assertEqual(pa_entry["sync_state"], "stale")
            finally:
                (ROOT / "data" / "projects.snapshot.json").write_text(orig_snap, encoding="utf-8")
                (ROOT / "data" / "atlas.snapshot.json").write_text(orig_atlas, encoding="utf-8")
        finally:
            tmp_reg_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
