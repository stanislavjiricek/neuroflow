"""Tests for skills/neuroflow-core/scripts/nf_check.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "neuroflow-core" / "scripts" / "nf_check.py"


def _load():
    name = "nf_check_under_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nf = _load()

CORE = textwrap.dedent("""\
    ---
    name: neuroflow-core
    description: core
    ---
    ## Global ~/.neuroflow/ structure

    | Thing | Purpose |
    |---|---|
    | `user.yaml` | not a project file |

    ## .neuroflow/ folder

    ### Root files

    | File | Purpose |
    |---|---|
    | `project_config.md` | config |
    | `flow.md` | index |
    | `sentinel.md` | report |

    ### Root folders

    | Folder | Purpose |
    |---|---|
    | `sessions/` | logs |
    | `reasoning/` | decisions |
    | `ethics/` | approvals |
    | `preregistration/` | plans |
    | `tasks/` | board |
    | `wiki/` | wiki |
    | `{phase}/` | one per command |

    ## Phase taxonomy

    **Valid `phase:` frontmatter values:** `ideation`, `data`, `data-analyze`, `notes`, `utility`
    """)


def command(name: str, phase: str, writes: list[str]) -> str:
    lines = ["---", f"name: {name}", "description: x", f"phase: {phase}", "reads:", "  - .neuroflow/flow.md",
             "writes:"] + [f"  - {w}" for w in writes] + ["lifecycle: full", "---", "body", ""]
    return "\n".join(lines)


def write(root: Path, files: dict[str, str | bytes]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_bytes(content.encode("utf-8"))


CONFIG = textwrap.dedent("""\
    ---
    nf_schema: 1   # integer
    project_name: Oddball EEG study
    active_phase: ideation
    default_mode: critic
    recommended_phases: [ideation, data]
    raw_roots: [sourcedata/]
    plugin_version: 0.3.0
    collaborators:
      - name: Example Person
        handle: example
    ---

    # Oddball EEG study

    Free notes.
    """)

CLAUDE_BLOCK = "## neuroflow\n\nThis project uses neuroflow. Read `.neuroflow/project_config.md` and `flow.md` first.\n"


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.plugin = tmp / "plugin"
        self.project = tmp / "project"
        self.home = tmp / "home"
        self.home.mkdir()
        write(self.plugin, {
            ".claude-plugin/plugin.json": json.dumps({"name": "neuroflow", "version": "0.3.0"}),
            "skills/neuroflow-core/SKILL.md": CORE,
            "skills/review-neuro/SKILL.md": "---\nname: review-neuro\n---\n",
            "commands/ideation.md": command("ideation", "ideation", [".neuroflow/ideation/", ".neuroflow/sessions/x.md"]),
            "commands/data-analyze.md": command("data-analyze", "data-analyze", [".neuroflow/data-analyze/"]),
            "commands/setup.md": command("setup", "utility", [".neuroflow/integrations.json"]),
        })
        write(self.project, {
            ".neuroflow/project_config.md": CONFIG,
            ".neuroflow/flow.md": "| File / Folder | Description | Last changed |\n|---|---|---|\n"
                                  "| project_config.md | Config. | 2026-10-01 |\n| sessions/ | Logs. | 2026-10-01 |\n"
                                  "| reasoning/ | Decisions. | 2026-10-01 |\n| ideation/ | Ideas. | 2026-10-01 |\n"
                                  "| tasks/ | Board. | 2026-10-01 |\n| wiki/ | Wiki. | 2026-10-01 |\n",
            ".neuroflow/sessions/2026-10-01.md": "## 10:00 — [ideation] session started\n",
            ".neuroflow/reasoning/flow.md": "| File / Folder | Description | Last changed |\n|---|---|---|\n"
                                            "| general.jsonl | Log. | 2026-10-01 |\n",
            ".neuroflow/reasoning/general.jsonl": json.dumps({"statement": "s", "source": "command:ideation | 2026-10-01",
                                                              "reasoning": "r", "at": "2026-10-01T10:00:00Z"}) + "\n",
            ".neuroflow/ideation/flow.md": "| File / Folder | Description | Last changed |\n|---|---|---|\n"
                                           "| idea.md | The idea. | 2026-10-01 |\n",
            ".neuroflow/ideation/idea.md": "# Idea\n",
            ".neuroflow/tasks/inbox/.gitkeep": "",
            ".neuroflow/wiki/index.md": "# Wiki\n",
            ".claude/CLAUDE.md": CLAUDE_BLOCK,
        })

    def tearDown(self):
        self._tmp.cleanup()

    def ctx(self, run_pii=True):
        return nf.Context(project=self.project, plugin_root=self.plugin, home=self.home,
                          today=dt.date(2026, 10, 7), run_pii=run_pii)

    def findings(self, check: str):
        found, _ = nf.run_checks(self.ctx(), {check})
        return [f for f in found if f.severity != nf.INFO]

    def messages(self, check: str) -> str:
        return "\n".join(f"{f.severity} {f.path} {f.message}" for f in self.findings(check))


class ParserTests(unittest.TestCase):
    def test_frontmatter_subset(self):
        text = textwrap.dedent("""\
            ---
            name: x  # comment
            quoted: "a: b"
            inline: [one, "two, three", four]
            empty_list: []
            block:
              - .neuroflow/a.md
              - .neuroflow/b/
            same_indent:
            - first
            people:
              - name: Alice Example
                email: alice@example.org
              - name: Bob
            files:
              .neuroflow/preregistration/p.md: 3f5a
            folded: >
              one
              two
            when: 2026-10-01T10:00:00Z
            ---
            body
            """)
        fm, body, err = nf.split_frontmatter(text)
        self.assertIsNone(err)
        self.assertEqual(body, "body\n")
        self.assertEqual(fm["name"], "x")
        self.assertEqual(fm["quoted"], "a: b")
        self.assertEqual(fm["inline"], ["one", "two, three", "four"])
        self.assertEqual(fm["empty_list"], [])
        self.assertEqual(fm["block"], [".neuroflow/a.md", ".neuroflow/b/"])
        self.assertEqual(fm["same_indent"], ["first"])
        self.assertEqual(fm["people"], [{"name": "Alice Example", "email": "alice@example.org"}, {"name": "Bob"}])
        self.assertEqual(fm["files"], {".neuroflow/preregistration/p.md": "3f5a"})
        self.assertEqual(fm["folded"], "one two")
        self.assertEqual(fm["when"], "2026-10-01T10:00:00Z")

    def test_no_or_unclosed_frontmatter(self):
        self.assertEqual(nf.split_frontmatter("# Title\n")[0], None)
        fm, _, err = nf.split_frontmatter("---\nname: x\n")
        self.assertIsNone(fm)
        self.assertIn("never closed", err)

    def test_flow_parser_separates_index_from_narrative(self):
        text = ("output_path: ../scripts\n| File / Folder | Description | Last changed |\n|---|---|---|\n"
                "| [plan](plan.md) | x | d |\n| `notes/` | y | d |\n\n| Step | Status |\n|---|---|\n| Convert | done |\n")
        entries, other = nf.parse_flow(text)
        self.assertEqual([e for e, _ in entries], ["plan.md", "notes/"])
        self.assertEqual(other, 1)


class StructureTests(Base):
    def test_documented_structure_reads_core_and_commands(self):
        s = nf.documented_structure(self.plugin)
        self.assertTrue(s["documented"])
        self.assertIn("project_config.md", s["root_files"])
        self.assertIn("integrations.json", s["root_files"])
        self.assertNotIn("user.yaml", s["root_files"])  # global section is not project memory
        self.assertIn("sessions", s["root_folders"])
        self.assertIn("ideation", s["phase_folders"])
        self.assertIn("review-neuro", s["skills"])

    def test_real_plugin_documents_the_basics(self):
        s = nf.documented_structure(REPO)
        self.assertIn("project_config.md", s["root_files"])
        self.assertIn("sessions", s["root_folders"])
        self.assertIn("ideation", nf.canonical_phases(REPO))


class CleanProjectTests(Base):
    def test_clean_project_has_no_findings(self):
        found, statuses = nf.run_checks(self.ctx())
        self.assertEqual([f for f in found if f.severity != nf.INFO], [])
        self.assertEqual(statuses["NF8"], "skipped")  # no pii_scan.py in the fixture plugin
        self.assertEqual(nf.exit_code(found, nf.WARN), 0)


class NF1Tests(Base):
    def test_unlisted_and_missing_entries(self):
        write(self.project, {".neuroflow/ideation/extra.md": "x",
                             ".neuroflow/data-analyze/plan.md": "x"})
        with open(self.project / ".neuroflow/ideation/flow.md", "a", encoding="utf-8") as fh:
            fh.write("| ghost.md | gone | 2026-10-01 |\n")
        text = self.messages("NF1")
        self.assertIn("file `extra.md` exists but is not listed", text)
        self.assertIn("lists `ghost.md`, which does not exist", text)
        self.assertIn("folder `data-analyze/` exists but is not listed", text)
        self.assertIn("data-analyze/ folder has no flow.md", text)

    def test_exempt_folders_need_no_flow_md(self):
        self.assertNotIn("tasks", self.messages("NF1"))
        self.assertNotIn("sessions/ folder has no flow.md", self.messages("NF1"))

    def test_narrative_table_reported_once(self):
        with open(self.project / ".neuroflow/ideation/flow.md", "a", encoding="utf-8") as fh:
            fh.write("\n| Step | Status |\n|---|---|\n| Brainstorm | done |\n")
        found = self.findings("NF1")
        self.assertEqual(len(found), 1)
        self.assertIn("not the file index", found[0].message)


class NF2Tests(Base):
    def set_config(self, text):
        write(self.project, {".neuroflow/project_config.md": text})

    def test_legacy_dialect(self):
        self.set_config("# Project config\n\n**Phase:** ideation\n**Plugin version:** 0.2.1\n")
        text = self.messages("NF2")
        self.assertIn("legacy dialect", text)
        self.assertIn("older than the installed plugin 0.3.0", text)

    def test_newer_schema_is_an_error(self):
        self.set_config(CONFIG.replace("nf_schema: 1", "nf_schema: 2"))
        errors = [f for f in self.findings("NF2") if f.severity == nf.ERROR]
        self.assertEqual(len(errors), 1)
        self.assertIn("do not write", errors[0].message)

    def test_fields(self):
        cfg = (CONFIG.replace("active_phase: ideation", "active_phase: brainstorming")
               .replace("default_mode: critic", "default_mode: chaos\nauto_issue_reporting: yes")
               .replace("recommended_phases: [ideation, data]\n", ""))
        self.set_config(cfg)
        text = self.messages("NF2")
        self.assertIn("`active_phase: brainstorming` is not a canonical phase", text)
        self.assertIn("default_mode: chaos", text)
        self.assertIn("`auto_issue_reporting`", text)
        self.assertIn("missing `recommended_phases`", text)

    def test_absolute_raw_root(self):
        self.set_config(CONFIG.replace("[sourcedata/]", "[/mnt/raw]"))
        self.assertIn("must be relative", self.messages("NF2"))


FREEZE = REPO / "skills" / "phase-preregistration" / "scripts" / "freeze.py"


class NF3Tests(Base):
    """NF3 delegates the hash re-check to freeze.py verify (the one home of the hash lock)."""

    def freeze(self, set_by="person"):
        write(self.project, {
            ".neuroflow/preregistration/prereg.md": "# Hypotheses\nH1.\n",
            ".neuroflow/preregistration/flow.md": "| File / Folder | D | L |\n|---|---|---|\n| prereg.md | x | d |\n"
                                                  "| status.md | x | d |\n",
        })
        target = self.plugin / nf.FREEZE_SCRIPT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(FREEZE.read_bytes())
        result = subprocess.run([sys.executable, str(target), "freeze", ".neuroflow/preregistration/prereg.md",
                                 "--set-by", set_by, "--root", str(self.project)],
                                cwd=self.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(FREEZE.is_file(), "freeze.py not in this checkout")
    def test_intact_freeze_passes_and_edits_are_errors(self):
        self.freeze()
        self.assertEqual(self.findings("NF3"), [])
        path = self.project / ".neuroflow/preregistration/prereg.md"
        path.write_bytes(path.read_bytes() + b"H2 added later.\n")
        errors = [f for f in self.findings("NF3") if f.severity == nf.ERROR]
        self.assertEqual([e.path for e in errors], [".neuroflow/preregistration/prereg.md"])
        self.assertIn("changed", errors[0].message)

    @unittest.skipUnless(FREEZE.is_file(), "freeze.py not in this checkout")
    def test_model_set_freeze_is_a_warning(self):
        self.freeze(set_by="model")
        found = self.findings("NF3")
        self.assertEqual([f.severity for f in found], [nf.WARN])
        self.assertIn("unconfirmed-freeze", found[0].message)

    def test_mapping_and_missing_script(self):
        write(self.project, {".neuroflow/preregistration/status.md":
                             "---\nnf_schema: 1\nstatus: frozen\nfrozen_at: 2026-10-01\nset_by: person\n---\n"})
        found, _ = nf.run_checks(self.ctx(), {"NF3"})
        self.assertEqual([f.severity for f in found], [nf.INFO])
        self.assertIn("not re-hashed", found[0].message)
        payload = {"status": "frozen", "findings": [{"kind": "banner-missing", "path": "p.md", "detail": "gone"},
                                                    {"kind": "missing", "path": "q.md", "detail": "missing"}]}
        write(self.plugin, {nf.FREEZE_SCRIPT: f"import json, sys\nprint(json.dumps({payload!r}))\nsys.exit(1)\n"})
        self.assertEqual([(f.severity, f.path) for f in self.findings("NF3")], [(nf.WARN, "p.md"), (nf.ERROR, "q.md")])

    def test_status_format(self):
        write(self.project, {".neuroflow/preregistration/status.md": "---\nnf_schema: 3\nstatus: locked\n---\n"})
        text = self.messages("NF3")
        self.assertIn("nf_schema 3", text)
        self.assertIn("must be draft or frozen", text)

    def test_ethics_expired(self):
        write(self.project, {".neuroflow/ethics/status.md":
                             "---\nnf_schema: 1\nstatus: approved\nexpires: 2026-06-30\nai_processing: none\n"
                             "set_by: person\n---\n"})
        errors = [f for f in self.findings("NF3") if f.severity == nf.ERROR]
        self.assertIn("expired on 2026-06-30", errors[0].message)

    def test_legacy_ethics_table(self):
        write(self.project, {".neuroflow/ethics/status.md":
                             "# Ethics\n\n| Field | Value |\n|---|---|\n| Status | Approved |\n| Expires | 2026-01-31 |\n"})
        text = self.messages("NF3")
        self.assertIn("legacy ethics status format", text)
        self.assertIn("expired on 2026-01-31", text)


class NF4Tests(Base):
    def test_jsonl_problems(self):
        write(self.project, {".neuroflow/reasoning/data.jsonl":
                             '{"statement": "s", "source": "x", "reasoning": "r"}\n{broken\n{"statement": "s"}\n'})
        found = self.findings("NF4")
        self.assertEqual([f.line for f in found], [2, 3])
        self.assertEqual(found[0].severity, nf.ERROR)
        self.assertIn("lacks `source`, `reasoning`", found[1].message)

    def test_legacy_json(self):
        write(self.project, {".neuroflow/reasoning/general.json": json.dumps([{"statement": "s"}])})
        text = self.messages("NF4")
        self.assertIn("legacy JSON-array log", text)
        self.assertIn("both general.json and general.jsonl exist", text)
        self.assertIn("1 entry lack", text)


class NF5Tests(Base):
    def test_conflict_markers(self):
        write(self.project, {".neuroflow/ideation/idea.md": "# Idea\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> branch\n"})
        found = self.findings("NF5")
        self.assertEqual([f.line for f in found], [2, 6])
        self.assertTrue(all(f.severity == nf.ERROR for f in found))


class NF6Tests(Base):
    def test_structure(self):
        write(self.project, {
            ".neuroflow/review-neuro/x.md": "x",
            ".neuroflow/flowie/profile.md": "x",
            ".neuroflow/random/x.md": "x",
            ".neuroflow/team.md": "x",
            ".neuroflow/integrations.json": "{}",
            ".neuroflow/data-analyze/flow.md": "",
        })
        text = self.messages("NF6")
        self.assertIn("named after a skill", text)
        self.assertIn("flowie never lives inside a project", text)
        self.assertIn("random/ folder is not part", text)
        self.assertIn("team.md legacy file", text)
        self.assertNotIn("integrations.json", text)
        self.assertNotIn("data-analyze", text)


class NF7Tests(Base):
    def test_active_phase_and_stale_copies(self):
        write(self.project, {".claude/CLAUDE.md": CLAUDE_BLOCK + "- Active phase: ideation\n",
                             "AGENTS.md": "# Agents\n\n## neuroflow\n\n- Active phase: data\n"})
        write(self.home, {".claude/CLAUDE.md": "## neuroflow\n\n- Active phase: ideation\n"})
        text = self.messages("NF7")
        self.assertIn("holds an `Active phase` line", text)
        self.assertIn("~/.claude/CLAUDE.md", text)
        self.assertIn("AGENTS.md stale neuroflow block", text)

    def test_missing_claude_md(self):
        (self.project / ".claude" / "CLAUDE.md").unlink()
        self.assertIn("missing", self.messages("NF7"))


class NF8Tests(Base):
    def install_scanner(self, code: int, payload: dict):
        write(self.plugin, {"skills/phase-output/scripts/pii_scan.py":
                            f"import json, sys\nprint(json.dumps({payload!r}))\nsys.exit({code})\n"})

    def test_delegated_findings(self):
        self.install_scanner(1, {"findings": [{"path": ".neuroflow/ideation/idea.md", "line": 3, "kind": "email"}]})
        found, statuses = nf.run_checks(self.ctx(), {"NF8"})
        self.assertEqual(statuses["NF8"], "warn")
        self.assertEqual(found[0].path, ".neuroflow/ideation/idea.md")
        self.assertIn("needs human review", found[0].message)

    def test_clean_and_skipped(self):
        self.install_scanner(0, {"findings": []})
        self.assertEqual(nf.run_checks(self.ctx(), {"NF8"})[1]["NF8"], "pass")
        self.assertEqual(nf.run_checks(self.ctx(run_pii=False), {"NF8"})[1]["NF8"], "skipped")


class CliTests(Base):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = nf.main(["--plugin-root", str(self.plugin), "--home", str(self.home), "--today", "2026-10-07", *args])
        return code, out.getvalue(), err.getvalue()

    def test_json_clean_from_a_subfolder(self):
        sub = self.project / "scripts" / "analysis"
        sub.mkdir(parents=True)
        code, out, _ = self.run_main("--project", str(sub), "--json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(Path(data["project"]), self.project.resolve())
        self.assertEqual(data["summary"]["error"], 0)
        self.assertEqual([c["id"] for c in data["checks"]], list(nf.CHECKS))

    def test_findings_and_fail_on(self):
        write(self.project, {".neuroflow/ideation/extra.md": "x"})
        self.assertEqual(self.run_main("--project", str(self.project))[0], 1)
        self.assertEqual(self.run_main("--project", str(self.project), "--fail-on", "error")[0], 0)

    def test_only_and_usage_errors(self):
        code, out, _ = self.run_main("--project", str(self.project), "--only", "nf5", "--json")
        self.assertEqual([c["id"] for c in json.loads(out)["checks"]], ["NF5"])
        self.assertEqual(self.run_main("--project", str(self.project), "--only", "NF9")[0], 2)

    def test_home_is_never_a_project(self):
        write(self.home, {".neuroflow/user.yaml": "x: 1\n"})
        code, _, err = self.run_main("--project", str(self.home))
        self.assertEqual(code, 2)
        self.assertIn("not project memory", err)

    def test_structure_flag(self):
        code, out, _ = self.run_main("--structure")
        self.assertEqual(code, 0)
        self.assertIn("project_config.md", json.loads(out)["root_files"])


if __name__ == "__main__":
    unittest.main()
