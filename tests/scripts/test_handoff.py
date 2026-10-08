"""Tests for skills/phase-output/scripts/handoff.py (stdlib unittest, local git only)."""

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
SCRIPT = REPO / "skills" / "phase-output" / "scripts" / "handoff.py"
TODAY = date(2026, 10, 7)


def load():
    name = "nf_test_handoff"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ho = load()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@unittest.skipUnless(shutil.which("git"), "git not installed")
class HandoffTests(unittest.TestCase):
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
        nf = self.root / ".neuroflow"
        write(nf / "project_config.md", "---\nnf_schema: 1\nproject_name: Oddball EEG study\n"
              "active_phase: data-analyze\nraw_roots: [sourcedata/]\nhive_repo: example-lab/hive\n---\n")
        write(nf / "ethics" / "status.md", "---\nstatus: approved\nexpires: 2027-06-30\nset_by: person\n---\n")
        (self.root / "sourcedata").mkdir()
        write(self.root / "sourcedata" / "dataset_description.json", "{}\n")
        write(self.root / ".gitignore", ".neuroflow/sessions/\n.neuroflow/integrations.json\n")

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(["git", *args], cwd=cwd or self.root, check=True, capture_output=True)

    def init_pushed_repo(self) -> None:
        remote = self.base / "remote.git"
        self.git("init", "-q", "--bare", str(remote), cwd=self.base)
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "-q", "-u", "origin", "main")

    def test_not_a_project(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = ho.main(["--root", str(self.base), "--no-hpc", "--json"])
        self.assertEqual(code, 2)

    def test_clean_project_needs_no_attention(self):
        self.init_pushed_repo()
        d = ho.build(self.root, hpc=False, today=TODAY)
        self.assertEqual(d["attention"], [], d["attention"])
        self.assertEqual(d["git"]["upstream"], "origin/main")
        self.assertEqual(d["data_roots"][0]["files"], 1)
        self.assertTrue(d["data_roots"][0]["bids"])
        self.assertEqual(d["project"]["hive_repo"], "example-lab/hive")

    def test_attention_items(self):
        self.init_pushed_repo()
        nf = self.root / ".neuroflow"
        write(nf / "ethics" / "status.md", "---\nstatus: approved\nexpires: 2026-10-20\nset_by: person\n---\n")
        write(nf / "tasks" / "t-001-ica.md", "---\nid: t-001\ntitle: Re-run ICA\nstatus: active\n"
              "due: 2026-10-01\nassignee: alice\n---\n")
        write(nf / "tasks" / "t-002-old.md", "---\nid: t-002\ntitle: Old\nstatus: done\nassignee: bob\n---\n")
        write(nf / "tasks" / "inbox" / "t-003.md", "---\nid: t-003\ntitle: Legacy column task\n---\n")
        write(nf / "integrations.json", json.dumps({"miro": {"MIRO_ACCESS_TOKEN": "tok-value-123"},
                                                    "custom_llm": {"provider": "my-gateway"}}))
        write(nf / "sessions" / "2026-10-07.md", "log\n")
        write(self.root / "scripts" / "new.py", "print(1)\n")
        (self.root / "sourcedata" / "dataset_description.json").unlink()
        (self.root / "sourcedata").rmdir()
        d = ho.build(self.root, hpc=False, today=TODAY)
        text = " | ".join(d["attention"])
        self.assertIn("uncommitted work", text)
        self.assertIn("expires in 13 days", text)
        self.assertIn("data root sourcedata/ is missing", text)
        self.assertEqual([t["id"] for t in d["tasks"]["alice"]], ["t-001"])
        self.assertTrue(d["tasks"]["alice"][0]["overdue"])
        self.assertNotIn("bob", d["tasks"])
        self.assertEqual(d["tasks"]["unassigned"][0]["id"], "t-003")
        self.assertEqual(d["integrations"], ["custom_llm.provider", "miro.MIRO_ACCESS_TOKEN"])
        self.assertIn({"path": ".neuroflow/sessions/", "files": 1}, d["stays_with_leaver"])
        md = ho.to_markdown(d)
        self.assertNotIn("tok-value-123", md)
        self.assertIn("## Open tasks by owner", md)
        self.assertIn("OVERDUE", md)

    def test_xray_files_stay_with_leaver(self):
        paper = self.root / ".neuroflow" / "paper"
        write(paper / "draft.md", "draft\n")
        write(paper / "xray-draft-2026-10-07.md", "critique\n")
        write(paper / "xray-draft-2026-10-07.jsonl", "{}\n")
        self.assertIn({"path": ".neuroflow/paper/xray-*", "files": 2}, ho.section_personal(self.root))

    def test_wiki_queue_counts_cards_not_its_own_gitignore(self):
        pending = self.root / ".neuroflow" / "wiki" / ".pending"
        write(pending / ".gitignore", "*\n")
        queue = [s for s in ho.section_personal(self.root) if s["path"] == ".neuroflow/wiki/.pending/"]
        self.assertEqual(queue, [])  # only the queue's own .gitignore: nothing stays with the leaver
        write(pending / "2026-10-07-fdr-across-electrodes.md", "---\ntitle: FDR across electrodes\nstatus: pending\n---\ncard\n")
        write(pending / "2026-10-01-baseline-window.md", "---\ntitle: Baseline window\nstatus: skipped\n---\ncard\n")
        self.assertIn({"path": ".neuroflow/wiki/.pending/", "files": 2}, ho.section_personal(self.root))

    def test_empty_local_folders_are_not_listed(self):
        # Every local-tier folder follows the queue's rule: no files (its own .gitignore aside), no line.
        (self.root / ".neuroflow" / "sessions").mkdir(parents=True, exist_ok=True)
        write(self.root / ".neuroflow" / "review" / ".gitignore", "*\n")
        paths = [s["path"] for s in ho.section_personal(self.root)]
        self.assertNotIn(".neuroflow/sessions/", paths)
        self.assertNotIn(".neuroflow/review/", paths)

    def test_model_set_approval_and_frozen_prereg(self):
        self.init_pushed_repo()
        nf = self.root / ".neuroflow"
        write(nf / "ethics" / "status.md", "---\nstatus: approved\nset_by: model\n---\n")
        write(nf / "preregistration" / "status.md", "---\nstatus: frozen\nset_by: person\n---\n")
        verify = {"status": "frozen", "files": [{"path": ".neuroflow/preregistration/p.md", "ok": False}],
                  "findings": [{"kind": "changed", "path": ".neuroflow/preregistration/p.md"}]}
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "status")
        self.git("push", "-q")
        with mock.patch.object(ho, "freeze_verify", return_value=verify):
            d = ho.build(self.root, hpc=False, today=TODAY)
        text = " | ".join(d["attention"])
        self.assertIn("not recorded by a person", text)
        self.assertIn("preregistration: changed", text)
        self.assertEqual(d["preregistration"]["files"][0]["state"], "changed or missing")

    def test_no_git_and_legacy_ethics_table(self):
        write(self.root / ".neuroflow" / "ethics" / "status.md",
              "# Ethics status\n\n| Item | Value |\n|---|---|\n| Status | expired |\n| Expires | 2026-01-01 |\n")
        d = ho.build(self.root, hpc=False, today=TODAY)
        text = " | ".join(d["attention"])
        self.assertIn("not a git repository", text)
        self.assertIn("ethics status is expired", text)
        self.assertIn("expired on 2026-01-01", text)

    def test_cli_exit_codes(self):
        self.init_pushed_repo()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ho.main(["--root", str(self.root), "--no-hpc"])
        self.assertIn(code, (0, 1))
        self.assertIn("# Handoff dossier - Oddball EEG study", buf.getvalue())


class OpenTaskTests(unittest.TestCase):
    """Open tasks read as commands/tasks.md defines the board (no git needed)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "proj"
        self.tasks = self.root / ".neuroflow" / "tasks"
        write(self.root / ".neuroflow" / "project_config.md",
              "---\nnf_schema: 1\nproject_name: Oddball EEG study\n---\n")

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, rel: str, *keys: str) -> None:
        write(self.tasks / rel, "---\n" + "".join(f"{k}\n" for k in keys) + "created: 2026-09-01\n---\n\nNotes.\n")

    def grouped(self) -> dict:
        return {owner: [t["id"] for t in tasks] for owner, tasks in ho.section_tasks(self.root, TODAY).items()}

    def test_current_tasks_are_grouped_by_owner(self):
        self.task("active/re-run-ica.md", 'title: "Re-run ICA on sub-07"', "status: active", "owner: alice",
                  "due: 2026-10-01")
        self.task("ready/qc-report.md", 'title: "QC report"', "status: ready", "owner: bob")
        by_owner = ho.section_tasks(self.root, TODAY)
        self.assertEqual(self.grouped(), {"alice": ["re-run-ica"], "bob": ["qc-report"]})
        ica = by_owner["alice"][0]
        self.assertEqual((ica["title"], ica["status"], ica["due"], ica["overdue"]),
                         ("Re-run ICA on sub-07", "active", "2026-10-01", True))
        self.assertEqual(by_owner["bob"][0]["status"], "ready")

    def test_a_task_naming_several_people_is_listed_under_each(self):
        self.task("active/spin-tests.md", "title: Spin tests", "status: active", "owner:", "  - carol", '  - "@Dan"')
        self.task("inbox/same-person.md", "title: Same person", "owner: alice", 'assignee: "@Alice"')
        self.task("meeting/handover-plan.md", "title: Handover plan", "owner: erin", "responsible: frank")
        self.task("review/shared-figure.md", "title: Shared figure", 'owner: [Alice, "@bob"]')
        self.assertEqual(self.grouped(), {"carol": ["spin-tests"], "Dan": ["spin-tests"],
                                          "alice": ["same-person", "shared-figure"],
                                          "erin": ["handover-plan"], "frank": ["handover-plan"],
                                          "bob": ["shared-figure"]})

    def test_a_readme_or_a_file_without_frontmatter_is_no_task(self):
        write(self.tasks / "README.md", "# The board\n\nOne file per task.\n")
        write(self.tasks / "inbox" / "notes.md", "Loose notes, no frontmatter.\n")
        self.task("inbox/fix-marker.md", "title: Fix marker", "owner: alice")
        self.assertEqual(self.grouped(), {"alice": ["fix-marker"]})

    def test_the_folder_is_the_column(self):
        self.task("done/finished.md", "title: Finished", "status: active", "owner: alice")
        self.task("archive/old.md", "title: Old", "status: archive", "owner: alice")
        self.task("active/reopened.md", "title: Reopened", "status: done", "owner: alice")
        self.task("inbox/fix-marker.md", "title: Fix marker", "status: inbox")
        by_owner = ho.section_tasks(self.root, TODAY)
        self.assertEqual(self.grouped(), {"alice": ["reopened"], "unassigned": ["fix-marker"]})
        self.assertEqual(by_owner["alice"][0]["status"], "active")

    def test_archive_columns_from_the_board_config(self):
        write(self.tasks / "config.json", json.dumps({"columns": [
            {"id": "todo"}, {"id": "doing"}, {"id": "done"},
            {"id": "shelved", "label": "Shelved", "archive": True}], "archive_after_days": 30}))
        self.task("doing/write-methods.md", "title: Write methods", "status: doing", "owner: alice")
        self.task("shelved/old-idea.md", "title: Old idea", "status: shelved", "owner: alice")
        self.task("t-009-plan.md", "id: t-009", "title: Plan", "assignee: bob")
        self.task("t-010-gone.md", "id: t-010", "title: Gone", "status: archived", "assignee: bob")
        by_owner = ho.section_tasks(self.root, TODAY)
        self.assertEqual(self.grouped(), {"alice": ["write-methods"], "bob": ["t-009"]})
        self.assertEqual(by_owner["alice"][0]["status"], "doing")
        self.assertEqual(by_owner["bob"][0]["status"], "todo", "a legacy task without status is in the first column")

    def test_legacy_flat_tasks_still_read(self):
        self.task("t-001-ica.md", "id: t-001", "title: Re-run ICA", "status: active", "assignee: alice")
        self.task("t-002-old.md", "id: t-002", "title: Old", "status: done", "assignee: bob")
        self.task("t-003-older.md", "id: t-003", "title: Older", "status: archived", "assignee: bob")
        self.task("t-004-plan.md", "id: t-004", "title: Plan", 'responsible: "@carol"')
        write(self.tasks / "flow.md", "# tasks\n")
        by_owner = ho.section_tasks(self.root, TODAY)
        self.assertEqual(self.grouped(), {"alice": ["t-001"], "carol": ["t-004"]})
        self.assertEqual(by_owner["alice"][0]["status"], "active")
        self.assertEqual(by_owner["carol"][0]["status"], "inbox")

    def test_markdown_lists_open_tasks_by_owner(self):
        self.task("review/shared-figure.md", "title: Shared figure", "status: review", "owner: [alice, bob]")
        self.task("inbox/fix-marker.md", "title: Fix marker", "status: inbox")
        with mock.patch.object(ho, "section_git", return_value={"repository": False}):
            md = ho.to_markdown(ho.build(self.root, hpc=False, today=TODAY))
        self.assertNotIn("by assignee", md)
        self.assertIn("## Open tasks by owner\n\n", md)
        section = md.split("## Open tasks by owner\n\n", 1)[1].split("\n\n## ", 1)[0]
        self.assertEqual(section.splitlines(), [
            "### alice", "- shared-figure - Shared figure (review)",
            "### bob", "- shared-figure - Shared figure (review)",
            "### unassigned", "- fix-marker - Fix marker (inbox)"])


if __name__ == "__main__":
    unittest.main()
