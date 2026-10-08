"""Tests for skills/phase-experiment/scripts/psychopy_audit.py (stdlib unittest; PsychoPy not needed)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-experiment" / "scripts" / "psychopy_audit.py"
_spec = importlib.util.spec_from_file_location("nf_psychopy_audit", SCRIPT)
audit = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = audit
_spec.loader.exec_module(audit)

BAD = textwrap.dedent(
    """
    from psychopy import visual, core, event, parallel
    import time
    REFRESH_RATE = 60
    frame_dur = 1 / 60
    win = visual.Window(fullscr=True)
    port = parallel.ParallelPort(address=0x0378)
    report = open('report.txt', 'w')
    for trial in range(10):
        stim.draw()
        win.flip()
        outlet.push_sample(['S'])
        port.setData(2)
        core.wait(0.1)
        win.flip()
        report.write('done')
        keys = event.getKeys()
        while clock.getTime() < 0.5:
            stim.draw()
            win.flip()
            time.sleep(0.001)
    """
)

GOOD = textwrap.dedent(
    """
    from psychopy import visual, core, logging, data
    win = visual.Window(fullscr=True)
    win.recordFrameIntervals = True
    rate = win.getActualFrameRate()
    logging.LogFile('run.log')
    exp = data.ExperimentHandler(dataFileName='x')
    n_frames = round(0.1 * rate)
    for trial in range(10):
        for f in range(n_frames):
            if f == 0:
                win.callOnFlip(outlet.push_sample, ['S'])
                win.callOnFlip(port.setData, 4)
            stim.draw()
            win.flip()
        win.callOnFlip(port.setData, 0)
        win.flip()
        core.wait(0.5)
        exp.addData('trial', trial)
        exp.nextEntry()
    """
)

PSYEXP = """<?xml version="1.0" ?>
<PsychoPy2experiment encoding="utf-8" version="2025.1.0">
  <Settings>
    <Param val="False" valType="bool" updates="None" name="Save csv file"/>
    <Param val="False" valType="bool" updates="None" name="Save wide csv file"/>
    <Param val="False" valType="bool" updates="None" name="Save psydat file"/>
    <Param val="False" valType="bool" updates="None" name="Save log file"/>
  </Settings>
  <Routines>
    <Routine name="trial">
      <TextComponent name="target">
        <Param val="time (s)" valType="str" updates="None" name="startType"/>
        <Param val="0.5" valType="code" updates="None" name="startVal"/>
        <Param val="duration (s)" valType="str" updates="None" name="stopType"/>
        <Param val="0.1" valType="code" updates="constant" name="stopVal"/>
      </TextComponent>
      <SerialOutComponent name="serial_trig">
        <Param val="1" valType="code" updates="None" name="startData"/>
      </SerialOutComponent>
      <ParallelOutComponent name="pp">
        <Param val="False" valType="bool" updates="None" name="syncScreen"/>
      </ParallelOutComponent>
      <KeyboardComponent name="resp">
        <Param val="False" valType="bool" updates="None" name="syncScreenRefresh"/>
      </KeyboardComponent>
      <CodeComponent name="code">
        <Param val="outlet.push_sample(['T'])" valType="extendedCode" updates="constant" name="Begin Routine"/>
        <Param val="core.wait(0.01)" valType="extendedCode" updates="constant" name="Each Frame"/>
        <Param val="psychoJS.experiment.addData('x', 1);" valType="extendedCode" updates="constant" name="Each JS Frame"/>
      </CodeComponent>
    </Routine>
  </Routines>
  <Flow><Routine name="trial"/></Flow>
</PsychoPy2experiment>
"""


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = audit.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class PsychoPyAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def rules(self, payload: dict, severity: str | None = None) -> set[str]:
        return {f["rule"] for f in payload["findings"] if severity is None or f["severity"] == severity}

    def test_bad_coder_script(self) -> None:
        path = self.write("bad.py", BAD)
        code, out, err = run(str(path), "--json")
        self.assertEqual(code, 1, err)
        payload = json.loads(out)
        warns = self.rules(payload, "warn")
        self.assertTrue({"PSY001", "PSY002", "PSY003", "PSY004", "PSY005"} <= warns, warns)
        self.assertTrue({"PSY006", "PSY007", "PSY008", "PSY009", "PSY010", "PSY012"} <= self.rules(payload, "info"))
        codes = {(m["via"], json.dumps(m["code"]), m["on_flip"]) for m in payload["markers"]}
        self.assertIn(("push_sample", '"S"', False), codes)
        self.assertIn(("setData", "2", False), codes)
        # report.write() is a file, not a trigger port: no marker entry for it
        self.assertFalse(any(m["via"] == "write" for m in payload["markers"]))

    def test_good_coder_script_is_clean(self) -> None:
        path = self.write("good.py", GOOD)
        code, out, err = run(str(path), "--json")
        payload = json.loads(out)
        self.assertEqual(code, 0, payload["findings"])
        self.assertEqual(self.rules(payload, "warn"), set())
        on_flip = {(m["via"], json.dumps(m["code"])) for m in payload["markers"] if m["on_flip"]}
        self.assertEqual(on_flip, {("push_sample", '"S"'), ("setData", "4")})

    def test_psyexp(self) -> None:
        path = self.write("task.psyexp", PSYEXP)
        code, out, err = run(str(path), "--json")
        self.assertEqual(code, 1, err)
        payload = json.loads(out)
        warns = [f for f in payload["findings"] if f["severity"] == "warn"]
        self.assertEqual(sum(1 for f in warns if f["rule"] == "PSY102"), 2, "serial default and parallel off")
        self.assertIn("PSY104", {f["rule"] for f in warns})
        self.assertIn("PSY003", {f["rule"] for f in warns})
        self.assertIn("PSY008", {f["rule"] for f in warns})
        infos = self.rules(payload, "info")
        self.assertTrue({"PSY101", "PSY103", "PSY009"} <= infos, infos)
        self.assertTrue(any(m["where"].startswith("trial/code") for m in payload["markers"]))

    def test_folder_audit_skips_non_psychopy_python(self) -> None:
        self.write("helper.py", "print('no stimulus code here')\n")
        self.write("task.psyexp", PSYEXP)
        code, out, _ = run(str(self.dir), "--json")
        files = json.loads(out)["files"]
        self.assertEqual([Path(f).name for f in files], ["task.psyexp"])

    def test_hook_mode(self) -> None:
        bad = self.write("bad.py", BAD)
        code, out, _ = run(str(bad), "--hook")
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "PostToolUse")
        self.assertIn("PSY003", ctx["additionalContext"])
        other = self.write("notes.py", "x = 1\n")
        code, out, _ = run(str(other), "--hook")
        self.assertEqual((code, out), (0, ""))
        code, out, _ = run(str(self.dir / "missing.py"), "--hook")
        self.assertEqual(code, 0)

    def test_frame_interval_log(self) -> None:
        intervals = ["0.01667"] * 200 + ["0.0334", "0.0501"]
        path = self.write("frameIntervals.log", ", ".join(intervals))
        code, out, _ = run("--csv", str(path), "--refresh-hz", "60", "--json")
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["summary"]["dropped"], 2)
        self.assertEqual(self.rules(payload), {"PSY201"})
        clean = self.write("clean.csv", "frame_interval\n" + "\n".join(["16.67"] * 100))
        code, out, _ = run("--csv", str(clean), "--json")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["input_unit"], "ms")
        self.assertAlmostEqual(payload["summary"]["measured_hz"], 59.99, places=1)

    def test_vsync_off_and_wrong_refresh(self) -> None:
        intervals = ["0.004"] * 50 + ["0.0167"] * 50
        path = self.write("tear.log", "\n".join(intervals))
        code, out, _ = run("--csv", str(path), "--refresh-hz", "60", "--json")
        self.assertEqual(code, 1)
        self.assertIn("PSY202", self.rules(json.loads(out)))
        path = self.write("hz.log", "\n".join(["0.00833"] * 50))
        code, out, _ = run("--csv", str(path), "--refresh-hz", "60", "--json")
        self.assertIn("PSY203", self.rules(json.loads(out)))

    def test_builder_trial_csv(self) -> None:
        rows = ["cond,target.started,target.stopped,key_resp.rt,frameRate"]
        for i in range(20):
            start = 1.0 + i
            dur = 0.1 if i != 7 else 0.1167
            rt = "" if i == 3 else "0.45"
            rows.append(f"{'A' if i % 2 else 'B'},{start},{start + dur},{rt},60.0")
        path = self.write("run.csv", "\n".join(rows) + "\n")
        code, out, err = run("--csv", str(path), "--condition-column", "cond", "--rt-column", "key_resp.rt", "--json")
        self.assertEqual(code, 1, err)
        summary = json.loads(out)["summary"]
        self.assertEqual(summary["components"]["target"]["off_by_a_frame"], 1)
        self.assertEqual(summary["trials_per_condition"], {"B": 10, "A": 10})
        self.assertEqual(summary["responses"]["missing"], 1)
        self.assertEqual(summary["refresh_hz"], 60.0)

    def test_usage_errors(self) -> None:
        self.assertEqual(run()[0], 2)
        path = self.write("empty.csv", "a,b\n1,2\n")
        self.assertEqual(run("--csv", str(path))[0], 2)
        broken = self.write("broken.py", "def (:\n")
        self.assertEqual(run(str(broken))[0], 2)


if __name__ == "__main__":
    unittest.main()
