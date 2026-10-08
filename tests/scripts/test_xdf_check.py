"""Tests for skills/phase-tool-validate/scripts/xdf_check.py (stdlib unittest; pyxdf faked)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-tool-validate" / "scripts" / "xdf_check.py"
_spec = importlib.util.spec_from_file_location("nf_xdf_check", SCRIPT)
xc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = xc
_spec.loader.exec_module(xc)


def eeg_stream(n=5000, srate=500.0, gap_at=None, clock=1.0):
    stamps = []
    t = 10.0
    for i in range(n):
        stamps.append(t)
        t += clock / srate
        if gap_at is not None and i == gap_at:
            t += 0.5
    return {"info": {"name": ["EEG"], "type": ["EEG"], "nominal_srate": [str(srate)], "channel_count": ["32"]},
            "time_stamps": stamps, "time_series": [[0.0] * 32 for _ in range(n)]}


def marker_stream(codes):
    return {"info": {"name": ["PsychoPyMarkers"], "type": ["Markers"], "nominal_srate": ["0"],
                     "channel_count": ["1"]},
            "time_stamps": [11.0 + i for i in range(len(codes))], "time_series": [[c] for c in codes]}


class XdfCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.xdf = Path(self._tmp.name) / "run.xdf"
        self.xdf.write_bytes(b"XDF:fake")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_with(self, streams, *argv):
        fake = types.ModuleType("pyxdf")
        calls = {}

        def load_xdf(path, **kwargs):
            calls.update(kwargs)
            return streams, {}

        fake.load_xdf = load_xdf
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"pyxdf": fake}), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = xc.main([str(self.xdf), *argv])
        return code, out.getvalue(), err.getvalue(), calls

    def test_clean_recording(self) -> None:
        code, out, err, calls = self.run_with([eeg_stream(), marker_stream(["1", "2", "1"])],
                                              "--expect", "EEG", "--expect", "Markers", "--expect-markers", "3",
                                              "--json")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(calls.get("dejitter_timestamps"), False)
        payload = json.loads(out)
        eeg = payload["streams"][0]
        self.assertAlmostEqual(eeg["effective_srate"], 500.0, places=2)
        self.assertEqual(eeg["gaps"], 0)
        self.assertEqual(payload["streams"][1]["marker_counts"], {"1": 2, "2": 1})

    def test_gap_drift_missing_and_counts(self) -> None:
        streams = [eeg_stream(gap_at=100, clock=1.01), marker_stream(["1"] * 5)]
        code, out, _, _ = self.run_with(streams, "--expect", "EyeTracker", "--expect-markers", "6", "--json")
        self.assertEqual(code, 1)
        findings = " | ".join(json.loads(out)["findings"])
        self.assertIn("'EyeTracker' is missing", findings)
        self.assertIn("gap", findings)
        self.assertIn("differs from nominal", findings)
        self.assertIn("5 marker(s) recorded, 6 expected", findings)

    def test_empty_stream(self) -> None:
        empty = eeg_stream(n=0)
        code, out, _, _ = self.run_with([empty])
        self.assertEqual(code, 1)
        self.assertIn("no samples", out)

    def test_without_pyxdf(self) -> None:
        err = io.StringIO()
        with mock.patch.dict(sys.modules, {"pyxdf": None}), contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = xc.main([str(self.xdf)])
        self.assertEqual(code, 2)
        self.assertIn("pip install pyxdf", err.getvalue())

    def test_missing_file(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = xc.main([str(self.xdf) + ".nope"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
