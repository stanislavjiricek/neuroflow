"""Tests for skills/neuroflow-core/scripts/doctor.py (stdlib unittest, no network)."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("doctor", ROOT / "skills" / "neuroflow-core" / "scripts" / "doctor.py")
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


def report(project: Path) -> tuple[int, dict]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = doctor.main(["--project", str(project), "--json"])
    return code, {item["id"]: item for item in json.loads(out.getvalue())["checks"]}


class DoctorTest(unittest.TestCase):
    def test_legacy_config_and_missing_gitignore_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".neuroflow").mkdir()
            (project / ".neuroflow" / "project_config.md").write_text("# Project config\nactive_phase: data\n", encoding="utf-8")
            code, checks = report(project)
            self.assertEqual(code, 1)
            self.assertEqual(checks["config"]["status"], "warn")
            self.assertIn("/neuroflow:migrate", checks["config"]["message"])
            self.assertEqual(checks["gitignore"]["status"], "warn")

    def test_current_contract_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".neuroflow").mkdir()
            (project / ".neuroflow" / "project_config.md").write_text("---\nnf_schema: 1\nactive_phase: data\n---\n", encoding="utf-8")
            (project / ".gitignore").write_text("\n".join(doctor.LOCAL_ONLY) + "\n", encoding="utf-8")
            (project / ".gitattributes").write_text("".join(f"{p} merge=union\n" for p in doctor.UNION_FILES), encoding="utf-8")
            _, checks = report(project)
            self.assertEqual(checks["config"]["status"], "ok")
            self.assertEqual(checks["gitignore"]["status"], "ok")
            self.assertEqual(checks["gitattributes"]["status"], "ok")

    def test_synced_folder_warns(self):
        checks: list = []
        doctor.check_location(checks, Path("C:/Users/me/OneDrive/projects/study"))
        self.assertEqual(checks[0]["status"], "warn")
        checks = []
        doctor.check_location(checks, Path("//server/share/study"))
        self.assertEqual(checks[0]["status"], "warn")

    def test_version_parse(self):
        self.assertEqual(doctor.parse_version("2.1.292 (Claude Code)"), (2, 1, 292))
        self.assertIsNone(doctor.parse_version("unknown"))

    def test_bad_project_is_usage_error(self):
        self.assertEqual(doctor.main(["--project", "/definitely/not/here/xyz"]), 2)


if __name__ == "__main__":
    unittest.main()
