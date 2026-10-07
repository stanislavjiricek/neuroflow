"""Tests for skills/neuroflow-core/scripts/migrate.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

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
        self.assertEqual(code, 0, result)
        self.assertEqual([level["name"] for level in result["levels"]], ["lab-a", "lab-b"])
        for name in ("lab-a", "lab-b"):
            self.assertTrue((self.hives / name / "tasks" / "review" / "plan.md").is_file())
            self.assertFalse((self.hives / name / "tasks" / "t-1-plan.md").exists())
        self.assertEqual(result["levels"][0]["commit_paths"], ["tasks/t-1-plan.md", "tasks/review/plan.md"])
        self.assertEqual(result["levels"][1]["commit_paths"], [])
        self.assertTrue(any("not a git repository" in note for note in result["levels"][1]["notes"]))

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


if __name__ == "__main__":
    unittest.main()
