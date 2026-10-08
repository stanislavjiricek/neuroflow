"""Tests for scripts/automation/bump_version.py on a fixture repo."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from .helpers import load, make_repo, write

bump = load("bump_version")
rc = load("repo_checks")


class BumpVersionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bump.main(["--root", str(self.root), *args])
        return code, out.getvalue() + err.getvalue()

    def versions(self):
        return {rel: rc.site_versions(self.root, rel) for rel in rc.VERSION_SITES}

    def test_next_patch(self):
        self.assertEqual(bump.next_patch("0.2.21"), "0.2.22")
        with self.assertRaises(ValueError):
            bump.next_patch("0.2")

    def test_patch_bump_writes_all_four_sites(self):
        code, out = self.main()
        self.assertEqual(code, 0, out)
        self.assertEqual(set(map(tuple, self.versions().values())), {("1.2.4",)})
        self.assertIn("What's new in 1.2.4", out)
        self.assertEqual(rc.run(self.root, only={"V2"}), [])

    def test_dry_run_writes_nothing(self):
        code, out = self.main("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("-> 1.2.4", out)
        self.assertEqual(set(map(tuple, self.versions().values())), {("1.2.3",)})

    def test_check_and_sync(self):
        write(self.root, {"mkdocs.yml": (self.root / "mkdocs.yml").read_text(encoding="utf-8")
                          .replace('version: "1.2.3"', 'version: "1.1.0"')})
        self.assertEqual(self.main("--check")[0], 1)
        self.assertEqual(self.main("--sync")[0], 0)
        self.assertEqual(self.main("--check")[0], 0)
        self.assertEqual(self.versions()[rc.MKDOCS_YML], ["1.2.3"])

    def test_set_and_bad_input(self):
        self.assertEqual(self.main("--set", "2.0.0")[0], 0)
        self.assertEqual(self.versions()[rc.PLUGIN_JSON], ["2.0.0"])
        self.assertEqual(self.main("--set", "two")[0], 2)

    def test_absent_repo_memory_is_skipped(self):
        (self.root / rc.REPO_CONFIG).unlink()
        code, out = self.main()
        self.assertEqual(code, 0, out)
        self.assertIsNone(self.versions()[rc.REPO_CONFIG])

    def test_crlf_files_keep_their_line_endings(self):
        path = self.root / rc.PLUGIN_JSON
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.main()
        data = path.read_bytes()
        self.assertIn(b'"version": "1.2.4"', data)
        self.assertEqual(data.count(b"\r\n"), data.count(b"\n"))


if __name__ == "__main__":
    unittest.main()
