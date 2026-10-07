"""Tests for skills/phase-brain-optimize/scripts/sweep_run.py (stdlib unittest, no network)."""

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
SCRIPT = REPO / "skills" / "phase-brain-optimize" / "scripts" / "sweep_run.py"

spec = importlib.util.spec_from_file_location("nf_sweep_run_under_test", SCRIPT)
sweep = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sweep
spec.loader.exec_module(sweep)

MODEL = """
import json, sys
a = dict(zip(sys.argv[1::2], sys.argv[2::2]))
g, tau = float(a["--g"]), float(a["--tau"])
if g == 2.0 and tau == 20:
    sys.exit(5)
json.dump({"populations": {"E": {"rate_hz": g * tau}}}, open(a["--out"], "w"))
print(f"rate={g * tau}")
"""


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sweep.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "models").mkdir()
        (self.root / "models" / "run_sim.py").write_text(textwrap.dedent(MODEL), encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def spec(self, name="spec.json", **over):
        s = {
            "name": "g-sweep",
            "command": [sys.executable, "models/run_sim.py", "--g", "{g}", "--tau", "{tau}", "--out", "{outdir}/m.json"],
            "grid": {"g": [0.1, 0.5, 1.0, 2.0], "tau": [5, 10, 20]},
            "metric": {"file": "{outdir}/m.json", "key": "populations.E.rate_hz"},
            "goal": "target", "target": 8.0,
            "out_dir": "models/optimize/g-sweep",
            "timeout_s": 120,
            "workers": 2,
        }
        s.update(over)
        path = self.root / name
        path.write_text(json.dumps(s), encoding="utf-8")
        return path

    def test_dry_run(self):
        code, out, _ = run(self.spec(), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("12 configuration(s)", out)
        self.assertFalse(Path("models/optimize").exists())

    def test_smoke_gate_failure_stops_the_sweep(self):
        code, out, _ = run(self.spec(smoke={"g": 2.0, "tau": 20}))
        self.assertEqual(code, 1)
        self.assertIn("SMOKE GATE FAILED", out)
        self.assertFalse(Path("models/optimize/g-sweep/runs").exists())

    def test_smoke_only(self):
        code, out, _ = run(self.spec(), "--smoke-only")
        self.assertEqual(code, 0)
        self.assertIn("Smoke gate passed", out)
        self.assertFalse(Path("models/optimize/g-sweep/runs").exists())

    def test_full_sweep_results_ranking_and_edge_warning(self):
        code, out, _ = run(self.spec())
        self.assertEqual(code, 1)  # g=2, tau=20 fails by design
        with open("models/optimize/g-sweep/results.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(r["status"] == "ok" for r in rows), 11)
        summary = json.loads(Path("models/optimize/g-sweep/summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["failed"], ["r012"])
        self.assertEqual(summary["best"][0]["metric"], 10.0)  # |10 - 8| is the closest
        self.assertTrue(summary["warnings"])
        self.assertIn("edge of the grid", out)
        self.assertEqual(json.loads(Path("models/optimize/g-sweep/runs/r001/result.json").read_text())["reused_from"],
                         "smoke gate")

    def test_resume_reruns_only_failures(self):
        run(self.spec())
        code, out, _ = run(self.spec(), "--resume")
        self.assertEqual(code, 1)
        self.assertEqual(out.count("FAILED"), 1)
        self.assertNotIn("r002", out.split("\n\n")[0].replace("[smoke", ""))

    def test_changed_spec_needs_new_out_dir(self):
        run(self.spec(), "--smoke-only")
        code, _, err = run(self.spec(grid={"g": [0.1], "tau": [5]}), "--smoke-only")
        self.assertEqual(code, 2)
        self.assertIn("different spec", err)
        # timeout and workers do not change what a run produces
        self.assertEqual(run(self.spec(timeout_s=99, workers=1), "--smoke-only")[0], 0)

    def test_points_and_regex_metric(self):
        spec = self.spec(grid={}, points=[{"g": 0.5, "tau": 10}, {"g": 1.0, "tau": 5}],
                         metric={"regex": r"rate=([0-9.]+)"}, goal=None)
        code, out, _ = run(spec)
        self.assertEqual(code, 0, out)
        summary = json.loads(Path("models/optimize/g-sweep/summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["ok"], 2)
        self.assertEqual(summary["best"], [])

    def test_spec_errors(self):
        self.assertEqual(run(self.spec(command=[sys.executable, "x.py", "{nope}"]))[0], 2)
        self.assertEqual(run(self.spec(goal="target", target=None))[0], 2)
        self.assertEqual(run(self.spec(points=[{"g": 1}]))[0], 2)


if __name__ == "__main__":
    unittest.main()
