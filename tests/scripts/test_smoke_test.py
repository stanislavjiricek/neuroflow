"""Tests for skills/phase-brain-build/scripts/smoke_test.py (stdlib unittest, no network)."""

import contextlib
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
SCRIPT = REPO / "skills" / "phase-brain-build" / "scripts" / "smoke_test.py"

spec = importlib.util.spec_from_file_location("nf_smoke_test_under_test", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)

MODEL = """
import json, os, sys
mode = sys.argv[1]
out = {
    "ok": {"populations": {"E": {"n_spikes": 400, "rate_hz": 10.0}, "I": {"n_spikes": 200, "rate_hz": 25.0}}},
    "runaway": {"populations": {"E": {"rate_hz": 480.0}}},
    "silent": {"populations": {"E": {"rate_hz": 0}, "I": {"rate_hz": 0.0}}},
    "nan": {"v_mean": float("nan"), "rate_hz": 5},
    "spikes_only": {"n_spikes": 0},
}.get(mode)
if mode == "crash":
    sys.exit(4)
if len(sys.argv) > 2:
    os.makedirs(os.path.dirname(sys.argv[2]), exist_ok=True)
    json.dump(out, open(sys.argv[2], "w"))
else:
    print("simulating...")
    print(json.dumps(out))
"""


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = smoke.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "models").mkdir()
        (self.root / "models" / "run_sim.py").write_text(textwrap.dedent(MODEL), encoding="utf-8")
        self.record = self.root / ".neuroflow" / "brain-build" / "smoke-record.json"
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def smoke(self, mode, *extra):
        return run("run", "--record", self.record, "--model-dir", "models", *extra,
                   "--", sys.executable, "models/run_sim.py", mode)

    def test_passing_smoke_writes_fresh_record(self):
        code, out, _ = self.smoke("ok")
        self.assertEqual(code, 0, out)
        rec = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertTrue(rec["passed"])
        self.assertEqual(rec["model_files"], 1)
        code, out, _ = run("status", "--record", self.record)
        self.assertEqual(code, 0)
        self.assertIn("FRESH", out)

    def test_model_change_makes_record_stale(self):
        self.smoke("ok")
        with open("models/run_sim.py", "a", encoding="utf-8") as fh:
            fh.write("# tuned\n")
        code, out, _ = run("status", "--record", self.record)
        self.assertEqual(code, 1)
        self.assertIn("STALE", out)

    def test_results_folder_does_not_affect_the_hash(self):
        self.smoke("ok")
        (self.root / "models" / "results").mkdir()
        (self.root / "models" / "results" / "spikes.npy").write_bytes(b"\x00\x01")
        self.assertEqual(run("status", "--record", self.record)[0], 0)

    def test_metrics_file_inside_model_dir_is_excluded(self):
        code, out, _ = self.smoke("ok", "--metrics", "models/m/metrics.json")
        self.assertNotEqual(code, 2, out)
        # the command above printed metrics to stdout, not to the file -> metrics missing -> fail
        self.assertEqual(code, 1)
        code, out, _ = run("run", "--record", self.record, "--model-dir", "models", "--metrics", "models/m/metrics.json",
                           "--", sys.executable, "models/run_sim.py", "ok", "models/m/metrics.json")
        self.assertEqual(code, 0, out)
        rec = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertIn("m/metrics.json", rec["exclude"])
        self.assertEqual(run("status", "--record", self.record)[0], 0)

    def test_failing_checks(self):
        for mode, needle in (("runaway", "runaway"), ("silent", "every rate is 0"), ("nan", "NaN"),
                             ("crash", "exit 4"), ("spikes_only", "no spikes")):
            code, out, _ = self.smoke(mode)
            self.assertEqual(code, 1, f"{mode}: {out}")
            self.assertIn(needle, out, mode)
            self.assertFalse(json.loads(self.record.read_text(encoding="utf-8"))["passed"])
        code, out, _ = run("status", "--record", self.record)
        self.assertEqual(code, 1)
        self.assertIn("FAILING", out)

    def test_allow_silence(self):
        self.assertEqual(self.smoke("silent", "--allow-silence")[0], 0)

    def test_missing_record_and_missing_model_dir(self):
        code, out, _ = run("status", "--record", self.record)
        self.assertEqual(code, 1)
        self.assertIn("MISSING", out)
        code, _, err = run("run", "--record", self.record, "--model-dir", "nope", "--", sys.executable, "-c", "pass")
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_check_command_with_own_ok_keys(self):
        m = self.root / "metrics.json"
        m.write_text(json.dumps({"populations": {"E": {"rate_hz": 3}}, "bounded_ok": False}), encoding="utf-8")
        code, out, _ = run("check", m)
        self.assertEqual(code, 1)
        self.assertIn("bounded_ok", out)
        m.write_text(json.dumps({"mean_field": {"bounded_ok": True, "r_E": 0.2}}), encoding="utf-8")
        self.assertEqual(run("check", m)[0], 0)
        m.write_text("not json", encoding="utf-8")
        self.assertEqual(run("check", m)[0], 2)


if __name__ == "__main__":
    unittest.main()
