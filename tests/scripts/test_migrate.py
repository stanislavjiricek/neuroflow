"""Tests for skills/neuroflow-core/scripts/migrate.py (stdlib unittest, no network)."""

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
from datetime import date
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "neuroflow-core" / "scripts" / "migrate.py"

spec = importlib.util.spec_from_file_location("nf_migrate_under_test", SCRIPT)
migrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate)


def run_git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "user.name=Test", "-c", "user.email=test@example.org",
                           "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout

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

    def test_zotero_answer_is_personal(self) -> None:
        self.write(".neuroflow/project_config.md", "# cfg\n\nactive_phase: ideation\nzotero: Yes\n")
        code, result = self.migrate()
        self.assertTrue(result["personal_pending"], "moved only after the person agrees")
        self.assertEqual([item["target"] for item in result["personal"]], ["zotero"])
        self.migrate("--apply", "--move-personal")
        self.assertNotIn("zotero", self.read(".neuroflow/project_config.md"))
        self.assertIn("zotero: yes\n", self.read(".neuroflow/user.yaml", base=self.home))

        self.write(".neuroflow/project_config.md", "---\nnf_schema: 1\nactive_phase: ideation\nzotero: no\n---\n")
        code, result = self.migrate("--apply", "--move-personal")
        self.assertNotIn("zotero", self.read(".neuroflow/project_config.md"))
        self.assertEqual(result["personal"][0]["status"], "user.yaml keeps its own value 'yes'; the project value is dropped")

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

    # -- plugin_version: the version the project was last brought up to date to ----

    def run_version(self, running: str, *extra: str) -> tuple[int, dict]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(["--root", str(self.project), "--home", str(self.home),
                                 "--plugin-version", running, "--json", *extra])
        return code, json.loads(out.getvalue())

    def test_versions_compare_number_by_number(self) -> None:
        self.assertTrue(migrate.is_older("0.2.9", "0.2.10"))
        self.assertFalse(migrate.is_older("0.2.10", "0.2.9"))
        self.assertTrue(migrate.is_older("0.2.21", "0.2.22"))
        self.assertFalse(migrate.is_older("0.2", "0.2.0"))
        self.assertFalse(migrate.is_older("0.2.22", "0.2.22"))

    def test_an_older_project_records_the_running_version(self) -> None:
        config = ("---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: paper\nrecommended_phases: []\n"
                  "plugin_version: 0.2.9\n---\n\nNotes.\n")
        self.write(".neuroflow/project_config.md", config)
        self.run_version("0.2.9", "--apply")  # everything else current
        self.assertEqual(self.read(".neuroflow/project_config.md"), config)

        code, result = self.run_version("0.2.10")  # a plugin update arrived
        self.assertEqual(code, 1)
        self.assertEqual([c["path"] for c in result["changes"]], [".neuroflow/project_config.md"])
        self.assertEqual(result["changes"][0]["summary"],
                         "record neuroflow 0.2.10 as the version the project is up to date with (was 0.2.9)")
        self.assertEqual(self.read(".neuroflow/project_config.md"), config, "a dry run writes nothing")

        code, result = self.run_version("0.2.10", "--apply")
        self.assertEqual(code, 0, result)
        self.assertEqual(self.read(".neuroflow/project_config.md"), config.replace("0.2.9", "0.2.10"))
        self.assertEqual(self.run_version("0.2.10")[1]["changes"], [], "a second run finds nothing to do")
        code, result = self.run_version("0.2.9")
        self.assertEqual((code, result["changes"]), (0, []), "a newer recorded version is never lowered")

    def test_a_newer_recorded_version_stays_while_other_changes_are_written(self) -> None:
        # A teammate on a newer neuroflow migrated the project; this older plugin still finds a key to add.
        config = "---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: paper\nplugin_version: 0.3.0\n---\n\nNotes.\n"
        self.write(".neuroflow/project_config.md", config)
        code, result = self.run_version("0.2.22", "--apply")
        self.assertTrue(result["applied"])
        change = next(c for c in result["changes"] if c["path"] == ".neuroflow/project_config.md")
        self.assertEqual(change["summary"], "update the frontmatter")
        self.assertEqual(self.read(".neuroflow/project_config.md"),
                         config.replace("plugin_version: 0.3.0\n", "recommended_phases: []\nplugin_version: 0.3.0\n"),
                         "the pending key is added; the newer version is never lowered")
        self.assertEqual(self.run_version("0.2.22")[1]["changes"], [], "nothing is left to do")

        legacy = "# cfg\n\n**Plugin version:** 0.3.0\n**Phase:** paper\n"  # the same in a legacy dialect
        self.write(".neuroflow/project_config.md", legacy)
        self.run_version("0.2.22", "--apply")
        converted = self.read(".neuroflow/project_config.md")
        self.assertIn("plugin_version: 0.3.0\n", converted)
        self.assertNotIn("0.2.22", converted)

    def test_a_missing_plugin_version_is_recorded(self) -> None:
        self.write(".neuroflow/project_config.md",
                   "---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: paper\nrecommended_phases: []\n---\n")
        code, result = self.run_version("0.2.22")
        change = next(c for c in result["changes"] if c["path"] == ".neuroflow/project_config.md")
        self.assertIn("(was not recorded)", change["summary"])
        self.run_version("0.2.22", "--apply")
        self.assertIn("plugin_version: 0.2.22\n", self.read(".neuroflow/project_config.md"))

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

    def test_a_project_file_that_is_not_utf8_blocks_and_is_never_rewritten(self) -> None:
        config = self.nf / "project_config.md"
        data = ("# Project config\n\n**Project:** Oddball\n**Active phase:** ideation\n"
                "Instituce: Příklad, oddělení řízení.\n").encode("cp1250")
        config.write_bytes(data)
        code, result = self.migrate("--apply")
        self.assertFalse(result["applied"])
        self.assertTrue(any("is not UTF-8" in item for item in result["blocking"]), result["blocking"])
        self.assertEqual(config.read_bytes(), data, "never rewritten")
        self.assertFalse((self.project / ".gitignore").exists(), "nothing is written while it blocks")

    def test_a_current_instruction_block_in_another_encoding_blocks_nothing(self) -> None:
        self.write(".neuroflow/project_config.md", "active_phase: data\n")
        claude = self.project / ".claude" / "CLAUDE.md"
        claude.parent.mkdir(parents=True, exist_ok=True)
        data = "# Poznámky k projektu\n\n".encode("cp1250") + migrate.sc.CLAUDE_BLOCK.encode("utf-8")
        claude.write_bytes(data)
        code, result = self.migrate("--apply")
        self.assertEqual(result["blocking"], [])
        self.assertTrue(result["applied"])
        self.assertIn("nf_schema: 1", self.read(".neuroflow/project_config.md"))
        self.assertEqual(claude.read_bytes(), data, "nothing to change there, so it is never rewritten")

    def test_project_config_is_written_last(self) -> None:
        # It records plugin_version: a run that stops part-way must leave the version notice in place.
        self.write(".neuroflow/project_config.md", KEY_VALUE_CONFIG)
        written: list[str] = []
        real = migrate.sc.write_text

        def record(path, text, newline="\n"):
            written.append(Path(path).name)
            real(path, text, newline)

        with mock.patch.object(migrate.sc, "write_text", record):
            code, result = self.migrate("--apply", "--move-personal")
        self.assertTrue(result["applied"])
        self.assertGreater(len(written), 2)
        self.assertEqual(written[-1], "project_config.md")

    def test_output_survives_a_legacy_code_page(self) -> None:
        # A Windows pipe defaults to the ANSI code page; the plan and its paths must reach the model whole.
        project = self.home / "studies" / "ü-日本"
        (project / ".git").mkdir(parents=True)
        self.write(".neuroflow/project_config.md",
                   "# Project config\n\n**Project:** Oddball\n**Active phase:** ideation\n"
                   "**Recommended phases:** ideation → data → paper\n", base=project)
        env = dict(os.environ, PYTHONIOENCODING="cp1250")
        for extra in ([], ["--json"]):
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(project), "--home", str(self.home),
                 "--plugin-version", "9.9.9", *extra],
                capture_output=True, env=env, timeout=60)
            self.assertEqual(proc.stderr.decode("utf-8", "replace"), "", "a traceback's exit 1 is not a finding")
            self.assertEqual(proc.returncode, 1)
            out = proc.stdout.decode("utf-8")
            self.assertIn("日本", json.loads(out)["root"] if extra else out)


class FlowieHiveTest(unittest.TestCase):
    """--flowie, --hive NAME and --hives: task files, local-only files, git staging (never a commit)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.home = Path(self._tmp.name) / "home"
        self.flowie = self.home / ".neuroflow" / "flowie"
        self.hives = self.home / ".neuroflow" / "hives"
        self.today = date.today().isoformat()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    def read(self, path: Path) -> str:
        with open(path, encoding="utf-8", newline="") as fh:
            return fh.read()

    def repo(self, folder: Path) -> None:
        run_git(folder, "init", "-q")
        run_git(folder, "add", "-A")
        run_git(folder, "commit", "-q", "-m", "init")

    def levels(self, *args: str, as_json: bool = True) -> tuple[int, dict | str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(["--home", str(self.home), *(["--json"] if as_json else []), *args])
        return code, json.loads(out.getvalue()) if as_json else out.getvalue()

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_flowie_tasks_move_into_their_column_folders(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-014-re-run-ica.md",
                   "---\nid: t-014\ntitle: Re-run ICA on sub-07\nstatus: active          # inbox | active | review | done"
                   " | archived\ncreated: 2026-08-13\nassignee: \"@jana\"\nproject: Oddball EEG\n---\n\nNotes stay.\n")
        self.write(tasks / "t-015-old-thing.md", "---\nid: t-015\ntitle: Old thing\nstatus: archived\ncreated: 2026-01-01\n---\n")
        self.write(tasks / "active" / "spin-tests.md",
                   "---\ntitle: Spin tests\nlevel: flowie\nresponsible: \"@stan\"\ncreated: 2026-04-01\n---\n\n## Context\n")
        current = "---\ntitle: Another task\nstatus: active\ncreated: 2026-04-01\nupdated: 2026-04-02\n---\n"
        self.write(tasks / "active" / "re-run-ica.md", current)
        self.write(self.flowie / ".gitignore", ".DS_Store\n")
        self.repo(self.flowie)
        self.write(self.flowie / "integrations.json", "{}\n")  # local and untracked, as it should be

        code, text = self.levels("--flowie", as_json=False)
        self.assertEqual(code, 1)
        self.assertIn("tasks/t-014-re-run-ica.md -> tasks/active/re-run-ica-2.md", text)
        code, result = self.levels("--flowie")
        self.assertEqual(code, 1)
        self.assertEqual({c["path"]: c.get("to") for c in result["levels"][0]["changes"]}, {
            "tasks/active/spin-tests.md": None,
            "tasks/t-014-re-run-ica.md": "tasks/active/re-run-ica-2.md",  # the slug is taken in a column: -2
            "tasks/t-015-old-thing.md": "tasks/archive/old-thing.md",  # archived = archive
            ".gitignore": None,
        })
        self.assertTrue((tasks / "t-014-re-run-ica.md").exists(), "a dry run writes nothing")

        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 0, result)
        self.assertEqual(self.read(tasks / "active" / "re-run-ica-2.md"),
                         "---\ntitle: Re-run ICA on sub-07\nstatus: active\ncreated: 2026-08-13\n"
                         f"updated: {self.today}\nowner: jana\nproject: Oddball EEG\n---\n\nNotes stay.\n")
        self.assertEqual(self.read(tasks / "active" / "spin-tests.md"),
                         "---\ntitle: Spin tests\nstatus: active\nowner: stan\ncreated: 2026-04-01\n"
                         f"updated: {self.today}\n---\n\n## Context\n")
        self.assertIn("status: archive\n", self.read(tasks / "archive" / "old-thing.md"))
        self.assertEqual(self.read(tasks / "active" / "re-run-ica.md"), current, "a current task is left alone")
        self.assertEqual(self.read(self.flowie / ".gitignore"),
                         ".DS_Store\n\n# neuroflow: settings that stay on this machine, never synced\nintegrations.json\n")

        tracked = run_git(self.flowie, "ls-files").split()
        self.assertNotIn("tasks/t-014-re-run-ica.md", tracked, "git mv: the move is staged")
        self.assertIn("tasks/active/re-run-ica-2.md", tracked)
        self.assertNotIn("integrations.json", tracked)
        self.assertEqual(run_git(self.flowie, "rev-list", "--count", "HEAD").strip(), "1", "it never commits")
        paths = result["levels"][0]["commit_paths"]
        self.assertEqual(paths, ["tasks/active/spin-tests.md", "tasks/t-014-re-run-ica.md", "tasks/active/re-run-ica-2.md",
                                 "tasks/t-015-old-thing.md", "tasks/archive/old-thing.md", ".gitignore"])
        run_git(self.flowie, "commit", "-q", "-m", "migrate", "--", *paths)  # the prose's commit by path
        self.assertEqual(run_git(self.flowie, "status", "--porcelain"), "")

        code, result = self.levels("--flowie")
        self.assertEqual((code, result["levels"][0]["changes"]), (0, []), "a second run finds nothing to do")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_tracked_integrations_file_is_reported_not_untracked(self) -> None:
        self.write(self.flowie / "profile.md", "# Research Profile\n")
        self.write(self.flowie / "integrations.json", '{"custom_llm": {"model": "m"}}\n')
        self.repo(self.flowie)
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1, "the tracked file stays a finding until the person acts")
        level = result["levels"][0]
        self.assertEqual([item["path"] for item in level["report"]], ["integrations.json"])
        self.assertIn("rm --cached integrations.json", level["report"][0]["message"])
        self.assertIn("integrations.json", run_git(self.flowie, "ls-files").split())
        self.assertEqual(self.read(self.flowie / ".gitignore"),
                         "# neuroflow: settings that stay on this machine, never synced\nintegrations.json\n")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_hive_keeps_sync_json_local_and_gets_current_tasks(self) -> None:
        hive = self.hives / "example-lab-hive"
        self.write(hive / "hive.md", "# Example Lab\n")
        self.write(hive / "sync.json", '{"member_handle": "alice"}\n')
        self.write(hive / "tasks" / "inbox" / "shared-pipeline.md",
                   "---\ntitle: Shared pipeline\nlevel: hive\nassignee: li\ncreated: 2026-09-01\n---\n")
        self.repo(hive)
        code, result = self.levels("--hive", "example-lab-hive")
        self.assertEqual(code, 1)
        level = result["levels"][0]
        self.assertEqual((level["level"], level["name"]), ("hive", "example-lab-hive"))
        self.assertEqual([c["path"] for c in level["changes"]], ["tasks/inbox/shared-pipeline.md", ".gitignore"])
        self.assertEqual([item["path"] for item in level["report"]], ["sync.json"])

        code, result = self.levels("--hive", "example-lab-hive", "--apply")
        self.assertEqual(code, 1, "sync.json is still tracked: agreeing on that is the team's call")
        self.assertEqual(self.read(hive / "tasks" / "inbox" / "shared-pipeline.md"),
                         f"---\ntitle: Shared pipeline\nstatus: inbox\nowner: li\ncreated: 2026-09-01\nupdated: {self.today}\n---\n")
        self.assertIn("sync.json", self.read(hive / ".gitignore").splitlines())
        self.assertEqual(result["levels"][0]["commit_paths"], ["tasks/inbox/shared-pipeline.md", ".gitignore"])
        self.assertEqual(run_git(hive, "rev-list", "--count", "HEAD").strip(), "1", "never commits, never pushes")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_hives_checks_every_cached_hive(self) -> None:
        for name in ("lab-a", "lab-b"):
            self.write(self.hives / name / "tasks" / "t-1-plan.md", "---\nid: t-1\ntitle: Plan\nstatus: review\n---\n")
        self.write(self.hives / "lab-a" / ".gitignore", "sync.json\n")
        self.repo(self.hives / "lab-a")  # lab-b is an older cache of copied files, not a clone
        code, result = self.levels("--hives", "--apply")
        self.assertEqual(code, 1, "lab-b stays a finding until /hive --init replaces it")
        self.assertTrue(result["applied"])
        self.assertEqual([level["name"] for level in result["levels"]], ["lab-a", "lab-b"])
        self.assertTrue((self.hives / "lab-a" / "tasks" / "review" / "plan.md").is_file())
        self.assertFalse((self.hives / "lab-a" / "tasks" / "t-1-plan.md").exists())
        self.assertEqual(result["levels"][0]["commit_paths"], ["tasks/t-1-plan.md", "tasks/review/plan.md"])
        lab_b = result["levels"][1]
        self.assertEqual((lab_b["changes"], lab_b["commit_paths"]), ([], []))
        self.assertEqual([item["message"] for item in lab_b["report"]],
                         ["not a git clone — /hive --init replaces it with a clone"])
        self.assertTrue((self.hives / "lab-b" / "tasks" / "t-1-plan.md").exists(), "the copied files stay as they are")
        self.assertFalse((self.hives / "lab-b" / "tasks" / "review").exists())

    def test_a_hive_cache_without_git_is_reported_never_written(self) -> None:
        cache = self.hives / "old-lab"  # copied files from an older /hive --init: no .git/
        legacy = "---\nid: t-3\ntitle: Shared plan\nstatus: active\nassignee: li\n---\n"
        self.write(cache / "tasks" / "t-3-shared-plan.md", legacy)
        self.write(cache / "hive.md", "# Old lab\n")
        for args in (("--hive", "old-lab"), ("--hive", "old-lab", "--apply"), ("--hives", "--apply")):
            code, result = self.levels(*args)
            self.assertEqual(code, 1, args)
            self.assertFalse(result["applied"], args)
            level = result["levels"][0]
            self.assertEqual(level["changes"], [], "no writes are planned for a copied-file cache")
            self.assertEqual(level["report"], [{"path": "~/.neuroflow/hives/old-lab",
                                                "message": "not a git clone — /hive --init replaces it with a clone"}])
        self.assertEqual(self.read(cache / "tasks" / "t-3-shared-plan.md"), legacy)
        self.assertEqual(sorted(p.relative_to(cache).as_posix() for p in cache.rglob("*")),
                         ["hive.md", "tasks", "tasks/t-3-shared-plan.md"], "not even a .gitignore is added")
        code, text = self.levels("--hive", "old-lab", as_json=False)
        self.assertIn("report only: ~/.neuroflow/hives/old-lab: not a git clone — /hive --init replaces it with a clone",
                      text)

    def test_what_cannot_be_moved_is_reported(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-3-wait.md", "---\nid: t-3\ntitle: Wait\nstatus: blocked\n---\n")
        self.write(tasks / "notes.md", "Loose notes, no frontmatter.\n")
        self.write(tasks / "flow.md", "| file | description |\n")
        self.write(tasks / "review" / "clash.md", "---\ntitle: Clash\nassignee: li\n<<<<<<< HEAD\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        level = result["levels"][0]
        self.assertEqual(level["changes"], [])
        self.assertEqual(sorted(item["path"] for item in level["report"]),
                         ["tasks/notes.md", "tasks/review/clash.md", "tasks/t-3-wait.md"])
        self.assertIn("'blocked'", next(i["message"] for i in level["report"] if i["path"] == "tasks/t-3-wait.md"))
        self.assertTrue((tasks / "t-3-wait.md").exists())

    def test_slugs_custom_columns_and_line_endings(self) -> None:
        self.assertEqual(migrate.slugify("Ré-run ICA: sub-07!"), "re-run-ica-sub-07")
        self.assertEqual(migrate.slugify("***"), "task")
        long = migrate.slugify("Write the methods section for the oddball paradigm paper draft")
        self.assertLessEqual(len(long), 40)
        self.assertFalse(long.endswith("-"))
        tasks = self.flowie / "tasks"
        self.write(tasks / "config.json", json.dumps({"columns": [
            {"id": "todo", "default": True}, {"id": "doing"}, {"id": "shelf", "archive": True}]}))
        self.write(tasks / "Big Idea.md", "---\r\ntitle: Big idea\r\nassignee: alice\r\n---\r\nBody\r\n")
        self.write(tasks / "t-9.md", "---\r\nid: t-9\r\ntitle: Ünïcode title\r\nstatus: archived\r\n---\r\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 0, result)
        big = self.read(tasks / "todo" / "big-idea.md")  # no status: the board's default column
        self.assertEqual(big, f"---\r\ntitle: Big idea\r\nstatus: todo\r\nowner: alice\r\nupdated: {self.today}\r\n---\r\nBody\r\n")
        self.assertTrue((tasks / "shelf" / "unicode-title.md").is_file(), "a name that is only the id: the title")

    def test_a_task_file_that_is_not_utf8_is_reported_never_rewritten(self) -> None:
        tasks = self.flowie / "tasks"
        flat = tasks / "t-2-priprava-dat.md"
        flat_bytes = "---\nid: t-2\ntitle: Příprava dat\nstatus: active\nassignee: jana\n---\n\nPoznámky.\n".encode("cp1250")
        in_column = tasks / "active" / "cisteni.md"
        column_bytes = "---\ntitle: Čištění\nassignee: li\n---\n".encode("cp1250")
        for path, data in ((flat, flat_bytes), (in_column, column_bytes)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        level = result["levels"][0]
        self.assertEqual(level["changes"], [])
        self.assertEqual({item["path"]: item["message"] for item in level["report"]}, {
            "tasks/t-2-priprava-dat.md": "not UTF-8 — convert it, then rerun",
            "tasks/active/cisteni.md": "not UTF-8 — convert it, then rerun",
        })
        self.assertEqual(flat.read_bytes(), flat_bytes, "never rewritten")
        self.assertEqual(in_column.read_bytes(), column_bytes, "never rewritten")

        flat.write_bytes(flat_bytes.decode("cp1250").encode("utf-8"))  # the person converts one: it migrates
        code, result = self.levels("--flowie", "--apply")
        self.assertTrue((tasks / "active" / "priprava-dat.md").is_file())
        self.assertIn("Příprava dat", self.read(tasks / "active" / "priprava-dat.md"))
        self.assertEqual([item["path"] for item in result["levels"][0]["report"]], ["tasks/active/cisteni.md"])

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_valid_legacy_slugs_are_kept_and_renames_carry_blocked_by(self) -> None:
        tasks = self.flowie / "tasks"
        long_slug = "write-the-methods-section-for-the-oddball-paradigm-paper"  # longer than 40 characters
        self.write(tasks / f"t-7-{long_slug}.md", "---\nid: t-7\ntitle: Methods\nstatus: inbox\n---\n")
        self.write(tasks / "Big Idea.md", "---\ntitle: Big idea\n---\n")  # not a slug /tasks would write
        self.write(tasks / "t-2-plan.md", "---\nid: t-2\ntitle: Plan B\nstatus: review\n---\n")
        self.write(tasks / "review" / "plan.md", "---\ntitle: Plan\nstatus: review\n---\n")
        after = "---\ntitle: After the plans\nstatus: active\nblocked_by: [Big Idea, plan, t-2, t-7]\nupdated: 2026-01-01\n---\n"
        self.write(tasks / "active" / "after-plans.md", after)
        self.write(tasks / "active" / "unrelated.md", "---\ntitle: Unrelated\nstatus: active\nblocked_by: [plan]\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        self.repo(self.flowie)

        code, result = self.levels("--flowie")
        level = result["levels"][0]
        self.assertEqual({c["path"]: c.get("to") for c in level["changes"]}, {
            f"tasks/t-7-{long_slug}.md": f"tasks/inbox/{long_slug}.md",  # kept verbatim, whatever its length
            "tasks/Big Idea.md": "tasks/inbox/big-idea.md",  # invalid characters: a new slug
            "tasks/t-2-plan.md": "tasks/review/plan-2.md",  # a -2 collision
            "tasks/active/after-plans.md": None,  # its blocked_by follows the renamed tasks
        })
        self.assertEqual(next(c["summary"] for c in level["changes"] if c["path"] == "tasks/active/after-plans.md"),
                         f"blocked_by: Big Idea -> big-idea, t-2 -> plan-2, t-7 -> {long_slug}")
        # 'plan' may now mean the task that has always been plan or the renamed t-2: reported, not guessed.
        self.assertEqual(sorted(item["path"] for item in level["report"]),
                         ["tasks/active/after-plans.md", "tasks/active/unrelated.md"])
        self.assertTrue(all("'plan'" in item["message"] and "plan or plan-2" in item["message"]
                            for item in level["report"]))

        code, text = self.levels("--flowie", "--apply", as_json=False)
        self.assertEqual(code, 1, "the unclear entries stay findings")
        self.assertEqual(self.read(tasks / "active" / "after-plans.md"),
                         "---\ntitle: After the plans\nstatus: active\n"
                         f"blocked_by: [big-idea, plan, plan-2, {long_slug}]\nupdated: {self.today}\n---\n")
        self.assertIn("blocked_by: [plan]\n", self.read(tasks / "active" / "unrelated.md"), "nothing to follow there")
        self.assertIn('"tasks/Big Idea.md"', text, "a path with a space is quoted")
        paths = [line for line in text.splitlines() if "commit exactly these paths" in line]
        self.assertEqual(len(paths), 1)
        staged = run_git(self.flowie, "diff", "--cached", "--name-only", "--no-renames", "-z").split("\0")
        self.assertIn("tasks/Big Idea.md", staged)
        self.assertIn("tasks/inbox/big-idea.md", staged)

    def test_a_task_naming_two_people_is_reported_and_nobody_is_dropped(self) -> None:
        tasks = self.flowie / "tasks"
        pair = "---\nid: t-5\ntitle: Pair task\nstatus: active\nassignee: jana\nresponsible: \"@li\"\n---\n"
        self.write(tasks / "t-5-pair-task.md", pair)
        owned = "---\ntitle: Owned\nstatus: review\nowner: stan\nassignee: jana\n---\n"
        self.write(tasks / "review" / "owned.md", owned)
        listed = "---\ntitle: Listed\nassignee: [jana, li]\n---\n"
        self.write(tasks / "inbox" / "listed.md", listed)
        same = "---\ntitle: Same person\nassignee: jana\nresponsible: \"@Jana\"\n---\n"
        self.write(tasks / "inbox" / "same.md", same)
        kept = "---\ntitle: Kept owner\nowner: li\nresponsible: li\n---\n"
        self.write(tasks / "inbox" / "kept.md", kept)
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        level = result["levels"][0]
        reported = {item["path"]: item["message"] for item in level["report"]}
        self.assertEqual(sorted(reported), ["tasks/inbox/listed.md", "tasks/review/owned.md", "tasks/t-5-pair-task.md"])
        self.assertIn("(jana, li)", reported["tasks/t-5-pair-task.md"])
        self.assertIn("(stan, jana)", reported["tasks/review/owned.md"])
        self.assertIn("(jana, li)", reported["tasks/inbox/listed.md"])
        for path, text in ((tasks / "t-5-pair-task.md", pair), (tasks / "review" / "owned.md", owned),
                           (tasks / "inbox" / "listed.md", listed)):
            self.assertEqual(self.read(path), text, "nobody is dropped: the file stays as it was")
        self.assertEqual(self.read(tasks / "inbox" / "same.md"),
                         f"---\ntitle: Same person\nstatus: inbox\nowner: jana\nupdated: {self.today}\n---\n")
        self.assertEqual(self.read(tasks / "inbox" / "kept.md"),
                         f"---\ntitle: Kept owner\nstatus: inbox\nowner: li\nupdated: {self.today}\n---\n")

    def test_a_task_left_as_it_is_learns_where_its_blocked_by_moved(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-4-collect.md", "---\nid: t-4\ntitle: Collect\nstatus: ready\n---\n")
        pair = "---\ntitle: Pair\nstatus: active\nassignee: jana\nresponsible: li\nblocked_by: [t-4]\n---\n"
        self.write(tasks / "active" / "pair.md", pair)
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        messages = [item["message"] for item in result["levels"][0]["report"] if item["path"] == "tasks/active/pair.md"]
        self.assertEqual(len(messages), 2, messages)
        self.assertIn("(jana, li)", messages[0])
        self.assertEqual(messages[1], "blocked_by: t-4 -> collect (those tasks moved): edit the entries when you fix "
                                      "this file")
        self.assertEqual(self.read(tasks / "active" / "pair.md"), pair)
        self.assertTrue((tasks / "ready" / "collect.md").is_file())

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_rebase_in_progress_blocks_writing(self) -> None:
        self.write(self.flowie / "tasks" / "t-1-x.md", "---\nid: t-1\ntitle: X\n---\n")
        (self.flowie / ".git" / "rebase-merge").mkdir(parents=True)
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        self.assertIn("rebase", result["levels"][0]["blocking"][0])
        self.assertTrue((self.flowie / "tasks" / "t-1-x.md").exists())

    def test_arguments_and_missing_levels(self) -> None:
        (self.hives / "example-lab").mkdir(parents=True)
        code, result = self.levels("--hive", "nope")
        self.assertEqual(code, 2)
        self.assertIn("example-lab", result["error"])
        code, result = self.levels("--flowie")
        self.assertEqual((code, result["levels"]), (0, []))
        self.assertTrue(any("no flowie" in note for note in result["notes"]))
        self.assertEqual(self.levels("--flowie", "--set", "active_phase=paper")[0], 2)
        self.assertEqual(self.levels("--hives", "--move-personal")[0], 2)

    def test_an_empty_owner_gives_way_to_the_legacy_person(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-1-plan.md", "---\nid: t-1\ntitle: Plan\nstatus: active\nowner:\nassignee: jana\n---\n")
        self.write(tasks / "review" / "check.md", "---\ntitle: Check\nowner: \"\"\nresponsible: \"@li\"\n---\n")
        self.write(tasks / "inbox" / "nobody.md", "---\ntitle: Nobody\nowner:\nlevel: flowie\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 0, result)
        self.assertEqual(self.read(tasks / "active" / "plan.md"),
                         f"---\ntitle: Plan\nstatus: active\nowner: jana\nupdated: {self.today}\n---\n")
        self.assertEqual(self.read(tasks / "review" / "check.md"),
                         f"---\ntitle: Check\nstatus: review\nowner: li\nupdated: {self.today}\n---\n")
        self.assertEqual(self.read(tasks / "inbox" / "nobody.md"),
                         f"---\ntitle: Nobody\nstatus: inbox\nowner:\nupdated: {self.today}\n---\n", "nobody invented")

    def test_a_yaml_null_owner_is_nobody(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "active" / "plan.md", "---\ntitle: Plan\nowner: null\nassignee: alice\n---\n")
        self.write(tasks / "inbox" / "tilde.md", "---\ntitle: Tilde\nowner: ~\nlevel: flowie\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual((code, result["levels"][0]["report"]), (0, []))
        self.assertEqual(self.read(tasks / "active" / "plan.md"),
                         f"---\ntitle: Plan\nstatus: active\nowner: alice\nupdated: {self.today}\n---\n")

    def test_a_task_held_for_an_unknown_status_learns_where_its_blocked_by_moved(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "T1-setup.md", "---\nid: T1\ntitle: Setup\nstatus: ready\n---\n")
        self.write(tasks / "T2-write.md", "---\nid: T2\ntitle: Write\nstatus: doing\nblocked_by: [T1]\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        messages = [item["message"] for item in result["levels"][0]["report"] if item["path"] == "tasks/T2-write.md"]
        self.assertTrue(any("is not a column" in message for message in messages), messages)
        self.assertTrue(any("T1 -> setup" in message for message in messages), messages)

    def test_a_level_gitignore_that_is_not_utf8_is_reported_never_rewritten(self) -> None:
        data = "# Poznámky k souborům\n.DS_Store\n".encode("cp1250")
        ignore = self.flowie / ".gitignore"
        ignore.parent.mkdir(parents=True, exist_ok=True)
        ignore.write_bytes(data)
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        level = result["levels"][0]
        self.assertEqual([item["path"] for item in level["report"]], [".gitignore"])
        self.assertIn("is not UTF-8", level["report"][0]["message"])
        self.assertEqual(ignore.read_bytes(), data, "never rewritten")

    def test_a_column_folder_legacy_id_in_blocked_by_follows_the_task(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "active" / "plan.md", "---\nid: t-2\ntitle: Plan\nassignee: jana\n---\n")
        self.write(tasks / "ready" / "after.md", "---\ntitle: After\nstatus: ready\nblocked_by: [t-2]\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 0, result)
        self.assertNotIn("id:", self.read(tasks / "active" / "plan.md"))
        self.assertIn("blocked_by: [plan]\n", self.read(tasks / "ready" / "after.md"), "the dropped id follows")

    # -- uncommitted changes in a level (git status) ---------------------------

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_local_changes_are_listed_and_a_change_to_one_is_flagged(self) -> None:
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-1-plan.md", "---\nid: t-1\ntitle: Plan\nstatus: active\n---\n\nNotes.\n")
        self.write(tasks / "t-2-draft.md", "---\nid: t-2\ntitle: Draft\nstatus: inbox\n---\n")
        self.write(self.flowie / "profile.md", "# Research Profile\n")
        self.write(self.flowie / ".gitignore", ".DS_Store\n")
        self.repo(self.flowie)
        with open(tasks / "t-1-plan.md", "a", encoding="utf-8", newline="") as fh:
            fh.write("A local note, not synced yet.\n")  # a tracked file the plan moves
        with open(self.flowie / ".gitignore", "a", encoding="utf-8", newline="") as fh:
            fh.write("*.tmp\n")  # a tracked file the plan rewrites
        with open(self.flowie / "profile.md", "a", encoding="utf-8", newline="") as fh:
            fh.write("Edited here.\n")  # a tracked file the plan does not touch
        self.write(self.flowie / "wellbeing" / "2026-10-08.json", "{}\n")  # untracked, as the mod leaves it
        self.write(self.flowie / "notes" / "my idea.md", "# Idea\n")

        code, result = self.levels("--flowie")
        self.assertEqual(code, 1)
        level = result["levels"][0]
        self.assertEqual(sorted(level["uncommitted"]), [
            ".gitignore", "notes/my idea.md", "profile.md", "tasks/t-1-plan.md", "wellbeing/2026-10-08.json"])
        self.assertEqual({c["path"]: c.get("local_changes", False) for c in level["changes"]}, {
            "tasks/t-1-plan.md": True, "tasks/t-2-draft.md": False, ".gitignore": True})
        self.assertEqual((level["blocking"], level["report"]), ([], []))
        code, text = self.levels("--flowie", as_json=False)
        flagged = [line for line in text.splitlines() if "has local changes" in line]
        self.assertEqual(len(flagged), 2, text)
        self.assertTrue(any("tasks/t-1-plan.md -> tasks/active/plan.md" in line for line in flagged), text)
        self.assertIn('"notes/my idea.md"', next(line for line in text.splitlines() if "not committed (uncommitted" in line))

        code, result = self.levels("--flowie", "--apply")  # the person agreed to include them (commands/migrate.md 5.3)
        self.assertEqual(code, 0, result)
        paths = result["levels"][0]["commit_paths"]
        self.assertEqual(paths, ["tasks/t-1-plan.md", "tasks/active/plan.md", "tasks/t-2-draft.md",
                                 "tasks/inbox/draft.md", ".gitignore"])
        run_git(self.flowie, "commit", "-q", "-m", "migrate: current task format", "--", *paths)
        self.assertIn("A local note, not synced yet.", run_git(self.flowie, "show", "HEAD:tasks/active/plan.md"))
        left = sorted(line[3:] for line in run_git(self.flowie, "status", "--porcelain", "-uall").splitlines())
        self.assertEqual(left, ['"notes/my idea.md"', "profile.md", "wellbeing/2026-10-08.json"],
                         "local changes outside the plan never join the migration commit")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_task_staged_but_never_committed_still_commits_by_path(self) -> None:
        # A file staged but never committed - new, or the new name of a staged rename - is in neither HEAD nor the
        # index after git mv: as a commit path, it would stop `git commit -- <paths>` and commit nothing.
        tasks = self.flowie / "tasks"
        self.write(tasks / "t-1-plan.md", "---\nid: t-1\ntitle: Plan\nstatus: active\n---\n")
        self.write(tasks / "t-3-old.md", "---\nid: t-3\ntitle: Review\nstatus: review\n---\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        self.repo(self.flowie)
        self.write(tasks / "t-7-new.md", "---\nid: t-7\ntitle: New\nstatus: inbox\n---\n")
        run_git(self.flowie, "add", "--", "tasks/t-7-new.md")
        run_git(self.flowie, "mv", "--", "tasks/t-3-old.md", "tasks/t-3-review.md")

        code, result = self.levels("--flowie")
        self.assertEqual({c["path"] for c in result["levels"][0]["changes"] if c.get("local_changes")},
                         {"tasks/t-3-review.md", "tasks/t-7-new.md"})
        code, result = self.levels("--flowie", "--apply")  # the person agreed to include them (commands/migrate.md 5.3)
        self.assertEqual(code, 0, result)
        paths = result["levels"][0]["commit_paths"]
        self.assertEqual(sorted(paths), ["tasks/active/plan.md", "tasks/inbox/new.md", "tasks/review/review.md",
                                         "tasks/t-1-plan.md"])
        run_git(self.flowie, "commit", "-q", "-m", "migrate: current task format", "--", *paths)
        tree = run_git(self.flowie, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
        for path in ("tasks/active/plan.md", "tasks/inbox/new.md", "tasks/review/review.md"):
            self.assertIn(path, tree)
        self.assertNotIn("tasks/t-1-plan.md", tree)
        self.assertEqual(run_git(self.flowie, "status", "--porcelain", "-uall").splitlines(), ["D  tasks/t-3-old.md"],
                         "the old name of the person's own staged rename is no part of the plan: it stays theirs")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_level_with_only_local_changes_is_current(self) -> None:
        self.write(self.flowie / "tasks" / "active" / "plan.md",
                   "---\ntitle: Plan\nstatus: active\ncreated: 2026-04-01\nupdated: 2026-04-02\n---\n")
        self.write(self.flowie / "profile.md", "# Research Profile\n")
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        self.repo(self.flowie)
        self.write(self.flowie / "profile.md", "# Research Profile\n\nEdited.\n")
        self.write(self.flowie / "wellbeing" / "2026-10-08.json", "{}\n")
        for args in (("--flowie",), ("--flowie", "--apply")):
            code, result = self.levels(*args)
            self.assertEqual(code, 0, "local changes alone are no finding: the exit-code contract stays")
            self.assertFalse(result["applied"])
            level = result["levels"][0]
            self.assertEqual((level["changes"], level["commit_paths"]), ([], []))
            self.assertEqual(sorted(level["uncommitted"]), ["profile.md", "wellbeing/2026-10-08.json"])
        self.assertEqual(run_git(self.flowie, "diff", "--cached", "--name-only"), "", "nothing is staged")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_hives_pending_changes_stay_out_of_the_migration_commit(self) -> None:
        hive = self.hives / "example-lab"
        self.write(hive / "ideas.md", "# Ideas\n")
        self.write(hive / ".gitignore", "sync.json\n")
        self.write(hive / "tasks" / "t-4-pipeline.md", "---\nid: t-4\ntitle: Pipeline\nstatus: ready\nassignee: li\n---\n")
        self.repo(hive)
        self.write(hive / "ideas.md", "# Ideas\n\n- a teammate's idea, not pushed yet\n")
        self.write(hive / "tasks" / "inbox" / "new-idea.md", "---\ntitle: New idea\nstatus: inbox\n---\n")
        code, result = self.levels("--hive", "example-lab", "--apply")
        self.assertEqual(code, 0, result)
        level = result["levels"][0]
        self.assertEqual(sorted(level["uncommitted"]), ["ideas.md", "tasks/inbox/new-idea.md"])
        self.assertFalse(any(change.get("local_changes") for change in level["changes"]))
        self.assertEqual(level["commit_paths"], ["tasks/t-4-pipeline.md", "tasks/ready/pipeline.md"])
        run_git(hive, "commit", "-q", "-m", "migrate: current task format", "--", *level["commit_paths"])
        self.assertEqual(sorted(line[3:] for line in run_git(hive, "status", "--porcelain", "-uall").splitlines()),
                         ["ideas.md", "tasks/inbox/new-idea.md"], "pending hive changes are left as they are")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_unresolved_conflicts_block_the_level(self) -> None:
        # What a pull with --autostash leaves when it cannot put the local changes back: UU files, no MERGE_HEAD.
        tasks = self.flowie / "tasks"
        self.write(tasks / "active" / "plan.md", "---\ntitle: Plan\nstatus: active\n---\n\nv1\n")
        legacy = "---\nid: t-1\ntitle: Old\nstatus: inbox\n---\n"
        self.write(tasks / "t-1-old.md", legacy)
        self.write(self.flowie / ".gitignore", "integrations.json\n")
        self.repo(self.flowie)
        self.write(tasks / "active" / "plan.md", "---\ntitle: Plan\nstatus: active\n---\n\nlocal\n")
        run_git(self.flowie, "stash", "-q")
        self.write(tasks / "active" / "plan.md", "---\ntitle: Plan\nstatus: active\n---\n\nupstream\n")
        run_git(self.flowie, "commit", "-q", "-am", "upstream")
        proc = subprocess.run(["git", "-c", "core.autocrlf=false", "stash", "apply"], cwd=self.flowie,
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0, "the stash must conflict for this test")
        self.assertFalse((self.flowie / ".git" / "MERGE_HEAD").exists())

        code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 1)
        self.assertFalse(result["applied"])
        level = result["levels"][0]
        self.assertEqual(level["blocking"], ["unresolved conflicts in tasks/active/plan.md; resolve them first "
                                             "(/flowie --sync)"])
        self.assertEqual(level["changes"], [])
        self.assertEqual(self.read(tasks / "t-1-old.md"), legacy, "nothing is written while it blocks")

    def test_git_status_output_is_parsed_exactly(self) -> None:
        text = "R  new name.md\0old.md\0 M a.md\0?? nested/\0UU c.md\0C  copy.md\0src.md\0AA both.md\0"
        self.assertEqual(migrate.parse_status(text), (
            ["new name.md", "old.md", "a.md", "nested/", "c.md", "copy.md", "both.md"], ["c.md", "both.md"]))
        self.assertEqual(migrate.parse_status(""), ([], []))

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_git_status_that_fails_is_a_failure(self) -> None:
        self.write(self.flowie / "tasks" / "t-1-x.md", "---\nid: t-1\ntitle: X\n---\n")
        self.repo(self.flowie)
        real = migrate.git

        def broken(root, *args):
            if "status" in args:
                return subprocess.CompletedProcess(args, 128, "", "fatal: detected dubious ownership in repository")
            return real(root, *args)

        with mock.patch.object(migrate, "git", broken):
            code, result = self.levels("--flowie", "--apply")
        self.assertEqual(code, 2)
        self.assertIn("git status failed", result["error"])
        self.assertTrue((self.flowie / "tasks" / "t-1-x.md").exists(), "nothing is written")

    def test_task_paths_survive_a_legacy_code_page(self) -> None:
        # The prose commits the paths it reads from --json: a name outside the ANSI code page must reach it.
        self.write(self.flowie / "tasks" / "t-2-日本語.md", "---\nid: t-2\ntitle: 日本語\nstatus: active\n---\n")
        env = dict(os.environ, PYTHONIOENCODING="cp1250")
        for extra in ([], ["--json"]):
            proc = subprocess.run([sys.executable, str(SCRIPT), "--home", str(self.home), "--flowie", *extra],
                                  capture_output=True, env=env, timeout=60)
            self.assertEqual(proc.stderr.decode("utf-8", "replace"), "", "a traceback's exit 1 is not a finding")
            self.assertEqual(proc.returncode, 1)
            out = proc.stdout.decode("utf-8")
            if extra:
                self.assertIn("tasks/t-2-日本語.md", [c["path"] for c in json.loads(out)["levels"][0]["changes"]])
            else:
                self.assertIn("t-2-日本語.md", out)


if __name__ == "__main__":
    unittest.main()
