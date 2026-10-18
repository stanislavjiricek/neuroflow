"""Tests for skills/phase-flowie/scripts/local_paths.py (machine-local paths in flowie files)."""
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "phase-flowie" / "scripts" / "local_paths.py"
spec = importlib.util.spec_from_file_location("local_paths", SCRIPT)
lp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp)


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = lp.main(list(args))
    return code, out.getvalue(), err.getvalue()


class FindingsTests(unittest.TestCase):
    def paths(self, text: str) -> list[str]:
        return [hit["path"] for hit in lp.findings_in_text(text)]

    def test_machine_local_paths_are_found(self) -> None:
        text = "\n".join([
            "| server-a | /scratch/alice/projects/Oddball | git clone example-lab/oddball |",
            "Laptop copy: `~/projects/Oddball`",
            "Data: C:\\Users\\alice\\Documents\\datasets\\oddball",
            "Also D:/data/eeg and \\\\fileserver\\lab\\raw",
            "Home: /home/alice/code/x",
        ])
        found = self.paths(text)
        self.assertIn("/scratch/alice/projects/Oddball", found)
        self.assertIn("~/projects/Oddball", found)
        self.assertIn("C:\\Users\\alice\\Documents\\datasets\\oddball", found)
        self.assertIn("D:/data/eeg", found)
        self.assertIn("\\\\fileserver\\lab\\raw", found)
        self.assertIn("/home/alice/code/x", found)

    def test_an_absolute_path_counts_inside_code_spans_and_table_rows_only(self) -> None:
        self.assertEqual(self.paths("| box | /opt/lab/oddball |"), ["/opt/lab/oddball"])
        self.assertEqual(self.paths("lives in `/opt/lab/oddball`"), ["/opt/lab/oddball"])
        self.assertEqual(self.paths("the api is /v1/items and/or something"), [])

    def test_urls_relative_paths_commands_and_neuroflow_paths_are_not_paths(self) -> None:
        text = "\n".join([
            "Repo: https://github.com/example-lab/oddball and git@github.com:example-lab/oddball.git",
            "See projects/Oddball.md and ../notes/x.md",
            "Run /flowie --sync or /neuroflow:tasks --level flowie",
            "Registry: ~/.neuroflow/local-projects.json",
            "Ratio 3/4, date 2026/10/08",
        ])
        self.assertEqual(self.paths(text), [])

    def test_line_numbers_and_kinds(self) -> None:
        hits = lp.findings_in_text("ok\n/home/alice/x\n")
        self.assertEqual(hits, [{"line": 2, "kind": "home or mount folder", "path": "/home/alice/x"}])


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.flowie = self.tmp / "flowie"
        (self.flowie / "projects").mkdir(parents=True)
        (self.flowie / ".git").mkdir()
        (self.flowie / ".git" / "config").write_text("url = /home/alice/remote\n", encoding="utf-8")
        (self.flowie / "integrations.json").write_text('{"x": "C:\\\\Users\\\\alice"}\n', encoding="utf-8")
        (self.flowie / "profile.md").write_text("# Alice\n", encoding="utf-8")

    def test_clean_flowie_exits_0(self) -> None:
        code, out, _ = run("--flowie", str(self.flowie))
        self.assertEqual((code, out), (0, ""))

    def test_findings_exit_1_with_file_and_line_and_skip_local_files(self) -> None:
        (self.flowie / "projects" / "Oddball.md").write_text("# Oddball\n\n| laptop | `~/code/oddball` |\n", encoding="utf-8")
        code, out, _ = run("--flowie", str(self.flowie), "--json")
        self.assertEqual(code, 1)
        result = json.loads(out)
        self.assertEqual([(hit["file"], hit["line"]) for hit in result["findings"]], [("projects/Oddball.md", 3)])
        code, out, _ = run(str(self.flowie / "projects" / "Oddball.md"))
        self.assertEqual(code, 1)
        self.assertIn("Oddball.md:3: home folder (~/): ~/code/oddball", out)
        self.assertEqual(run(str(self.flowie / "integrations.json"))[0], 0, "a local-only file is never checked")

    def test_usage_errors_exit_2(self) -> None:
        self.assertEqual(run()[0], 2)
        self.assertEqual(run("--flowie", str(self.tmp / "missing"))[0], 2)
        self.assertEqual(run(str(self.tmp / "missing.md"))[0], 2)


if __name__ == "__main__":
    unittest.main()
