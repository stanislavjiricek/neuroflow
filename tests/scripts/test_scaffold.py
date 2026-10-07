"""Tests for skills/neuroflow-core/scripts/scaffold.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "neuroflow-core" / "scripts" / "scaffold.py"
CORE_SKILL = REPO / "skills" / "neuroflow-core" / "SKILL.md"

spec = importlib.util.spec_from_file_location("nf_scaffold_under_test", SCRIPT)
scaffold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaffold)


def run(*args: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = scaffold.main([*args, "--json"])
    return code, json.loads(out.getvalue())


class ScaffoldTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.project = self.home / "studies" / "oddball"
        self.project.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def scaffold(self, *extra: str, root: Path | None = None) -> tuple[int, dict]:
        return run("--root", str(root or self.project), "--home", str(self.home),
                   "--plugin-version", "9.9.9", *extra)

    def test_creates_the_full_tree(self) -> None:
        code, report = self.scaffold("--project-name", "Oddball EEG")
        self.assertEqual(code, 0, report)
        nf = self.project / ".neuroflow"
        for rel in ("flow.md", "sessions/.gitkeep", "tasks/.gitkeep", "reasoning/flow.md",
                    "reasoning/general.jsonl", "wiki/index.md", "wiki/log.md", "wiki/schema.md",
                    "wiki/raw/.gitkeep", "wiki/pages/methods/.gitkeep"):
            self.assertTrue((nf / rel).is_file(), rel)
        self.assertFalse((nf / "tasks" / "inbox").exists(), "tasks/ is one folder; status lives in each task file")
        self.assertEqual((nf / "reasoning" / "general.jsonl").read_text(encoding="utf-8"), "")
        config = (nf / "project_config.md").read_text(encoding="utf-8")
        self.assertTrue(config.startswith(
            "---\nnf_schema: 1\nproject_name: Oddball EEG\nactive_phase: setup\nrecommended_phases: []\n"))
        self.assertIn("plugin_version: 9.9.9", config)
        self.assertNotIn("auto_issue_reporting", config, "consent is personal and never goes in the project file")
        attrs = (self.project / ".gitattributes").read_text(encoding="utf-8").splitlines()
        self.assertTrue(set(scaffold.GITATTRIBUTES_LINES) <= set(attrs))
        ignore = (self.project / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertTrue(set(scaffold.GITIGNORE_LINES) <= set(ignore))
        self.assertEqual((self.project / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"), scaffold.CLAUDE_BLOCK)

    def test_idempotent(self) -> None:
        self.scaffold()
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        code, report = self.scaffold()
        self.assertEqual(code, 0)
        self.assertEqual(report["created"], [])
        self.assertEqual(report["appended"], {})
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_never_overwrites_and_appends_missing_lines(self) -> None:
        (self.project / ".gitignore").write_text("node_modules/\n.neuroflow/sessions/\n", encoding="utf-8")
        nf = self.project / ".neuroflow"
        nf.mkdir()
        mine = "---\nnf_schema: 1\nproject_name: Mine\nactive_phase: paper\n---\n\nMy notes.\n"
        (nf / "project_config.md").write_text(mine, encoding="utf-8")
        claude = self.project / ".claude" / "CLAUDE.md"
        claude.parent.mkdir()
        claude.write_text("# Team rules\n\nBe kind.", encoding="utf-8")
        code, report = self.scaffold()
        self.assertEqual(code, 0, report)
        self.assertEqual((nf / "project_config.md").read_text(encoding="utf-8"), mine)
        ignore = (self.project / ".gitignore").read_text(encoding="utf-8")
        self.assertTrue(ignore.startswith("node_modules/\n.neuroflow/sessions/\n"))
        self.assertEqual(ignore.count(".neuroflow/sessions/"), 1)
        self.assertEqual(report["appended"][".gitignore"], len(scaffold.GITIGNORE_LINES) - 1)
        text = claude.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Team rules\n\nBe kind.\n"))
        self.assertTrue(text.endswith(scaffold.CLAUDE_BLOCK))

    def test_dry_run_writes_nothing(self) -> None:
        code, report = self.scaffold("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn(".neuroflow/project_config.md", report["created"])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_refuses_home_and_nested_projects(self) -> None:
        code, report = self.scaffold(root=self.home)
        self.assertEqual(code, 2)
        self.assertIn("home directory", report["errors"][0])
        self.scaffold()
        sub = self.project / "analysis"
        sub.mkdir()
        code, report = self.scaffold(root=sub)
        self.assertEqual(code, 2)
        self.assertFalse((sub / ".neuroflow").exists())

    def test_git_root_ends_the_walk_up(self) -> None:
        self.scaffold()
        inner = self.project / "vendor" / "toolbox"
        (inner / ".git").mkdir(parents=True)
        code, report = self.scaffold(root=inner)
        self.assertEqual(code, 0, report)
        self.assertTrue((inner / ".neuroflow" / "project_config.md").is_file())

    def test_home_neuroflow_is_not_a_project(self) -> None:
        (self.home / ".neuroflow").mkdir()
        (self.home / ".neuroflow" / "user.yaml").write_text("flowie_handle: alice\n", encoding="utf-8")
        self.assertIsNone(scaffold.find_project_root(self.project, self.home))
        code, _ = self.scaffold()
        self.assertEqual(code, 0)

    def test_legacy_config_is_left_alone_and_flagged(self) -> None:
        nf = self.project / ".neuroflow"
        nf.mkdir()
        legacy = "# Project config\n\n**Phase:** paper\n"
        (nf / "project_config.md").write_text(legacy, encoding="utf-8")
        code, report = self.scaffold()
        self.assertEqual(code, 1)
        self.assertIn("migrate", report["notes"][0])
        self.assertEqual((nf / "project_config.md").read_text(encoding="utf-8"), legacy)

    def test_newer_schema_refuses_without_writing(self) -> None:
        nf = self.project / ".neuroflow"
        nf.mkdir()
        (nf / "project_config.md").write_text("---\nnf_schema: 2\n---\n", encoding="utf-8")
        code, report = self.scaffold()
        self.assertEqual(code, 2)
        self.assertEqual(sorted(p.name for p in self.project.rglob("*")), [".neuroflow", "project_config.md"])

    def test_stale_block_is_flagged_not_rewritten(self) -> None:
        claude = self.project / ".claude" / "CLAUDE.md"
        claude.parent.mkdir()
        stale = "## neuroflow\n\n- Active phase: ideation\n- Config: `.neuroflow/project_config.md`\n"
        claude.write_text(stale, encoding="utf-8")
        code, report = self.scaffold()
        self.assertEqual(code, 1)
        self.assertEqual(claude.read_text(encoding="utf-8"), stale)

    def test_crlf_files_keep_crlf(self) -> None:
        with open(self.project / ".gitignore", "w", encoding="utf-8", newline="") as fh:
            fh.write("node_modules/\r\n")
        self.scaffold()
        raw = (self.project / ".gitignore").read_bytes()
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_contract_text_matches_neuroflow_core(self) -> None:
        skill = CORE_SKILL.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.search(r"### Project instruction block.*?```markdown\n(.*?)```", skill, re.DOTALL)
        self.assertIsNotNone(m, "neuroflow-core must show the block under '### Project instruction block'")
        self.assertEqual(m.group(1), scaffold.CLAUDE_BLOCK)
        for line in scaffold.GITATTRIBUTES_LINES + scaffold.GITIGNORE_LINES:
            self.assertIn(line, skill)

    def test_main_rejects_bad_arguments(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(scaffold.main(["--no-such-flag"]), 2)


if __name__ == "__main__":
    unittest.main()
