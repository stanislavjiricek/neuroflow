#!/usr/bin/env python3
"""Marker-to-photodiode latency and jitter for a pilot recording (/tool-validate).

Pairs every marker with the next photodiode onset and reports the latency
distribution (p50, p95, max, jitter), markers without an onset, extra onsets, and
one-frame offsets. A photodiode on the stimulus screen is the real check of stimulus
onset timing; software frame logs are not.

Input, either:
  --xdf FILE --markers NAME --photodiode NAME [--channel 0]
        an XDF recording (needs pyxdf: pip install pyxdf; clocks are synchronised
        by pyxdf). NAME matches the stream name, else the stream type.
  --marker-csv FILE --photodiode-csv FILE [--column NAME]
        markers: columns time (s) and optionally code; photodiode: time (s) plus the
        signal column (default: the first column after time).

Onset detection: a crossing of --threshold (default: midpoint of the 5th and 95th
signal percentiles) after at least --min-off-ms below it, so backlight PWM flicker
during an "on" period does not count as a new onset. --polarity falling for a dark
patch on a bright screen. The report includes the on/off contrast relative to the
sample-to-sample noise: a weak signal means sensor placement or brightness must be
fixed before any latency number is trusted.

Record and verify: --record prints a fenced ```json timing-check``` block with the
input SHA-256 hashes, parameters and results, to paste into validation-results.md.
--verify-record FILE recomputes every such block in FILE from its recorded inputs and
fails on any mismatch, so a hand-edited number is caught.

Usage:
    python <phase-tool-validate base dir>/scripts/timing_check.py --xdf pilot.xdf
        --markers PsychoPyMarkers --photodiode EEG --channel 64 [--codes 1 2]
        [--refresh-hz 60] [--max-latency-ms 20] [--max-jitter-ms 2] [--record] [--json]
    python <phase-tool-validate base dir>/scripts/timing_check.py --verify-record
        .neuroflow/tool-validate/validation-results.md

Exit codes:
    0  pass: every marker has an onset, detection quality is good, criteria met (if given)
    1  findings: missing onsets, weak photodiode signal, criteria exceeded, record mismatch
    2  usage or runtime error (missing input, unreadable file, pyxdf not installed)

Stdlib only (pyxdf optional, imported only for --xdf). Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path

RECORD_RE = re.compile(r"```json timing-check\s*\n(.*?)\n```", re.DOTALL)


class InputError(Exception):
    pass


# ------------------------------------------------------------------ statistics


def percentile(values: list[float], q: float) -> float:
    data = sorted(values)
    if not data:
        return math.nan
    pos = (len(data) - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return data[lo] + (data[hi] - data[lo]) * (pos - lo)


def detect_onsets(times, values, threshold: float, polarity: str = "rising", min_off_s: float = 0.02) -> list[float]:
    """Threshold crossings (linearly interpolated) that follow at least min_off_s below threshold."""
    sign = 1.0 if polarity == "rising" else -1.0
    thr = sign * threshold
    onsets: list[float] = []
    prev_t = prev_v = None
    below_since = None
    for t, raw in zip(times, values):
        v = sign * raw
        if prev_v is None:
            below_since = t if v < thr else None
        elif v >= thr > prev_v:
            if below_since is not None and t - below_since >= min_off_s:
                frac = (thr - prev_v) / (v - prev_v) if v != prev_v else 0.0
                onsets.append(prev_t + frac * (t - prev_t))
            below_since = None
        elif v < thr <= prev_v:
            below_since = prev_t + ((thr - prev_v) / (v - prev_v)) * (t - prev_t) if v != prev_v else t
        prev_t, prev_v = t, v
    return onsets


def robust_sd(values: list[float]) -> float:
    """1.4826 x median absolute deviation: baseline noise, insensitive to occasional dips."""
    if len(values) < 2:
        return 0.0
    med = statistics.median(values)
    mad = statistics.median(abs(v - med) for v in values)
    return 1.4826 * mad if mad > 0 else statistics.pstdev(values)


def signal_quality(values, threshold: float) -> dict:
    """On/off contrast (median above minus median below threshold) relative to the sample-to-sample noise."""
    lo, hi = percentile(values, 5), percentile(values, 95)
    off = [v for v in values if v < threshold]
    on = [v for v in values if v >= threshold]
    contrast = statistics.median(on) - statistics.median(off) if on and off else 0.0
    diffs = [b - a for a, b in zip(values, values[1:])]
    noise = robust_sd(diffs) / math.sqrt(2.0)
    ratio = contrast / noise if noise > 0 else (math.inf if contrast > 0 else 0.0)
    return {"p5": lo, "p95": hi, "separation": hi - lo, "contrast": contrast, "noise_sd": noise,
            "snr": ratio if math.isfinite(ratio) else 1e9}


def pair(markers: list[float], onsets: list[float], lo_s: float, hi_s: float) -> tuple[list[float], int, int]:
    """Pair each marker with the first unused onset in [marker+lo, marker+hi]."""
    latencies: list[float] = []
    used = 0
    j = 0
    missing = 0
    for m in markers:
        while j < len(onsets) and onsets[j] < m + lo_s:
            j += 1
        if j < len(onsets) and onsets[j] <= m + hi_s:
            latencies.append(onsets[j] - m)
            used += 1
            j += 1
        else:
            missing += 1
    return latencies, missing, len(onsets) - used


def analyse(marker_times: list[float], pd_times, pd_values, params: dict) -> tuple[dict, list[str]]:
    if not marker_times:
        raise InputError("no markers to analyse (check --markers / --codes)")
    if len(pd_values) < 10:
        raise InputError("photodiode signal has fewer than 10 samples")
    threshold = params.get("threshold")
    if threshold is None:
        threshold = (percentile(pd_values, 5) + percentile(pd_values, 95)) / 2.0
    quality = signal_quality(pd_values, threshold)
    findings: list[str] = []
    if quality["separation"] <= 0:
        raise InputError("photodiode signal is flat: no on/off contrast")
    onsets = detect_onsets(pd_times, pd_values, threshold, params["polarity"], params["min_off_ms"] / 1000.0)
    lo_s, hi_s = params["window_ms"][0] / 1000.0, params["window_ms"][1] / 1000.0
    lat, missing, extra = pair(sorted(marker_times), onsets, lo_s, hi_s)
    ms = [v * 1000.0 for v in lat]
    results: dict = {
        "markers": len(marker_times), "onsets": len(onsets), "paired": len(ms), "missing": missing,
        "extra_onsets": extra, "threshold": round(threshold, 6),
        "signal": {k: round(v, 6) for k, v in quality.items()},
    }
    if ms:
        results["latency_ms"] = {
            "mean": round(statistics.fmean(ms), 3), "sd": round(statistics.pstdev(ms), 3),
            "min": round(min(ms), 3), "p5": round(percentile(ms, 5), 3), "p50": round(percentile(ms, 50), 3),
            "p95": round(percentile(ms, 95), 3), "max": round(max(ms), 3),
            "jitter_p95_p5": round(percentile(ms, 95) - percentile(ms, 5), 3),
        }
        if params.get("refresh_hz"):
            frame = 1000.0 / params["refresh_hz"]
            late = [v for v in ms if v > results["latency_ms"]["p50"] + 0.75 * frame]
            early = [v for v in ms if v < results["latency_ms"]["p50"] - 0.75 * frame]
            results["frame_ms"] = round(frame, 3)
            results["off_by_a_frame"] = {"late": len(late), "early": len(early)}
            if late or early:
                findings.append(f"{len(late)} late and {len(early)} early marker(s) by a frame or more "
                                "(dropped or skipped frames, or markers not sent on the flip)")
    if quality["snr"] < 5:
        findings.append(f"weak photodiode signal (on/off contrast {quality['contrast']:.4g} vs noise "
                        f"{quality['noise_sd']:.4g}): fix sensor placement or patch brightness before trusting latencies")
    if missing:
        findings.append(f"{missing} marker(s) without a photodiode onset in the window {params['window_ms']} ms")
    if not ms:
        findings.append("no marker could be paired with an onset")
    crit_lat, crit_jit = params.get("max_latency_ms"), params.get("max_jitter_ms")
    if ms and crit_lat is not None and results["latency_ms"]["p95"] > crit_lat:
        findings.append(f"p95 latency {results['latency_ms']['p95']} ms exceeds {crit_lat} ms")
    if ms and crit_jit is not None and results["latency_ms"]["jitter_p95_p5"] > crit_jit:
        findings.append(f"jitter (p95-p5) {results['latency_ms']['jitter_p95_p5']} ms exceeds {crit_jit} ms")
    results["pass"] = not findings
    return results, findings


# ------------------------------------------------------------------ inputs


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def code_matches(code, wanted: list[str] | None) -> bool:
    return not wanted or str(code).strip() in wanted


def load_csv_inputs(marker_csv: Path, pd_csv: Path, column: str | None, codes):
    for path in (marker_csv, pd_csv):
        if not path.is_file():
            raise InputError(f"file not found: {path}")
    with marker_csv.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "time" not in rows[0]:
        raise InputError(f"{marker_csv}: needs a 'time' column (seconds)")
    code_key = next((k for k in ("code", "value", "marker") if k in rows[0]), None)
    markers = [float(r["time"]) for r in rows if r["time"].strip()
               and code_matches(r.get(code_key, "") if code_key else "", codes)]
    with pd_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if "time" not in fields:
            raise InputError(f"{pd_csv}: needs a 'time' column (seconds)")
        col = column or next((f for f in fields if f != "time"), None)
        if col not in fields:
            raise InputError(f"{pd_csv}: signal column {col!r} not found")
        times, values = [], []
        for r in reader:
            if r["time"].strip() and r[col].strip():
                times.append(float(r["time"]))
                values.append(float(r[col]))
    return markers, times, values


def pick_stream(streams, key: str):
    for attr in ("name", "type"):
        for s in streams:
            if str(s["info"][attr][0]) == key:
                return s
    names = ", ".join(f"{s['info']['name'][0]} ({s['info']['type'][0]})" for s in streams)
    raise InputError(f"stream {key!r} not found; streams in the file: {names}")


def load_xdf_inputs(path: Path, marker_key: str, pd_key: str, channel: int, codes):
    if not path.is_file():
        raise InputError(f"file not found: {path}")
    try:
        import pyxdf  # optional dependency
    except ImportError as exc:
        raise InputError("reading XDF needs pyxdf: pip install pyxdf (or export CSVs and use --marker-csv)") from exc
    streams, _header = pyxdf.load_xdf(str(path))
    mk = pick_stream(streams, marker_key)
    pd = pick_stream(streams, pd_key)
    markers = []
    for ts, sample in zip(list(mk["time_stamps"]), list(mk["time_series"])):
        code = sample[0] if isinstance(sample, (list, tuple)) or hasattr(sample, "shape") else sample
        if code_matches(code, codes):
            markers.append(float(ts))
    series = pd["time_series"]
    values = [float(row[channel]) if hasattr(row, "__getitem__") else float(row) for row in series]
    return markers, [float(t) for t in pd["time_stamps"]], values


def load_inputs(inputs: dict, codes):
    if inputs["kind"] == "xdf":
        return load_xdf_inputs(Path(inputs["xdf"]), inputs["markers"], inputs["photodiode"], inputs["channel"], codes)
    return load_csv_inputs(Path(inputs["marker_csv"]), Path(inputs["photodiode_csv"]), inputs.get("column"), codes)


def input_hashes(inputs: dict) -> dict:
    keys = ["xdf"] if inputs["kind"] == "xdf" else ["marker_csv", "photodiode_csv"]
    return {inputs[k]: sha256_file(Path(inputs[k])) for k in keys}


# ------------------------------------------------------------------ record / verify


def make_record(inputs: dict, params: dict, results: dict) -> str:
    body = {"tool": "timing_check.py", "version": 1, "inputs": inputs, "sha256": input_hashes(inputs),
            "params": params, "results": results}
    return "```json timing-check\n" + json.dumps(body, indent=2, sort_keys=True) + "\n```"


def verify_records(path: Path) -> tuple[int, list[str]]:
    if not path.is_file():
        raise InputError(f"file not found: {path}")
    blocks = RECORD_RE.findall(path.read_text(encoding="utf-8"))
    if not blocks:
        raise InputError(f"{path}: no ```json timing-check``` block found")
    problems: list[str] = []
    for index, block in enumerate(blocks, start=1):
        try:
            rec = json.loads(block)
            inputs, params = rec["inputs"], rec["params"]
        except (json.JSONDecodeError, KeyError) as exc:
            problems.append(f"block {index}: unreadable record ({exc})")
            continue
        try:
            hashes = input_hashes(inputs)
        except OSError as exc:
            problems.append(f"block {index}: input missing ({exc})")
            continue
        if hashes != rec.get("sha256"):
            problems.append(f"block {index}: an input file changed since the record was made")
            continue
        markers, times, values = load_inputs(inputs, params.get("codes"))
        results, _ = analyse(markers, times, values, params)
        if json.loads(json.dumps(results)) != rec.get("results"):
            problems.append(f"block {index}: recorded numbers differ from a recomputation")
    return len(blocks), problems


# ------------------------------------------------------------------ main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Marker-to-photodiode latency and jitter (stimulus onset timing).")
    parser.add_argument("--xdf", help="XDF recording (needs pyxdf)")
    parser.add_argument("--markers", help="XDF marker stream name or type")
    parser.add_argument("--photodiode", help="XDF stream name or type that carries the photodiode channel")
    parser.add_argument("--channel", type=int, default=0, help="photodiode channel index in that stream (default 0)")
    parser.add_argument("--marker-csv", help="CSV with time (s) and optional code columns")
    parser.add_argument("--photodiode-csv", help="CSV with time (s) and the photodiode signal")
    parser.add_argument("--column", help="photodiode signal column in --photodiode-csv")
    parser.add_argument("--codes", nargs="+", help="only these marker codes (e.g. the visual-onset codes)")
    parser.add_argument("--threshold", type=float, help="onset threshold (default: midpoint of p5 and p95)")
    parser.add_argument("--polarity", choices=["rising", "falling"], default="rising")
    parser.add_argument("--min-off-ms", type=float, default=20.0, help="time below threshold before an onset counts")
    parser.add_argument("--window-ms", type=float, nargs=2, default=[-50.0, 200.0], metavar=("LO", "HI"),
                        help="search window for the onset after each marker (default -50 200)")
    parser.add_argument("--refresh-hz", type=float, help="display refresh rate, to flag one-frame offsets")
    parser.add_argument("--max-latency-ms", type=float, help="pass criterion: p95 latency at most this")
    parser.add_argument("--max-jitter-ms", type=float, help="pass criterion: p95-p5 spread at most this")
    parser.add_argument("--record", action="store_true", help="also print a block for validation-results.md")
    parser.add_argument("--verify-record", metavar="FILE", help="recompute the timing-check blocks in FILE")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    try:
        if args.verify_record:
            count, problems = verify_records(Path(args.verify_record))
            if args.json:
                print(json.dumps({"records": count, "problems": problems}, indent=2))
            else:
                print(f"{count} timing-check record(s) in {args.verify_record}")
                print("\n".join(f"MISMATCH {p}" for p in problems) if problems else "all records reproduce")
            return 1 if problems else 0
        if args.xdf:
            if not (args.markers and args.photodiode):
                raise InputError("--xdf needs --markers and --photodiode")
            inputs = {"kind": "xdf", "xdf": args.xdf, "markers": args.markers, "photodiode": args.photodiode,
                      "channel": args.channel}
        elif args.marker_csv and args.photodiode_csv:
            inputs = {"kind": "csv", "marker_csv": args.marker_csv, "photodiode_csv": args.photodiode_csv,
                      "column": args.column}
        else:
            raise InputError("give --xdf FILE (with --markers/--photodiode) or --marker-csv and --photodiode-csv")
        params = {"codes": args.codes, "threshold": args.threshold, "polarity": args.polarity,
                  "min_off_ms": args.min_off_ms, "window_ms": list(args.window_ms), "refresh_hz": args.refresh_hz,
                  "max_latency_ms": args.max_latency_ms, "max_jitter_ms": args.max_jitter_ms}
        markers, times, values = load_inputs(inputs, args.codes)
        results, findings = analyse(markers, times, values, params)
        record = make_record(inputs, params, results) if args.record else None
    except (InputError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"results": results, "findings": findings, "record": record}, indent=2))
    else:
        lat = results.get("latency_ms", {})
        print(f"markers {results['markers']}, onsets {results['onsets']}, paired {results['paired']}, "
              f"missing {results['missing']}, extra onsets {results['extra_onsets']}")
        if lat:
            print(f"latency ms: p50 {lat['p50']}  p95 {lat['p95']}  max {lat['max']}  mean {lat['mean']}  "
                  f"sd {lat['sd']}  jitter(p95-p5) {lat['jitter_p95_p5']}")
        sig = results["signal"]
        print(f"photodiode: threshold {results['threshold']}, on/off contrast {sig['contrast']}, "
              f"noise sd {sig['noise_sd']}, contrast/noise {sig['snr']:.1f}")
        for finding in findings:
            print(f"FINDING {finding}")
        print("PASS" if results["pass"] else "FAIL")
        if record:
            print(record)
    return 0 if results["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
