#!/usr/bin/env python3
"""Exact totals for neuroflow expense logs.

Reads the expense table(s) in .neuroflow/finance/expenses-*.md:

    | date | grant | category | budget_line | amount | currency | description | reference |
    |---|---|---|---|---|---|---|---|
    | 2026-03-14 | GR-2025-001 | consumables | consumables | 1240.00 | EUR | EEG caps (2x) | INV-0314 |

and prints totals per currency: by grant, by grant and category, and by grant
and budget line. Optional: --budget compares spending with a budget file's
"Budget lines" table (| grant | budget_line | amount | currency |) and flags
overspent lines; --csv exports the validated rows.

Read-only. It never writes or edits an expense, never converts currencies
(totals are per currency), and never books AI usage or any other figure as an
expense — every row comes from a person with a receipt.

Exit codes: 0 = clean; 1 = findings (malformed rows, unknown categories,
overspent or unknown budget lines); 2 = usage or runtime error.
"""

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

CATEGORIES = ("personnel", "equipment", "consumables", "travel", "other")
EXPENSE_REQUIRED = ("date", "grant", "category", "amount", "currency")
EXPENSE_COLUMNS = (
    "date",
    "grant",
    "category",
    "budget_line",
    "amount",
    "currency",
    "description",
    "reference",
)
BUDGET_REQUIRED = ("grant", "budget_line", "amount", "currency")
AMOUNT_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")


class UsageError(Exception):
    """Bad arguments or unreadable input (exit 2)."""


@dataclass
class Row:
    file: str
    line: int
    date: str
    grant: str
    category: str
    budget_line: str
    amount: Decimal
    currency: str
    description: str
    reference: str


def split_cells(line: str) -> list[str]:
    """Split a markdown table row on unescaped pipes; '\\|' stays a literal pipe."""
    body = line.strip().removeprefix("|")
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells, cur, i = [], [], 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def header_key(cell: str) -> str:
    return re.sub(r"\s+", "_", cell.strip().strip("*_`").strip().lower())


def tables(path: Path) -> list[tuple[list[str], list[tuple[int, list[str]]]]]:
    """Every markdown table in a file as (header keys, [(line number, cells)])."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"cannot read {path}: {exc}") from exc
    found = []
    idx = 0
    while idx < len(lines) - 1:
        line = lines[idx]
        if line.lstrip().startswith("|") and SEPARATOR_RE.match(lines[idx + 1].strip()):
            header = [header_key(c) for c in split_cells(line)]
            rows = []
            j = idx + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, split_cells(lines[j])))
                j += 1
            found.append((header, rows))
            idx = j
            continue
        idx += 1
    return found


def parse_amount(raw: str) -> Decimal | None:
    value = raw.replace(" ", "")
    if not AMOUNT_RE.match(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def fmt(amount: Decimal) -> str:
    if amount.as_tuple().exponent >= -2:
        amount = amount.quantize(Decimal("0.01"))
    return format(amount, "f")


def read_expenses(files: list[Path], findings: list[dict]) -> list[Row]:
    rows: list[Row] = []
    for path in files:
        seen_table = False
        for header, body in tables(path):
            if not all(col in header for col in EXPENSE_REQUIRED):
                continue
            seen_table = True
            for line_no, cells in body:
                where = {"file": str(path), "line": line_no}
                if all(not c for c in cells):
                    continue
                if len(cells) != len(header):
                    findings.append(
                        {
                            **where,
                            "message": f"row has {len(cells)} cells, header has {len(header)}",
                        }
                    )
                    continue
                rec = dict(zip(header, cells))
                problems = []
                try:
                    when = date.fromisoformat(rec["date"]).isoformat()
                except ValueError:
                    when = ""
                    problems.append(f"date '{rec['date']}' is not YYYY-MM-DD")
                category = rec["category"].strip().lower()
                if category not in CATEGORIES:
                    problems.append(
                        f"category '{rec['category']}' is not one of {', '.join(CATEGORIES)}"
                    )
                amount = parse_amount(rec["amount"])
                if amount is None:
                    problems.append(
                        f"amount '{rec['amount']}' is not a plain decimal (write e.g. 1240.00 - no thousands separators)"
                    )
                currency = rec["currency"].strip()
                if not CURRENCY_RE.match(currency):
                    problems.append(
                        f"currency '{rec['currency']}' is not a 3-letter ISO code in capitals (e.g. EUR)"
                    )
                if not rec["grant"].strip():
                    problems.append("grant is empty")
                if problems:
                    findings.extend({**where, "message": p} for p in problems)
                    continue
                rows.append(
                    Row(
                        file=str(path),
                        line=line_no,
                        date=when,
                        grant=rec["grant"].strip(),
                        category=category,
                        budget_line=rec.get("budget_line", "").strip(),
                        amount=amount,
                        currency=currency,
                        description=rec.get("description", "").strip(),
                        reference=rec.get("reference", "").strip(),
                    )
                )
        if not seen_table:
            findings.append(
                {
                    "file": str(path),
                    "line": 0,
                    "message": "no expense table (needs columns "
                    + ", ".join(EXPENSE_REQUIRED)
                    + ")",
                }
            )
    return rows


def read_budget(
    path: Path, findings: list[dict]
) -> dict[tuple[str, str, str], Decimal]:
    budget: dict[tuple[str, str, str], Decimal] = {}
    found = False
    for header, body in tables(path):
        if not all(col in header for col in BUDGET_REQUIRED) or "date" in header:
            continue
        found = True
        for line_no, cells in body:
            where = {"file": str(path), "line": line_no}
            if len(cells) != len(header):
                findings.append(
                    {
                        **where,
                        "message": f"budget row has {len(cells)} cells, header has {len(header)}",
                    }
                )
                continue
            rec = dict(zip(header, cells))
            amount = parse_amount(rec["amount"])
            currency = rec["currency"].strip()
            if amount is None or not CURRENCY_RE.match(currency):
                findings.append(
                    {
                        **where,
                        "message": f"budget row needs a plain decimal amount and an ISO currency: {rec['amount']} {rec['currency']}",
                    }
                )
                continue
            key = (rec["grant"].strip(), rec["budget_line"].strip(), currency)
            budget[key] = budget.get(key, Decimal(0)) + amount
    if not found:
        raise UsageError(
            f"{path}: no budget-lines table (needs columns {', '.join(BUDGET_REQUIRED)})"
        )
    return budget


def total(rows: list[Row], *keys: str) -> list[dict]:
    sums: dict[tuple, Decimal] = {}
    for row in rows:
        key = tuple(getattr(row, k) for k in keys) + (row.currency,)
        sums[key] = sums.get(key, Decimal(0)) + row.amount
    return [
        dict(zip((*keys, "currency"), key), total=fmt(value))
        for key, value in sorted(sums.items())
    ]


def compare_budget(
    rows: list[Row], budget: dict, findings: list[dict], budget_file: str
) -> list[dict]:
    spent: dict[tuple[str, str, str], Decimal] = {}
    for row in rows:
        key = (row.grant, row.budget_line, row.currency)
        spent[key] = spent.get(key, Decimal(0)) + row.amount
    lines = []
    for key in sorted(set(budget) | set(spent)):
        grant, line, currency = key
        planned = budget.get(key)
        used = spent.get(key, Decimal(0))
        if planned is None:
            other = sorted(c for (g, b, c) in budget if g == grant and b == line)
            if not line:
                msg = f"{grant}: {fmt(used)} {currency} spent without a budget line"
            elif other:
                msg = f"{grant} / {line}: spent in {currency} but budgeted in {', '.join(other)} - ledger.py never converts; log the amount in the budget currency at the rate your funder requires"
            else:
                msg = f"{grant} / {line}: not in the budget ({fmt(used)} {currency} spent)"
            findings.append({"file": budget_file, "line": 0, "message": msg})
            lines.append(
                {
                    "grant": grant,
                    "budget_line": line,
                    "currency": currency,
                    "budget": None,
                    "spent": fmt(used),
                    "remaining": None,
                    "overspent": False,
                }
            )
            continue
        remaining = planned - used
        over = remaining < 0
        if over:
            findings.append(
                {
                    "file": budget_file,
                    "line": 0,
                    "message": f"{grant} / {line} ({currency}) overspent by {fmt(-remaining)}",
                }
            )
        lines.append(
            {
                "grant": grant,
                "budget_line": line,
                "currency": currency,
                "budget": fmt(planned),
                "spent": fmt(used),
                "remaining": fmt(remaining),
                "overspent": over,
            }
        )
    return lines


def collect_files(paths: list[str]) -> list[Path]:
    targets = paths or [str(Path(".neuroflow") / "finance")]
    files: list[Path] = []
    for raw in targets:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.glob("expenses-*.md")))
        elif p.is_file():
            files.append(p)
        else:
            raise UsageError(f"{raw}: no such file or folder")
    if not files:
        raise UsageError(
            "no expense files found (expected .neuroflow/finance/expenses-*.md)"
        )
    return files


def table_text(head: list[str], rows: list[list[str]], right: set[int]) -> list[str]:
    widths = (
        [max(len(str(x)) for x in col) for col in zip(head, *rows)]
        if rows
        else [len(h) for h in head]
    )

    def fmt_row(r: list[str]) -> str:
        return (
            "  "
            + "  ".join(
                str(c).rjust(w) if i in right else str(c).ljust(w)
                for i, (c, w) in enumerate(zip(r, widths))
            ).rstrip()
        )

    return [fmt_row(head)] + [fmt_row(r) for r in rows]


def render_text(report: dict) -> str:
    out = [
        f"Expense ledger - {report['rows']} row(s) from {len(report['files'])} file(s)"
    ]
    out += [f"  {f}" for f in report["files"]]
    t = report["totals"]
    out += ["", "By grant"] + table_text(
        ["grant", "currency", "total"],
        [[r["grant"], r["currency"], r["total"]] for r in t["by_grant"]],
        {2},
    )
    out += ["", "By grant and category"] + table_text(
        ["grant", "category", "currency", "total"],
        [
            [r["grant"], r["category"], r["currency"], r["total"]]
            for r in t["by_grant_category"]
        ],
        {3},
    )
    out += ["", "By grant and budget line"] + table_text(
        ["grant", "budget_line", "currency", "total"],
        [
            [r["grant"], r["budget_line"] or "-", r["currency"], r["total"]]
            for r in t["by_grant_budget_line"]
        ],
        {3},
    )
    if report.get("budget") is not None:
        out += ["", f"Budget ({report['budget_file']})"] + table_text(
            ["grant", "budget_line", "currency", "budget", "spent", "remaining", ""],
            [
                [
                    b["grant"],
                    b["budget_line"] or "-",
                    b["currency"],
                    b["budget"] or "-",
                    b["spent"],
                    b["remaining"] or "-",
                    "OVERSPENT" if b["overspent"] else "",
                ]
                for b in report["budget"]
            ],
            {3, 4, 5},
        )
    if report["findings"]:
        out += ["", f"Findings ({len(report['findings'])})"]
        for f in report["findings"]:
            where = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            out.append(f"  {where}  {f['message']}")
    else:
        out += ["", "No findings."]
    return "\n".join(out)


def write_csv(rows: list[Row], target: str) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([*EXPENSE_COLUMNS, "file", "line"])
    for r in rows:
        writer.writerow(
            [
                r.date,
                r.grant,
                r.category,
                r.budget_line,
                fmt(r.amount),
                r.currency,
                r.description,
                r.reference,
                r.file,
                r.line,
            ]
        )
    if target == "-":
        sys.stdout.write(buf.getvalue())
        return
    try:
        Path(target).write_text(buf.getvalue(), encoding="utf-8", newline="")
    except OSError as exc:
        raise UsageError(f"cannot write {target}: {exc.strerror or exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ledger.py",
        description="Totals for neuroflow expense logs, per currency, by grant / category / budget line. Read-only; never converts currencies.",
    )
    ap.add_argument(
        "paths",
        nargs="*",
        help="expense files or folders (default: .neuroflow/finance/ -> expenses-*.md)",
    )
    ap.add_argument(
        "--budget",
        help="budget file with a budget-lines table (| grant | budget_line | amount | currency |)",
    )
    ap.add_argument("--grant", help="only rows for this grant")
    ap.add_argument(
        "--from", dest="date_from", help="only rows on or after this date (YYYY-MM-DD)"
    )
    ap.add_argument(
        "--to", dest="date_to", help="only rows on or before this date (YYYY-MM-DD)"
    )
    ap.add_argument(
        "--csv",
        help="export the validated rows as CSV to this file ('-' for stdout, nothing else printed)",
    )
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    findings: list[dict] = []
    try:
        bounds = [
            date.fromisoformat(d).isoformat() if d else None
            for d in (args.date_from, args.date_to)
        ]
    except ValueError:
        print("ledger: --from/--to must be YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        files = collect_files(args.paths)
        rows = read_expenses(files, findings)
        if args.grant:
            rows = [r for r in rows if r.grant == args.grant]
        if bounds[0]:
            rows = [r for r in rows if r.date >= bounds[0]]
        if bounds[1]:
            rows = [r for r in rows if r.date <= bounds[1]]
        report: dict = {
            "files": [str(f) for f in files],
            "rows": len(rows),
            "totals": {
                "by_grant": total(rows, "grant"),
                "by_grant_category": total(rows, "grant", "category"),
                "by_grant_budget_line": total(rows, "grant", "budget_line"),
            },
            "budget": None,
            "budget_file": None,
        }
        if args.budget:
            budget = read_budget(Path(args.budget), findings)
            if args.grant:
                budget = {k: v for k, v in budget.items() if k[0] == args.grant}
            report["budget"] = compare_budget(rows, budget, findings, args.budget)
            report["budget_file"] = args.budget
        report["findings"] = findings
        if args.csv:
            write_csv(rows, args.csv)
    except UsageError as exc:
        print(f"ledger: {exc}", file=sys.stderr)
        return 2
    if args.csv == "-":
        for f in findings:
            print(f"ledger: {f['file']}:{f['line']}: {f['message']}", file=sys.stderr)
    elif args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
