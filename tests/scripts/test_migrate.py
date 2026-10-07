"""Tests for skills/neuroflow-core/scripts/migrate.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "neuroflow-core" / "scripts" / "migrate.py"

spec = importlib.util.spec_from_file_location("nf_migrate_under_test", SCRIPT)
migrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate)

STALE_BLOCK = (
    "## neuroflow\n\nThis project uses the neuroflow workflow. Project memory is in `.neuroflow/`.\n\n"
    "- Active phase: ideation\n- Config: `.neuroflow/project_config.md`\n"
)

KEY_VALUE_CONFIG = """# Project config

project_name: Oddball EEG study
institution: University of Example
active_phase: data analyze
plugin_version: 0.2.10
auto_issue_reporting: yes
writing_style: plain, active voice
default_mode: Critic
recommended_phases: [ideation, data, data-analyze, paper]
**Target journal:** `eLife`
collaborators:
  - name: Alice Example
    email: alice@example.org
    handle: alice

## Output paths

| Phase | Path |
|---|---|
| data-analyze | scripts/analysis/ |
"""

BOLD_CONFIG = """# Example project config

**Project:** Example plugin
**Plugin version:** 0.2.21
**Phase:** active development
**Repo:** https://example.org/repo

## Description

Some notes.
"""


class MigrateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.project = self.home / "studies" / "oddball"
        (self.project / ".git").mkdir(parents=True)
        self.nf = self.project / ".neuroflow"
        (self.nf / "reasoning").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel: str, text: str, base: Path | None = None) -> Path:
        path = (base or self.project) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def read(self, rel: str, base: Path | None = None) -> str:
        with open((base or self.project) / rel, encoding="utf-8", newline="") as fh:
            return fh.read()

    def migrate(self, *extra: str, root: Path | None = None) -> tuple[int, dict]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(["--root", str(root or self.project), "--home", str(self.home),
                                 "--plugin-version", "9.9.9", "--json", *extra])
        return code, json.loads(out.getvalue())

    # -- project_config.md ---------------------------------------------------

    def test_key_value_dialect_becomes_frontmatter(self) -> None:
        self.write(".neuroflow/project_config.md", KEY_VALUE_CONFIG)
        code, result = self.migrate("--apply", "--move-personal")
        self.assertEqual(result["blocking"], [])
        self.assertTrue(result["applied"])
        config = self.read(".neuroflow/project_config.md")
        front, body = config.split("\n---\n", 1)
        self.assertEqual(front.splitlines()[:7], [
            "---", "nf_schema: 1", "project_name: Oddball EEG study", "active_phase: data-analyze",
            "default_mode: critic", "target_journal: eLife",
            "recommended_phases: [ideation, data, data-analyze, paper]"])
        self.assertIn("collaborators:\n  - name: Alice Example\n    email: alice@example.org\n    handle: alice", front)
        self.assertIn("plugin_version: 9.9.9", front)
        self.assertIn("institution: University of Example", body)
        self.assertIn("## Output paths", body)
        for gone in ("auto_issue_reporting", "writing_style", "active_phase", "**Target journal:**"):
            self.assertNotIn(gone, body)
        user = self.read(".neuroflow/user.yaml", base=self.home)
        self.assertIn("auto_issue_reporting: yes", user)
        self.assertIn("writing_style: plain, active voice", user)

    def test_bold_dialect_with_unknown_phase_blocks_until_set(self) -> None:
        self.write(".neuroflow/project_config.md", BOLD_CONFIG)
        code, result = self.migrate("--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        self.assertEqual(result["dialect"], "bold labels")
        self.assertIn("active development", result["blocking"][0])
        self.assertEqual(self.read(".neuroflow/project_config.md"), BOLD_CONFIG)
        self.assertFalse((self.project / ".gitattributes").exists(), "nothing is written while a decision is open")

        code, result = self.migrate("--apply", "--set", "active_phase=paper")
        self.assertTrue(result["applied"])
        self.assertEqual(code, 0, result)
        config = self.read(".neuroflow/project_config.md")
        self.assertTrue(config.startswith("---\nnf_schema: 1\nproject_name: Example plugin\nactive_phase: paper\n"))
        self.assertIn("**Repo:** https://example.org/repo", config)
        self.assertNotIn("**Phase:**", config)

    def test_idempotent(self) -> None:
        self.write(".neuroflow/project_config.md", KEY_VALUE_CONFIG)
        self.write(".neuroflow/reasoning/general.json", '[{"statement": "a", "source": "s", "reasoning": "r"}]')
        self.migrate("--apply", "--move-personal")
        snapshot = {p: p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        code, result = self.migrate("--apply", "--move-personal")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["changes"], [])
        self.assertEqual(snapshot, {p: p.read_bytes() for p in self.home.rglob("*") if p.is_file()})

    def test_personal_fields_stay_without_consent(self) -> None:
        self.write(".neuroflow/project_config.md", KEY_VALUE_CONFIG)
        code, result = self.migrate("--apply")
        self.assertEqual(code, 1)
        self.assertTrue(result["personal_pending"])
        self.assertIn("auto_issue_reporting: yes", self.read(".neuroflow/project_config.md"))
        self.assertFalse((self.home / ".neuroflow" / "user.yaml").exists())

    def test_existing_user_value_is_never_overwritten(self) -> None:
        self.write(".neuroflow/project_config.md", KEY_VALUE_CONFIG)
        self.write(".neuroflow/user.yaml", "flowie_handle: alice\nauto_issue_reporting: no\n", base=self.home)
        self.migrate("--apply", "--move-personal")
        user = self.read(".neuroflow/user.yaml", base=self.home)
        self.assertIn("auto_issue_reporting: no", user)
        self.assertNotIn("auto_issue_reporting: yes", user)
        self.assertTrue(user.startswith("flowie_handle: alice\n"))

    def test_frontmatter_without_schema_keeps_its_lines(self) -> None:
        self.write(".neuroflow/project_config.md",
                   "---\nproject_name: X   # team name\nactive_phase: data\ncustom_key: kept\n---\n\nNotes.\n")
        code, result = self.migrate("--apply")
        config = self.read(".neuroflow/project_config.md")
        self.assertTrue(config.startswith("---\nnf_schema: 1\nproject_name: X   # team name\n"))
        self.assertIn("custom_key: kept", config)
        self.assertIn("plugin_version: 9.9.9", config)
        self.assertTrue(config.endswith("---\n\nNotes.\n"))

    def test_missing_contract_keys_are_added_once(self) -> None:
        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: paper\n---\n\nNotes.\n")
        code, result = self.migrate("--apply")
        config = self.read(".neuroflow/project_config.md")
        self.assertIn("project_name: oddball\n", config)
        self.assertIn("recommended_phases: []\n", config)
        self.assertIn("plugin_version: 9.9.9\n", config)
        code, result = self.migrate("--apply")
        self.assertEqual(result["changes"], [])
        self.assertEqual(code, 0, result)

    def test_ethics_flag_and_legacy_ethics_status(self) -> None:
        self.write(".neuroflow/project_config.md", "# cfg\n\nactive_phase: data\nethics: not-applicable\n")
        status = "# Ethics status\n\n| Item | Value |\n|---|---|\n| Status | approved |\n| Expires | 2027-06-30 |\n"
        self.write(".neuroflow/ethics/status.md", status)
        code, result = self.migrate("--apply")
        self.assertIn("ethics: not-applicable", self.read(".neuroflow/project_config.md").split("\n---\n")[0])
        self.assertEqual(self.read(".neuroflow/ethics/status.md"), status, "approval values need a person")
        self.assertTrue(any("/ethics" in item["message"] for item in result["report"]))
        self.assertEqual(code, 1)

    def test_leading_rule_is_not_frontmatter(self) -> None:
        self.write(".neuroflow/project_config.md", "---\n# Project config\n---\n\n**Phase:** paper\n")
        code, result = self.migrate()
        self.assertEqual(result["dialect"], "bold labels")
        self.assertEqual(result["blocking"], [])

    def test_newer_schema_is_refused(self) -> None:
        original = "---\nnf_schema: 2\nactive_phase: paper\n---\n"
        self.write(".neuroflow/project_config.md", original)
        self.write(".neuroflow/reasoning/general.json", "[]")
        code, result = self.migrate("--apply")
        self.assertEqual(code, 2)
        self.assertIn("newer", result["error"])
        self.assertEqual(self.read(".neuroflow/project_config.md"), original)
        self.assertTrue((self.nf / "reasoning" / "general.json").exists())

    def test_no_project_found(self) -> None:
        elsewhere = self.home / "empty"
        (elsewhere / ".git").mkdir(parents=True)
        code, result = self.migrate(root=elsewhere)
        self.assertEqual(code, 2)
        self.assertIn("no .neuroflow/project_config.md", result["error"])

    def test_bad_set_is_a_usage_error(self) -> None:
        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: paper\n---\n")
        self.assertEqual(self.migrate("--set", "active_phase=writing")[0], 2)
        self.assertEqual(self.migrate("--set", "nf_schema=3")[0], 2)

    def test_crlf_is_preserved(self) -> None:
        self.write(".neuroflow/project_config.md", "# cfg\r\n\r\n**Phase:** paper\r\n\r\nNotes.\r\n")
        self.migrate("--apply")
        raw = self.read(".neuroflow/project_config.md")
        self.assertTrue(raw.startswith("---\r\nnf_schema: 1\r\n"))
        self.assertNotIn("\n", raw.replace("\r\n", ""))

    # -- reasoning logs ------------------------------------------------------

    def test_reasoning_arrays_become_jsonl(self) -> None:
        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: paper\n---\n")
        entries = [{"statement": "Use FDR", "source": "command:data-analyze | 2026-01-01", "reasoning": "r"},
                   {"statement": "Average reference", "source": "x", "reasoning": "y"}]
        self.write(".neuroflow/reasoning/general.json", json.dumps(entries, indent=2))
        self.write(".neuroflow/reasoning/paper.json", "[]")
        self.write(".neuroflow/reasoning/data.jsonl", json.dumps(entries[0]) + "\n")
        self.write(".neuroflow/reasoning/data.json", json.dumps(entries))
        self.write(".neuroflow/reasoning/flow.md",
                   "| File / Folder | Description | Last changed |\n|---|---|---|\n"
                   "| general.json | Project log. | 2026-01-01 |\n")
        code, result = self.migrate("--apply")
        self.assertTrue(result["applied"])
        lines = self.read(".neuroflow/reasoning/general.jsonl").splitlines()
        self.assertEqual([json.loads(x) for x in lines], entries)
        self.assertEqual(self.read(".neuroflow/reasoning/paper.jsonl"), "")
        self.assertEqual(len(self.read(".neuroflow/reasoning/data.jsonl").splitlines()), 2, "duplicates are skipped")
        for name in ("general", "paper", "data"):
            self.assertFalse((self.nf / "reasoning" / f"{name}.json").exists())
            self.assertTrue((self.nf / "reasoning" / f"{name}.json.bak").exists())
        index = self.read(".neuroflow/reasoning/flow.md")
        for row in ("| general.jsonl |", "| general.json.bak |", "| paper.jsonl |", "| data.json.bak |"):
            self.assertIn(row, index, "every file in reasoning/ stays indexed")

    def test_invalid_reasoning_json_blocks(self) -> None:
        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: paper\n---\n")
        self.write(".neuroflow/reasoning/general.json", '[{"statement": "a"}\n<<<<<<< HEAD\n')
        code, result = self.migrate("--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        self.assertTrue(any("general.json" in item for item in result["blocking"]))

    # -- git files and instruction blocks -------------------------------------

    def test_git_lines_and_blocks(self) -> None:
        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: paper\n---\n")
        self.write(".gitignore", "node_modules/\n")
        self.write(".claude/CLAUDE.md", "# Rules\n\n" + STALE_BLOCK + "\n## Other\n\nkeep me\n")
        self.write("AGENTS.md", "# Agents\n\n" + STALE_BLOCK)
        self.write(".github/copilot-instructions.md", STALE_BLOCK)
        global_claude = self.write(".claude/CLAUDE.md", "# Mine\n\n" + STALE_BLOCK, base=self.home)
        code, result = self.migrate("--apply")
        self.assertEqual(code, 1, "report-only items remain")
        attrs = self.read(".gitattributes").splitlines()
        self.assertTrue(set(migrate.sc.GITATTRIBUTES_LINES) <= set(attrs))
        ignore = self.read(".gitignore")
        self.assertTrue(ignore.startswith("node_modules/\n"))
        self.assertTrue(set(migrate.sc.GITIGNORE_LINES) <= set(ignore.splitlines()))
        claude = self.read(".claude/CLAUDE.md")
        self.assertIn(migrate.sc.CLAUDE_BLOCK, claude)
        self.assertNotIn("Active phase", claude)
        self.assertTrue(claude.startswith("# Rules\n\n") and claude.endswith("## Other\n\nkeep me\n"))
        reported = sorted(Path(item["path"]).name for item in result["report"])
        self.assertEqual(reported, ["AGENTS.md", "CLAUDE.md", "copilot-instructions.md"])
        with open(global_claude, encoding="utf-8") as fh:
            self.assertIn("Active phase", fh.read(), "files outside the project are only reported")
        self.assertIn("Active phase", self.read("AGENTS.md"))

    def test_canonical_phases_come_from_core(self) -> None:
        phases = migrate.canonical_phases()
        self.assertIn("data-analyze", phases)
        self.assertIn("setup", phases)
        self.assertNotIn("utility", phases)


if __name__ == "__main__":
    unittest.main()
