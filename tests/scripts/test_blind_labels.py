"""Tests for skills/phase-data-preprocess/scripts/blind_labels.py (stdlib unittest, no network)."""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-data-preprocess" / "scripts" / "blind_labels.py"

spec = importlib.util.spec_from_file_location("nf_blind_labels_under_test", SCRIPT)
blind_labels = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = blind_labels
spec.loader.exec_module(blind_labels)

PARTICIPANTS = "participant_id\tgroup\tsex\tage\nsub-01\tpatient\tF\t31\nsub-02\tcontrol\tM\t29\n" \
               "sub-03\tpatient\tF\t40\nsub-04\tcontrol\tM\t35\n"
EVENTS = "onset\tduration\ttrial_type\tvalue\n1.0\t0.1\ttarget\t2\n2.0\t0.1\tstandard\t1\n" \
         "3.0\t0.1\tstandard\t1\n4.0\t0.1\ttarget\t2\n5.0\t0.1\tn/a\tn/a\n"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = blind_labels.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


def read_tsv(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return header, [dict(zip(header, ln.split("\t"))) for ln in lines[1:]]


class BlindLabelsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.bids = self.project / "bids"
        for sub in ("sub-01", "sub-02"):
            d = self.bids / sub / "eeg"
            d.mkdir(parents=True)
            (d / f"{sub}_task-odd_events.tsv").write_text(EVENTS, encoding="utf-8")
        (self.bids / "participants.tsv").write_text(PARTICIPANTS, encoding="utf-8")
        (self.bids / "participants.json").write_text('{"group": {"Levels": {"patient": "p"}}}', encoding="utf-8")
        self.plan = self.project / "preprocess-config.md"
        self.plan.write_text("filter 0.1-40 Hz\n", encoding="utf-8")
        self.keys = self.root / "keys"
        self.out = self.bids / "derivatives" / "blinded"
        self.log = self.project / ".neuroflow" / "data-preprocess" / "blinding.md"
        self.cwd = os.getcwd()
        os.chdir(self.project)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def blind(self, *extra, key="k.json"):
        return run("blind", "--bids-root", self.bids, "--out", self.out, "--key", self.keys / key,
                   "--participants-column", "group", "--plan", self.plan, "--log", self.log, *extra)

    def test_blind_codes_labels_consistently_and_writes_key_outside(self):
        code, out, _ = self.blind("--drop-column", "value", "--drop-column", "sex")
        self.assertEqual(code, 0, out)
        key = json.loads((self.keys / "k.json").read_text(encoding="utf-8"))
        trial_map = key["columns"]["events:trial_type"]
        self.assertEqual(set(trial_map.values()), {"target", "standard"})
        self.assertEqual(set(key["columns"]["participants:group"].values()), {"patient", "control"})
        header, rows = read_tsv(self.out / "sub-01" / "eeg" / "sub-01_task-odd_events.tsv")
        self.assertNotIn("value", header)
        coded = [r["trial_type"] for r in rows]
        self.assertTrue(all(c in trial_map or c == "n/a" for c in coded))
        self.assertEqual(coded[0], coded[3])         # same label -> same code
        self.assertNotEqual(coded[0], coded[1])
        self.assertEqual(coded[4], "n/a")
        _, prow = read_tsv(self.out / "participants.tsv")
        self.assertNotIn("sex", prow[0])
        # originals untouched, sidecar not copied, labels never printed
        self.assertIn("target", (self.bids / "sub-01" / "eeg" / "sub-01_task-odd_events.tsv").read_text())
        self.assertFalse((self.out / "participants.json").exists())
        for label in ("target", "standard", "patient", "control"):
            self.assertNotIn(label, out)
        self.assertIn("sidecar", out)
        log = self.log.read_text(encoding="utf-8")
        self.assertIn("**blinded**", log)
        self.assertNotIn("patient", log)

    def test_leak_warning_exit_1(self):
        code, out, _ = self.blind()
        self.assertEqual(code, 1)
        self.assertIn("events:value determines events:trial_type", out)
        self.assertIn("participants:sex determines participants:group", out)
        self.assertTrue((self.keys / "k.json").exists())

    def test_key_inside_project_is_refused(self):
        code, _, err = run("blind", "--bids-root", self.bids, "--out", self.out, "--key", self.bids / "key.json")
        self.assertEqual(code, 2)
        self.assertIn("outside the project", err)
        self.assertFalse(self.out.exists())

    def test_existing_key_and_out_need_force(self):
        self.blind("--drop-column", "value", "--drop-column", "sex")
        code, _, err = self.blind("--drop-column", "value", "--drop-column", "sex", key="k2.json")
        self.assertEqual(code, 2)
        self.assertIn("not empty", err)
        code, _, err = run("blind", "--bids-root", self.bids, "--out", self.root / "other", "--key", self.keys / "k.json")
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_missing_column_is_error_and_writes_nothing(self):
        code, _, err = run("blind", "--bids-root", self.bids, "--out", self.out, "--key", self.keys / "k.json",
                           "--events-column", "condition")
        self.assertEqual(code, 2)
        self.assertIn("condition", err)
        self.assertFalse((self.keys / "k.json").exists())
        self.assertFalse(self.out.exists())

    def test_unblind_decodes_whole_cells_and_contrasts(self):
        self.blind("--drop-column", "value", "--drop-column", "sex")
        key = json.loads((self.keys / "k.json").read_text(encoding="utf-8"))
        inv = {v: k for k, v in key["columns"]["events:trial_type"].items()}
        table = self.project / "results.tsv"
        table.write_text(f"trial_type\tamp\n{inv['target']}\t1.5\n{inv['target']} - {inv['standard']}\t0.3\n",
                         encoding="utf-8")
        dst = self.project / "results_unblinded.tsv"
        code, out, _ = run("unblind", "--key", self.keys / "k.json", "--input", table, "--column", "trial_type",
                           "--out", dst, "--plan", self.plan, "--log", self.log)
        self.assertEqual(code, 0, out)
        _, rows = read_tsv(dst)
        self.assertEqual(rows[0]["trial_type"], "target")
        self.assertEqual(rows[1]["trial_type"], "target - standard")
        self.assertIn(inv["target"], table.read_text())  # the coded table stays coded
        self.assertIn("**unblinded**", self.log.read_text(encoding="utf-8"))

    def test_unblind_reports_changed_plan(self):
        self.blind("--drop-column", "value", "--drop-column", "sex")
        self.plan.write_text("filter 1-40 Hz\n", encoding="utf-8")
        table = self.project / "r.csv"
        table.write_text("group,score\nG01,1\n", encoding="utf-8")
        code, out, _ = run("unblind", "--key", self.keys / "k.json", "--input", table, "--column", "group",
                           "--out", self.project / "r2.csv", "--plan", self.plan)
        self.assertEqual(code, 1)
        self.assertIn("changed after blinding", out)

    def test_unblind_unknown_column_is_error(self):
        self.blind("--drop-column", "value", "--drop-column", "sex")
        table = self.project / "r.csv"
        table.write_text("x\n1\n", encoding="utf-8")
        code, _, err = run("unblind", "--key", self.keys / "k.json", "--input", table, "--column", "nope",
                           "--out", self.project / "r2.csv")
        self.assertEqual(code, 2)
        self.assertIn("not in the key", err)


if __name__ == "__main__":
    unittest.main()
