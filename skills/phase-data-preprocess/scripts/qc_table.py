#!/usr/bin/env python3
"""qc_table.py - build the subject x metric QC table from per-subject QC JSON files.

Part of the neuroflow `phase-data-preprocess` skill. The preprocessing pipeline writes one
QC JSON file per subject (contract: the skill's "QC JSON contract" section); this script
collects them and renders the QC matrix as markdown and/or CSV, flagging values that cross
thresholds. The numbers in the preprocessing report come from code - never transcribe them.

Examples:
  python qc_table.py derivatives/preprocessing/qc/
  python qc_table.py qc/ --markdown .neuroflow/data-preprocess/qc-table.md --csv qc/qc-table.csv
  python qc_table.py qc/ --threshold "pct_bad_channels>15" --threshold "pct_epochs_rejected>=30"
  python qc_table.py qc/ --robust-z 3.5 --json

Exit codes: 0 = table built, nothing flagged; 1 = table built, at least one value flagged;
            2 = usage error, no QC files found, or a malformed QC file (listed).
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import operator
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

QC_VERSION = 1
DEFAULT_PATTERN = "*_qc.json"
# Placeholders - replace them with the preregistered (or a-priori documented) exclusion criteria.
DEFAULT_THRESHOLDS = ("pct_bad_channels>20", "pct_epochs_rejected>25")
ID_FIELDS = ("subject", "session", "task", "run")
ROBUST_Z_MIN_N = 5
_OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}
_RULE_RE = re.compile(r"^\s*([A-Za-z_][\w.-]*)\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*$")


class UsageError(Exception):
    """Bad arguments or nothing to work on (exit 2)."""


@dataclass
class Rule:
    metric: str
    op: str
    value: float

    def hit(self, v: float) -> bool:
        return _OPS[self.op](v, self.value)

    def __str__(self) -> str:
        return f"{self.metric} {self.op} {fmt_number(self.value)}"


@dataclass
class Row:
    key: str
    ids: dict
    metrics: dict
    file: str
    flags: list = field(default_factory=list)
    flagged_metrics: set = field(default_factory=set)


def parse_rule(text: str) -> Rule:
    m = _RULE_RE.match(text)
    if not m:
        raise UsageError(f"threshold {text!r} is not of the form metric>value (operators: > >= < <=)")
    return Rule(m.group(1), m.group(2), float(m.group(3)))


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_finite(v) -> bool:
    return is_number(v) and math.isfinite(v)


def fmt_number(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool) or not is_number(v):
        return str(v)
    if not math.isfinite(v):
        return "NaN" if math.isnan(v) else ("inf" if v > 0 else "-inf")
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    if abs(v) >= 1000:
        return f"{v:.0f}"
    if abs(v) >= 1:
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return f"{v:.3g}"


def json_safe(metrics: dict) -> dict:
    """Non-finite numbers become strings so the JSON output stays standard JSON."""
    return {k: (fmt_number(v) if is_number(v) and not math.isfinite(v) else v) for k, v in metrics.items()}


def natural_key(text: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def find_files(paths: list[str], pattern: str) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            found.append(p)
        elif p.is_dir():
            found.extend(sorted(p.rglob(pattern)))
        else:
            raise UsageError(f"{raw}: no such file or directory")
    seen, unique = set(), []
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def load_qc(path: Path) -> tuple[Row | None, str | None, list[str]]:
    """Return (row, error, notes) for one QC file."""
    notes: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, f"{path}: not readable JSON ({e})", notes
    if not isinstance(data, dict):
        return None, f"{path}: top level must be a JSON object", notes
    version = data.get("nf_qc", QC_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        return None, f"{path}: nf_qc must be an integer", notes
    if version > QC_VERSION:
        return None, f"{path}: nf_qc {version} is newer than this script understands ({QC_VERSION}) - update neuroflow", notes
    subject = data.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        return None, f"{path}: missing 'subject' (a non-empty string such as \"sub-01\")", notes
    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        return None, f"{path}: missing 'metrics' (an object of metric name -> number or null)", notes
    for name, value in metrics.items():
        if value is not None and not is_number(value):
            return None, (f"{path}: metric {name!r} is {type(value).__name__}; metrics must be numbers or null "
                          "(put lists and text under 'details')"), notes
        if is_number(value) and not math.isfinite(value):
            notes.append(f"{subject}: {name} is {fmt_number(value)} (not compared with thresholds)")
    ids = {}
    for f in ID_FIELDS:
        v = data.get(f)
        if v is not None and str(v).strip():
            ids[f] = str(v).strip()
    key = "_".join(ids[f] for f in ID_FIELDS if f in ids)
    return Row(key=key, ids=ids, metrics=dict(metrics), file=str(path)), None, notes


def apply_rules(rows: list[Row], rules: list[Rule], notes: list[str]) -> None:
    present = {m for r in rows for m in r.metrics}
    for rule in rules:
        if rule.metric not in present:
            notes.append(f"threshold `{rule}`: metric not present in any QC file")
            continue
        for row in rows:
            v = row.metrics.get(rule.metric)
            if is_finite(v) and rule.hit(v):
                row.flags.append(str(rule))
                row.flagged_metrics.add(rule.metric)


def apply_robust_z(rows: list[Row], metrics: list[str], z_limit: float, notes: list[str]) -> None:
    for metric in metrics:
        vals = [(row, row.metrics.get(metric)) for row in rows if is_finite(row.metrics.get(metric))]
        if len(vals) < ROBUST_Z_MIN_N:
            notes.append(f"robust z skipped for {metric}: {len(vals)} values (needs at least {ROBUST_Z_MIN_N})")
            continue
        med = statistics.median(v for _, v in vals)
        mad = statistics.median(abs(v - med) for _, v in vals)
        if mad == 0:
            notes.append(f"robust z skipped for {metric}: median absolute deviation is 0")
            continue
        for row, v in vals:
            z = 0.6745 * (v - med) / mad
            if abs(z) > z_limit:
                row.flags.append(f"{metric} robust z = {z:.1f}")
                row.flagged_metrics.add(metric)


def metric_columns(rows: list[Row], wanted: list[str] | None) -> list[str]:
    if wanted:
        return wanted
    cols: list[str] = []
    for row in rows:
        for m in row.metrics:
            if m not in cols:
                cols.append(m)
    return cols


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(rows, cols, rules, used_defaults, z_limit, n_files, notes, errors) -> str:
    out = ["## QC matrix", ""]
    out.append("| Subject | " + " | ".join(escape_cell(c) for c in cols) + " | Flags |")
    out.append("|---|" + "---:|" * len(cols) + "---|")
    for row in rows:
        cells = []
        for c in cols:
            v = row.metrics.get(c)
            text = "n/a" if v is None else fmt_number(v)
            if c in row.flagged_metrics and v is not None:
                text = f"**{text}**"
            cells.append(text)
        out.append(f"| {escape_cell(row.key)} | " + " | ".join(cells) + f" | {escape_cell('; '.join(row.flags))} |")
    out.append("")
    flagged = sum(1 for r in rows if r.flags)
    out.append(f"- QC files: {n_files}; rows flagged: {flagged} of {len(rows)}")
    rule_text = ", ".join(f"`{r}`" for r in rules) if rules else "none"
    if used_defaults:
        rule_text += " (defaults - replace them with the preregistered or a-priori exclusion criteria)"
    out.append(f"- Thresholds: {rule_text}")
    out.append(f"- Robust z: {'|z| > ' + fmt_number(z_limit) if z_limit else 'off'}")
    out.append("- A flag marks a value to look at, not an exclusion. Exclude only by criteria fixed before the "
               "outcome is known, and log each exclusion decision.")
    for n in notes:
        out.append(f"- Note: {n}")
    for e in errors:
        out.append(f"- ERROR: {e}")
    out.append("")
    out.append(f"_Generated by qc_table.py on {date.today().isoformat()} from per-subject QC JSON - "
               "regenerate it, do not edit by hand._")
    return "\n".join(out) + "\n"


def write_csv(path: Path, rows: list[Row], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(list(ID_FIELDS) + cols + ["flags", "file"])
        for row in rows:
            ids = [row.ids.get(f, "") for f in ID_FIELDS]
            vals = ["" if row.metrics.get(c) is None else row.metrics.get(c) for c in cols]
            w.writerow(ids + vals + ["; ".join(row.flags), row.file])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="qc_table.py",
        description="Build the subject x metric QC table from per-subject QC JSON files (neuroflow).",
        epilog="Exit codes: 0 = nothing flagged, 1 = values flagged, 2 = usage error or malformed QC file.",
    )
    p.add_argument("paths", nargs="+", help="QC JSON files or folders (searched recursively)")
    p.add_argument("--pattern", default=DEFAULT_PATTERN, help=f"file pattern inside folders (default {DEFAULT_PATTERN})")
    p.add_argument("--threshold", action="append", default=[], metavar="RULE",
                   help="flag rule such as 'pct_bad_channels>20' (repeatable; replaces the defaults)")
    p.add_argument("--no-default-thresholds", action="store_true", help="apply no thresholds unless --threshold is given")
    p.add_argument("--robust-z", type=float, default=None, metavar="Z",
                   help=f"also flag |robust z| > Z per metric (skipped below {ROBUST_Z_MIN_N} values or when MAD = 0)")
    p.add_argument("--metrics", default=None, help="comma-separated metric columns to show, in order (default: all)")
    p.add_argument("--markdown", default=None, metavar="PATH", help="also write the markdown table to PATH")
    p.add_argument("--csv", default=None, metavar="PATH", help="also write the table as CSV to PATH")
    p.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.robust_z is not None and args.robust_z <= 0:
            raise UsageError("--robust-z must be positive")
        if args.threshold:
            rules = [parse_rule(t) for t in args.threshold]
            used_defaults = False
        elif args.no_default_thresholds:
            rules, used_defaults = [], False
        else:
            rules, used_defaults = [parse_rule(t) for t in DEFAULT_THRESHOLDS], True
        files = find_files(args.paths, args.pattern)
        if not files:
            raise UsageError(f"no QC files matching {args.pattern!r} under {', '.join(args.paths)}")
    except UsageError as e:
        print(f"qc_table.py: error: {e}", file=sys.stderr)
        return 2

    rows: list[Row] = []
    errors: list[str] = []
    notes: list[str] = []
    for path in files:
        row, err, file_notes = load_qc(path)
        notes.extend(file_notes)
        if err:
            errors.append(err)
        elif row is not None:
            rows.append(row)
    by_key: dict[str, Row] = {}
    for row in rows:
        if row.key in by_key:
            errors.append(f"duplicate QC entry for {row.key}: {by_key[row.key].file} and {row.file}")
        else:
            by_key[row.key] = row
    rows = sorted(by_key.values(), key=lambda r: natural_key(r.key))

    wanted = [m.strip() for m in args.metrics.split(",") if m.strip()] if args.metrics else None
    cols = metric_columns(rows, wanted)
    apply_rules(rows, rules, notes)
    if args.robust_z:
        apply_robust_z(rows, cols, args.robust_z, notes)

    markdown = render_markdown(rows, cols, rules, used_defaults, args.robust_z, len(files), notes, errors)
    try:
        if args.markdown:
            out = Path(args.markdown)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(markdown, encoding="utf-8", newline="\n")
        if args.csv:
            write_csv(Path(args.csv), rows, cols)
    except OSError as e:
        print(f"qc_table.py: error: cannot write output ({e})", file=sys.stderr)
        return 2

    flagged = [r for r in rows if r.flags]
    if args.json:
        payload = {
            "tool": "qc_table",
            "qc_version": QC_VERSION,
            "files": len(files),
            "metrics": cols,
            "thresholds": [str(r) for r in rules],
            "default_thresholds": used_defaults,
            "robust_z": args.robust_z,
            "rows": [
                {**{f: r.ids.get(f) for f in ID_FIELDS}, "key": r.key, "metrics": json_safe(r.metrics),
                 "flags": r.flags, "file": r.file}
                for r in rows
            ],
            "flagged_rows": len(flagged),
            "notes": notes,
            "errors": errors,
        }
        print(json.dumps(payload, indent=2))
    else:
        sys.stdout.write(markdown)

    if errors:
        return 2
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
