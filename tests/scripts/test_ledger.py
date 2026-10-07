"""Tests for skills/phase-finance/scripts/ledger.py (stdlib unittest, no network)."""

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
SCRIPT = REPO / "skills" / "phase-finance" / "scripts" / "ledger.py"

spec = importlib.util.spec_from_file_location("nf_ledger_under_test", SCRIPT)
ledger = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ledger
spec.loader.exec_module(ledger)

EXPENSES_2026 = """# Expenses 2026

Notes above the table are ignored.

| date | grant | category | budget_line | amount | currency | description | reference |
|---|---|---|---|---|---|---|---|
| 2026-03-14 | GR-1 | consumables | consumables | 1240.00 | EUR | EEG caps (2x) | INV-0314 |
| 2026-04-02 | GR-1 | travel | travel | 950.50 | EUR | Conference \\| poster trip | TRV-0402 |
| 2026-05-10 | GR-1 | travel | travel | 1100.00 | EUR | Second trip | TRV-0510 |
| 2026-06-01 | GR-2 | equipment | amplifier | 300 | USD | Cable kit | INV-0601 |
"""

EXPENSES_2025 = """| Date | Grant | Category | Budget line | Amount | Currency | Description | Reference |
|---|---|---|---|---|---|---|---|
| 2025-11-20 | GR-1 | personnel | personnel | 2000.00 | EUR | RA hours Nov | PAY-1120 |
"""

BUDGET = """# Budget GR-1

## Budget lines

| grant | budget_line | category | amount | currency |
|---|---|---|---|---|
| GR-1 | consumables | consumables | 5000.00 | EUR |
| GR-1 | travel | travel | 2000.00 | EUR |
| GR-1 | personnel | personnel | 30000.00 | EUR |
| GR-2 | amplifier | equipment | 400.00 | USD |
"""


def run(*args: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ledger.main([*args, "--json"])
    return code, json.loads(out.getvalue())


class LedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.finance = Path(self._tmp.name) / ".neuroflow" / "finance"
        self.finance.mkdir(parents=True)
        (self.finance / "expenses-2026.md").write_text(EXPENSES_2026, encoding="utf-8")
        (self.finance / "expenses-2025.md").write_text(EXPENSES_2025, encoding="utf-8")
        self.budget = self.finance / "budget-gr1-2025-01-10.md"
        self.budget.write_text(BUDGET, encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_totals_per_grant_category_and_currency(self) -> None:
        code, report = run(str(self.finance))
        self.assertEqual(code, 0, report["findings"])
        self.assertEqual(report["rows"], 5)
        by_grant = {
            (r["grant"], r["currency"]): r["total"]
            for r in report["totals"]["by_grant"]
        }
        self.assertEqual(
            by_grant, {("GR-1", "EUR"): "5290.50", ("GR-2", "USD"): "300.00"}
        )
        by_cat = {
            (r["grant"], r["category"]): r["total"]
            for r in report["totals"]["by_grant_category"]
        }
        self.assertEqual(by_cat[("GR-1", "travel")], "2050.50")
        self.assertEqual(by_cat[("GR-1", "personnel")], "2000.00")

    def test_budget_comparison_flags_overspend(self) -> None:
        code, report = run(str(self.finance), "--budget", str(self.budget))
        self.assertEqual(code, 1)
        travel = next(b for b in report["budget"] if b["budget_line"] == "travel")
        self.assertEqual(
            (
                travel["budget"],
                travel["spent"],
                travel["remaining"],
                travel["overspent"],
            ),
            ("2000.00", "2050.50", "-50.50", True),
        )
        self.assertTrue(
            any("overspent by 50.50" in f["message"] for f in report["findings"])
        )
        amp = next(b for b in report["budget"] if b["budget_line"] == "amplifier")
        self.assertEqual(amp["remaining"], "100.00")

    def test_grant_and_date_filters(self) -> None:
        code, report = run(
            str(self.finance),
            "--grant",
            "GR-1",
            "--from",
            "2026-01-01",
            "--to",
            "2026-04-30",
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["rows"], 2)
        self.assertEqual(
            report["totals"]["by_grant"],
            [{"grant": "GR-1", "currency": "EUR", "total": "2190.50"}],
        )

    def test_malformed_rows_are_findings_and_excluded(self) -> None:
        bad = (
            EXPENSES_2026
            + "| 2026-07-01 | GR-1 | snacks | other | 1.240,00 | eur | Party | - |\n| 2026-13-01 | GR-1 | other | other | 5 | EUR |\n"
        )
        (self.finance / "expenses-2026.md").write_text(bad, encoding="utf-8")
        code, report = run(str(self.finance))
        self.assertEqual(code, 1)
        messages = " | ".join(f["message"] for f in report["findings"])
        self.assertIn("category 'snacks'", messages)
        self.assertIn("amount '1.240,00' is not a plain decimal", messages)
        self.assertIn("currency 'eur'", messages)
        self.assertIn("row has 6 cells, header has 8", messages)
        self.assertEqual(report["rows"], 5)

    def test_currency_mismatch_is_reported_not_converted(self) -> None:
        extra = (
            EXPENSES_2026
            + "| 2026-08-01 | GR-1 | travel | travel | 120.00 | USD | Taxi abroad | TX-1 |\n"
        )
        (self.finance / "expenses-2026.md").write_text(extra, encoding="utf-8")
        code, report = run(str(self.finance), "--budget", str(self.budget))
        self.assertEqual(code, 1)
        self.assertTrue(
            any(
                "budgeted in EUR" in f["message"] and "never converts" in f["message"]
                for f in report["findings"]
            )
        )
        by_grant = {
            (r["grant"], r["currency"]): r["total"]
            for r in report["totals"]["by_grant"]
        }
        self.assertEqual(by_grant[("GR-1", "USD")], "120.00")

    def test_csv_export(self) -> None:
        target = Path(self._tmp.name) / "ledger.csv"
        code, _ = run(str(self.finance), "--csv", str(target))
        self.assertEqual(code, 0)
        with target.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["date"], "2025-11-20")
        trip = next(r for r in rows if r["reference"] == "TRV-0402")
        self.assertEqual(trip["description"], "Conference | poster trip")
        self.assertEqual(trip["amount"], "950.50")

    def test_no_files_is_usage_error(self) -> None:
        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(ledger.main([str(empty)]), 2)
            self.assertEqual(ledger.main([str(Path(self._tmp.name) / "missing")]), 2)

    def test_budget_without_table_is_usage_error(self) -> None:
        plain = self.finance / "budget-plain.md"
        plain.write_text("# Budget\n\nPersonnel 30k, travel 2k.\n", encoding="utf-8")
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(
                ledger.main([str(self.finance), "--budget", str(plain)]), 2
            )

    def test_text_report(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger.main([str(self.finance)])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("By grant and category", text)
        self.assertIn("5290.50", text)
        self.assertIn("No findings.", text)


if __name__ == "__main__":
    unittest.main()
