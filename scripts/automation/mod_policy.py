#!/usr/bin/env python3
"""mod_policy.py: hold the neuroflow mod to what a reviewer allowed (charter: feature budget).

`claude plugin validate --json` reports, for the hooks module, every engine call it makes, the
environment variables it reads and writes, and the state it writes; the events it hooks are read from
the module's source (the validator shortens that list). This script compares the inventory with
hooks/mod/policy.json:

- anything the module does that the policy does not list fails, until a reviewer adds it;
- anything the policy lists that the module no longer does is reported, so the policy shrinks too;
- a gating hook without a `.catch` always fails (a guard must fail closed, an observer must pass through).

Usage:
    python scripts/automation/mod_policy.py                  # run the validator, compare
    python scripts/automation/mod_policy.py --report r.json  # compare a saved `claude plugin validate --json`
    python scripts/automation/mod_policy.py --write          # rewrite policy.json from the current inventory
                                                              # (after review, in the same commit as the change)

Exit codes: 0 = the module stays within the policy (or the claude CLI is not installed: skipped);
1 = something new, or a gating hook without .catch; 2 = the report could not be read.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "hooks" / "mod" / "policy.json"
SOURCE = ROOT / "hooks" / "mod"
MODULE = "./mod/neuroflow.ts"

# note prefix after "<module> " -> policy key
FIELDS = {
    "calls": "calls",
    "env reads": "envReads",
    "env writes": "envWrites",
    "state writes": "stateWrites",
}


def split_items(text: str) -> list[str]:
    """Split a comma-separated inventory, keeping commas inside {...}, (...) and /.../ intact."""
    items, depth, current, in_regex = [], 0, [], False
    for ch in text:
        if ch == "/" and (not current or current[-1] in "=\"") and depth > 0:
            in_regex = not in_regex
        if not in_regex:
            if ch in "{(":
                depth += 1
            elif ch in "})":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(current).strip())
                current = []
                continue
        current.append(ch)
    if "".join(current).strip():
        items.append("".join(current).strip())
    return [item for item in items if item and item != "nothing"]


def strip_via(call: str) -> str:
    """`$.fs.read (via ioOf, decide)` -> `$.fs.read`: which helper makes a call may change freely."""
    return call.split(" (via ", 1)[0].strip()


def inventory(report: dict, module: str = MODULE) -> dict:
    """The module's inventory from a validate --json report."""
    found: dict[str, list[str]] = {key: [] for key in FIELDS.values()}
    found["gatingWithoutCatch"] = []
    for content in report.get("contents", []):
        for note in content.get("notes", []):
            if not isinstance(note, str) or not note.startswith(module + " "):
                continue
            rest = note[len(module) + 1:]
            for prefix, key in FIELDS.items():
                if rest.startswith(prefix + ": "):
                    values = split_items(rest[len(prefix) + 2:])
                    if key == "calls":
                        values = [strip_via(value) for value in values]
                    found[key].extend(values)
        for gate in content.get("gatingHooks", []):
            if gate.get("module") == module and not gate.get("hasCatch", False):
                found["gatingWithoutCatch"].append(gate.get("hook", "?"))
    return {key: sorted(set(values)) for key, values in found.items()}


def truncated(report: dict, module: str = MODULE) -> bool:
    """The validator shortens long notes ('… [+N chars]'): an inventory it shortened cannot be compared."""
    prefixes = tuple(f"{module} {prefix}: " for prefix in FIELDS)
    for content in report.get("contents", []):
        for note in content.get("notes", []):
            if isinstance(note, str) and note.startswith(prefixes) and "… [+" in note:
                return True
    return False


EVENT = re.compile(r"""\bon\(\s*['"]([a-z][\w.]*)['"]""")


def source_events(source: Path = SOURCE) -> list[str]:
    """The events the module hooks: every on('event', ...) in hooks/mod outside the tests."""
    events = set()
    for path in sorted(source.rglob("*.ts*")):
        if "tests" in path.relative_to(source).parts or path.name.endswith((".test.ts", ".test.tsx")):
            continue
        events.update(EVENT.findall(path.read_text(encoding="utf-8")))
    return sorted(events)


def compare(current: dict, policy: dict) -> tuple[list[str], list[str]]:
    """(failures, notes): what is new against the policy, and what the policy lists that is gone."""
    failures, notes = [], []
    for key in ["events", *FIELDS.values()]:
        allowed = set(policy.get(key, []))
        now = set(current.get(key, []))
        for item in sorted(now - allowed):
            failures.append(f"{key}: not in hooks/mod/policy.json: {item}")
        for item in sorted(allowed - now):
            notes.append(f"{key}: listed in the policy but no longer used: {item}")
    for hook in current.get("gatingWithoutCatch", []):
        failures.append(f"gating hook without .catch: {hook}")
    return failures, notes


def run_validator() -> dict | None:
    claude = shutil.which("claude")
    if claude is None:
        return None
    proc = subprocess.run([claude, "plugin", "validate", str(ROOT), "--json"], capture_output=True, text=True, encoding="utf-8")
    return json.loads(proc.stdout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare the neuroflow mod's inventory with hooks/mod/policy.json.")
    ap.add_argument("--report", type=Path, help="a saved `claude plugin validate --json` report")
    ap.add_argument("--write", action="store_true", help="rewrite policy.json from the current inventory")
    ap.add_argument("--policy", type=Path, default=POLICY, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    try:
        report = json.loads(args.report.read_text(encoding="utf-8")) if args.report else run_validator()
    except (OSError, ValueError) as exc:
        print(f"mod_policy: cannot read the validator report: {exc}", file=sys.stderr)
        return 2
    if report is None:
        print("mod_policy: skipped - the claude CLI is not installed here")
        return 0
    if truncated(report):
        print("mod_policy: the validator shortened the module's inventory; run it with a newer CLI", file=sys.stderr)
        return 2
    current = inventory(report)
    current["events"] = source_events()
    if not any(current[key] for key in FIELDS.values()):
        print(f"mod_policy: the report has no inventory for {MODULE}", file=sys.stderr)
        return 2

    if args.write:
        policy = {"_comment": "What the neuroflow mod may do. CI compares `claude plugin validate --json` with this file "
                              "(scripts/automation/mod_policy.py); change it only with a reviewed change to the mod."}
        policy.update({key: current[key] for key in ["events", *FIELDS.values()]})
        args.policy.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"mod_policy: wrote {args.policy.relative_to(ROOT) if args.policy.is_relative_to(ROOT) else args.policy}")
        return 0

    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"mod_policy: cannot read {args.policy}: {exc}", file=sys.stderr)
        return 2
    failures, notes = compare(current, policy)
    for line in failures:
        print(f"FAIL {line}")
    for line in notes:
        print(f"note {line}")
    if not failures:
        counts = ", ".join(f"{len(current[key])} {key}" for key in ["events", *FIELDS.values()])
        print(f"mod_policy: OK - within the policy ({counts})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
