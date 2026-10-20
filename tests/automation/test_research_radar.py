"""Tests for scripts/automation/research_radar.py: the recent-changes context comes from docs/changelog.md."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from .helpers import load, make_repo, write

rr = load("research_radar")

CHANGELOG = (
    "---\ntitle: Changelog\n---\n\n# Changelog\n\n## 1.2.3\n\n- x\n\n### Fixes\n\n## Not a version\n\n"
    "## v1.2.2\n\n- y\n\n## 1.2.1 — a patch\n\n## 1.2.0\n"
)


class RecentChangelogTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_the_version_headings_of_the_changelog_newest_first(self):
        write(self.root, {"docs/changelog.md": CHANGELOG})
        self.assertEqual(rr.recent_changelog_items(3, self.root), ["1.2.3", "1.2.2", "1.2.1"])
        self.assertEqual(rr.recent_changelog_items(root=self.root), ["1.2.3", "1.2.2", "1.2.1", "1.2.0"])

    def test_the_readme_is_not_the_source(self):
        # README.md keeps only the newest release; its heading must not stand in for the changelog
        write(self.root, {"docs/changelog.md": "# Changelog\n\n## 1.2.3\n\n## 1.2.2\n"})
        self.assertIn("What's new in 1.2.3", (self.root / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(rr.recent_changelog_items(5, self.root), ["1.2.3", "1.2.2"])

    def test_no_changelog_gives_nothing(self):
        (self.root / "docs" / "changelog.md").unlink()
        self.assertEqual(rr.recent_changelog_items(5, self.root), [])

    def test_the_report_names_the_changelog_versions(self):
        write(self.root, {"docs/changelog.md": CHANGELOG})
        with mock.patch.object(rr, "REPO_ROOT", self.root):
            report = rr.build_report("2026-01-02", "Week 1, 2026")
        self.assertIn("Most recent versions in changelog: 1.2.3, 1.2.2, 1.2.1, 1.2.0", report)
        self.assertIn("neuroflow v1.2.3", report)
        self.assertIn("1 commands", report)


if __name__ == "__main__":
    unittest.main()
