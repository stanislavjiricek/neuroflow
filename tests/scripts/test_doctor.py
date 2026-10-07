"""Tests for skills/neuroflow-core/scripts/doctor.py (stdlib unittest, no network)."""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("doctor", ROOT / "skills" / "neuroflow-core" / "scripts" / "doctor.py")
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


def report(project: Path, home: Path | None = None) -> tuple[int, dict]:
    """The doctor's JSON report by check id; `home` stands in for the home directory (default: an empty one)."""
    out = io.StringIO()
    with redirect_stdout(out):
        code = doctor.main(["--project", str(project), "--json", "--home", str(home or project / "no-home")])
    return code, {item["id"]: item for item in json.loads(out.getvalue())["checks"]}


def flowie_checks(home: Path | None) -> dict:
    checks: list = []
    doctor.check_flowie(checks, home)
    return {item["id"]: item for item in checks}


class DoctorTest(unittest.TestCase):
    def test_legacy_config_and_missing_gitignore_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".neuroflow").mkdir()
            (project / ".neuroflow" / "project_config.md").write_text("# Project config\nactive_phase: data\n", encoding="utf-8")
            code, checks = report(project)
            self.assertEqual(code, 1)
            self.assertEqual(checks["config"]["status"], "warn")
            self.assertIn("/neuroflow:migrate", checks["config"]["message"])
            self.assertEqual(checks["gitignore"]["status"], "warn")

    def test_current_contract_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".neuroflow").mkdir()
            (project / ".neuroflow" / "project_config.md").write_text("---\nnf_schema: 1\nactive_phase: data\n---\n", encoding="utf-8")
            (project / ".gitignore").write_text("\n".join(doctor.LOCAL_ONLY) + "\n", encoding="utf-8")
            (project / ".gitattributes").write_text("".join(f"{p} merge=union\n" for p in doctor.UNION_FILES), encoding="utf-8")
            _, checks = report(project)
            self.assertEqual(checks["config"]["status"], "ok")
            self.assertEqual(checks["gitignore"]["status"], "ok")
            self.assertEqual(checks["gitattributes"]["status"], "ok")

    def test_synced_folder_warns(self):
        checks: list = []
        doctor.check_location(checks, Path("C:/Users/me/OneDrive/projects/study"))
        self.assertEqual(checks[0]["status"], "warn")
        checks = []
        doctor.check_location(checks, Path("//server/share/study"))
        self.assertEqual(checks[0]["status"], "warn")

    def test_version_parse(self):
        self.assertEqual(doctor.parse_version("2.1.292 (Claude Code)"), (2, 1, 292))
        self.assertIsNone(doctor.parse_version("unknown"))

    def test_bad_project_is_usage_error(self):
        self.assertEqual(doctor.main(["--project", "/definitely/not/here/xyz"]), 2)

    def test_text_output_survives_a_legacy_code_page(self):
        # A Windows pipe defaults to the ANSI code page, which has no check mark and no CJK.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "日本"
            (project / ".neuroflow").mkdir(parents=True)
            env = dict(os.environ, PYTHONIOENCODING="cp1250")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "skills" / "neuroflow-core" / "scripts" / "doctor.py"),
                 "--project", str(project), "--home", str(Path(tmp) / "no-home")],
                capture_output=True, env=env, timeout=120)
            self.assertIn(proc.returncode, (0, 1), proc.stderr.decode("utf-8", "replace"))
            self.assertIn("✔", proc.stdout.decode("utf-8"))


class FlowieTest(unittest.TestCase):
    """G119: the person's flowie — unpushed commits and logged auto-sync failures."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.home = self.base / "home"
        self.flowie = self.home / ".neuroflow" / "flowie"
        self.log = self.home / ".neuroflow" / "flowie-sync.log"

    def tearDown(self):
        self._tmp.cleanup()

    def test_absent_flowie_says_nothing(self):
        self.assertEqual(flowie_checks(self.home), {})
        self.assertEqual(flowie_checks(None), {})
        self.home.mkdir()  # a home with no ~/.neuroflow/ at all
        self.assertEqual(flowie_checks(self.home), {})
        project = self.base / "project"
        project.mkdir()
        _, checks = report(project, self.home)
        self.assertFalse([cid for cid in checks if cid.startswith("flowie")])

    def test_logged_failures_are_counted_from_the_first_timestamp(self):
        self.flowie.mkdir(parents=True)
        self.log.write_text("2026-10-01T08:00:00Z push failed: tasks/inbox/review-figure-2.md\n\n"
                            "2026-10-02T09:30:00.000Z git pull failed: (command start)\n", encoding="utf-8")
        found = flowie_checks(self.home)
        self.assertEqual(set(found), {"flowie-sync-log"})  # not a git repository: no unpushed count
        self.assertEqual(found["flowie-sync-log"]["status"], "warn")
        self.assertIn("2 flowie auto-sync failure(s) since 2026-10-01T08:00:00Z", found["flowie-sync-log"]["message"])
        self.assertIn("/neuroflow:flowie --sync", found["flowie-sync-log"]["message"])
        project = self.base / "project"
        project.mkdir()
        code, checks = report(project, self.home)
        self.assertEqual(code, 1)
        self.assertEqual(checks["flowie-sync-log"]["status"], "warn")

    def test_empty_log_says_nothing(self):
        self.flowie.mkdir(parents=True)
        self.log.write_text("\n", encoding="utf-8")
        self.assertEqual(flowie_checks(self.home), {})


@unittest.skipUnless(shutil.which("git"), "needs git")
class FlowieGitTest(unittest.TestCase):
    """The unpushed count needs a git repository with an upstream; a local bare remote keeps it offline."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        gitconfig = self.base / "gitconfig"
        gitconfig.write_text("", encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.base),
            "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.org",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.org"})
        self.env.start()
        self.home = self.base / "home"
        self.flowie = self.home / ".neuroflow" / "flowie"
        self.flowie.mkdir(parents=True)
        self.git(self.flowie, "init", "-q", "-b", "main")
        self.commit("profile.md")

    def tearDown(self):
        self.env.stop()
        self._tmp.cleanup()

    def git(self, cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    def commit(self, name: str) -> None:
        (self.flowie / name).write_text(f"# {name}\n", encoding="utf-8")
        self.git(self.flowie, "add", "--", name)
        self.git(self.flowie, "commit", "-q", "-m", name, "--", name)

    def test_no_upstream_says_nothing(self):
        self.assertEqual(flowie_checks(self.home), {})

    def test_unpushed_commits_are_counted(self):
        remote = self.base / "remote.git"
        self.git(self.base, "init", "-q", "--bare", "-b", "main", str(remote))
        self.git(self.flowie, "remote", "add", "origin", str(remote))
        self.git(self.flowie, "push", "-q", "-u", "origin", "main")
        self.assertEqual(flowie_checks(self.home)["flowie-unpushed"]["status"], "ok")
        self.commit("ideas.md")
        self.commit("tasks.md")
        found = flowie_checks(self.home)["flowie-unpushed"]
        self.assertEqual(found["status"], "warn")
        self.assertIn("2 flowie commit(s) not pushed", found["message"])
        self.assertIn("/neuroflow:flowie --sync", found["message"])


if __name__ == "__main__":
    unittest.main()
