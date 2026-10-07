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
        self.assertIn("## Open tasks by assignee", md)
        self.assertIn("OVERDUE", md)

    def test_xray_files_stay_with_leaver(self):
        paper = self.root / ".neuroflow" / "paper"
        write(paper / "draft.md", "draft\n")
        write(paper / "xray-draft-2026-10-07.md", "critique\n")
        write(paper / "xray-draft-2026-10-07.jsonl", "{}\n")
        self.assertIn({"path": ".neuroflow/paper/xray-*", "files": 2}, ho.section_personal(self.root))

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


if __name__ == "__main__":
    unittest.main()
