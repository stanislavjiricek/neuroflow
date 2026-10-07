"""Tests for skills/phase-output/scripts/history_audit.py (stdlib unittest, local git only).

Token-shaped test strings are assembled at runtime so this file itself never
contains a secret-looking literal.
"""

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
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-output" / "scripts" / "history_audit.py"


def load():
    name = "nf_test_history_audit"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ha = load()
GH_TOKEN = "gh" + "p_" + "Zy9Xw8Vu7Ts6" * 3


@unittest.skipUnless(shutil.which("git"), "git not installed")
class HistoryAuditTests(unittest.TestCase):
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
        self.root = self.base / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def commit(self, files: dict[str, bytes | str], message: str = "c") -> None:
        for rel, data in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, str):
                path.write_text(data, encoding="utf-8")
            else:
                path.write_bytes(data)
        self.git("add", "-A", "-f")
        self.git("commit", "-q", "-m", message)

    def run_audit(self, *extra: str) -> tuple[int, dict, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = ha.main(["--root", str(self.root), "--json", *extra])
        out = buf.getvalue()
        return code, json.loads(out), out

    def test_clean_history(self):
        self.commit({"README.md": "# project\n", "scripts/run.py": "print('hi')\n"})
        code, rep, _ = self.run_audit()
        self.assertEqual(code, 0, rep)
        self.assertEqual(rep["findings"], [])
        self.assertEqual(rep["commits"], 1)

    def test_deleted_files_are_still_found(self):
        self.commit({".neuroflow/sessions/2026-10-01.md": "log\n",
                     ".neuroflow/finance/budget.md": "money\n",
                     "config.py": f'TOKEN = "{GH_TOKEN}"\n',
                     "data/sub-01_eeg.edf": b"0       " + b" " * 248,
                     ".neuroflow/ideation/papers/smith2020.pdf": b"%PDF-1.4\n"})
        self.git("rm", "-q", "-r", ".neuroflow/sessions", "config.py", "data")
        self.git("commit", "-q", "-m", "remove")
        code, rep, out = self.run_audit()
        self.assertEqual(code, 1)
        found = {(f["kind"], f["path"]) for f in rep["findings"]}
        self.assertIn(("sensitive-path", ".neuroflow/sessions/2026-10-01.md"), found)
        self.assertIn(("sensitive-path", ".neuroflow/finance/budget.md"), found)
        self.assertIn(("secret", "config.py"), found)
        self.assertIn(("data-file", "data/sub-01_eeg.edf"), found)
        self.assertIn(("paper-pdf", ".neuroflow/ideation/papers/smith2020.pdf"), found)
        self.assertNotIn(GH_TOKEN, out)
        secret = next(f for f in rep["findings"] if f["kind"] == "secret")
        self.assertTrue(secret["first_commit"])

    def test_personal_data_and_known_collaborators(self):
        self.commit({".neuroflow/project_config.md": "---\nproject_name: P\n---\n- email: pi@uni-lab.org\n",
                     "notes/contacts.md": "pi@uni-lab.org\nother.person@clinic-lab.org\n"})
        code, rep, out = self.run_audit()
        self.assertEqual(code, 1)
        personal = [f for f in rep["findings"] if f["kind"] == "personal-data"]
        self.assertEqual([f["path"] for f in personal], ["notes/contacts.md"])
        self.assertEqual(personal[0]["count"], 1)
        self.assertNotIn("other.person", out)

    def test_large_blob(self):
        self.commit({"big.txt": "a" * 5000})
        code, rep, _ = self.run_audit("--large-mb", "0.001")
        self.assertEqual(code, 1)
        self.assertEqual(rep["findings"][0]["kind"], "large-file")

    def test_memory_note(self):
        self.commit({".neuroflow/reasoning/general.jsonl": '{"statement": "x"}\n'})
        code, rep, _ = self.run_audit()
        self.assertEqual(code, 0)
        self.assertTrue(rep["notes"])

    def test_not_a_repository(self):
        other = self.base / "plain"
        other.mkdir()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = ha.main(["--root", str(other), "--json"])
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(buf.getvalue()))


if __name__ == "__main__":
    unittest.main()
