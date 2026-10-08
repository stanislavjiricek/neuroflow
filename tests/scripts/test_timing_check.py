"""Tests for skills/phase-tool-validate/scripts/timing_check.py (stdlib unittest; pyxdf faked)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import random
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-tool-validate" / "scripts" / "timing_check.py"
_spec = importlib.util.spec_from_file_location("nf_timing_check", SCRIPT)
tc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = tc
_spec.loader.exec_module(tc)

FS = 2000.0


def synth(n_markers=40, latency=0.012, late=(5, 17), drop=(), on_level=1.0, noise=0.01, seed=1):
    """Markers every 0.5 s; the photodiode turns on `latency` later (one frame later for `late`)."""
    rng = random.Random(seed)
    markers = [1.0 + 0.5 * k for k in range(n_markers)]
    onsets = {}
    for k, m in enumerate(markers):
        if k in drop:
            continue
        onsets[k] = m + latency + (1 / 60 if k in late else 0.0)
    duration = markers[-1] + 1.0
    times, values = [], []
    on_windows = sorted(onsets.values())
    w = 0
    for i in range(int(duration * FS)):
        t = i / FS
        while w < len(on_windows) and t > on_windows[w] + 0.1:
            w += 1
        on = w < len(on_windows) and on_windows[w] <= t <= on_windows[w] + 0.1
        v = on_level if on else 0.1
        if on and i % 5 == 0:
            v = 0.15  # backlight PWM dip inside an "on" period
        times.append(t)
        values.append(v + rng.gauss(0, noise))
    return markers, times, values


def write_csvs(base: Path, markers, times, values) -> tuple[Path, Path]:
    mk = base / "markers.csv"
    pd = base / "photodiode.csv"
    mk.write_text("time,code\n" + "".join(f"{m:.6f},1\n" for m in markers), encoding="utf-8")
    pd.write_text("time,pd\n" + "".join(f"{t:.6f},{v:.6f}\n" for t, v in zip(times, values)), encoding="utf-8")
    return mk, pd


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TimingCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_latency_and_frame_offsets(self) -> None:
        markers, times, values = synth()
        params = {"polarity": "rising", "min_off_ms": 20.0, "window_ms": [-50, 200], "refresh_hz": 60}
        results, findings = tc.analyse(markers, times, values, params)
        self.assertEqual(results["paired"], 40)
        self.assertEqual(results["missing"], 0)
        self.assertEqual(results["onsets"], 40, "PWM dips must not create extra onsets")
        self.assertAlmostEqual(results["latency_ms"]["p50"], 12.0, delta=0.6)
        self.assertEqual(results["off_by_a_frame"]["late"], 2)
        self.assertEqual(len(findings), 1)
        self.assertIn("late", findings[0])

    def test_missing_onset_and_criteria(self) -> None:
        markers, times, values = synth(late=(), drop=(3,))
        mk, pd = write_csvs(self.dir, markers, times, values)
        code, out, err = run("--marker-csv", str(mk), "--photodiode-csv", str(pd), "--max-latency-ms", "10", "--json")
        self.assertEqual(code, 1, err)
        payload = json.loads(out)
        self.assertEqual(payload["results"]["missing"], 1)
        self.assertTrue(any("exceeds 10" in f for f in payload["findings"]))
        self.assertFalse(payload["results"]["pass"])

    def test_clean_pass(self) -> None:
        markers, times, values = synth(late=())
        mk, pd = write_csvs(self.dir, markers, times, values)
        code, out, err = run("--marker-csv", str(mk), "--photodiode-csv", str(pd), "--max-latency-ms", "20",
                             "--max-jitter-ms", "2", "--refresh-hz", "60")
        self.assertEqual(code, 0, out + err)
        self.assertIn("PASS", out)

    def test_weak_signal_flagged(self) -> None:
        markers, times, values = synth(late=(), on_level=0.13, noise=0.02)
        params = {"polarity": "rising", "min_off_ms": 20.0, "window_ms": [-50, 200]}
        _, findings = tc.analyse(markers, times, values, params)
        self.assertTrue(any("weak photodiode signal" in f for f in findings), findings)

    def test_record_and_verify(self) -> None:
        markers, times, values = synth(late=())
        mk, pd = write_csvs(self.dir, markers, times, values)
        code, out, _ = run("--marker-csv", str(mk), "--photodiode-csv", str(pd), "--record", "--json")
        self.assertEqual(code, 0)
        record = json.loads(out)["record"]
        results_md = self.dir / "validation-results.md"
        results_md.write_text("# Validation results\n\n" + record + "\n", encoding="utf-8")
        code, out, _ = run("--verify-record", str(results_md))
        self.assertEqual(code, 0, out)
        tampered = results_md.read_text(encoding="utf-8").replace('"p95": ', '"p95": 1', 1)
        results_md.write_text(tampered, encoding="utf-8")
        code, out, _ = run("--verify-record", str(results_md))
        self.assertEqual(code, 1)
        self.assertIn("differ", out)
        results_md.write_text("# Validation results\n\n" + record + "\n", encoding="utf-8")
        pd.write_text(pd.read_text(encoding="utf-8") + "999.0,0.1\n", encoding="utf-8")
        code, out, _ = run("--verify-record", str(results_md))
        self.assertEqual(code, 1)
        self.assertIn("changed", out)

    def test_xdf_with_fake_pyxdf(self) -> None:
        markers, times, values = synth(late=())
        streams = [
            {"info": {"name": ["PsychoPyMarkers"], "type": ["Markers"]},
             "time_stamps": markers, "time_series": [["1"] for _ in markers]},
            {"info": {"name": ["EEG"], "type": ["EEG"]},
             "time_stamps": times, "time_series": [[0.0, v] for v in values]},
        ]
        fake = types.ModuleType("pyxdf")
        fake.load_xdf = lambda path: (streams, {})
        xdf = self.dir / "pilot.xdf"
        xdf.write_bytes(b"XDF:fake")
        with mock.patch.dict(sys.modules, {"pyxdf": fake}):
            code, out, err = run("--xdf", str(xdf), "--markers", "Markers", "--photodiode", "EEG", "--channel", "1",
                                 "--codes", "1", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["results"]["paired"], 40)

    def test_xdf_without_pyxdf_is_usage_error(self) -> None:
        xdf = self.dir / "pilot.xdf"
        xdf.write_bytes(b"XDF:fake")
        with mock.patch.dict(sys.modules, {"pyxdf": None}):
            code, _, err = run("--xdf", str(xdf), "--markers", "M", "--photodiode", "P")
        self.assertEqual(code, 2)
        self.assertIn("pip install pyxdf", err)

    def test_percentile(self) -> None:
        self.assertEqual(tc.percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertAlmostEqual(tc.percentile([0, 10], 95), 9.5)


if __name__ == "__main__":
    unittest.main()
