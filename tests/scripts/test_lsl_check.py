"""Tests for skills/phase-tool-validate/scripts/lsl_check.py (stdlib unittest; pylsl faked, no network)."""

from __future__ import annotations

import contextlib
import csv
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
SCRIPT = ROOT / "skills" / "phase-tool-validate" / "scripts" / "lsl_check.py"
_spec = importlib.util.spec_from_file_location("nf_lsl_check", SCRIPT)
lc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = lc
_spec.loader.exec_module(lc)


class FakeInfo:
    def __init__(self, name, srate=100.0, host="rig-pc", latency=0.004, gap_at=None, offset=-0.5):
        self._name, self._srate, self._host = name, srate, host
        self.latency, self.gap_at, self.offset = latency, gap_at, offset

    def name(self):
        return self._name

    def type(self):
        return "EEG"

    def source_id(self):
        return f"{self._name}-1"

    def hostname(self):
        return self._host

    def channel_count(self):
        return 8

    def nominal_srate(self):
        return self._srate


def make_fake_pylsl(infos):
    clock = {"t": 1000.0}
    module = types.ModuleType("pylsl")

    def local_clock():
        return clock["t"]

    class StreamInlet:
        def __init__(self, info, max_buflen=360):
            self.info = info
            self.next_ts = clock["t"] - info.offset  # sender clock = local - offset
            self.count = 0

        def time_correction(self, timeout=2.0):
            return self.info.offset

        def pull_chunk(self, timeout=0.2):
            n = int(round(0.1 * self.info._srate))  # 100 ms of samples per pull
            stamps = []
            for _ in range(n):
                stamps.append(self.next_ts)
                self.next_ts += 1.0 / self.info._srate
                self.count += 1
                if self.info.gap_at is not None and self.count == self.info.gap_at:
                    self.next_ts += 0.2
            # the newest sample arrives `latency` after it was stamped (local clock)
            clock["t"] = stamps[-1] + self.info.offset + self.info.latency
            return [[0.0] * 8 for _ in stamps], stamps

        def close_stream(self):
            pass

    module.local_clock = local_clock
    module.StreamInlet = StreamInlet
    module.resolve_streams = lambda wait_time=1.0: list(infos)
    return module


def run(fake, *argv):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(sys.modules, {"pylsl": fake}), contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        code = lc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class LslCheckTests(unittest.TestCase):
    def test_list_only_opens_no_inlet(self) -> None:
        fake = make_fake_pylsl([FakeInfo("EEG"), FakeInfo("Markers", srate=0.0)])
        fake.StreamInlet = None  # any inlet would crash the test
        code, out, err = run(fake, "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual([s["name"] for s in payload["streams"]], ["EEG", "Markers"])
        self.assertEqual(payload["measured"], [])

    def test_measure_latency_and_budget(self) -> None:
        fake = make_fake_pylsl([FakeInfo("EEG", latency=0.004)])
        code, out, err = run(fake, "--stream", "EEG", "--duration", "2", "--budget-ms", "10", "--json")
        self.assertEqual(code, 0, out + err)
        measured = json.loads(out)["measured"][0]
        self.assertAlmostEqual(measured["latency_ms"]["p50"], 4.0, delta=0.5)
        self.assertAlmostEqual(measured["effective_srate"], 100.0, delta=1.0)
        self.assertEqual(measured["gaps"], 0)
        fake = make_fake_pylsl([FakeInfo("EEG", latency=0.030)])
        code, out, _ = run(fake, "--stream", "EEG", "--duration", "2", "--budget-ms", "10", "--json")
        self.assertEqual(code, 1)
        self.assertIn("exceeds the 10 ms budget", " ".join(json.loads(out)["findings"]))

    def test_gaps_missing_stream_and_log(self) -> None:
        fake = make_fake_pylsl([FakeInfo("EEG", gap_at=50)])
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "lat.csv"
            code, out, _ = run(fake, "--stream", "EEG", "--stream", "Gaze", "--duration", "1", "--log", str(log),
                               "--json")
            with log.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(code, 1)
        findings = " | ".join(json.loads(out)["findings"])
        self.assertIn("gap", findings)
        self.assertIn("'Gaze' not found", findings)
        self.assertGreater(len(rows), 5)
        self.assertEqual(rows[0]["stream"], "EEG")

    def test_nothing_resolved_hints_multicast(self) -> None:
        code, out, _ = run(make_fake_pylsl([]))
        self.assertEqual(code, 1)
        self.assertIn("multicast", out)

    def test_without_pylsl(self) -> None:
        code, _, err = run(None)
        self.assertEqual(code, 2)
        self.assertIn("pip install pylsl", err)


if __name__ == "__main__":
    unittest.main()
