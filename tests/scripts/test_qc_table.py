"""Tests for skills/phase-data-preprocess/scripts/qc_table.py (stdlib unittest, no network)."""

import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-data-preprocess" / "scripts" / "qc_table.py"

spec = importlib.util.spec_from_file_location("nf_qc_table_under_test", SCRIPT)
qc_table = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = qc_table
spec.loader.exec_module(qc_table)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = qc_table.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


def write_qc(folder: Path, subject: str, metrics: dict, **extra) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    data = {"nf_qc": 1, "subject": subject, "metrics": metrics, **extra}
    path = folder / f"{subject}{'_' + extra['session'] if 'session' in extra else ''}_qc.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class QcTableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.qc = self.root / "derivatives" / "qc"

    def tearDown(self):
        self.tmp.cleanup()

    def cohort(self):
        rows = [("sub-01", 2, 10.0), ("sub-02", 15, 12.5), ("sub-03", 3, 40.0), ("sub-04", 1, 5.0), ("sub-10", 0, 8.0)]
        for sub, bad, rej in rows:
            write_qc(self.qc, sub, {"n_channels": 64, "n_bad_channels": bad,
                                     "pct_bad_channels": round(bad / 64 * 100, 2), "pct_epochs_rejected": rej},
                     details={"bad_channels": ["Fp1"] * bad})

    def test_default_thresholds_flag_rows_and_exit_1(self):
        self.cohort()
        code, out, _ = run(self.qc)
        self.assertEqual(code, 1)
        self.assertIn("| sub-02 |", out)
        self.assertIn("**23.44**", out)
        self.assertIn("pct_bad_channels > 20", out)
        self.assertIn("pct_epochs_rejected > 25", out)
        self.assertIn("defaults", out)
        # natural sort: sub-10 after sub-04
        self.assertLess(out.index("| sub-04 |"), out.index("| sub-10 |"))

    def test_custom_threshold_replaces_defaults(self):
        self.cohort()
        code, out, _ = run(self.qc, "--threshold", "pct_epochs_rejected>=50")
        self.assertEqual(code, 0)
        self.assertNotIn("pct_bad_channels > 20", out)
        self.assertNotIn("(defaults", out)

    def test_no_default_thresholds(self):
        self.cohort()
        code, out, _ = run(self.qc, "--no-default-thresholds")
        self.assertEqual(code, 0)
        self.assertIn("Thresholds: none", out)

    def test_bad_threshold_syntax_is_usage_error(self):
        self.cohort()
        code, _, err = run(self.qc, "--threshold", "pct_bad_channels=20")
        self.assertEqual(code, 2)
        self.assertIn("not of the form", err)

    def test_markdown_and_csv_outputs(self):
        self.cohort()
        md = self.root / ".neuroflow" / "data-preprocess" / "qc-table.md"
        cs = self.qc / "qc-table.csv"
        code, _, _ = run(self.qc, "--markdown", md, "--csv", cs)
        self.assertEqual(code, 1)
        self.assertTrue(md.read_text(encoding="utf-8").startswith("## QC matrix"))
        with cs.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 5)
        flagged = {r["subject"]: r["flags"] for r in rows}
        self.assertIn("pct_bad_channels > 20", flagged["sub-02"])
        self.assertEqual(flagged["sub-01"], "")

    def test_robust_z_flags_outlier_and_skips_zero_mad(self):
        for i, v in enumerate([5.0, 5.5, 6.0, 5.2, 30.0, 5.8], start=1):
            write_qc(self.qc, f"sub-{i:02d}", {"pct_epochs_rejected": v, "n_channels": 64})
        code, out, _ = run(self.qc, "--no-default-thresholds", "--robust-z", "3.5")
        self.assertEqual(code, 1)
        self.assertIn("pct_epochs_rejected robust z", out)
        self.assertIn("robust z skipped for n_channels", out)

    def test_robust_z_needs_enough_subjects(self):
        for i in range(1, 4):
            write_qc(self.qc, f"sub-{i:02d}", {"pct_epochs_rejected": float(i * 10)})
        code, out, _ = run(self.qc, "--no-default-thresholds", "--robust-z", "2")
        self.assertEqual(code, 0)
        self.assertIn("robust z skipped for pct_epochs_rejected: 3 values", out)

    def test_malformed_file_is_exit_2(self):
        self.cohort()
        (self.qc / "sub-99_qc.json").write_text("{not json", encoding="utf-8")
        code, out, _ = run(self.qc)
        self.assertEqual(code, 2)
        self.assertIn("ERROR", out)

    def test_list_metric_is_rejected(self):
        write_qc(self.qc, "sub-01", {"bad_channels": ["Fp1"]})
        code, out, _ = run(self.qc)
        self.assertEqual(code, 2)
        self.assertIn("details", out)

    def test_duplicate_subject_is_exit_2(self):
        write_qc(self.qc, "sub-01", {"pct_bad_channels": 1.0})
        write_qc(self.root / "other", "sub-01", {"pct_bad_channels": 2.0})
        code, out, _ = run(self.qc, self.root / "other")
        self.assertEqual(code, 2)
        self.assertIn("duplicate QC entry for sub-01", out)

    def test_sessions_make_distinct_rows(self):
        write_qc(self.qc, "sub-01", {"pct_bad_channels": 1.0}, session="ses-01")
        write_qc(self.qc, "sub-01", {"pct_bad_channels": 2.0}, session="ses-02")
        code, out, _ = run(self.qc)
        self.assertEqual(code, 0)
        self.assertIn("| sub-01_ses-01 |", out)
        self.assertIn("| sub-01_ses-02 |", out)

    def test_no_files_is_exit_2(self):
        self.qc.mkdir(parents=True)
        code, _, err = run(self.qc)
        self.assertEqual(code, 2)
        self.assertIn("no QC files", err)

    def test_newer_contract_is_refused(self):
        write_qc(self.qc, "sub-01", {"pct_bad_channels": 1.0})
        (self.qc / "sub-02_qc.json").write_text(json.dumps({"nf_qc": 99, "subject": "sub-02", "metrics": {"x": 1}}))
        code, out, _ = run(self.qc)
        self.assertEqual(code, 2)
        self.assertIn("newer", out)

    def test_json_output_is_standard_json_with_nan(self):
        (self.qc).mkdir(parents=True)
        (self.qc / "sub-01_qc.json").write_text('{"subject": "sub-01", "metrics": {"pct_epochs_rejected": NaN}}')
        code, out, _ = run(self.qc, "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out, parse_constant=lambda c: self.fail(f"non-standard JSON constant {c}"))
        self.assertEqual(payload["rows"][0]["metrics"]["pct_epochs_rejected"], "NaN")
        self.assertTrue(any("NaN" in n for n in payload["notes"]))


if __name__ == "__main__":
    unittest.main()
