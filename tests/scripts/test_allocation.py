"""Tests for skills/phase-experiment/scripts/allocation.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-experiment" / "scripts" / "allocation.py"
_spec = importlib.util.spec_from_file_location("nf_allocation", SCRIPT)
alloc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = alloc
_spec.loader.exec_module(alloc)


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = alloc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class DesignTests(unittest.TestCase):
    def assert_latin(self, rows: list[list[int]], n: int) -> None:
        for pos in range(n):
            counts = Counter(r[pos] for r in rows)
            self.assertEqual(set(counts), set(range(n)))
            self.assertEqual(len(set(counts.values())), 1, "each condition equally often at each position")

    def test_williams_even_is_carryover_balanced(self) -> None:
        for n in (2, 4, 6):
            rows = alloc.williams_rows(n)
            self.assertEqual(len(rows), n)
            self.assert_latin(rows, n)
            pairs = Counter((r[i], r[i + 1]) for r in rows for i in range(n - 1))
            self.assertEqual(len(pairs), n * (n - 1))
            self.assertEqual(set(pairs.values()), {1})

    def test_williams_odd_uses_mirror(self) -> None:
        for n in (3, 5):
            rows = alloc.williams_rows(n)
            self.assertEqual(len(rows), 2 * n)
            self.assert_latin(rows, n)
            pairs = Counter((r[i], r[i + 1]) for r in rows for i in range(n - 1))
            self.assertEqual(set(pairs.values()), {2})

    def test_latin_and_full(self) -> None:
        self.assert_latin(alloc.latin_rows(5), 5)
        self.assertEqual(len(alloc.full_rows(4)), 24)
        with self.assertRaises(alloc.UsageError):
            alloc.full_rows(7)

    def test_schedule_is_deterministic_and_seed_dependent(self) -> None:
        params = {"scheme": "williams", "participants": 16, "seed": 42, "conditions": ["A", "B", "C", "D"]}
        first = alloc.build_schedule(params)
        self.assertEqual(first, alloc.build_schedule(dict(params)))
        self.assertNotEqual(first, alloc.build_schedule(dict(params, seed=43)))
        cycles = [first[:4], first[4:8], first[8:12], first[12:]]
        for cycle in cycles:  # each complete cycle uses every row of the square once
            self.assertEqual(len(set(cycle)), 4)

    def test_block_randomisation_balances_each_block(self) -> None:
        params = {"scheme": "block", "participants": 40, "seed": 7, "groups": ["ctl", "trn"], "block_size": 4}
        schedule = alloc.build_schedule(params)
        for start in range(0, 40, 4):
            self.assertEqual(Counter(schedule[start:start + 4]), Counter({"ctl": 2, "trn": 2}))


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.schedule = self.dir / "allocation" / "schedule.csv"
        self.ledger = self.dir / "allocation" / "ledger.csv"
        code, out, err = run("generate", "--scheme", "williams", "--conditions", "A", "B", "C", "D",
                             "--participants", "8", "--seed", "20261007", "--out", str(self.schedule), "--json")
        self.assertEqual(code, 0, err)
        self.digest = json.loads(out)["sha256"]

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def next(self, participant: str, *extra: str) -> tuple[int, dict]:
        code, out, err = run("next", "--schedule", str(self.schedule), "--ledger", str(self.ledger),
                             "--participant", participant, *extra, "--json")
        return code, json.loads(out) if out.strip() else {"error": err}

    def test_generate_refuses_overwrite(self) -> None:
        code, _, err = run("generate", "--scheme", "latin", "--conditions", "A", "B", "--participants", "4",
                           "--seed", "1", "--out", str(self.schedule))
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_next_hands_out_slots_in_order_and_never_reassigns(self) -> None:
        code, first = self.next("sub-01")
        self.assertEqual((code, first["slot"], first["kind"]), (0, 1, "new"))
        code, second = self.next("sub-02")
        self.assertEqual(second["slot"], 2)
        code, again = self.next("sub-01")
        self.assertEqual(code, 1)
        self.assertIn("already allocated", again["refused"])
        with self.ledger.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([r["participant"] for r in rows], ["sub-01", "sub-02"])
        self.assertTrue(all(r["schedule_sha256"] == self.digest for r in rows))

    def test_replacement_takes_over_slot(self) -> None:
        self.next("sub-01")
        _, original = self.next("sub-02")
        code, repl = self.next("sub-09", "--replaces", "sub-02")
        self.assertEqual(code, 0)
        self.assertEqual((repl["slot"], repl["assignment"], repl["kind"]), (2, original["assignment"], "replacement"))
        _, nxt = self.next("sub-03")
        self.assertEqual(nxt["slot"], 3)
        code, out, _ = run("verify", "--schedule", str(self.schedule), "--ledger", str(self.ledger),
                           "--expect-sha256", self.digest, "--json")
        result = json.loads(out)
        self.assertEqual(code, 0, result["findings"])
        self.assertTrue(result["reproducible_from_seed"])
        self.assertEqual(result["allocated_slots"], 3)

    def test_exhausted_schedule(self) -> None:
        for i in range(1, 9):
            self.assertEqual(self.next(f"sub-{i:02d}")[0], 0)
        code, result = self.next("sub-99")
        self.assertEqual(code, 1)
        self.assertIn("exhausted", result["refused"])

    def test_names_refused(self) -> None:
        code, result = self.next("Jane Doe")
        self.assertEqual(code, 2)
        self.assertIn("pseudonymous", result["error"])

    def test_tampered_schedule_detected(self) -> None:
        self.next("sub-01")
        text = self.schedule.read_text(encoding="utf-8").splitlines()
        slot, assignment = text[2].split(",")
        text[2] = f"{slot},{'>'.join(reversed(assignment.split('>')))}"
        self.schedule.write_text("\n".join(text) + "\n", encoding="utf-8")
        code, result = self.next("sub-02")
        self.assertEqual(code, 1)
        self.assertIn("changed", result["refused"])
        code, out, _ = run("verify", "--schedule", str(self.schedule), "--ledger", str(self.ledger), "--json")
        self.assertEqual(code, 1)
        self.assertGreaterEqual(len(json.loads(out)["findings"]), 2)

    def test_crlf_copy_keeps_hash(self) -> None:
        data = self.schedule.read_bytes().replace(b"\n", b"\r\n")
        self.schedule.write_bytes(data)
        code, out, _ = run("verify", "--schedule", str(self.schedule), "--json")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
