#!/usr/bin/env python3
"""smoke_test.py - run a model's smoke test, check its metrics in code, keep a smoke record tied to the model code.

Part of the neuroflow `phase-brain-build` skill (also used by /brain-run and /brain-optimize).

  run     runs a short simulation command, checks the metrics it reports, and writes a smoke record
          holding a hash of the model code - the record goes stale as soon as the code changes
  status  is there a passing smoke record for the model code as it is now?
  check   the same checks on any metrics file, e.g. the output of a full run

Metrics contract - a JSON object the command writes to --metrics FILE, or prints as the last line of
its stdout:
  {"duration_ms": 500,
   "populations": {"E": {"n": 80, "n_spikes": 412, "rate_hz": 10.3},
                   "I": {"n": 20, "n_spikes": 240, "rate_hz": 24.0}}}
Checks: the command exits 0; metrics exist; no NaN or infinity anywhere; no value under a key named
"rate_hz" (or ending in "_rate_hz") above --max-rate (runaway); not all of them 0 (silent network) -
when there are no rate keys, "n_spikes"/"spike_count" values must not all be 0. Any key ending in
"_ok" whose value is false fails (own checks, e.g. "bounded_ok" for a mean-field model, which has no
spikes and gets only the NaN check otherwise).

Examples:
  python smoke_test.py run --record .neuroflow/brain-build/smoke-record.json --model-dir models \
      --metrics models/smoke/metrics.json -- python models/run_sim.py --duration 500 --out models/smoke
  python smoke_test.py status --record .neuroflow/brain-build/smoke-record.json
  python smoke_test.py check models/results/run-01/metrics.json --max-rate 200

Exit codes: 0 = passed / record fresh and passing; 1 = a check failed, or the record is stale,
failing or missing; 2 = usage error, unreadable metrics, or the command could not start.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RECORD_VERSION = 1
DEFAULT_MAX_RATE = 300.0
EXCLUDE_DIRS = {"results", "optimize", "__pycache__", ".ipynb_checkpoints", ".git", "x86_64", "arm64",
                "aarch64", "i686", "output", "outputs", "smoke"}
EXCLUDE_GLOBS = ["*.pyc", "*.o", "*.so", "*.dll", "*.dylib", "*.log"]


class SmokeError(Exception):
    """Usage or runtime problem (exit 2)."""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ model hash

def excluded(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    if any(p in EXCLUDE_DIRS for p in parts[:-1]):
        return True
    name = parts[-1]
    if any(fnmatch.fnmatch(name, g) for g in EXCLUDE_GLOBS):
        return True
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p) or rel.startswith(p.rstrip("/") + "/")
               for p in patterns)


def model_hash(model_dir: Path, patterns: list[str]) -> tuple[str, int]:
    if not model_dir.is_dir():
        raise SmokeError(f"model folder {model_dir} not found")
    h = hashlib.sha256()
    count = 0
    for f in sorted(p for p in model_dir.rglob("*") if p.is_file()):
        rel = f.relative_to(model_dir).as_posix()
        if excluded(rel, patterns):
            continue
        fh = hashlib.sha256(f.read_bytes()).hexdigest()
        h.update(f"{rel}\0{fh}\n".encode("utf-8"))
        count += 1
    return h.hexdigest(), count


# ------------------------------------------------------------------ checks

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def last_key(path: str) -> str:
    return path.split(".")[-1].split("[")[0]


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def run_checks(metrics: dict, max_rate: float, allow_silence: bool) -> list[dict]:
    checks = []
    leaves = list(walk(metrics))
    bad = [p for p, v in leaves if (is_num(v) and not math.isfinite(v)) or (isinstance(v, str) and v.lower() in {"nan", "inf", "-inf"})]
    checks.append({"check": "no NaN or infinity", "ok": not bad, "detail": ", ".join(bad[:5])})
    flags = [p for p, v in leaves if last_key(p).endswith("_ok") and v is False]
    if any(last_key(p).endswith("_ok") for p, _ in leaves):
        checks.append({"check": "own *_ok checks", "ok": not flags, "detail": ", ".join(flags[:5])})
    rates = [(p, float(v)) for p, v in leaves
             if (last_key(p) == "rate_hz" or last_key(p).endswith("_rate_hz")) and is_num(v) and math.isfinite(v)]
    if rates:
        high = [f"{p}={v:g}" for p, v in rates if v > max_rate]
        checks.append({"check": f"no runaway rate (> {max_rate:g} Hz)", "ok": not high, "detail": ", ".join(high[:5])})
        if not allow_silence:
            silent = all(v == 0 for _, v in rates)
            checks.append({"check": "not silent (some rate > 0)", "ok": not silent,
                           "detail": "every rate is 0" if silent else ""})
    else:
        spikes = [(p, v) for p, v in leaves if last_key(p) in {"n_spikes", "spike_count"} and is_num(v)]
        if spikes and not allow_silence:
            silent = all(v == 0 for _, v in spikes)
            checks.append({"check": "not silent (some spikes)", "ok": not silent,
                           "detail": "no spikes at all" if silent else ""})
    return checks


def load_metrics_file(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SmokeError(f"cannot read metrics {path}: {e}")
    if not isinstance(data, dict):
        raise SmokeError(f"{path}: metrics must be a JSON object")
    return data


def metrics_from_stdout(stdout: str) -> dict | None:
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
    return None


def print_checks(title: str, checks: list[dict], passed: bool) -> None:
    print(title)
    for c in checks:
        print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['check']}" + (f" - {c['detail']}" if c.get("detail") else ""))
    print("PASSED" if passed else "FAILED")


# ------------------------------------------------------------------ subcommands

def cmd_run(args) -> int:
    cmd = list(args.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise SmokeError("give the smoke command after --")
    model_dir = Path(args.model_dir)
    if not model_dir.is_dir():
        raise SmokeError(f"model folder {model_dir} not found (set --model-dir)")
    record_path = Path(args.record)
    patterns = list(args.exclude or [])
    for extra in (args.metrics, args.record):
        if extra:
            try:
                patterns.append(Path(extra).resolve().relative_to(model_dir.resolve()).as_posix())
            except ValueError:
                pass
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout, check=False)
        code, stdout, stderr = proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        code, stdout, stderr = "timeout", "", f"stopped after {args.timeout} s"
    except OSError as e:
        raise SmokeError(f"cannot start {cmd[0]}: {e}")
    duration = round(time.time() - t0, 2)
    checks = [{"check": "command exits 0", "ok": code == 0,
               "detail": "" if code == 0 else f"exit {code}; {stderr.strip()[-300:]}"}]
    metrics = None
    if args.metrics:
        mp = Path(args.metrics)
        if mp.is_file():
            try:
                metrics = load_metrics_file(mp)
            except SmokeError as e:
                checks.append({"check": "metrics readable", "ok": False, "detail": str(e)})
    else:
        metrics = metrics_from_stdout(stdout)
    if metrics is None:
        if not any(c["check"] == "metrics readable" for c in checks):
            checks.append({"check": "metrics reported", "ok": False,
                           "detail": f"no metrics in {args.metrics}" if args.metrics else "no JSON line on stdout"})
    else:
        checks.extend(run_checks(metrics, args.max_rate, args.allow_silence))
    passed = all(c["ok"] for c in checks)
    sha, n_files = model_hash(model_dir, patterns)
    record = {
        "nf_smoke": RECORD_VERSION, "at": now_utc(), "passed": passed, "command": cmd, "exit_code": code,
        "duration_s": duration, "model_dir": model_dir.as_posix(), "exclude": patterns,
        "model_sha256": sha, "model_files": n_files, "max_rate_hz": args.max_rate,
        "allow_silence": args.allow_silence, "metrics": metrics, "checks": checks,
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(record, indent=2, default=str))
    else:
        print_checks(f"Smoke test ({duration} s, model {sha[:12]} over {n_files} file(s)):", checks, passed)
        print(f"Smoke record: {record_path.as_posix()}")
    return 0 if passed else 1


def cmd_status(args) -> int:
    record_path = Path(args.record)
    if not record_path.is_file():
        state = {"state": "missing", "detail": f"no smoke record at {record_path.as_posix()} - run the smoke test first"}
    else:
        try:
            rec = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise SmokeError(f"cannot read {record_path}: {e}")
        sha, _ = model_hash(Path(args.model_dir or rec.get("model_dir", "models")), rec.get("exclude") or [])
        if not rec.get("passed"):
            state = {"state": "failing", "detail": f"the last smoke test ({rec.get('at')}) failed"}
        elif sha != rec.get("model_sha256"):
            state = {"state": "stale", "detail": f"the model code changed since the smoke test of {rec.get('at')} - rerun it"}
        else:
            state = {"state": "fresh", "detail": f"passing smoke test of {rec.get('at')} matches the current model code"}
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(f"{state['state'].upper()}: {state['detail']}")
    return 0 if state["state"] == "fresh" else 1


def cmd_check(args) -> int:
    metrics = load_metrics_file(Path(args.metrics))
    checks = run_checks(metrics, args.max_rate, args.allow_silence)
    passed = all(c["ok"] for c in checks)
    if args.json:
        print(json.dumps({"passed": passed, "checks": checks}, indent=2))
    else:
        print_checks(f"Checks on {args.metrics}:", checks, passed)
    return 0 if passed else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="smoke_test.py",
                                description="Smoke test for computational models, with a record tied to the model code (neuroflow).",
                                epilog="Exit codes: 0 = passed / fresh; 1 = failed, stale or missing; 2 = usage or runtime error.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the smoke command, check it, write the smoke record")
    r.add_argument("--record", required=True, help="smoke record to write, e.g. .neuroflow/brain-build/smoke-record.json")
    r.add_argument("--model-dir", default="models", help="model code folder to hash (default models)")
    r.add_argument("--exclude", action="append", help="extra path or glob under the model folder to leave out of the hash")
    r.add_argument("--metrics", help="metrics JSON the command writes (default: last JSON line of its stdout)")
    r.add_argument("--timeout", type=float, default=600, help="seconds (default 600)")
    r.add_argument("--max-rate", type=float, default=DEFAULT_MAX_RATE, help=f"runaway threshold in Hz (default {DEFAULT_MAX_RATE:g})")
    r.add_argument("--allow-silence", action="store_true", help="silence is expected (e.g. no input in this test)")
    r.add_argument("--json", action="store_true")
    r.add_argument("command", nargs=argparse.REMAINDER, help="-- smoke command")
    s = sub.add_parser("status", help="is the smoke record fresh and passing?")
    s.add_argument("--record", required=True)
    s.add_argument("--model-dir", help="override the model folder stored in the record")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("check", help="run the metric checks on a metrics JSON file")
    c.add_argument("metrics")
    c.add_argument("--max-rate", type=float, default=DEFAULT_MAX_RATE)
    c.add_argument("--allow-silence", action="store_true")
    c.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "run":
            return cmd_run(args)
        if args.cmd == "status":
            return cmd_status(args)
        return cmd_check(args)
    except SmokeError as e:
        print(f"smoke_test.py: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
