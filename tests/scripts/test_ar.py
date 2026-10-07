"""Tests for the autoresearch bookkeeping script (skills/autoresearch-protocol/scripts/ar.py).

Stdlib unittest only, no network: every test builds its own loop folder in a temp dir.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "autoresearch-protocol" / "scripts" / "ar.py"
_spec = importlib.util.spec_from_file_location("autoresearch_ar", SCRIPT)
ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ar)

PROGRAM = """# Autoresearch Program \u2014 connectivity (data-analyze)
Started: 2026-10-07

## Task
Improve the connectivity analysis.

## Loop configuration
loop_name: connectivity
integrity_mode: confirmatory          # set by the INIT integrity gate
max_iterations: {max_iterations}                 # CAP
max_wall_clock: {max_wall_clock}                 # CAP
max_cost: n/a
max_consecutive_errors: 3
branching: agent-decided

## Iteration checklist
1. RECALL \u2014 run ar.py status first
"""

THETASK = """# Task Manifest

> EVERY ITERATION: follow the "## Iteration checklist" in program.md in full.

## Tracked files
- `../connectivity.py`
- `../helpers/graph_metrics.py`
- `../figure.bin`

## Task description
Improve the connectivity analysis.

## Current best snapshot
history/v000/

## Iterations run
0 (last: 2026-10-07)
"""

BINARY = bytes(range(256)) + b"\x00\r\n\x00"


def run(*argv: object) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = ar.main([str(arg) for arg in argv])
        except SystemExit as exc:  # argparse usage errors
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def run_json(*argv: object) -> tuple[int, dict]:
    code, out, _ = run(*argv, "--json")
    return code, json.loads(out)


class LoopTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ar-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.make_loop()

    def make_loop(self, max_iterations: str = "50", max_wall_clock: str = "8h", eol: str = "\n") -> None:
        self.root = self.tmp / "scripts" / "analysis"
        self.loop = self.root / "connectivity_autoresearch"
        (self.root / "helpers").mkdir(parents=True, exist_ok=True)
        self.loop.mkdir(exist_ok=True)
        self.write("connectivity.py", "x = 1\n")
        self.write("helpers/graph_metrics.py", "def degree():\n    return 1\n")
        (self.root / "figure.bin").write_bytes(BINARY)
        (self.loop / "__thetask__.md").write_bytes(THETASK.replace("\n", eol).encode("utf-8"))
        program = PROGRAM.format(max_iterations=max_iterations, max_wall_clock=max_wall_clock)
        (self.loop / "program.md").write_text(program, encoding="utf-8")

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(text, encoding="utf-8")

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def thetask(self) -> str:
        return (self.loop / "__thetask__.md").read_text(encoding="utf-8")

    def results_rows(self) -> list[list[str]]:
        rows = []
        for line in (self.loop / "results.md").read_text(encoding="utf-8").splitlines():
            cells = ar.split_row(line) if line.startswith("|") else []
            if cells and cells[0].isdigit():
                rows.append(cells)
        return rows

    def start(self) -> None:
        self.assertEqual(run("init", self.loop)[0], 0)
        self.assertEqual(run("begin", self.loop)[0], 0)


class InitTests(LoopTestCase):
    def test_init_creates_baseline_snapshot_row_and_counters(self) -> None:
        code, out = run_json("init", self.loop)
        self.assertEqual(code, 0)
        self.assertTrue(out["created"])
        snap = self.loop / "history" / "v000"
        self.assertEqual((snap / "connectivity.py").read_text(encoding="utf-8"), "x = 1\n")
        self.assertTrue((snap / "helpers" / "graph_metrics.py").is_file())
        self.assertEqual((snap / "figure.bin").read_bytes(), BINARY)
        manifest = json.loads((snap / ".ar-manifest.json").read_text(encoding="utf-8"))
        tracked = ["../connectivity.py", "../helpers/graph_metrics.py", "../figure.bin"]
        self.assertEqual([f["tracked"] for f in manifest["files"]], tracked)
        self.assertEqual(self.results_rows(), [["000", "\u2014", "0", "0", "KEPT (baseline)", "\u2014"]])
        results = (self.loop / "results.md").read_text(encoding="utf-8")
        self.assertIn("# Autoresearch Results \u2014 connectivity", results)
        self.assertIn("## Current best snapshot\nhistory/v000/", self.thetask())

    def test_init_twice_is_idempotent(self) -> None:
        self.assertEqual(run("init", self.loop)[0], 0)
        code, out = run_json("init", self.loop)
        self.assertEqual(code, 0)
        self.assertFalse(out["created"])
        self.assertEqual(len(self.results_rows()), 1)

    def test_init_refuses_once_iterations_exist(self) -> None:
        self.start()
        self.write("connectivity.py", "x = 2\n")
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 2)[0], 0)
        code, _, err = run("init", self.loop)
        self.assertEqual(code, 2)
        self.assertIn("past its baseline", err)

    def test_extra_columns(self) -> None:
        self.assertEqual(run("init", self.loop, "--column", "power", "--column", "R2")[0], 0)
        self.write("connectivity.py", "x = 2\n")
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 1, "--value", "0.81")[0], 0)
        rows = self.results_rows()
        self.assertEqual(rows[0][-2:], ["\u2014", "\u2014"])
        self.assertEqual(rows[1][-2:], ["0.81", "\u2014"])

    def test_not_a_loop_folder(self) -> None:
        code, out = run_json("status", self.tmp)
        self.assertEqual(code, 2)
        self.assertFalse(out["ok"])
        self.assertIn("__thetask__.md", out["error"])


class KeepRevertTests(LoopTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.start()

    def test_keep_snapshots_records_and_updates_counters(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        code, out = run_json("keep", self.loop, "--iter", 1, "--delta", 3, "--focus", "edge | weights")
        self.assertEqual(code, 0)
        self.assertEqual(out["snapshot"], "history/v001/")
        self.assertEqual(out["running"], 3)
        self.assertEqual((self.loop / "history" / "v001" / "connectivity.py").read_text(encoding="utf-8"), "x = 2\n")
        self.assertEqual(self.results_rows()[-1], ["001", "BETTER", "+3", "3", "KEPT", "edge / weights"])
        self.assertIn("## Current best snapshot\nhistory/v001/", self.thetask())
        self.assertRegex(self.thetask(), r"## Iterations run\n1 \(last: \d{4}-\d{2}-\d{2}\)")

    def test_keep_twice_is_idempotent(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 3)[0], 0)
        code, out = run_json("keep", self.loop, "--iter", 1, "--delta", 3)
        self.assertEqual(code, 0)
        self.assertTrue(out["already_recorded"])
        self.assertEqual(len(self.results_rows()), 2)

    def test_keep_resumes_after_a_crash_between_snapshot_and_row(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        ar.take_snapshot(ar.Loop(str(self.loop)), 1)  # the call died right after the snapshot
        code, out = run_json("keep", self.loop, "--iter", 1, "--delta", 2)
        self.assertEqual(code, 0)
        self.assertFalse(out["already_recorded"])
        self.assertEqual(self.results_rows()[-1][:5], ["001", "BETTER", "+2", "2", "KEPT"])

    def test_wrong_iteration_number_and_bad_delta_are_refused(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        code, _, err = run("keep", self.loop, "--iter", 3, "--delta", 1)
        self.assertEqual(code, 2)
        self.assertIn("the next one is 001", err)
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 9)[0], 2)
        self.assertEqual(run("revert", self.loop, "--iter", 1, "--verdict", "MAYBE", "--delta", 0)[0], 2)
        self.assertEqual(len(self.results_rows()), 1)

    def test_revert_restores_the_best_snapshot_byte_exact(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        run("keep", self.loop, "--iter", 1, "--delta", 3)
        self.write("connectivity.py", "x = broken\n")
        (self.root / "figure.bin").write_bytes(b"garbage")
        code, out = run_json("revert", self.loop, "--iter", 2, "--verdict", "WORSE", "--delta", -2)
        self.assertEqual(code, 0)
        self.assertEqual(self.read("connectivity.py"), "x = 2\n")
        self.assertEqual((self.root / "figure.bin").read_bytes(), BINARY)
        self.assertEqual(sorted(out["restored"]), ["../connectivity.py", "../figure.bin"])
        self.assertEqual(self.results_rows()[-1][:5], ["002", "WORSE", "-2", "3", "REVERTED"])
        self.assertIn("## Current best snapshot\nhistory/v001/", self.thetask())

    def test_revert_again_never_touches_newer_work(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        run("keep", self.loop, "--iter", 1, "--delta", 3)
        self.write("connectivity.py", "x = 3\n")
        self.assertEqual(run("revert", self.loop, "--iter", 2, "--verdict", "NO CHANGE", "--delta", 0)[0], 0)
        self.write("connectivity.py", "x = 4  # iteration 3 work\n")
        code, out = run_json("revert", self.loop, "--iter", 2, "--verdict", "no-change", "--delta", 0)
        self.assertEqual(code, 0)
        self.assertTrue(out["already_recorded"])
        self.assertEqual(self.read("connectivity.py"), "x = 4  # iteration 3 work\n")
        self.assertEqual(len(self.results_rows()), 3)

    def test_conflicting_record_is_refused(self) -> None:
        self.write("connectivity.py", "x = 2\n")
        run("revert", self.loop, "--iter", 1, "--verdict", "WORSE", "--delta", -1)
        self.write("connectivity.py", "x = 2\n")
        code, _, err = run("keep", self.loop, "--iter", 1, "--delta", 1)
        self.assertEqual(code, 2)
        self.assertIn("already recorded as REVERTED", err)

    def test_existing_snapshot_with_other_content_is_never_overwritten(self) -> None:
        other = self.loop / "history" / "v001"
        other.mkdir(parents=True)
        (other / "connectivity.py").write_text("something else\n", encoding="utf-8")
        self.write("connectivity.py", "x = 2\n")
        code, _, err = run("keep", self.loop, "--iter", 1, "--delta", 1)
        self.assertEqual(code, 2)
        self.assertIn("refusing to overwrite", err)
        self.assertEqual((other / "connectivity.py").read_text(encoding="utf-8"), "something else\n")

    def test_edited_snapshot_is_refused_and_nothing_restored(self) -> None:
        (self.loop / "history" / "v000" / "connectivity.py").write_text("tampered\n", encoding="utf-8")
        self.write("connectivity.py", "x = 2\n")
        code, _, err = run("revert", self.loop, "--iter", 1, "--verdict", "WORSE", "--delta", -1)
        self.assertEqual(code, 2)
        self.assertIn("no longer matches its manifest", err)
        self.assertEqual(self.read("connectivity.py"), "x = 2\n")
        self.assertEqual(len(self.results_rows()), 1)


class StatusTests(LoopTestCase):
    def test_clean_dirty_restore_adopt(self) -> None:
        self.start()
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 0, out["findings"])
        self.assertEqual(out["next_iter"], 1)
        self.assertEqual(out["best"], "history/v000/")

        self.write("connectivity.py", "x = cut off mid-iteration\n")
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual([f["kind"] for f in out["findings"]], ["dirty"])

        code, out = run_json("restore", self.loop)
        self.assertEqual((code, out["restored"]), (0, ["../connectivity.py"]))
        self.assertEqual(self.read("connectivity.py"), "x = 1\n")
        self.assertEqual(run("status", self.loop)[0], 0)

        self.assertEqual(run("adopt", self.loop, "--iter", 1)[0], 2)  # nothing to adopt
        self.write("connectivity.py", "x = 1  # the human fixed a comment\n")
        code, out = run_json("adopt", self.loop, "--iter", 1, "--focus", "outside edit")
        self.assertEqual((code, out["snapshot"]), (0, "history/v001/"))
        self.assertEqual(self.results_rows()[-1][:5], ["001", "\u2014", "0", "0", "KEPT (outside edit)"])
        self.assertEqual(run("status", self.loop)[0], 0)

    def test_plateau_is_reported_but_is_not_a_finding(self) -> None:
        self.start()
        for i in range(1, 6):
            self.write("connectivity.py", f"x = {i + 10}\n")
            self.assertEqual(run("revert", self.loop, "--iter", i, "--verdict", "WORSE", "--delta", -1)[0], 0)
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 0, out["findings"])
        self.assertEqual(out["reverts_in_a_row"], 5)
        self.assertTrue(out["plateau"])
        self.assertIn("PLATEAU", run("status", self.loop)[1])

    def test_iteration_cap(self) -> None:
        self.make_loop(max_iterations="2", max_wall_clock="none")
        self.start()
        for i in (1, 2):
            self.write("connectivity.py", f"x = {i + 1}\n")
            run("keep", self.loop, "--iter", i, "--delta", 1)
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual(out["findings"][0]["kind"], "cap")
        self.assertIn("max_iterations reached (2 of 2", out["findings"][0]["detail"])
        self.assertEqual(run("begin", self.loop)[0], 0)  # a resumed run gets a fresh budget
        self.assertEqual(run("status", self.loop)[0], 0)

    def test_wall_clock_cap(self) -> None:
        self.make_loop(max_iterations="none", max_wall_clock="2h30m")
        self.start()
        earlier = (datetime.now().astimezone() - timedelta(hours=3)).isoformat(timespec="seconds")
        text = ar.set_section(self.thetask(), "## Current run", [f"started: {earlier}", "iterations at start: 0"])
        (self.loop / "__thetask__.md").write_text(text, encoding="utf-8")
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertIn("max_wall_clock reached", out["findings"][0]["detail"])

    def test_no_cap_and_no_run_are_findings(self) -> None:
        self.make_loop(max_iterations="none", max_wall_clock="n/a")
        self.assertEqual(run("init", self.loop)[0], 0)
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual(sorted(f["kind"] for f in out["findings"]), ["no-cap", "no-run"])
        code, out = run_json("begin", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual([f["kind"] for f in out["findings"]], ["no-cap"])

    def test_unreadable_cap_is_a_finding(self) -> None:
        self.make_loop(max_iterations="fifty", max_wall_clock="8h")
        self.start_without_check()
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual([f["kind"] for f in out["findings"]], ["cap-unreadable"])

    def start_without_check(self) -> None:
        run("init", self.loop)
        run("begin", self.loop)

    def test_missing_tracked_file(self) -> None:
        self.start()
        (self.root / "helpers" / "graph_metrics.py").unlink()
        code, out = run_json("status", self.loop)
        self.assertEqual(code, 1)
        self.assertEqual([f["kind"] for f in out["findings"]], ["missing"])
        self.write("connectivity.py", "x = 2\n")
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 1)[0], 2)

    def test_text_output_is_plain_ascii(self) -> None:
        self.start()
        code, out, _ = run("status", self.loop)
        self.assertEqual(code, 0)
        out.replace(str(self.loop), "").encode("ascii")  # own text is ASCII: safe on a narrow console


class FileFormatTests(LoopTestCase):
    def test_crlf_files_stay_crlf(self) -> None:
        self.make_loop(eol="\r\n")
        self.start()
        self.write("connectivity.py", "x = 2\n")
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 1)[0], 0)
        raw = (self.loop / "__thetask__.md").read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        self.assertIn(b"## Current best snapshot\r\nhistory/v001/\r\n", raw)

    def test_hand_made_snapshot_without_manifest(self) -> None:
        legacy = self.loop / "history" / "v000"
        legacy.mkdir(parents=True)
        shutil.copy2(self.root / "connectivity.py", legacy / "connectivity.py")
        shutil.copy2(self.root / "helpers" / "graph_metrics.py", legacy / "graph_metrics.py")  # flat, by basename
        shutil.copy2(self.root / "figure.bin", legacy / "figure.bin")
        (self.loop / "results.md").write_text(
            "# Autoresearch Results \u2014 connectivity\n\n"
            "| # | Verdict | \u0394 | Running | Decision | Next focus |\n"
            "|---|---------|---|---------|----------|------------|\n"
            "| 000 | \u2014 | 0 | 0 | KEPT (baseline) | \u2014 |\n",
            encoding="utf-8",
        )
        self.write("helpers/graph_metrics.py", "def degree():\n    return 2\n")
        code, out = run_json("revert", self.loop, "--iter", 1, "--verdict", "WORSE", "--delta", -1)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("helpers/graph_metrics.py"), "def degree():\n    return 1\n")

    def test_lock_held_then_stale(self) -> None:
        self.start()
        lock = self.loop / "history" / ".ar-lock"
        lock.mkdir()
        old_wait = ar.LOCK_WAIT_SECONDS
        ar.LOCK_WAIT_SECONDS = 0.3
        self.addCleanup(setattr, ar, "LOCK_WAIT_SECONDS", old_wait)
        self.write("connectivity.py", "x = 2\n")
        code, _, err = run("keep", self.loop, "--iter", 1, "--delta", 1)
        self.assertEqual(code, 2)
        self.assertIn(".ar-lock", err)
        stale = time.time() - ar.LOCK_STALE_SECONDS - 60
        os.utime(lock, (stale, stale))
        self.assertEqual(run("keep", self.loop, "--iter", 1, "--delta", 1)[0], 0)
        self.assertFalse(lock.exists())


class ParserTests(unittest.TestCase):
    def test_durations(self) -> None:
        self.assertEqual(ar.parse_duration("8h"), 8 * 3600)
        self.assertEqual(ar.parse_duration("2h30m"), 9000)
        self.assertEqual(ar.parse_duration("90 min"), 5400)
        self.assertEqual(ar.parse_duration("1d"), 86400)
        self.assertEqual(ar.parse_duration("6"), 6 * 3600)
        self.assertIsNone(ar.parse_duration("none"))
        for bad in ("soon", "2h30", "0h", "5 weeks"):
            with self.assertRaises(ValueError, msg=bad):
                ar.parse_duration(bad)

    def test_counts(self) -> None:
        self.assertEqual(ar.parse_count("50"), 50)
        self.assertIsNone(ar.parse_count("n/a"))
        for bad in ("0", "-3", "fifty"):
            with self.assertRaises(ValueError, msg=bad):
                ar.parse_count(bad)

    def test_storage_plan_strips_parent_parts_and_resolves_collisions(self) -> None:
        plan = ar.storage_plan(["../a.py", "../../a.py", "../sub/b.py", "C:/abs/c.py"])
        expected = {"../a.py": "a.py", "../../a.py": "_2/a.py", "../sub/b.py": "sub/b.py", "C:/abs/c.py": "abs/c.py"}
        self.assertEqual(plan, expected)

    def test_tracked_files_parsing(self) -> None:
        text = (
            "## Tracked files\n- `../a.py`\n- ..\\b.py \u2014 helper\n* ./c.md\n- `../a.py`\n"
            "\n## Task description\nx\n"
        )
        self.assertEqual(ar.parse_tracked(text), ["../a.py", "../b.py", "c.md"])


if __name__ == "__main__":
    unittest.main()
