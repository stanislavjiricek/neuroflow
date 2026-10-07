#!/usr/bin/env python3
"""Turn bids-validator JSON output into a compact digest (counts per issue code, first locations).

Reads the JSON of the schema validator (`bids-validator --json`, the Deno/JSR build or
the bids-validator-deno PyPI binary: {"issues": {"issues": [...], "codeMessages": {...}},
"summary": {...}}) and of the legacy 1.x validator ({"issues": {"errors": [...],
"warnings": [...]}, "summary": {...}}). The digest keeps every issue code with its
count - nothing is summarised away - plus the first --locations paths per code and the
dataset summary (subjects, sessions, tasks, modalities, files). Participant metadata in
the summary (age, sex) is never printed. Keep the full JSON file: the digest names it.

Usage:
    bids-validator /path/to/bids --json > bids-validator.json   (command depends on the build)
    python <bids base dir>/scripts/bids_digest.py bids-validator.json [--locations 5] [--strict] [--json]
    ... | python <bids base dir>/scripts/bids_digest.py -

Exit codes:
    0  no errors (warnings may be listed)
    1  errors found (with --strict: errors or warnings)
    2  usage or runtime error (unreadable file, not validator JSON)

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SUMMARY_KEYS = ["subjects", "sessions", "tasks", "modalities", "dataTypes", "totalFiles", "size", "schemaVersion"]


class InputError(Exception):
    pass


def _group(issues: list[dict], severity: str, messages: dict, limit: int) -> list[dict]:
    groups: dict[str, dict] = {}
    for issue in issues:
        code = str(issue.get("code") or issue.get("key") or "UNKNOWN")
        entry = groups.setdefault(code, {"code": code, "severity": severity, "count": 0, "locations": [],
                                         "message": messages.get(code, "")})
        entry["count"] += 1
        location = issue.get("location")
        if location and len(entry["locations"]) < limit and location not in entry["locations"]:
            entry["locations"].append(location)
    return sorted(groups.values(), key=lambda g: (-g["count"], g["code"]))


def digest_schema(data: dict, limit: int) -> dict:
    issues = data["issues"].get("issues", [])
    messages = data["issues"].get("codeMessages", {}) or {}
    by_sev: dict[str, list[dict]] = {"error": [], "warning": []}
    for issue in issues:
        sev = issue.get("severity") or "error"
        if sev in by_sev:
            by_sev[sev].append(issue)
    return {"format": "schema", "errors": _group(by_sev["error"], "error", messages, limit),
            "warnings": _group(by_sev["warning"], "warning", messages, limit)}


def digest_legacy(data: dict, limit: int) -> dict:
    out: dict = {"format": "legacy"}
    for key, sev in (("errors", "error"), ("warnings", "warning")):
        expanded: list[dict] = []
        messages: dict[str, str] = {}
        for issue in data["issues"].get(key, []) or []:
            code = str(issue.get("key") or issue.get("code") or "UNKNOWN")
            messages.setdefault(code, issue.get("reason", ""))
            files = issue.get("files") or []
            if not files:
                expanded.append({"code": code})
            for item in files:
                file_info = (item or {}).get("file") or {}
                expanded.append({"code": code, "location": file_info.get("relativePath") or file_info.get("path")})
            extra = int(issue.get("additionalFileCount") or 0)
            expanded += [{"code": code}] * extra
        out[key] = _group(expanded, sev, messages, limit)
    return out


def digest(data: dict, limit: int) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("issues"), dict):
        raise InputError("not bids-validator JSON: no 'issues' object")
    issues = data["issues"]
    if "issues" in issues:
        result = digest_schema(data, limit)
    elif "errors" in issues or "warnings" in issues:
        result = digest_legacy(data, limit)
    else:
        raise InputError("unknown bids-validator JSON layout")
    summary = data.get("summary") or {}
    result["summary"] = {k: summary[k] for k in SUMMARY_KEYS if k in summary}
    for key in ("subjects", "sessions", "tasks"):
        if isinstance(result["summary"].get(key), list):
            result["summary"][f"n_{key}"] = len(result["summary"][key])
    result["error_count"] = sum(g["count"] for g in result["errors"])
    result["warning_count"] = sum(g["count"] for g in result["warnings"])
    derivatives = data.get("derivativesSummary") or {}
    if derivatives:
        result["derivatives"] = {name: {"errors": sum(1 for i in (d.get("issues", {}).get("issues") or [])
                                                       if (i.get("severity") or "error") == "error")}
                                 for name, d in derivatives.items()}
    return result


def render(result: dict, source: str) -> list[str]:
    s = result["summary"]
    lines = [f"bids-validator digest ({result['format']} format) - full output: {source}",
             f"{result['error_count']} error(s), {result['warning_count']} warning(s)"]
    if s:
        lines.append(f"dataset: {s.get('n_subjects', '?')} subject(s), {s.get('n_sessions', 0)} session(s), "
                     f"tasks {', '.join(map(str, s.get('tasks', []))) or '-'}, "
                     f"modalities {', '.join(map(str, s.get('modalities', []))) or '-'}, "
                     f"{s.get('totalFiles', '?')} file(s)")
    for title, groups in (("ERRORS", result["errors"]), ("WARNINGS", result["warnings"])):
        if not groups:
            continue
        lines.append(f"{title}:")
        for g in groups:
            lines.append(f"  {g['code']} x{g['count']}" + (f" - {g['message']}" if g["message"] else ""))
            for loc in g["locations"]:
                lines.append(f"      {loc}")
            if g["count"] > len(g["locations"]) and g["locations"]:
                lines.append(f"      ... {g['count'] - len(g['locations'])} more")
    for name, d in (result.get("derivatives") or {}).items():
        lines.append(f"derivative {name}: {d['errors']} error(s)")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compact digest of bids-validator --json output.")
    parser.add_argument("input", help="validator JSON file, or - for stdin")
    parser.add_argument("--locations", type=int, default=5, help="locations listed per issue code (default 5)")
    parser.add_argument("--strict", action="store_true", help="warnings also count as findings (exit 1)")
    parser.add_argument("--json", action="store_true", help="print the digest as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    try:
        if args.input == "-":
            text, source = sys.stdin.read(), "<stdin>"
        else:
            path = Path(args.input)
            if not path.is_file():
                raise InputError(f"file not found: {path}")
            text, source = path.read_text(encoding="utf-8-sig"), path.as_posix()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InputError(f"not JSON ({exc}); run the validator with --json") from exc
        result = digest(data, max(0, args.locations))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result["source"] = source
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n".join(render(result, source)))
    if result["error_count"] or (args.strict and result["warning_count"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
