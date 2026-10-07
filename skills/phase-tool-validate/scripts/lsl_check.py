#!/usr/bin/env python3
"""LSL stream health snapshot and latency check (/tool-validate, /tool-build, /experiment).

Without --stream it only lists the streams it can resolve on the network (name, type,
source_id, host, channels, nominal rate) and opens no inlet. With --stream NAME
(repeatable; only the named streams are opened, so a busy shared subnet is not
drained) it reads each stream for --duration seconds and reports:

  - effective vs nominal sampling rate, gaps, timestamps that go backwards
  - the clock offset to the sender (time_correction) at start and end
  - latency: local_clock() at receipt minus (sample timestamp + clock offset), for
    the newest sample of each chunk -> p50 / p95 / max (ms)

What the latency means: the time from the sample's LSL timestamp to its arrival here.
If the sender stamps samples when it acquires them, this is transport plus buffering
delay. A closed-loop tool that pushes its output with the timestamp of the input
sample it was computed from (outlet.push_sample(x, timestamp=source_ts)) makes this
the end-to-end processing latency of the tool. It is never stimulus-to-photon latency:
use a photodiode (timing_check.py) for that.

Usage:
    python <phase-tool-validate base dir>/scripts/lsl_check.py [--resolve-timeout 3]
    python <phase-tool-validate base dir>/scripts/lsl_check.py --stream EEG --stream Feedback
        [--duration 10] [--budget-ms 50] [--gap-factor 3] [--log latencies.csv] [--json]

Needs pylsl (pip install pylsl). When nothing resolves, multicast discovery is often
blocked: check the firewall (LSL uses UDP 16571 for discovery and ports 16572-16603
for data), VPNs, and Wi-Fi client isolation.

Exit codes:
    0  streams found (and, with --stream, each named stream delivered data within budget)
    1  findings: no streams resolved, a named stream missing or silent, gaps, rate off by
       more than 1%, p95 latency above --budget-ms
    2  usage or runtime error (pylsl not installed, bad arguments)

Stdlib only apart from pylsl. Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path


class InputError(Exception):
    pass


def percentile(values: list[float], q: float) -> float:
    data = sorted(values)
    if not data:
        return math.nan
    pos = (len(data) - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return data[lo] + (data[hi] - data[lo]) * (pos - lo)


def import_pylsl():
    try:
        import pylsl  # optional dependency
    except ImportError as exc:
        raise InputError("lsl_check needs pylsl: pip install pylsl") from exc
    return pylsl


def describe(info) -> dict:
    return {"name": info.name(), "type": info.type(), "source_id": info.source_id(), "host": info.hostname(),
            "channels": info.channel_count(), "nominal_srate": info.nominal_srate()}


def summarise(name: str, nominal: float, stamps: list[float], latencies: list[float], offsets: list[float],
              gap_factor: float, budget_ms: float | None) -> tuple[dict, list[str]]:
    findings: list[str] = []
    report: dict = {"name": name, "samples": len(stamps), "nominal_srate": nominal,
                    "clock_offset_s": [round(o, 6) for o in offsets]}
    if not stamps:
        findings.append(f"{name}: no samples received")
        return report, findings
    if len(stamps) >= 2 and stamps[-1] > stamps[0]:
        report["effective_srate"] = round((len(stamps) - 1) / (stamps[-1] - stamps[0]), 3)
    if nominal > 0:
        gaps = [b - a for a, b in zip(stamps, stamps[1:]) if b - a > gap_factor / nominal]
        report["gaps"] = len(gaps)
        if gaps:
            findings.append(f"{name}: {len(gaps)} gap(s), largest {max(gaps) * 1000:.1f} ms")
        eff = report.get("effective_srate")
        if eff and abs(eff - nominal) / nominal > 0.01:
            findings.append(f"{name}: effective rate {eff} Hz vs nominal {nominal:g} Hz")
    backwards = sum(1 for a, b in zip(stamps, stamps[1:]) if b < a)
    if backwards:
        findings.append(f"{name}: {backwards} timestamp(s) go backwards")
    if latencies:
        ms = [v * 1000.0 for v in latencies]
        report["latency_ms"] = {"p50": round(percentile(ms, 50), 3), "p95": round(percentile(ms, 95), 3),
                                "max": round(max(ms), 3), "chunks": len(ms)}
        if budget_ms is not None and report["latency_ms"]["p95"] > budget_ms:
            findings.append(f"{name}: p95 latency {report['latency_ms']['p95']} ms exceeds the {budget_ms:g} ms budget")
    return report, findings


def measure(pylsl, info, duration: float, log_rows: list | None) -> tuple[list[float], list[float], list[float]]:
    inlet = pylsl.StreamInlet(info, max_buflen=max(1, int(math.ceil(duration)) + 1))
    offsets = [inlet.time_correction(timeout=2.0)]
    stamps: list[float] = []
    latencies: list[float] = []
    end = pylsl.local_clock() + duration
    while pylsl.local_clock() < end:
        _samples, ts = inlet.pull_chunk(timeout=0.2)
        if not ts:
            continue
        now = pylsl.local_clock()
        stamps.extend(float(t) for t in ts)
        latency = now - (float(ts[-1]) + offsets[0])
        latencies.append(latency)
        if log_rows is not None:
            log_rows.append({"stream": info.name(), "received_at": round(now, 6), "newest_timestamp": float(ts[-1]),
                             "samples": len(ts), "latency_ms": round(latency * 1000.0, 3)})
    offsets.append(inlet.time_correction(timeout=2.0))
    try:
        inlet.close_stream()
    except Exception:  # pragma: no cover - best effort
        pass
    return stamps, latencies, offsets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List LSL streams; with --stream, measure rate, gaps and latency.")
    parser.add_argument("--stream", action="append", help="stream name to open and measure (repeatable)")
    parser.add_argument("--resolve-timeout", type=float, default=3.0, help="seconds to wait for stream discovery")
    parser.add_argument("--duration", type=float, default=10.0, help="seconds to read each named stream")
    parser.add_argument("--budget-ms", type=float, help="latency budget: p95 above it is a finding")
    parser.add_argument("--gap-factor", type=float, default=3.0, help="a gap is an interval > this many periods")
    parser.add_argument("--log", help="write per-chunk latencies to this CSV")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    if args.duration <= 0 or args.resolve_timeout <= 0:
        print("error: --duration and --resolve-timeout must be positive", file=sys.stderr)
        return 2
    try:
        pylsl = import_pylsl()
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    infos = list(pylsl.resolve_streams(wait_time=args.resolve_timeout))
    listed = [describe(i) for i in infos]
    findings: list[str] = []
    measured: list[dict] = []
    log_rows: list[dict] | None = [] if args.log else None
    if not infos:
        findings.append("no LSL streams resolved: multicast discovery may be blocked (firewall: UDP 16571, "
                        "ports 16572-16603; VPN; Wi-Fi client isolation), or no sender is running")
    for wanted in args.stream or []:
        matches = [i for i in infos if i.name() == wanted]
        if not matches:
            findings.append(f"stream {wanted!r} not found")
            continue
        if len(matches) > 1:
            hosts = ", ".join(sorted({m.hostname() for m in matches}))
            findings.append(f"{len(matches)} streams named {wanted!r} (hosts: {hosts}); measuring the first")
        info = matches[0]
        stamps, latencies, offsets = measure(pylsl, info, args.duration, log_rows)
        report, more = summarise(wanted, info.nominal_srate(), stamps, latencies, offsets, args.gap_factor,
                                 args.budget_ms)
        measured.append(report)
        findings += more
    if args.log and log_rows is not None:
        with Path(args.log).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["stream", "received_at", "newest_timestamp", "samples",
                                                        "latency_ms"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(log_rows)
    if args.json:
        print(json.dumps({"streams": listed, "measured": measured, "findings": findings}, indent=2))
    else:
        print(f"{len(listed)} stream(s) resolved at {time.strftime('%H:%M:%S')}")
        for s in listed:
            print(f"  {s['name']} [{s['type']}] {s['channels']} ch @ {s['nominal_srate']:g} Hz  "
                  f"host {s['host']}  source_id {s['source_id']}")
        for m in measured:
            lat = m.get("latency_ms", {})
            print(f"  measured {m['name']}: {m['samples']} samples, effective {m.get('effective_srate', 'n/a')} Hz, "
                  f"gaps {m.get('gaps', 0)}, latency p50 {lat.get('p50', 'n/a')} / p95 {lat.get('p95', 'n/a')} / "
                  f"max {lat.get('max', 'n/a')} ms, clock offset {m['clock_offset_s']}")
        for finding in findings:
            print(f"FINDING {finding}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
