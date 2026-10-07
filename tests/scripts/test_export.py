"""Tests for skills/phase-output/scripts/export.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-output" / "scripts" / "export.py"


def load():
    name = "nf_test_export"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ex = load()


def write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_project(root: Path) -> None:
    nf = root / ".neuroflow"
    write(nf / "project_config.md", "---\nnf_schema: 1\nproject_name: Oddball EEG study\n"
          "active_phase: data-analyze\nraw_roots: [sourcedata/]\n---\n\n# Notes\n")
    write(nf / "flow.md", "| File | Description | Last changed |\n")
    write(nf / "reasoning" / "general.jsonl", '{"statement": "s"}\n')
    write(nf / "sessions" / "2026-10-07.md", "## 10:00 - [output] x\n")
    write(nf / "review" / "review-x.md", "confidential\n")
    write(nf / "integrations.json", "{}\n")
    write(nf / "fails" / "core.md", "complaint\n")
    write(nf / "finance" / "budget.md", "money\n")
    write(nf / "ethics" / "status.md", "---\nstatus: approved\n---\n")
    write(nf / "ethics" / "consent-v2.md", "form\n")
    write(nf / "ethics" / "signed-consents.md", "names\n")
    write(nf / "data-analyze" / "plan.md", "plan\n")
    write(nf / "data-analyze" / ".env", "TOKEN=1\n")


def run_main(args: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = ex.main(args)
    return code, buf.getvalue()


class ClassifyTests(unittest.TestCase):
    def test_local_tier_and_never_exported(self):
        self.assertEqual(ex.classify(".neuroflow/sessions/2026-10-07.md"), ex.LOCAL_REASON)
        self.assertEqual(ex.classify(".neuroflow/review/r.md"), ex.LOCAL_REASON)
        self.assertEqual(ex.classify(".neuroflow/integrations.json"), ex.LOCAL_REASON)
        self.assertEqual(ex.classify(".neuroflow/flowie/profile.md"), ex.LOCAL_REASON)
        self.assertIn("never exported", ex.classify(".neuroflow/fails/core.md"))
        self.assertIn("never exported", ex.classify(".neuroflow/finance/budget.md"))

    def test_ethics_allowlist(self):
        self.assertIsNone(ex.classify(".neuroflow/ethics/status.md"))
        self.assertIsNone(ex.classify(".neuroflow/ethics/consent-v3.md"))
        self.assertIsNone(ex.classify(".neuroflow/ethics/protocol-v2.md"))
        self.assertEqual(ex.classify(".neuroflow/ethics/participants.xlsx"), ex.ETHICS_REASON)
        self.assertEqual(ex.classify(".neuroflow/ethics/scans/a.pdf"), ex.ETHICS_REASON)
        allowed = frozenset({".neuroflow/ethics/participants.xlsx"})
        self.assertIsNone(ex.classify(".neuroflow/ethics/participants.xlsx", allowed))

    def test_include_ethics_cannot_override_local_tier(self):
        allowed = frozenset({".neuroflow/sessions/a.md"})
        self.assertEqual(ex.classify(".neuroflow/sessions/a.md", allowed), ex.LOCAL_REASON)

    def test_credentials_anywhere(self):
        for rel in ("config/.env", "keys/server.pem", "id_ed25519", "client_secret_123.json", "a/integrations.json"):
            self.assertEqual(ex.classify(rel), ex.CREDENTIAL_REASON, rel)
        self.assertIsNone(ex.classify(".env.example"))
        self.assertIsNone(ex.classify("scripts/analysis/run.py"))

    def test_nested_and_windows_paths(self):
        self.assertTrue(ex.is_local_tier("sub/.neuroflow/sessions/x.md"))
        self.assertTrue(ex.is_local_tier(".neuroflow\\review\\x.md"))
        self.assertFalse(ex.is_local_tier("sessions/x.md"))


class ConfigTests(unittest.TestCase):
    def test_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            cfg = ex.read_config(root)
            self.assertEqual(cfg["project_name"], "Oddball EEG study")
            self.assertEqual(cfg["raw_roots"], ["sourcedata/"])

    def test_legacy_dialects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".neuroflow" / "project_config.md",
                  "# Project config\n\nproject_name: Legacy one\n**Phase:** data\n")
            cfg = ex.read_config(root)
            self.assertEqual(cfg["project_name"], "Legacy one")
            self.assertEqual(cfg["active_phase"], "data")

    def test_block_list_and_map(self):
        data = ex.parse_frontmatter("---\nfiles:\n  a/b.md: abc123\nroots:\n- x/\n- 'y z/'\nk: v # c\n---\n")
        self.assertEqual(data["files"], {"a/b.md": "abc123"})
        self.assertEqual(data["roots"], ["x/", "y z/"])
        self.assertEqual(data["k"], "v")

    def test_slugify(self):
        self.assertEqual(ex.slugify("Oddball EEG study"), "oddball-eeg-study")
        self.assertEqual(ex.slugify(None), "project")


class PlanAndExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "proj"
        make_project(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_memory_plan_excludes_before_copying(self):
        plan = ex.build_plan(self.root, "memory")
        files = {rel for rel, _ in plan.files}
        held = dict(plan.held_back)
        self.assertIn(".neuroflow/reasoning/general.jsonl", files)
        self.assertIn(".neuroflow/ethics/consent-v2.md", files)
        for rel in (".neuroflow/sessions/2026-10-07.md", ".neuroflow/review/review-x.md",
                    ".neuroflow/integrations.json", ".neuroflow/fails/core.md",
                    ".neuroflow/finance/budget.md", ".neuroflow/ethics/signed-consents.md",
                    ".neuroflow/data-analyze/.env"):
            self.assertNotIn(rel, files)
            self.assertIn(rel, held)

    def test_paper_xray_files_never_exported(self):
        paper = self.root / ".neuroflow" / "paper"
        write(paper / "draft.md", "draft\n")
        xray = ("xray-draft-2026-10-07.md", "xray-draft-2026-10-07.jsonl", "xray-changes-2026-10-07.md")
        for name in xray:
            write(paper / name, "critique of an unpublished manuscript\n")
        for scope, phase in (("memory", None), ("phase", "paper")):
            plan = ex.build_plan(self.root, scope, phase)
            held = dict(plan.held_back)
            self.assertIn(".neuroflow/paper/draft.md", {rel for rel, _ in plan.files})
            for name in xray:
                self.assertEqual(held.get(f".neuroflow/paper/{name}"), ex.LOCAL_REASON, (scope, name))
        dest = self.base / "share.zip"
        code, out = run_main(["--root", str(self.root), "--scope", "memory", "--dest", str(dest), "--json"])
        self.assertEqual(code, 0, out)
        with zipfile.ZipFile(dest) as z:
            names = z.namelist()
        self.assertIn("share/.neuroflow/paper/draft.md", names)
        self.assertFalse(any("xray" in n for n in names))

    def test_phase_plan(self):
        plan = ex.build_plan(self.root, "phase", "data-analyze")
        self.assertEqual({rel for rel, _ in plan.files},
                         {".neuroflow/data-analyze/plan.md", ".neuroflow/project_config.md", ".neuroflow/flow.md"})
        with self.assertRaises(ex.ExportError):
            ex.build_plan(self.root, "phase", "nope")

    def test_no_neuroflow(self):
        with self.assertRaises(ex.ExportError):
            ex.build_plan(self.base, "memory")

    def test_zip_export_verified(self):
        dest = self.base / "out.zip"
        code, out = run_main(["--root", str(self.root), "--scope", "memory", "--dest", str(dest), "--json"])
        self.assertEqual(code, 0, out)
        rep = json.loads(out)
        self.assertTrue(rep["verified"])
        with zipfile.ZipFile(dest) as z:
            names = set(z.namelist())
        self.assertIn("out/.neuroflow/reasoning/general.jsonl", names)
        self.assertFalse(any("sessions" in n or "review" in n or "fails" in n for n in names))

    def test_folder_export(self):
        dest = self.base / "copy"
        code, out = run_main(["--root", str(self.root), "--scope", "memory", "--format", "folder",
                              "--dest", str(dest), "--json"])
        self.assertEqual(code, 0, out)
        self.assertTrue((dest / ".neuroflow" / "flow.md").is_file())
        self.assertFalse((dest / ".neuroflow" / "sessions").exists())

    def test_dry_run_writes_nothing(self):
        dest = self.base / "dry.zip"
        code, out = run_main(["--root", str(self.root), "--scope", "memory", "--dest", str(dest),
                              "--dry-run", "--json"])
        self.assertEqual(code, 0)
        self.assertFalse(dest.exists())
        rep = json.loads(out)
        self.assertTrue(rep["dry_run"])
        self.assertTrue(any(h["path"] == ".neuroflow/review/review-x.md" for h in rep["held_back"]))

    def test_refuses_destination_inside_exported_tree(self):
        code, out = run_main(["--root", str(self.root), "--scope", "memory",
                              "--dest", str(self.root / ".neuroflow" / "x.zip"), "--json"])
        self.assertEqual(code, 2)
        self.assertIn("inside the exported tree", json.loads(out)["error"])

    def test_refuses_existing_destination(self):
        dest = self.base / "exists.zip"
        dest.write_bytes(b"")
        code, _ = run_main(["--root", str(self.root), "--scope", "memory", "--dest", str(dest)])
        self.assertEqual(code, 2)

    def test_include_ethics(self):
        plan = ex.build_plan(self.root, "memory", include_ethics=frozenset({".neuroflow/ethics/signed-consents.md"}))
        self.assertIn(".neuroflow/ethics/signed-consents.md", {rel for rel, _ in plan.files})

    def test_verification_failure_exit_1(self):
        dest = self.base / "bad.zip"
        with mock.patch.object(ex, "write_zip", return_value=["missing from archive: x"]):
            code, _ = run_main(["--root", str(self.root), "--scope", "memory", "--dest", str(dest)])
        self.assertEqual(code, 1)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class ProjectScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        gitconfig = self.base / "gitconfig"
        gitconfig.write_text("", encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.base),
            "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.org",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.org"})
        self.env.start()
        self.root = self.base / "proj"
        make_project(self.root)
        write(self.root / "scripts" / "analysis" / "run.py", "print(1)\n")
        write(self.root / "notes.txt", "untracked\n")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "scripts", ".neuroflow/fails/core.md"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_tracked_plus_memory(self):
        plan = ex.build_plan(self.root, "project")
        files = {rel for rel, _ in plan.files}
        self.assertIn("scripts/analysis/run.py", files)
        self.assertIn(".neuroflow/flow.md", files)
        self.assertNotIn("notes.txt", files)  # not git-tracked
        self.assertIn(".neuroflow/fails/core.md", dict(plan.held_back))  # tracked but never exported

    def test_project_default_dest_is_outside_the_tree(self):
        plan = ex.build_plan(self.root, "project")
        dest = ex.default_dest(plan, "zip", "Oddball", "2026-10-07")
        self.assertEqual(dest.parent, self.root.parent)
        ex.check_dest(dest, plan, "zip")
        with self.assertRaises(ex.ExportError):
            ex.check_dest(self.root / "x.zip", plan, "zip")

    def test_project_scope_without_git(self):
        other = self.base / "nogit"
        make_project(other)
        with self.assertRaises(ex.ExportError):
            ex.build_plan(other, "project")


if __name__ == "__main__":
    unittest.main()
