"""Tests for skills/phase-flowie/scripts/local_paths.py (machine-local paths in flowie files)."""
import importlib.util
import io
import json
import shutil
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

    def test_other_spellings_of_a_local_folder(self) -> None:
        text = "\n".join([
            "on the server it is /projects/oddball/raw",
            "the Mac copy: /Volumes/LabDisk/oddball",
            "$HOME/code/oddball and %USERPROFILE%\\data\\oddball",
            "open file:///C:/Users/alice/report.pdf",
            "files C:\\Users\\alice\\data\\*.edf and /home/alice/sub-*/eeg",
            "old memory in ~/.neuroflow-old/flowie",
            '{"repo": "/projects/oddball"}',
        ])
        found = self.paths(text)
        for path in ("/projects/oddball/raw", "/Volumes/LabDisk/oddball", "$HOME/code/oddball",
                     "%USERPROFILE%\\data\\oddball", "file:///C:/Users/alice/report.pdf",
                     "C:\\Users\\alice\\data\\*.edf", "/home/alice/sub-*/eeg", "~/.neuroflow-old/flowie"):
            self.assertIn(path, found)

    def test_paths_in_a_fenced_code_block(self) -> None:
        text = "```bash\ncd /opt2/lab/oddball\nls\n```\nafter the block /opt2/lab/x is prose\n"
        self.assertEqual(self.paths(text), ["/opt2/lab/oddball"])

    def test_an_absolute_path_counts_inside_code_spans_and_table_rows_only(self) -> None:
        self.assertEqual(self.paths("| box | /labdisk/alice/oddball |"), ["/labdisk/alice/oddball"])
        self.assertEqual(self.paths("lives in `/labdisk/alice/oddball`"), ["/labdisk/alice/oddball"])
        self.assertEqual(self.paths("joined in code: `'/sub-01/eeg'`"), [], "two parts: a fragment, not a folder")
        self.assertEqual(self.paths("the topic is cats/dogs and/or something"), [])

    def test_system_and_web_paths_links_and_examples_are_not_paths(self) -> None:
        text = "\n".join([
            "Repo: https://github.com/example-lab/oddball and git@github.com:example-lab/oddball.git",
            "See projects/Oddball.md and ../notes/x.md",
            "Run /flowie --sync or /neuroflow:tasks --level flowie",
            "Registry: ~/.neuroflow/local-projects.json and `~/.neuroflow/flowie/`",
            "Ratio 3/4, date 2026/10/08",
            "Discard with `> /dev/null`, run `/usr/bin/python3`, see `/etc/hosts`",
            "| GET | /api/v1/users |",
            "`POST /v1/chat/completions`",
            "| ICA | [notes](/wiki/methods/ica.md) |",
            "Example: `/storage/.../data`, `~/{project}`, C:\\Users\\<name>\\data",
        ])
        self.assertEqual(self.paths(text), [])

    def test_a_marked_line_is_kept(self) -> None:
        self.assertEqual(self.paths("server: /scratch/alice/oddball <!-- nf: local-path-ok -->"), [])

    def test_review_cases(self) -> None:
        self.assertEqual(self.paths("see `/path/to/your/data` and `'/sub-01/ses-01/eeg'` in the code"), [])
        self.assertEqual(self.paths("cluster copy: /beegfs/alice/oddball"), ["/beegfs/alice/oddball"])

    def test_line_numbers_and_kinds(self) -> None:
        hits = lp.findings_in_text("ok\n/home/alice/x\n")
        self.assertEqual(hits, [{"line": 2, "kind": "home or storage folder", "path": "/home/alice/x"}])


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
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
        self.assertIn("Oddball.md:3: home folder: ~/code/oddball", out)
        self.assertEqual(run(str(self.flowie / "integrations.json"))[0], 0, "a local-only file is never checked")

    def test_paths_relative_to_root(self) -> None:
        (self.flowie / "projects" / "Oddball.md").write_text("/home/alice/oddball\n", encoding="utf-8")
        code, out, _ = run("--root", str(self.flowie), "--json", "projects/Oddball.md", "profile.md")
        self.assertEqual(code, 1)
        result = json.loads(out)
        self.assertEqual((result["checked"], result["findings"][0]["file"]), (2, "projects/Oddball.md"))
        self.assertEqual(run("--root", str(self.flowie), "projects/gone.md")[0], 0, "a path that is gone has nothing to check")

    def test_usage_errors_exit_2(self) -> None:
        self.assertEqual(run()[0], 2)
        self.assertEqual(run("--flowie", str(self.tmp / "missing"))[0], 2)
        self.assertEqual(run("--root", str(self.tmp / "missing"), "x.md")[0], 2)
        self.assertEqual(run(str(self.tmp / "missing.md"))[0], 2)


if __name__ == "__main__":
    unittest.main()
