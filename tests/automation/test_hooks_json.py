"""Smoke test for hooks/hooks.json: feed simulated PostToolUse events into the real command hooks.

Hooks end in `; true`, so a broken hook fails invisibly (the ruff and flowie hooks were dead for
many releases before 0.2.21). This runs each command with sample stdin JSON and checks the
outcome: ruff is called on .py files only, and an edit inside ~/.neuroflow/flowie/ is committed
and pushed without integrations.json. A fake `ruff` and a throwaway flowie repo with a bare
remote keep it offline.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SH = shutil.which("sh") or shutil.which("bash")


def hook_commands() -> list[str]:
    data = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    return [h["command"] for group in data.get("hooks", {}).get("PostToolUse", [])
            for h in group.get("hooks", []) if h.get("type") == "command"]


def pick(fragment: str) -> str:
    matches = [c for c in hook_commands() if fragment in c]
    if len(matches) != 1:
        raise AssertionError(f"expected one PostToolUse command hook containing {fragment!r}, found {len(matches)}")
    return matches[0]


@unittest.skipUnless(SH and shutil.which("git"), "needs a POSIX shell and git")
class HookSmokeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.ruff_log = self.tmp / "ruff.log"
        fake = self.bin / "ruff"
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$RUFF_LOG"\n', encoding="utf-8", newline="\n")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.env = dict(os.environ, RUFF_LOG=str(self.ruff_log),
                        PATH=str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")

    def tearDown(self):
        self._tmp.cleanup()

    def run_hook(self, command: str, file_path: Path | None):
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_response": {"type": "update"},
                   "tool_input": {"file_path": str(file_path)} if file_path else {}}
        return subprocess.run([SH, "-c", command], input=json.dumps(payload), capture_output=True, text=True,
                              env=self.env, timeout=120)

    def git(self, cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                              env=self.env).stdout.strip()

    def test_ruff_hook_formats_python_files_only(self):
        command = pick("ruff format")
        script = self.tmp / "analysis.py"
        script.write_text("x=1\n", encoding="utf-8")
        notes = self.tmp / "notes.md"
        notes.write_text("# notes\n", encoding="utf-8")
        for target in (notes, None):
            self.assertEqual(self.run_hook(command, target).returncode, 0)
        self.assertFalse(self.ruff_log.exists(), "ruff ran on a non-Python file")
        result = self.run_hook(command, script)
        self.assertEqual(result.returncode, 0)
        if not self.ruff_log.exists():
            self.skipTest("this shell could not run the fake ruff executable")
        logged = self.ruff_log.read_text(encoding="utf-8").split()
        self.assertEqual(logged[0], "format")
        self.assertEqual(logged[1].replace("\\", "/"), str(script).replace("\\", "/"))

    def test_flowie_hook_commits_and_pushes_without_credentials(self):
        command = pick(".neuroflow/flowie")
        remote = self.tmp / "remote.git"
        flowie = self.tmp / "home" / ".neuroflow" / "flowie"
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(remote))
        flowie.mkdir(parents=True)
        self.git(flowie, "init", "-q", "-b", "main")
        (flowie / "profile.md").write_text("# profile\n", encoding="utf-8")
        self.git(flowie, "add", "-A")
        self.git(flowie, "commit", "-q", "-m", "init")
        self.git(flowie, "remote", "add", "origin", str(remote))
        self.git(flowie, "push", "-q", "-u", "origin", "main")

        (flowie / "profile.md").write_text("# profile\n\nNew line.\n", encoding="utf-8")
        (flowie / "integrations.json").write_text('{"api_key": "not-for-git"}\n', encoding="utf-8")
        result = self.run_hook(command, flowie / "profile.md")
        self.assertEqual(result.returncode, 0)

        remote_files = self.git(remote, "ls-tree", "-r", "--name-only", "main").split()
        self.assertIn("profile.md", remote_files)
        self.assertNotIn("integrations.json", remote_files)
        self.assertIn("New line.", self.git(remote, "show", "main:profile.md"))

    def test_hooks_ignore_unrelated_paths_and_bad_input(self):
        command = pick(".neuroflow/flowie")
        self.assertEqual(self.run_hook(command, self.tmp / "project" / "x.md").returncode, 0)
        broken = subprocess.run([SH, "-c", command], input="not json", capture_output=True, text=True,
                                env=self.env, timeout=60)
        self.assertEqual(broken.returncode, 0)


if __name__ == "__main__":
    unittest.main()
