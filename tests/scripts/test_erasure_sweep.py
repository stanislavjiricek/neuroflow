"""Tests for skills/phase-data/scripts/erasure_sweep.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-data" / "scripts" / "erasure_sweep.py"
_spec = importlib.util.spec_from_file_location("nf_erasure_sweep", SCRIPT)
sweep = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = sweep
_spec.loader.exec_module(sweep)


def snapshot(base: Path) -> dict[str, bytes]:
    return {p.relative_to(base).as_posix(): p.read_bytes() for p in base.rglob("*") if p.is_file()}


class ErasureSweepTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.project = base / "study"
        self.home = base / "home"
        self.tmpdir = base / "tmp"
        for d in (self.project / ".neuroflow" / "ethics", self.project / "sourcedata" / "sub-07",
                  self.home / ".claude" / "projects" / "study", self.home / ".neuroflow" / "flowie" / "wiki",
                  self.tmpdir):
            d.mkdir(parents=True)
        (self.project / "participants.tsv").write_text(
            "participant_id\tage\nsub-07\t25\nsub-070\t30\nSUB-07\t25\n", encoding="utf-8"
        )
        (self.project / "sourcedata" / "sub-07" / "rec.vhdr").write_text("Brain Vision header\n", encoding="utf-8")
        (self.project / "notes.md").write_text("nothing relevant, xsub-07 is glued\n", encoding="utf-8")
        (self.home / ".claude" / "projects" / "study" / "abc.jsonl").write_text(
            json.dumps({"content": "row sub-07 and Dvořák"}) + "\n", encoding="utf-8"
        )
        (self.home / ".neuroflow" / "flowie" / "wiki" / "page.md").write_text("met sub-07 today\n", encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {"CLAUDE_CODE_TMPDIR": str(self.tmpdir)}, clear=False)
        self.env.start()
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        self.home_patch = mock.patch("pathlib.Path.home", return_value=self.home)
        self.home_patch.start()

    def tearDown(self) -> None:
        self.home_patch.stop()
        self.env.stop()
        self._tmp.cleanup()

    def run_sweep(self, *argv: str) -> tuple[int, dict | str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sweep.main(list(argv))
        text = out.getvalue()
        try:
            return code, json.loads(text), err.getvalue()
        except json.JSONDecodeError:
            return code, text, err.getvalue()

    def test_finds_project_transcript_and_home_hits_without_deleting(self) -> None:
        before_project, before_home = snapshot(self.project), snapshot(self.home)
        code, report, err = self.run_sweep("--id", "sub-07", "--root", str(self.project), "--no-git", "--json")
        self.assertEqual(code, 1, err)
        by_scope: dict[str, list[dict]] = {}
        for loc in report["locations"]:
            by_scope.setdefault(loc["scope"], []).extend(loc["files"])
        project = {f["path"]: f for f in by_scope["project"]}
        # case-insensitive by default: sub-07 and SUB-07 count, sub-070 does not
        self.assertEqual(project["participants.tsv"]["occurrences"], 2)
        self.assertTrue(project["sourcedata/sub-07/rec.vhdr"]["path_match"])
        self.assertNotIn("notes.md", project)
        self.assertTrue(any(f["path"].endswith("abc.jsonl") for f in by_scope["claude-code"]))
        self.assertTrue(any(f["path"].endswith("page.md") for f in by_scope["neuroflow"]))
        self.assertEqual(snapshot(self.project), before_project)
        self.assertEqual(snapshot(self.home), before_home)
        self.assertNotIn("sub-07", json.dumps(report["not_searched"]))

    def test_case_sensitive_and_json_escaped_names(self) -> None:
        code, report, _ = self.run_sweep("--id", "sub-07", "--root", str(self.project), "--no-git",
                                         "--case-sensitive", "--no-claude", "--no-neuroflow-home", "--json")
        self.assertEqual(code, 1)
        files = {f["path"]: f for f in report["locations"][0]["files"]}
        self.assertEqual(files["participants.tsv"]["occurrences"], 1)
        code, report, _ = self.run_sweep("--id", "Dvořák", "--root", str(self.project), "--no-git",
                                         "--no-neuroflow-home", "--json")
        self.assertEqual(code, 1)
        claude = [f for loc in report["locations"] if loc["scope"] == "claude-code" for f in loc["files"]]
        self.assertEqual(len(claude), 1, "the JSON-escaped form inside a transcript must be found")

    def test_no_hits_exit_zero_and_text_output(self) -> None:
        code, text, _ = self.run_sweep("--id", "sub-99", "--root", str(self.project), "--no-git")
        self.assertEqual(code, 0)
        self.assertIn("Nothing was deleted", text)
        self.assertIn("Not searched - check by hand", text)

    def test_short_id_refused(self) -> None:
        code, _, err = self.run_sweep("--id", "07", "--root", str(self.project))
        self.assertEqual(code, 2)
        self.assertIn("shorter than 3", err)

    def test_large_file_head_only(self) -> None:
        big = self.project / "raw.bin"
        big.write_bytes(b"sub-07" + b"\0" * (2 * 1024 * 1024) + b"sub-07")
        code, report, _ = self.run_sweep("--id", "sub-07", "--root", str(self.project), "--no-git", "--no-claude",
                                         "--no-neuroflow-home", "--max-full-mb", "1", "--head-kb", "4", "--json")
        files = {f["path"]: f for f in report["locations"][0]["files"]}
        self.assertEqual(files["raw.bin"]["occurrences"], 1)
        self.assertTrue(files["raw.bin"]["head_only"])

    def test_chunk_edges_counted_once(self) -> None:
        patterns = sweep.build_patterns(["sub-07"], case_sensitive=False)
        parts = []
        for i in range(400):
            parts.append(b"." * (i % 13) + (b"sub-07" if i % 3 else b"xsub-07") + b"_" + b"sub-070" * (i % 2))
        data = b"".join(parts)
        expected = sum(len(p.findall(data)) for p in patterns)
        path = self.project / "edges.txt"
        path.write_bytes(data)
        with mock.patch.object(sweep, "CHUNK", 64):
            got, head_only = sweep.scan_file(path, patterns, None, 0, overlap=20)
        self.assertFalse(head_only)
        self.assertEqual(got, expected)
        self.assertGreater(expected, 100)

    @unittest.skipUnless(shutil.which("git"), "git not available")
    def test_git_history_commits_counted(self) -> None:
        def git(*args: str) -> None:
            subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-C", str(self.project),
                            *args], check=True, capture_output=True)

        git("init", "-q")
        (self.project / "log.md").write_text("sub-07 session\n", encoding="utf-8")
        git("add", "log.md")
        git("commit", "-q", "-m", "add")
        (self.project / "log.md").write_text("session\n", encoding="utf-8")
        git("commit", "-q", "-am", "remove")
        code, report, _ = self.run_sweep("--id", "sub-07", "--root", str(self.project), "--no-claude",
                                         "--no-neuroflow-home", "--json")
        self.assertEqual(code, 1)
        project_git = report["git"][0]
        self.assertTrue(project_git["available"])
        self.assertEqual(project_git["commits"], 2)
        self.assertEqual(report["total_commits"], 2)
        self.assertTrue(re.fullmatch(r".*study", project_git["repo"]))


if __name__ == "__main__":
    unittest.main()
