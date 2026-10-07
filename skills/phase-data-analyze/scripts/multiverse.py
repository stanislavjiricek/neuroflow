#!/usr/bin/env python3
"""multiverse.py - run a declared grid of analysis specifications; log every one to the multiverse ledger.

Part of the neuroflow `phase-data-analyze` skill. A multiverse (specification-curve) analysis runs the
same analysis under every combination of defensible choices - filter cutoff, reference, rejection
threshold, time window - and reports ALL results, not the best one. Each specification is appended to
the multiverse ledger (.neuroflow/data-analyze/multiverse.md, format of
skills/autoresearch-protocol/references/integrity.md) as soon as it finishes: failed or not. Everything
it produces is exploratory.

Spec file (JSON), declared before anything runs:
  {
    "name": "p3-window",
    "command": ["python", "scripts/analysis/p3.py", "--lowcut", "{lowcut}", "--ref", "{ref}",
                "--out", "{outdir}/result.json"],
    "grid": {"lowcut": [0.1, 0.5, 1.0], "ref": ["average", "mastoids"]},
    "result": {"file": "{outdir}/result.json", "keys": ["d", "p"]},
    "p_key": "p",
    "out_dir": "results/exploratory/multiverse/p3-window",
    "timeout_s": 3600
  }
"result" may instead be {"regex": {"d": "d = ([-0-9.eE+]+)"}} - applied to the command's stdout, last
match wins. Placeholders: {<parameter>}, {outdir} (this specification's folder), {spec_id}.
"command" should be a list (no shell); a string is split into words.

Examples:
  python multiverse.py spec.json --dry-run      list the specifications; run nothing
  python multiverse.py spec.json                run all; append each to the ledger
  python multiverse.py spec.json --resume       skip specifications that already have a result

Exit codes: 0 = every specification ran and produced its result values;
            1 = at least one specification failed (it is still in the ledger);
            2 = usage or spec error - nothing ran.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import re
import shlex
import statistics
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_LEDGER = ".neuroflow/data-analyze/multiverse.md"
LEDGER_HEADER = (
    "# Analysis multiverse \u2014 EXPLORATORY\n\n"
    "> Every analysis specification run on the study data \u2014 by autoresearch loops and by multiverse.py "
    "\u2014 with its result, kept and discarded.\n"
    "> Nothing here is confirmatory. A result that came from this search is reported together with this "
    "ledger or its summary.\n\n"
    "| Date | Loop | Iter | Choice | Value | Result | Kept |\n"
    "|------|------|------|--------|-------|--------|------|\n"
)
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class SpecError(Exception):
    """Bad spec or arguments (exit 2)."""


def fmt_value(v) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SpecError(f"cannot read spec {path}: {e}")
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    name = spec.get("name")
    if not isinstance(name, str) or not name.strip() or "|" in name:
        raise SpecError("'name' must be a non-empty string without '|'")
    cmd = spec.get("command")
    if isinstance(cmd, str):
        cmd = shlex.split(cmd, posix=os.name != "nt")
    if not isinstance(cmd, list) or not cmd or not all(isinstance(c, (str, int, float)) for c in cmd):
        raise SpecError("'command' must be a non-empty list of strings")
    spec["command"] = [str(c) for c in cmd]
    grid = spec.get("grid")
    if not isinstance(grid, dict) or not grid:
        raise SpecError("'grid' must map each parameter to a non-empty list of values")
    for k, vals in grid.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
            raise SpecError(f"grid parameter {k!r} must be an identifier")
        if k in {"outdir", "spec_id"}:
            raise SpecError(f"grid parameter name {k!r} is reserved")
        if not isinstance(vals, list) or not vals:
            raise SpecError(f"grid parameter {k!r} needs a non-empty list of values")
    res = spec.get("result")
    if not isinstance(res, dict) or not (("file" in res and res.get("keys")) or res.get("regex")):
        raise SpecError("'result' needs {'file': ..., 'keys': [...]} or {'regex': {name: pattern}}")
    if "regex" in res:
        if not isinstance(res["regex"], dict):
            raise SpecError("'result.regex' must map a name to a pattern")
        for k, pat in res["regex"].items():
            try:
                if re.compile(pat).groups < 1:
                    raise SpecError(f"regex for {k!r} needs one capture group")
            except re.error as e:
                raise SpecError(f"regex for {k!r} is invalid: {e}")
    keys = result_keys(spec)
    if spec.get("p_key") and spec["p_key"] not in keys:
        raise SpecError("'p_key' must be one of the result keys")
    if not isinstance(spec.get("out_dir"), str) or not spec["out_dir"].strip():
        raise SpecError("'out_dir' is required")
    t = spec.get("timeout_s")
    if t is not None and (not isinstance(t, (int, float)) or t <= 0):
        raise SpecError("'timeout_s' must be a positive number")
    known = set(grid) | {"outdir", "spec_id"}
    for token in spec["command"] + [str(res.get("file", ""))]:
        for ph in _PLACEHOLDER.findall(token):
            if ph not in known:
                raise SpecError(f"placeholder {{{ph}}} is not a grid parameter")
    return spec


def result_keys(spec: dict) -> list[str]:
    res = spec["result"]
    return list(res["regex"]) if "regex" in res else [str(k) for k in res["keys"]]


def expand(spec: dict) -> list[tuple[str, dict]]:
    names = list(spec["grid"])
    combos = list(itertools.product(*(spec["grid"][n] for n in names)))
    width = max(2, len(str(len(combos))))
    return [(f"s{i:0{width}d}", dict(zip(names, c))) for i, c in enumerate(combos, start=1)]


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


def extract(spec: dict, values: dict, stdout: str) -> tuple[dict, str | None]:
    res = spec["result"]
    found: dict = {}
    if "regex" in res:
        for k, pat in res["regex"].items():
            matches = re.findall(pat, stdout)
            if not matches:
                return found, f"no match for {k!r} in the output"
            m = matches[-1]
            found[k] = m[0] if isinstance(m, tuple) else m
    else:
        path = Path(substitute(str(res["file"]), values))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return found, f"result file not readable ({path}: {e})"
        for k in res["keys"]:
            try:
                found[str(k)] = dig(data, str(k))
            except KeyError:
                return found, f"result key {k!r} missing"
    for k, v in list(found.items()):
        try:
            num = float(v)
            if math.isfinite(num):
                found[k] = num
        except (TypeError, ValueError):
            pass
    return found, None


def ensure_ledger(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(LEDGER_HEADER, encoding="utf-8", newline="\n")


def append_row(path: Path, name: str, spec_id: str, params: dict, result_text: str) -> None:
    row = (f"| {date.today().isoformat()} | multiverse:{cell(name)} | {spec_id} | "
           f"{cell(', '.join(params))} | {cell(', '.join(str(v) for v in params.values()))} | "
           f"{cell(result_text)} | n/a |\n")
    with path.open("rb+") as fh:
        fh.seek(0, os.SEEK_END)
        if fh.tell() > 0:
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                fh.write(b"\n")
        fh.write(row.encode("utf-8"))


def run_one(spec: dict, spec_id: str, params: dict, out_dir: Path, timeout: float | None) -> dict:
    sdir = out_dir / spec_id
    sdir.mkdir(parents=True, exist_ok=True)
    values = {**params, "outdir": sdir.as_posix(), "spec_id": spec_id}
    argv = [substitute(a, values) for a in spec["command"]]
    t0 = time.time()
    rec = {"spec_id": spec_id, "params": params, "command": argv, "status": "failed", "exit_code": None,
           "values": {}, "error": None}
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        rec["exit_code"] = proc.returncode
        (sdir / "log.txt").write_text((proc.stdout or "") + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else ""),
                                      encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            rec["error"] = f"exit code {proc.returncode}"
        else:
            vals, err = extract(spec, values, proc.stdout or "")
            rec["values"] = vals
            if err:
                rec["error"] = err
            else:
                rec["status"] = "ok"
    except subprocess.TimeoutExpired:
        rec["error"] = f"timeout after {timeout} s"
    except OSError as e:
        rec["error"] = f"cannot start {argv[0]}: {e}"
    rec["duration_s"] = round(time.time() - t0, 3)
    rec["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (sdir / "spec-result.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    return rec


def result_text(rec: dict) -> str:
    if rec["status"] == "ok":
        return ", ".join(f"{k} = {fmt_value(v)}" for k, v in rec["values"].items())
    return f"FAILED ({rec['error']})"


def write_tables(out_dir: Path, spec: dict, records: list[dict]) -> None:
    names, keys = list(spec["grid"]), result_keys(spec)
    header = ["spec_id"] + names + ["status"] + keys + ["error"]
    with (out_dir / "specifications.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in records:
            w.writerow([r["spec_id"]] + [r["params"][n] for n in names] + [r["status"]]
                       + [r["values"].get(k, "") for k in keys] + [r["error"] or ""])
    primary = keys[0]
    ok = [r for r in records if r["status"] == "ok" and isinstance(r["values"].get(primary), float)]
    ok.sort(key=lambda r: r["values"][primary])
    with (out_dir / "curve.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "spec_id"] + names + keys)
        for i, r in enumerate(ok, start=1):
            w.writerow([i, r["spec_id"]] + [r["params"][n] for n in names] + [r["values"].get(k, "") for k in keys])


def summarize(spec: dict, records: list[dict], alpha: float) -> dict:
    keys = result_keys(spec)
    primary = keys[0]
    ok = [r for r in records if r["status"] == "ok"]
    nums = [r["values"][primary] for r in ok if isinstance(r["values"].get(primary), float)]
    out = {"specifications": len(records), "ok": len(ok), "failed": len(records) - len(ok), "primary": primary}
    if nums:
        out.update({"min": min(nums), "median": statistics.median(nums), "max": max(nums)})
    p_key = spec.get("p_key")
    if p_key:
        ps = [r["values"][p_key] for r in ok if isinstance(r["values"].get(p_key), float)]
        out["p_below_alpha"] = sum(1 for p in ps if p < alpha)
        out["p_reported"] = len(ps)
        out["alpha"] = alpha
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="multiverse.py",
                                 description="Run a declared specification grid and log every specification "
                                             "to the multiverse ledger (neuroflow).",
                                 epilog="Exit codes: 0 = all ran with results; 1 = some failed (logged); "
                                        "2 = usage or spec error.")
    ap.add_argument("spec", help="spec JSON file")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"ledger file (default {DEFAULT_LEDGER})")
    ap.add_argument("--dry-run", action="store_true", help="list the specifications; run nothing")
    ap.add_argument("--resume", action="store_true", help="skip specifications whose result already exists")
    ap.add_argument("--alpha", type=float, default=0.05, help="threshold for the p-value count (default 0.05)")
    ap.add_argument("--allow-outdir", action="store_true",
                    help="allow an out_dir outside an 'exploratory' folder (not recommended)")
    ap.add_argument("--json", action="store_true", help="print a JSON summary")
    args = ap.parse_args(argv)
    try:
        spec = load_spec(Path(args.spec))
        out_dir = Path(spec["out_dir"])
        if not args.allow_outdir and not any("exploratory" in part.lower() for part in out_dir.parts):
            raise SpecError(f"out_dir {out_dir} is not inside an 'exploratory' folder - multiverse outputs never "
                            "go where confirmatory results live (or pass --allow-outdir)")
        specs = expand(spec)
    except SpecError as e:
        print(f"multiverse.py: error: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        if args.json:
            print(json.dumps({"name": spec["name"], "specifications": [{"spec_id": s, "params": p} for s, p in specs]},
                             indent=2, default=str))
        else:
            print(f"{spec['name']}: {len(specs)} specification(s) declared (nothing run)")
            for s, p in specs:
                print(f"  {s}  " + ", ".join(f"{k}={fmt_value(v)}" for k, v in p.items()))
        return 0

    ledger = Path(args.ledger)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        ensure_ledger(ledger)
    except OSError as e:
        print(f"multiverse.py: error: {e}", file=sys.stderr)
        return 2
    timeout = spec.get("timeout_s")
    records: list[dict] = []
    for i, (spec_id, params) in enumerate(specs, start=1):
        done = out_dir / spec_id / "spec-result.json"
        if args.resume and done.exists():
            try:
                prev = json.loads(done.read_text(encoding="utf-8"))
                if prev.get("status") == "ok":
                    records.append(prev)
                    print(f"[{i}/{len(specs)}] {spec_id} already done - skipped (already in the ledger)")
                    continue
            except (OSError, json.JSONDecodeError):
                pass
        rec = run_one(spec, spec_id, params, out_dir, timeout)
        append_row(ledger, spec["name"], spec_id, params, result_text(rec))
        records.append(rec)
        print(f"[{i}/{len(specs)}] {spec_id} " + ", ".join(f"{k}={fmt_value(v)}" for k, v in params.items())
              + f" -> {result_text(rec)}")
    write_tables(out_dir, spec, records)
    summary = summarize(spec, records, args.alpha)
    summary["ledger"] = ledger.as_posix()
    summary["coverage"] = ("counts cover this grid only; the ledger holds only specifications logged by "
                           "multiverse.py or autoresearch - analyses run any other way are not in it")
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\n{spec['name']}: {summary['specifications']} specification(s) in this grid - "
              f"{summary['ok']} ok, {summary['failed']} failed. All are logged in {ledger.as_posix()}.")
        if "median" in summary:
            print(f"{summary['primary']}: min {fmt_value(summary['min'])}, median {fmt_value(summary['median'])}, "
                  f"max {fmt_value(summary['max'])} (curve: {(out_dir / 'curve.csv').as_posix()})")
        if "p_below_alpha" in summary:
            print(f"{summary['p_below_alpha']} of {summary['p_reported']} specification(s) with "
                  f"{spec['p_key']} < {args.alpha}")
        print("EXPLORATORY - report the whole curve, not the best specification. Coverage: " + summary["coverage"] + ".")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
