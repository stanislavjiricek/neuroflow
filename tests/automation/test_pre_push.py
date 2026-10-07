"""Tests for scripts/automation/pre_push_version_check.py against a throwaway git repo."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from .helpers import load

pre_push = load("pre_push_version_check")
ZERO = "0" * 40


@unittest.skipUnless(shutil.which("git"), "git not installed")
class PrePushTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.commit({".claude-plugin/plugin.json": self.manifest("1.0.0"), "skills/x/SKILL.md": "x\n"}, "base")
        # Pretend the base commit is what origin's main points at.
        self.git("update-ref", "refs/remotes/origin/main", self.head())
        self.git("checkout", "-q", "-b", "feature")

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def manifest(version):
        return json.dumps({"name": "neuroflow", "version": version}, indent=2) + "\n"

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                              cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def head(self):
        return self.git("rev-parse", "HEAD")

    def commit(self, files, message):
        for rel, content in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def push(self, remote_sha=ZERO):
        line = f"refs/heads/feature {self.head()} refs/heads/feature {remote_sha}\n"
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = pre_push.main(stdin=[line], cwd=str(self.root))
        return code, err.getvalue()

    def test_first_push_of_a_new_branch_is_checked(self):
        self.commit({"skills/x/SKILL.md": "changed\n"}, "change")
        code, err = self.push()
        self.assertEqual(code, 1)
        self.assertIn("bump_version.py", err)

    def test_bumped_branch_passes_on_every_later_push(self):
        self.commit({"skills/x/SKILL.md": "changed\n", ".claude-plugin/plugin.json": self.manifest("1.0.1")}, "bump")
        first = self.head()
        self.assertEqual(self.push()[0], 0)
        self.commit({"skills/x/SKILL.md": "changed again\n"}, "follow-up")
        self.assertEqual(self.push(remote_sha=first)[0], 0)  # same bump vs main, like CI

    def test_exempt_paths_need_no_bump(self):
        self.commit({".github/workflows/x.yml": "on: push\n", "tests/automation/t.py": "pass\n"}, "ci")
        self.assertEqual(self.push()[0], 0)


if __name__ == "__main__":
    unittest.main()
