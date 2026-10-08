#!/usr/bin/env python3
"""PR-time validation for the neuroflow plugin repo (CI and local runs).

Stdlib only. Run from anywhere:

    python scripts/automation/validate_pr.py [--base origin/main] [--json] [--only V3,V8]

Runs every check in scripts/automation/repo_checks.py - the single implementation that
sentinel_check.py (daily report) also runs and agents/sentinel-dev.md cites (V1-V15; V7
only with --base). `fail` findings fail the run; `warn` findings are printed for human
review and do not fail it.

Exit code 0 = no failures, 1 = at least one failure, 2 = usage or internal error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_checks  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate the neuroflow plugin repo (the checks CI runs on every PR).")
    ap.add_argument("--base", help="git ref to compare against for the version-bump check V7 (e.g. origin/main)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    ap.add_argument("--only", help=f"comma-separated check ids ({', '.join(repo_checks.CHECK_IDS)})")
    ap.add_argument("--root", type=Path, default=repo_checks.ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # messages quote repo text; local consoles may not encode it
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    only = None
    if args.only:
        only = {c.strip().upper() for c in args.only.split(",") if c.strip()}
        unknown = only - set(repo_checks.CHECK_IDS)
        if unknown:
            print(f"validate_pr: unknown check id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
    try:
        findings = repo_checks.run(root=args.root.resolve(), base=args.base, only=only)
    except Exception as exc:  # a crash is not a verdict
        print(f"validate_pr: internal error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    failures = [f for f in findings if f.severity == repo_checks.FAIL]
    warnings = [f for f in findings if f.severity == repo_checks.WARN]
    code = 1 if failures else 0
    if args.json:
        print(json.dumps({
            "tool": "validate_pr",
            "findings": [{"check": f.check, "severity": f.severity, "message": f.message} for f in findings],
            "summary": {"fail": len(failures), "warn": len(warnings)},
            "exit_code": code,
        }, indent=2))
        return code
    if failures:
        print(f"FAIL validate_pr: {len(failures)} failure(s), {len(warnings)} warning(s)\n")
        for f in failures:
            print(f"  [{f.check}] {f.message}")
    else:
        print(f"OK validate_pr: all checks passed ({len(warnings)} warning(s))")
    if warnings:
        print("\nWarnings (human review, not blocking):")
        for f in warnings:
            print(f"  [{f.check}] {f.message}")
    return code


if __name__ == "__main__":
    sys.exit(main())
