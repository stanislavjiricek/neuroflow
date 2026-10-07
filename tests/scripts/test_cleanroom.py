"""Tests for skills/phase-data-analyze/scripts/cleanroom.py (stdlib unittest, no network; needs git)."""

import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-data-analyze" / "scripts" / "cleanroom.py"

spec = importlib.util.spec_from_file_location("nf_cleanroom_under_test", SCRIPT)
cleanroom = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cleanroom
spec.loader.exec_module(cleanroom)

HAS_GIT = shutil.which("git") is not None

STATS = """
import json, os, random
vals = [float(x) for x in open("data/in.csv").read().strip().split(",")]
mean = sum(vals) / len(vals) + float(os.environ.get("NF_TEST_NOISE", "0")) * random.random()
os.makedirs("results", exist_ok=True)
json.dump({"mean": mean, "n": len(vals), "label": "ok"}, open("results/stats.json", "w"))
open("results/table.csv", "w").write(f"metric,value\\nmean,{mean}\\n")
"""


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cleanroom.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.org", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


@unittest.skipUnless(HAS_GIT, "git is not installed")
class CleanroomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "project"
        (self.repo / "scripts" / "analysis").mkdir(parents=True)
        (self.repo / "data").mkdir()
        (self.repo / ".gitignore").write_text("data/\nresults/\n", encoding="utf-8")
        (self.repo / "data" / "in.csv").write_text("1,2,3,4", encoding="utf-8")
        (self.repo / "scripts" / "analysis" / "stats.py").write_text(textwrap.dedent(STATS), encoding="utf-8")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        subprocess.run([sys.executable, "scripts/analysis/stats.py"], cwd=self.repo, check=True)
        os.environ.pop("NF_TEST_NOISE", None)

    def tearDown(self):
        os.environ.pop("NF_TEST_NOISE", None)
        self.tmp.cleanup()

    def clean(self, *extra, workdir="w"):
        return run("--current-python", "--repo", self.repo, "--workdir", self.root / workdir, *extra)

    def cmd(self):
        return ["--", sys.executable, "scripts/analysis/stats.py"]

    def test_identical_outputs_reproduce(self):
        report = self.root / "rep.md"
        code, out, _ = self.clean("--output", "results/stats.json", "--output", "results/table.csv",
                                  "--link", "data", "--report", report, *self.cmd())
        self.assertEqual(code, 0, out)
        self.assertIn("**reproduced**", report.read_text(encoding="utf-8"))
        self.assertIn("| `results/stats.json` | identical |", out)
        self.assertFalse((self.root / "w" / "repo").exists())   # cleaned up
        self.assertTrue((self.repo / "data" / "in.csv").exists())  # linked data untouched

    def test_small_float_drift_is_within_tolerance(self):
        os.environ["NF_TEST_NOISE"] = "1e-9"
        code, out, _ = self.clean("--output", "results/stats.json", "--output", "results/table.csv",
                                  "--link", "data", *self.cmd())
        self.assertEqual(code, 0, out)
        self.assertIn("within-tolerance", out)

    def test_real_difference_is_not_reproduced_and_keeps_scratch(self):
        os.environ["NF_TEST_NOISE"] = "0.5"
        code, out, _ = self.clean("--output", "results/stats.json", "--link", "data", *self.cmd())
        self.assertEqual(code, 1)
        self.assertIn("NOT reproduced", out)
        self.assertIn("$.mean", out)
        self.assertTrue((self.root / "w" / "repo").exists())
        self.assertFalse(os.path.lexists(self.root / "w" / "repo" / "data"))  # link removed after the run
        self.assertTrue((self.repo / "data" / "in.csv").exists())

    def test_missing_data_means_missing_output(self):
        code, out, _ = self.clean("--output", "results/stats.json", *self.cmd())
        self.assertEqual(code, 1)
        self.assertIn("| `results/stats.json` | missing |", out)

    def test_output_inside_linked_folder_is_refused(self):
        code, _, err = self.clean("--output", "data/derived.json", "--link", "data", *self.cmd())
        self.assertEqual(code, 2)
        self.assertIn("write into the original data", err)

    def test_record_supplies_command_commit_and_hashes(self):
        stats = self.repo / "results" / "stats.json"
        record = {
            "nf_provenance": 1, "script": "scripts/analysis/stats.py", "argv": ["scripts/analysis/stats.py"],
            "cwd": ".", "git": {"commit": git(self.repo, "rev-parse", "HEAD"), "dirty": False},
            "outputs": [{"path": "results/stats.json", "sha256": hashlib.sha256(stats.read_bytes()).hexdigest()}],
        }
        rec_path = self.root / "record.json"
        rec_path.write_text(json.dumps(record), encoding="utf-8")
        stats.write_text('{"changed": true}', encoding="utf-8")  # the working tree drifted since the run
        code, out, _ = self.clean("--record", rec_path, "--link", "data")
        self.assertEqual(code, 0, out)
        self.assertIn("identical", out)

    def test_unknown_commit_is_setup_error(self):
        code, _, err = self.clean("--ref", "0" * 40, "--output", "results/stats.json", *self.cmd())
        self.assertEqual(code, 2)
        self.assertIn("git", err)


class CompareTests(unittest.TestCase):
    def test_environment_choice_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            cleanroom.main(["--output", "x", "--", "python", "x.py"])
        self.assertEqual(cm.exception.code, 2)

    def test_json_tolerance(self):
        ok, diff, _ = cleanroom.compare_json({"a": [1.0, 2.0], "b": "x"}, {"a": [1.0, 2.0 + 1e-12], "b": "x"}, 1e-6, 1e-9)
        self.assertTrue(ok)
        self.assertLess(diff, 1e-9)
        ok, _, msg = cleanroom.compare_json({"a": 1.0}, {"a": 1.1}, 1e-6, 1e-9)
        self.assertFalse(ok)
        self.assertIn("$.a", msg)
        self.assertFalse(cleanroom.compare_json({"a": 1}, {"b": 1}, 1e-6, 1e-9)[0])
        self.assertFalse(cleanroom.compare_json([1], ["1"], 1e-6, 1e-9)[0])
        self.assertTrue(cleanroom.compare_json(math.nan, math.nan, 1e-6, 1e-9)[0])
        self.assertFalse(cleanroom.compare_json(True, 1, 1e-6, 1e-9)[0])

    def test_table_tolerance(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c = Path(d) / "a.csv", Path(d) / "b.csv", Path(d) / "c.csv"
            a.write_text("m,v\nmean,2.5\n", encoding="utf-8")
            b.write_text("m,v\nmean,2.5000000001\n", encoding="utf-8")
            c.write_text("m,v\nmedian,2.5\n", encoding="utf-8")
            self.assertTrue(cleanroom.compare_table(a, b, 1e-6, 1e-9)[0])
            self.assertFalse(cleanroom.compare_table(a, c, 1e-6, 1e-9)[0])


if __name__ == "__main__":
    unittest.main()
