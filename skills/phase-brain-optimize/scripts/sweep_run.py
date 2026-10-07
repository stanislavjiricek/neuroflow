#!/usr/bin/env python3
"""sweep_run.py - run a declared parameter grid as processes, behind a smoke-test gate.

Part of the neuroflow `phase-brain-optimize` skill. The sweep is declared in a JSON spec. Before the
sweep starts, the smoke configuration(s) run first - by default the first grid point; the sweep is
refused unless every smoke run exits 0 and reports a finite metric. Then every configuration runs in
its own folder; results land in results.csv and summary.json, and the best configurations and a
grid-edge check are computed in code, not eyeballed.

Spec file (JSON):
  {
    "name": "ge-sweep",
    "command": ["python", "models/run_sim.py", "--g_exc", "{g_exc}", "--tau", "{tau}",
                "--out", "{outdir}/metrics.json"],
    "grid": {"g_exc": [0.1, 0.5, 1.0, 2.0], "tau": [5, 10, 20]},
    "points": [{"g_exc": 0.3, "tau": 7}],
    "metric": {"file": "{outdir}/metrics.json", "key": "populations.E.rate_hz"},
    "goal": "target", "target": 8.0,
    "smoke": [{"g_exc": 0.5, "tau": 10}],
    "out_dir": "models/optimize/ge-sweep",
    "timeout_s": 600,
    "workers": 1
  }
"metric" may instead be {"regex": "rate=([0-9.eE+-]+)"} on stdout (last match). "goal": "min",
"max" or "target" (needs "target"); without a goal no ranking is made. "points" adds explicit
configurations (e.g. Latin-hypercube samples generated elsewhere) to - or instead of - the grid.
Placeholders: {<parameter>}, {outdir} (this run's folder), {run_id}.

Examples:
  python sweep_run.py spec.json --dry-run       list the configurations; run nothing
  python sweep_run.py spec.json --smoke-only    run only the smoke gate
  python sweep_run.py spec.json                 smoke gate, then the sweep
  python sweep_run.py spec.json --resume        rerun only what has no successful result yet

Exit codes: 0 = smoke gate passed and every configuration produced its metric;
            1 = smoke gate failed (sweep not started) or some configurations failed;
            2 = usage or spec error - nothing ran.
Long sweeps: start this in the background and register it in runs.md (phase-brain-run long-run convention).
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import itertools
import json
import math
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
RESERVED = {"outdir", "run_id"}


class SpecError(Exception):
    """Bad spec or arguments (exit 2)."""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt(v) -> str:
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SpecError(f"cannot read spec {path}: {e}")
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    cmd = spec.get("command")
    if isinstance(cmd, str):
        cmd = shlex.split(cmd, posix=os.name != "nt")
    if not isinstance(cmd, list) or not cmd:
        raise SpecError("'command' must be a non-empty list of strings")
    spec["command"] = [str(c) for c in cmd]
    grid = spec.get("grid") or {}
    points = spec.get("points") or []
    if not isinstance(grid, dict) or not isinstance(points, list):
        raise SpecError("'grid' must be an object and 'points' a list")
    if not grid and not points:
        raise SpecError("declare a 'grid' and/or 'points'")
    for k, vals in grid.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) or k in RESERVED:
            raise SpecError(f"grid parameter {k!r} must be an identifier other than outdir/run_id")
        if not isinstance(vals, list) or not vals:
            raise SpecError(f"grid parameter {k!r} needs a non-empty list of values")
    if grid:
        names = list(grid)
    else:
        names = list(points[0]) if isinstance(points[0], dict) else []
    for p in points:
        if not isinstance(p, dict) or (names and set(p) != set(names)):
            raise SpecError(f"every point must set exactly the parameters {names}")
    metric = spec.get("metric")
    if not isinstance(metric, dict) or not (("file" in metric and metric.get("key")) or metric.get("regex")):
        raise SpecError("'metric' needs {'file': ..., 'key': ...} or {'regex': pattern}")
    if "regex" in metric:
        try:
            if re.compile(metric["regex"]).groups < 1:
                raise SpecError("metric regex needs one capture group")
        except re.error as e:
            raise SpecError(f"metric regex is invalid: {e}")
    goal = spec.get("goal")
    if goal not in (None, "min", "max", "target"):
        raise SpecError("'goal' must be min, max or target")
    if goal == "target" and not isinstance(spec.get("target"), (int, float)):
        raise SpecError("goal 'target' needs a numeric 'target'")
    if not isinstance(spec.get("out_dir"), str) or not spec["out_dir"].strip():
        raise SpecError("'out_dir' is required")
    smoke = spec.get("smoke")
    if smoke is not None:
        if isinstance(smoke, dict):
            smoke = [smoke]
        if not isinstance(smoke, list) or not smoke or not all(isinstance(s, dict) and set(s) == set(names) for s in smoke):
            raise SpecError(f"'smoke' must be a configuration (or list) setting exactly {names}")
        spec["smoke"] = smoke
    known = set(names) | RESERVED
    for token in spec["command"] + [str(metric.get("file", ""))]:
        for ph in _PLACEHOLDER.findall(token):
            if ph not in known:
                raise SpecError(f"placeholder {{{ph}}} is not a parameter")
    spec["_names"] = names
    return spec


def expand(spec: dict) -> list[tuple[str, dict]]:
    names = list(spec.get("grid") or {})
    configs = [dict(zip(names, c)) for c in itertools.product(*(spec["grid"][n] for n in names))] if names else []
    configs += [dict(p) for p in spec.get("points") or []]
    width = max(3, len(str(len(configs))))
    return [(f"r{i:0{width}d}", c) for i, c in enumerate(configs, start=1)]


def spec_digest(spec: dict) -> str:
    """Hash of what defines each run's result - goal, timeout or workers may change between resumes."""
    core = {k: spec.get(k) for k in ("command", "grid", "points", "metric")}
    return hashlib.sha256(json.dumps(core, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def substitute(text: str, values: dict) -> str:
    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), text)


def dig(data, dotted: str):
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(dotted)
    return cur


def read_metric(spec: dict, values: dict, stdout: str) -> tuple[float | None, str | None]:
    m = spec["metric"]
    if "regex" in m:
        found = re.findall(m["regex"], stdout)
        if not found:
            return None, "metric pattern not found in the output"
        raw = found[-1][0] if isinstance(found[-1], tuple) else found[-1]
    else:
        path = Path(substitute(str(m["file"]), values))
        try:
            raw = dig(json.loads(path.read_text(encoding="utf-8")), str(m["key"]))
        except (OSError, json.JSONDecodeError) as e:
            return None, f"metric file not readable ({path}: {e})"
        except KeyError:
            return None, f"metric key {m['key']!r} missing"
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None, f"metric is not a number ({raw!r})"
    if not math.isfinite(val):
        return None, f"metric is {val}"
    return val, None


def run_config(spec: dict, run_id: str, params: dict, run_dir: Path, timeout) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    values = {**params, "outdir": run_dir.as_posix(), "run_id": run_id}
    argv = [substitute(a, values) for a in spec["command"]]
    rec = {"run_id": run_id, "params": params, "command": argv, "status": "failed", "exit_code": None,
           "metric": None, "error": None}
    t0 = time.time()
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        rec["exit_code"] = proc.returncode
        (run_dir / "log.txt").write_text((proc.stdout or "") + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else ""),
                                         encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            rec["error"] = f"exit code {proc.returncode}"
        else:
            rec["metric"], rec["error"] = read_metric(spec, values, proc.stdout or "")
            if rec["error"] is None:
                rec["status"] = "ok"
    except subprocess.TimeoutExpired:
        rec["error"] = f"timeout after {timeout} s"
    except OSError as e:
        rec["error"] = f"cannot start {argv[0]}: {e}"
    rec["duration_s"] = round(time.time() - t0, 3)
    rec["finished_at"] = now_utc()
    (run_dir / "result.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    return rec


def rank(spec: dict, ok: list[dict]) -> list[dict]:
    goal = spec.get("goal")
    if goal == "min":
        return sorted(ok, key=lambda r: r["metric"])
    if goal == "max":
        return sorted(ok, key=lambda r: -r["metric"])
    if goal == "target":
        return sorted(ok, key=lambda r: abs(r["metric"] - spec["target"]))
    return []


def edge_warnings(spec: dict, best: dict | None) -> list[str]:
    if not best:
        return []
    out = []
    for name, vals in (spec.get("grid") or {}).items():
        nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(nums) >= 3 and best["params"].get(name) in (min(nums), max(nums)):
            out.append(f"best value of {name} ({fmt(best['params'][name])}) is at the edge of the grid - "
                       "the optimum may lie outside the range")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sweep_run.py",
                                 description="Run a declared parameter grid behind a smoke-test gate (neuroflow).",
                                 epilog="Exit codes: 0 = all ok; 1 = smoke gate failed or runs failed; 2 = usage or spec error.")
    ap.add_argument("spec", help="sweep spec JSON")
    ap.add_argument("--dry-run", action="store_true", help="list the configurations; run nothing")
    ap.add_argument("--smoke-only", action="store_true", help="run only the smoke gate")
    ap.add_argument("--resume", action="store_true", help="keep successful results already in out_dir")
    ap.add_argument("--workers", type=int, default=None, help="parallel runs (default: spec 'workers' or 1)")
    ap.add_argument("--top", type=int, default=5, help="how many best configurations to report (default 5)")
    ap.add_argument("--json", action="store_true", help="print a JSON summary")
    args = ap.parse_args(argv)
    try:
        spec = load_spec(Path(args.spec))
        configs = expand(spec)
        workers = args.workers or int(spec.get("workers") or 1)
        if workers < 1:
            raise SpecError("workers must be at least 1")
    except SpecError as e:
        print(f"sweep_run.py: error: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"{spec.get('name', 'sweep')}: {len(configs)} configuration(s) declared (nothing run)")
        for rid, p in configs:
            print(f"  {rid}  " + ", ".join(f"{k}={fmt(v)}" for k, v in p.items()))
        return 0

    out_dir = Path(spec["out_dir"])
    digest = spec_digest(spec)
    stamp = out_dir / "spec.json"
    if stamp.exists():
        try:
            previous = json.loads(stamp.read_text(encoding="utf-8")).get("digest")
        except (OSError, json.JSONDecodeError):
            previous = None
        if previous and previous != digest:
            print(f"sweep_run.py: error: {out_dir} holds a sweep with a different spec - use a new out_dir",
                  file=sys.stderr)
            return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    clean_spec = {k: v for k, v in spec.items() if not k.startswith("_")}
    stamp.write_text(json.dumps({"digest": digest, "spec": clean_spec}, indent=2, default=str), encoding="utf-8")
    timeout = spec.get("timeout_s")

    # ---- smoke gate
    smoke_cfgs = spec.get("smoke") or [configs[0][1]]
    smoke_results = []
    for i, params in enumerate(smoke_cfgs, start=1):
        prev = out_dir / "smoke" / f"s{i}" / "result.json"
        rec = None
        if args.resume and prev.exists():
            try:
                rec = json.loads(prev.read_text(encoding="utf-8"))
                rec = rec if rec.get("status") == "ok" and rec.get("params") == params else None
            except (OSError, json.JSONDecodeError):
                rec = None
        if rec is None:
            rec = run_config(spec, f"smoke{i}", params, out_dir / "smoke" / f"s{i}", timeout)
        smoke_results.append(rec)
        print(f"[smoke {i}/{len(smoke_cfgs)}] " + ", ".join(f"{k}={fmt(v)}" for k, v in params.items())
              + (f" -> ok, metric {fmt(rec['metric'])} ({rec['duration_s']} s)" if rec["status"] == "ok"
                 else f" -> FAILED: {rec['error']}"))
    gate_ok = all(r["status"] == "ok" for r in smoke_results)
    if not gate_ok or args.smoke_only:
        summary = {"name": spec.get("name"), "smoke_gate": "passed" if gate_ok else "failed",
                   "smoke": smoke_results, "configurations": len(configs), "started": False}
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        if args.json:
            print(json.dumps(summary, indent=2, default=str))
        elif not gate_ok:
            print("SMOKE GATE FAILED - the sweep was not started. Fix the model or the spec and rerun.")
        else:
            print(f"Smoke gate passed. {len(configs)} configuration(s) ready; per-run time ~{smoke_results[0]['duration_s']} s.")
        return 0 if gate_ok else 1

    # ---- sweep
    records: dict[str, dict] = {}
    todo = []
    for rid, params in configs:
        prev = out_dir / "runs" / rid / "result.json"
        if args.resume and prev.exists():
            try:
                rec = json.loads(prev.read_text(encoding="utf-8"))
                if rec.get("status") == "ok" and rec.get("params") == params:
                    records[rid] = rec
                    continue
            except (OSError, json.JSONDecodeError):
                pass
        reuse = next((s for s in smoke_results if s["params"] == params), None)
        if reuse is not None:
            records[rid] = {**reuse, "run_id": rid, "reused_from": "smoke gate"}
            (out_dir / "runs" / rid).mkdir(parents=True, exist_ok=True)
            (out_dir / "runs" / rid / "result.json").write_text(json.dumps(records[rid], indent=2, default=str),
                                                                 encoding="utf-8")
            continue
        todo.append((rid, params))
    done = len(records)
    total = len(configs)
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_config, spec, rid, params, out_dir / "runs" / rid, timeout): rid for rid, params in todo}
        for fut in cf.as_completed(futures):
            rec = fut.result()
            records[rec["run_id"]] = rec
            done += 1
            print(f"[{done}/{total}] {rec['run_id']} " + ", ".join(f"{k}={fmt(v)}" for k, v in rec["params"].items())
                  + (f" -> {fmt(rec['metric'])}" if rec["status"] == "ok" else f" -> FAILED: {rec['error']}"), flush=True)

    ordered = [records[rid] for rid, _ in configs]
    names = spec["_names"]
    with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id"] + names + ["status", "metric", "exit_code", "duration_s", "error"])
        for r in ordered:
            w.writerow([r["run_id"]] + [r["params"].get(n) for n in names]
                       + [r["status"], "" if r["metric"] is None else r["metric"], r["exit_code"], r.get("duration_s"),
                          r["error"] or ""])
    ok = [r for r in ordered if r["status"] == "ok"]
    failed = [r for r in ordered if r["status"] != "ok"]
    ranked = rank(spec, ok)
    warnings = edge_warnings(spec, ranked[0] if ranked else None)
    summary = {
        "name": spec.get("name"), "smoke_gate": "passed", "configurations": total, "ok": len(ok),
        "failed": [r["run_id"] for r in failed], "goal": spec.get("goal"), "target": spec.get("target"),
        "best": [{"run_id": r["run_id"], "params": r["params"], "metric": r["metric"]} for r in ranked[: args.top]],
        "warnings": warnings, "results_csv": (out_dir / "results.csv").as_posix(),
        "note": "a grid search returns the best grid point, not an optimum; 'converged' does not apply",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(f"\n{summary['name'] or 'sweep'}: {total} configuration(s), {len(ok)} ok, {len(failed)} failed "
              f"-> {summary['results_csv']}")
        for b in summary["best"]:
            print(f"  best {b['run_id']}: " + ", ".join(f"{k}={fmt(v)}" for k, v in b["params"].items())
                  + f" -> {fmt(b['metric'])}")
        for w_ in warnings:
            print(f"WARNING: {w_}")
        if failed:
            print("Failed: " + ", ".join(r["run_id"] for r in failed) + " (see runs/<id>/log.txt)")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
