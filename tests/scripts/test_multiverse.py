"""Tests for skills/phase-data-analyze/scripts/multiverse.py (stdlib unittest, no network)."""

import contextlib
import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-data-analyze" / "scripts" / "multiverse.py"

spec = importlib.util.spec_from_file_location("nf_multiverse_under_test", SCRIPT)
multiverse = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = multiverse
spec.loader.exec_module(multiverse)

ANALYSIS = """
import json, sys
a = dict(zip(sys.argv[1::2], sys.argv[2::2]))
low, ref = float(a["--lowcut"]), a["--ref"]
if low == 1.0 and ref == "mastoids":
    sys.exit(3)
d = round(0.3 + low / 10 + (0.05 if ref == "average" else 0), 4)
json.dump({"stats": {"d": d}, "p": 0.04 if low < 1 else 0.2}, open(a["--out"], "w"))
print(f"d={d}")
"""


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = multiverse.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class MultiverseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "ana.py").write_text(textwrap.dedent(ANALYSIS), encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.ledger = Path(".neuroflow/data-analyze/multiverse.md")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def spec(self, **over):
        s = {
            "name": "p3-window",
            "command": [sys.executable, "ana.py", "--lowcut", "{lowcut}", "--ref", "{ref}", "--out", "{outdir}/result.json"],
            "grid": {"lowcut": [0.1, 0.5, 1.0], "ref": ["average", "mastoids"]},
            "result": {"file": "{outdir}/result.json", "keys": ["stats.d", "p"]},
            "p_key": "p",
            "out_dir": "results/exploratory/multiverse/p3-window",
            "timeout_s": 120,
        }
        s.update(over)
        path = self.root / "spec.json"
        path.write_text(json.dumps(s), encoding="utf-8")
        return path

    def ledger_rows(self):
        return [ln for ln in self.ledger.read_text(encoding="utf-8").splitlines() if ln.startswith("| 20")]

    def test_dry_run_lists_and_runs_nothing(self):
        code, out, _ = run(self.spec(), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("6 specification(s) declared", out)
        self.assertFalse(self.ledger.exists())
        self.assertFalse(Path("results").exists())

    def test_full_run_logs_every_specification(self):
        code, out, _ = run(self.spec())
        self.assertEqual(code, 1)  # s06 fails by design
        text = self.ledger.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Analysis multiverse"))
        self.assertIn("| Date | Loop | Iter | Choice | Value | Result | Kept |", text)
        rows = self.ledger_rows()
        self.assertEqual(len(rows), 6)
        self.assertIn("| multiverse:p3-window | s01 | lowcut, ref | 0.1, average | stats.d = 0.36, p = 0.04 | n/a |", rows[0])
        self.assertIn("FAILED (exit code 3)", rows[5])
        self.assertNotIn("Specifications tried", text)  # no running totals in an append-only ledger
        with open("results/exploratory/multiverse/p3-window/curve.csv", newline="", encoding="utf-8") as fh:
            curve = list(csv.DictReader(fh))
        self.assertEqual(len(curve), 5)
        self.assertEqual(curve[0]["spec_id"], "s02")  # smallest d first
        self.assertIn("4 of 5 specification(s) with p < 0.05", out)
        self.assertIn("EXPLORATORY", out)
        self.assertIn("not in it", out)

    def test_resume_does_not_duplicate_rows(self):
        run(self.spec())
        code, out, _ = run(self.spec(), "--resume")
        self.assertEqual(code, 1)
        rows = self.ledger_rows()
        self.assertEqual(len(rows), 7)  # only the failed s06 is retried and logged again
        self.assertEqual(sum("| s06 |" in r for r in rows), 2)
        self.assertIn("already done", out)

    def test_all_ok_exit_0_with_regex_result(self):
        spec = self.spec(grid={"lowcut": [0.1, 0.5], "ref": ["average"]}, result={"regex": {"d": r"d=([0-9.]+)"}})
        spec_data = json.loads(spec.read_text())
        spec_data.pop("p_key")
        spec.write_text(json.dumps(spec_data), encoding="utf-8")
        code, out, _ = run(spec)
        self.assertEqual(code, 0, out)
        self.assertIn("d = 0.36", self.ledger_rows()[0])

    def test_out_dir_must_be_exploratory(self):
        code, _, err = run(self.spec(out_dir="results/p3"))
        self.assertEqual(code, 2)
        self.assertIn("exploratory", err)
        self.assertFalse(self.ledger.exists())

    def test_unknown_placeholder_is_spec_error(self):
        code, _, err = run(self.spec(command=[sys.executable, "ana.py", "{nope}"]))
        self.assertEqual(code, 2)
        self.assertIn("{nope}", err)

    def test_existing_ledger_is_appended_not_rewritten(self):
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text("# Analysis multiverse — EXPLORATORY\n\n| Date | Loop | Iter | Choice | Value | Result | Kept |\n"
                               "|------|------|------|--------|-------|--------|------|\n"
                               "| 2026-10-01 | connectivity | 012 | band-pass low cutoff | 1 Hz | d = 0.41 | no |",
                               encoding="utf-8")
        run(self.spec(grid={"lowcut": [0.1], "ref": ["average"]}))
        text = self.ledger.read_text(encoding="utf-8")
        self.assertIn("| 2026-10-01 | connectivity | 012 |", text)
        self.assertEqual(len(self.ledger_rows()), 2)
        self.assertTrue(text.endswith("| n/a |\n"))

    def test_pipes_in_values_are_escaped(self):
        self.assertEqual(multiverse.cell("a|b\nc"), "a\\|b c")


if __name__ == "__main__":
    unittest.main()
