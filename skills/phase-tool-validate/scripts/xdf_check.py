#!/usr/bin/env python3
"""Check an XDF recording right after it was made: streams present, rates, drift, gaps, markers.

A standalone check for the acquisition PC or the analysis machine — no AI agent needs
to run during the recording. Run it after each run while the run can still be repeated.

Per stream: name, type, channels, nominal vs effective sampling rate (from the raw LSL
timestamps; drift in %), duration, gaps (intervals longer than --gap-factor sample
periods) and, for marker streams (nominal rate 0), the count per marker code.

Usage:
    python <phase-tool-validate base dir>/scripts/xdf_check.py sub-01_task-oddball_run-1.xdf
        [--expect EEG --expect PsychoPyMarkers] [--max-drift-pct 0.5] [--gap-factor 3]
        [--expect-markers 300] [--json]

Needs pyxdf (pip install pyxdf); the file is loaded with clock synchronisation on and
timestamp de-jittering off, so gaps in the raw timestamps stay visible.

Exit codes:
    0  every expected stream is present and has data; no gaps; drift within limits
    1  findings: missing or empty stream, gaps, drift above --max-drift-pct, marker count off
    2  usage or runtime error (file missing, not XDF, pyxdf not installed)

Stdlib only apart from pyxdf. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class InputError(Exception):
    pass


def _first(info: dict, key: str, default=""):
    value = info.get(key, [default])
    return value[0] if isinstance(value, list) and value else value


def stream_report(stream: dict, gap_factor: float) -> dict:
    info = stream.get("info", {})
    name = str(_first(info, "name"))
    stype = str(_first(info, "type"))
    try:
        nominal = float(_first(info, "nominal_srate", 0) or 0)
    except (TypeError, ValueError):
        nominal = 0.0
    try:
        channels = int(_first(info, "channel_count", 0) or 0)
    except (TypeError, ValueError):
        channels = 0
    stamps = [float(t) for t in list(stream.get("time_stamps", []))]
    report: dict = {"name": name, "type": stype, "channels": channels, "nominal_srate": nominal,
                    "samples": len(stamps)}
    if len(stamps) >= 2:
        duration = stamps[-1] - stamps[0]
        report["duration_s"] = round(duration, 3)
        if nominal > 0 and duration > 0:
            effective = (len(stamps) - 1) / duration
            report["effective_srate"] = round(effective, 4)
            report["drift_pct"] = round(100.0 * (effective - nominal) / nominal, 4)
            limit = gap_factor / nominal
            gaps = [b - a for a, b in zip(stamps, stamps[1:]) if b - a > limit]
            report["gaps"] = len(gaps)
            report["largest_gap_s"] = round(max(gaps), 4) if gaps else 0.0
            report["backwards_steps"] = sum(1 for a, b in zip(stamps, stamps[1:]) if b < a)
    if nominal == 0:
        counts: dict[str, int] = {}
        for sample in list(stream.get("time_series", [])):
            code = sample[0] if isinstance(sample, (list, tuple)) or hasattr(sample, "shape") else sample
            counts[str(code)] = counts.get(str(code), 0) + 1
        report["marker_counts"] = dict(sorted(counts.items()))
    return report


def check(streams: list[dict], args) -> tuple[list[dict], list[str]]:
    reports = [stream_report(s, args.gap_factor) for s in streams]
    findings: list[str] = []
    for want in args.expect or []:
        if not any(r["name"] == want or r["type"] == want for r in reports):
            findings.append(f"expected stream {want!r} is missing")
    for r in reports:
        label = f"{r['name']} ({r['type']})"
        if r["samples"] == 0:
            findings.append(f"{label}: no samples")
            continue
        if r.get("gaps"):
            findings.append(f"{label}: {r['gaps']} gap(s), largest {r['largest_gap_s']} s")
        if r.get("backwards_steps"):
            findings.append(f"{label}: {r['backwards_steps']} timestamp(s) go backwards")
        if "drift_pct" in r and abs(r["drift_pct"]) > args.max_drift_pct:
            findings.append(f"{label}: effective rate {r['effective_srate']} Hz differs from nominal "
                            f"{r['nominal_srate']:g} Hz by {r['drift_pct']}%")
    if args.expect_markers is not None:
        marker_streams = [r for r in reports if r["nominal_srate"] == 0]
        total = sum(r["samples"] for r in marker_streams)
        if total != args.expect_markers:
            findings.append(f"{total} marker(s) recorded, {args.expect_markers} expected")
    return reports, findings


def load(path: Path) -> list[dict]:
    if not path.is_file():
        raise InputError(f"file not found: {path}")
    try:
        import pyxdf  # optional dependency
    except ImportError as exc:
        raise InputError("xdf_check needs pyxdf: pip install pyxdf") from exc
    try:
        streams, _header = pyxdf.load_xdf(str(path), synchronize_clocks=True, dejitter_timestamps=False)
    except Exception as exc:  # pyxdf raises plain Exceptions on corrupt files
        raise InputError(f"cannot read {path} as XDF: {exc}") from exc
    return streams


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the streams of an XDF recording (presence, rate, gaps, markers).")
    parser.add_argument("xdf", help="the .xdf file")
    parser.add_argument("--expect", action="append", help="stream name or type that must be present (repeatable)")
    parser.add_argument("--max-drift-pct", type=float, default=0.5, help="allowed effective-vs-nominal rate difference")
    parser.add_argument("--gap-factor", type=float, default=3.0, help="a gap is an interval > this many sample periods")
    parser.add_argument("--expect-markers", type=int, help="total number of markers the run should contain")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    try:
        streams = load(Path(args.xdf))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    reports, findings = check(streams, args)
    if args.json:
        print(json.dumps({"file": args.xdf, "streams": reports, "findings": findings}, indent=2))
    else:
        print(f"{args.xdf}: {len(reports)} stream(s)")
        for r in reports:
            rate = (f"{r['nominal_srate']:g} Hz nominal, {r.get('effective_srate', 'n/a')} effective "
                    f"({r.get('drift_pct', 'n/a')}%)" if r["nominal_srate"] else "irregular (markers)")
            print(f"  {r['name']} [{r['type']}] {r['channels']} ch, {r['samples']} samples, "
                  f"{r.get('duration_s', 0)} s, {rate}, gaps {r.get('gaps', 0)}")
            if "marker_counts" in r:
                print("    codes: " + ", ".join(f"{k}: {v}" for k, v in r["marker_counts"].items()))
        for finding in findings:
            print(f"FINDING {finding}")
        print("OK" if not findings else f"{len(findings)} finding(s) - consider repeating the run")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
