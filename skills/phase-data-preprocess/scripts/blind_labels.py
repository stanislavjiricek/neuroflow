#!/usr/bin/env python3
"""blind_labels.py - label-coded copies of BIDS label files, so preprocessing decisions are made blind.

Part of the neuroflow `phase-data-preprocess` skill. `blind` writes a coded copy of the
condition column(s) of every *_events.tsv and, optionally, the group column(s) of
participants.tsv: each original label is replaced by a random code (C01, C02 ... / G01, G02 ...).
The code -> label key goes to a file the person keeps OUTSIDE the project. Preprocessing
decisions (bad channels, ICA components, epoch rejection) are then made on the coded copy.
`unblind` maps codes back in a results table once those decisions are final.

The script never prints original labels or per-label counts, and never writes into the BIDS root.

Examples:
  python blind_labels.py blind --bids-root data/bids --out derivatives/blinded \
      --key ~/blind-keys/oddball.json --participants-column group \
      --plan .neuroflow/data-preprocess/preprocess-config.md --log .neuroflow/data-preprocess/blinding.md
  python blind_labels.py unblind --key ~/blind-keys/oddball.json --input results/qc_by_condition.tsv \
      --column trial_type --out results/qc_by_condition_unblinded.tsv \
      --plan .neuroflow/data-preprocess/preprocess-config.md --log .neuroflow/data-preprocess/blinding.md

Exit codes: 0 = done, nothing to warn about;
            1 = done, but warnings: a remaining column may reveal the blinded labels (blind),
                or the plan file changed since blinding (unblind);
            2 = usage or runtime error - nothing was written.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KEY_VERSION = 1
NA_VALUES = {"", "n/a"}
SKIP_DIRS = {"derivatives", "sourcedata", ".git", "code", ".datalad"}
TIMING_COLUMNS = {"onset", "duration", "sample"}
EVENT_PREFIXES = "CDEFKLMN"
PARTICIPANT_PREFIXES = "GHJPQRSTUVWXYZ"


class BlindError(Exception):
    """Usage or runtime problem (exit 2)."""


# ---------------------------------------------------------------- small helpers

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def git_toplevel(start: Path) -> Path | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True,
                             text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    top = out.stdout.strip()
    return Path(top) if out.returncode == 0 and top else None


def display_path(path: Path) -> str:
    """Path for logs: relative to the cwd when inside it, else with the home folder shortened to ~."""
    p = path.expanduser().resolve()
    try:
        return p.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        pass
    try:
        return "~/" + p.relative_to(Path.home().resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def read_tsv(path: Path) -> tuple[list[str], list[list[str]], str]:
    raw = path.read_bytes().decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = [ln for ln in raw.splitlines() if ln.strip() != ""]
    if not lines:
        raise BlindError(f"{path}: empty TSV file")
    header = lines[0].split("\t")
    rows = []
    for i, ln in enumerate(lines[1:], start=2):
        cells = ln.split("\t")
        if len(cells) != len(header):
            raise BlindError(f"{path}: line {i} has {len(cells)} fields, header has {len(header)}")
        rows.append(cells)
    return header, rows, newline


def write_tsv(path: Path, header: list[str], rows: list[list[str]], newline: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = newline.join(["\t".join(header)] + ["\t".join(r) for r in rows]) + newline
    path.write_bytes(text.encode("utf-8"))


def append_log(log: Path, line: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    new = not log.exists() or log.stat().st_size == 0
    with log.open("a", encoding="utf-8", newline="\n") as fh:
        if new:
            fh.write("# Blinding log\n\n> Append-only. When labels were coded and when they were revealed - "
                     "never the key or the labels themselves.\n\n")
        fh.write(line.rstrip("\n") + "\n")


def code_for(prefix: str, index: int, total: int) -> str:
    width = max(2, len(str(total)))
    return f"{prefix}{index:0{width}d}"


def make_codes(values: set[str], prefix: str) -> dict[str, str]:
    """original -> code, assigned in a random order so codes carry no information."""
    ordered = sorted(values)
    random.SystemRandom().shuffle(ordered)
    return {orig: code_for(prefix, i, len(ordered)) for i, orig in enumerate(ordered, start=1)}


def leak_warnings(header: list[str], rows: list[list[str]], blinded: list[str]) -> list[tuple[str, str]]:
    """(column, blinded column) pairs where a remaining column determines the blinded labels."""
    found = []
    n = len(rows)
    for b in blinded:
        if b not in header:
            continue
        bi = header.index(b)
        b_values = {r[bi] for r in rows if r[bi] not in NA_VALUES}
        if len(b_values) < 2:
            continue
        for ci, c in enumerate(header):
            if c in blinded or c in TIMING_COLUMNS:
                continue
            groups: dict[str, set[str]] = {}
            for r in rows:
                if r[ci] in NA_VALUES or r[bi] in NA_VALUES:
                    continue
                groups.setdefault(r[ci], set()).add(r[bi])
            if len(groups) < 2 or len(groups) > max(2, n // 2):
                continue
            if all(len(s) == 1 for s in groups.values()):
                found.append((c, b))
    return found


# ---------------------------------------------------------------- blind

def find_events(bids_root: Path, out_dir: Path) -> list[Path]:
    found = []
    for p in sorted(bids_root.rglob("*_events.tsv")):
        rel_parts = p.relative_to(bids_root).parts
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if is_within(p, out_dir):
            continue
        found.append(p)
    return found


def cmd_blind(args) -> int:
    bids_root = Path(args.bids_root).expanduser()
    out_dir = Path(args.out).expanduser()
    key_path = Path(args.key).expanduser()
    if not bids_root.is_dir():
        raise BlindError(f"--bids-root {bids_root} is not a folder")
    if out_dir.resolve() == bids_root.resolve() or is_within(bids_root, out_dir):
        raise BlindError("--out must not be the BIDS root or a folder that contains it")
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise BlindError(f"--out {out_dir} exists and is not empty (use --force to overwrite the coded copy)")
    if key_path.exists() and not args.force:
        raise BlindError(f"--key {key_path} already exists - overwriting it would lose the earlier mapping "
                         "(choose a new key path, or --force)")
    if not args.allow_key_in_repo:
        guarded = [bids_root, out_dir]
        top = git_toplevel(Path.cwd()) or git_toplevel(bids_root)
        if top:
            guarded.append(top)
        for g in guarded:
            if is_within(key_path, g):
                raise BlindError(f"--key {key_path} is inside {g}; keep the key outside the project "
                                 "(or pass --allow-key-in-repo if it is encrypted or otherwise protected)")

    events_cols = [] if args.no_events else (args.events_column or ["trial_type"])
    part_cols = args.participants_column or []
    if not events_cols and not part_cols:
        raise BlindError("nothing to blind: give --events-column and/or --participants-column")
    drop = set(args.drop_column or [])
    if drop & (set(events_cols) | set(part_cols)):
        raise BlindError("a column cannot be both blinded and dropped")

    # read everything first - nothing is written unless all inputs are valid
    tables: dict[Path, tuple[list[str], list[list[str]], str]] = {}
    events_files = find_events(bids_root, out_dir) if events_cols else []
    if events_cols and not events_files:
        raise BlindError(f"no *_events.tsv files under {bids_root}")
    for p in events_files:
        tables[p] = read_tsv(p)
    participants = bids_root / "participants.tsv"
    if part_cols:
        if not participants.is_file():
            raise BlindError(f"{participants} not found (needed for --participants-column)")
        tables[participants] = read_tsv(participants)

    notes: list[str] = []
    maps: dict[str, dict[str, str]] = {}
    for i, col in enumerate(events_cols):
        values: set[str] = set()
        missing = 0
        for p in events_files:
            header, rows, _ = tables[p]
            if col not in header:
                missing += 1
                continue
            ci = header.index(col)
            values |= {r[ci] for r in rows if r[ci] not in NA_VALUES}
        if missing == len(events_files):
            raise BlindError(f"column {col!r} is in none of the {len(events_files)} events files")
        if missing:
            notes.append(f"column {col!r} missing in {missing} events file(s) - those copies keep their other columns")
        maps[f"events:{col}"] = make_codes(values, EVENT_PREFIXES[i % len(EVENT_PREFIXES)])
    for i, col in enumerate(part_cols):
        header, rows, _ = tables[participants]
        if col not in header:
            raise BlindError(f"column {col!r} not in participants.tsv")
        ci = header.index(col)
        values = {r[ci] for r in rows if r[ci] not in NA_VALUES}
        maps[f"participants:{col}"] = make_codes(values, PARTICIPANT_PREFIXES[i % len(PARTICIPANT_PREFIXES)])

    plan_hashes = {}
    for plan in args.plan or []:
        pp = Path(plan).expanduser()
        if not pp.is_file():
            raise BlindError(f"--plan {plan} not found")
        plan_hashes[display_path(pp)] = sha256_file(pp)

    # build coded copies in memory; the key is written before any coded file
    leaks: dict[tuple[str, str], int] = {}
    coded: list[tuple[Path, list[str], list[list[str]], str]] = []
    for p, (header, rows, newline) in tables.items():
        kind = "participants" if p == participants else "events"
        cols = part_cols if kind == "participants" else events_cols
        coded_rows = []
        for r in rows:
            r2 = list(r)
            for col in cols:
                if col in header:
                    ci = header.index(col)
                    if r2[ci] not in NA_VALUES:
                        r2[ci] = maps[f"{kind}:{col}"][r2[ci]]
            coded_rows.append(r2)
        keep = [i for i, h in enumerate(header) if h not in drop]
        header2 = [header[i] for i in keep]
        rows2 = [[r[i] for i in keep] for r in coded_rows]
        for c, b in leak_warnings(header2, rows2, cols):
            leaks[(f"{kind}:{c}", f"{kind}:{b}")] = leaks.get((f"{kind}:{c}", f"{kind}:{b}"), 0) + 1
        coded.append((p.relative_to(bids_root), header2, rows2, newline))
    written = [rel.as_posix() for rel, _, _, _ in coded]

    sidecars = [s for s in [bids_root / "participants.json"] if s.is_file()]
    sidecars += [s for s in bids_root.rglob("*_events.json")
                 if not any(part in SKIP_DIRS for part in s.relative_to(bids_root).parts[:-1])]
    if sidecars:
        notes.append(f"{len(sidecars)} JSON sidecar(s) may name the original levels - they were not copied; "
                     "do not open them while blinded")

    key = {
        "nf_blind_key": KEY_VERSION,
        "created_at": now_utc(),
        "bids_root": display_path(bids_root),
        "coded_copy": display_path(out_dir),
        "columns": {cid: {code: orig for orig, code in m.items()} for cid, m in maps.items()},
        "dropped_columns": sorted(drop),
        "plan_sha256": plan_hashes,
        "files": written,
    }
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    fingerprint = sha256_file(key_path)[:12]
    for rel, header2, rows2, newline in coded:
        write_tsv(out_dir / rel, header2, rows2, newline)

    warnings = [f"column {c} determines {b} in {n} file(s) - blind it too or drop it (--drop-column)"
                for (c, b), n in sorted(leaks.items())]
    if args.log:
        plan_txt = "; ".join(f"{k} sha256 {v[:12]}" for k, v in plan_hashes.items()) or "none recorded"
        append_log(Path(args.log), f"- {now_utc()} - **blinded** {', '.join(maps)}; coded copy {display_path(out_dir)}; "
                                   f"key fingerprint {fingerprint}; plan: {plan_txt}")

    summary = {
        "action": "blind",
        "coded_copy": display_path(out_dir),
        "files": len(written),
        "columns": {cid: {"levels": len(m), "codes": sorted(m.values())} for cid, m in maps.items()},
        "dropped_columns": sorted(drop),
        "key": display_path(key_path),
        "key_fingerprint": fingerprint,
        "plan_sha256": plan_hashes,
        "warnings": warnings,
        "notes": notes,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Coded copy written: {summary['coded_copy']} ({len(written)} file(s))")
        for cid, info in summary["columns"].items():
            print(f"  {cid}: {info['levels']} level(s) -> {', '.join(info['codes'])}")
        print(f"Key (the person keeps it; do not read it): {summary['key']}  fingerprint {fingerprint}")
        for w in warnings:
            print(f"WARNING: {w}")
        for n in notes:
            print(f"Note: {n}")
    return 1 if warnings else 0


# ---------------------------------------------------------------- unblind

def resolve_column_map(key: dict, spec: str) -> tuple[str, dict[str, str]]:
    cols = key.get("columns") or {}
    if spec in cols:
        return spec, cols[spec]
    matches = [cid for cid in cols if cid.split(":", 1)[-1] == spec]
    if len(matches) == 1:
        return matches[0], cols[matches[0]]
    if not matches:
        raise BlindError(f"column {spec!r} is not in the key (key columns: {', '.join(cols) or 'none'})")
    raise BlindError(f"column {spec!r} is ambiguous - use one of {', '.join(matches)}")


def cmd_unblind(args) -> int:
    key_path = Path(args.key).expanduser()
    src = Path(args.input).expanduser()
    dst = Path(args.out).expanduser()
    try:
        key = json.loads(key_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise BlindError(f"cannot read key {key_path}: {e}")
    if not isinstance(key, dict) or "columns" not in key:
        raise BlindError(f"{key_path} is not a blind_labels key file")
    if key.get("nf_blind_key", KEY_VERSION) > KEY_VERSION:
        raise BlindError("key written by a newer blind_labels.py - update neuroflow")
    if not src.is_file():
        raise BlindError(f"--input {src} not found")
    if dst.exists() and not args.force:
        raise BlindError(f"--out {dst} exists (use --force to overwrite)")
    if dst.resolve() == src.resolve():
        raise BlindError("--out must differ from --input (the coded table stays as it is)")
    maps = [resolve_column_map(key, c) for c in args.column]

    suffix = src.suffix.lower()
    if suffix not in {".tsv", ".csv"}:
        raise BlindError("--input must be a .tsv or .csv table")
    newline = "\n"
    if suffix == ".tsv":
        header, rows, newline = read_tsv(src)
    else:
        with src.open(newline="", encoding="utf-8-sig") as fh:
            table = list(csv.reader(fh))
        if not table:
            raise BlindError(f"{src} is empty")
        header, rows = table[0], table[1:]
    replaced = 0
    for (cid, m), spec in zip(maps, args.column):
        name = cid.split(":", 1)[-1]
        target = spec if spec in header else name
        if target not in header:
            raise BlindError(f"column {target!r} not in {src.name}")
        ci = header.index(target)
        pattern = re.compile(r"\b(" + "|".join(re.escape(c) for c in sorted(m, key=len, reverse=True)) + r")\b")
        for r in rows:
            if ci < len(r) and r[ci]:
                new = pattern.sub(lambda mo, codes=m: codes[mo.group(1)], r[ci])
                if new != r[ci]:
                    replaced += 1
                    r[ci] = new
    if suffix == ".tsv":
        write_tsv(dst, header, rows, newline)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh, lineterminator="\n").writerows([header] + rows)

    stored = key.get("plan_sha256") or {}
    changed, unchanged, unknown = [], [], []
    for plan in args.plan or []:
        pp = Path(plan).expanduser()
        name = display_path(pp)
        if not pp.is_file():
            raise BlindError(f"--plan {plan} not found")
        if name not in stored:
            unknown.append(name)
        elif sha256_file(pp) == stored[name]:
            unchanged.append(name)
        else:
            changed.append(name)
    if args.log:
        state = ("changed since blinding: " + ", ".join(changed)) if changed else (
            "unchanged since blinding" if unchanged else "not checked")
        append_log(Path(args.log), f"- {now_utc()} - **unblinded** {display_path(src)} -> {display_path(dst)}; "
                                   f"columns {', '.join(cid for cid, _ in maps)}; plan {state}")
    summary = {"action": "unblind", "input": display_path(src), "out": display_path(dst),
               "cells_replaced": replaced, "plan_changed": changed, "plan_unchanged": unchanged,
               "plan_not_in_key": unknown}
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Unblinded copy written: {summary['out']} ({replaced} cell(s) decoded)")
        for c in changed:
            print(f"WARNING: plan {c} changed after blinding - record why in the preprocessing report")
        for u in unknown:
            print(f"Note: plan {u} was not recorded at blinding time")
    return 1 if changed else 0


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="blind_labels.py",
        description="Label-coded copies of BIDS events/participants files for blind preprocessing (neuroflow).",
        epilog="Exit codes: 0 = done; 1 = done with warnings; 2 = usage or runtime error (nothing written).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("blind", help="write a coded copy and a key file kept outside the project")
    b.add_argument("--bids-root", required=True, help="BIDS dataset root (read only)")
    b.add_argument("--out", required=True, help="folder for the coded copy (same relative paths)")
    b.add_argument("--key", required=True, help="key file path, OUTSIDE the project; the person keeps it")
    b.add_argument("--events-column", action="append", help="events.tsv column to code (repeatable; default trial_type)")
    b.add_argument("--no-events", action="store_true", help="do not code events files")
    b.add_argument("--participants-column", action="append", help="participants.tsv column to code (repeatable)")
    b.add_argument("--drop-column", action="append", help="column to leave out of the coded copies (repeatable)")
    b.add_argument("--plan", action="append", help="plan/config file whose sha256 is recorded (repeatable)")
    b.add_argument("--log", help="append-only blinding log, e.g. .neuroflow/data-preprocess/blinding.md")
    b.add_argument("--allow-key-in-repo", action="store_true", help="allow the key inside the project (protect it!)")
    b.add_argument("--force", action="store_true", help="overwrite an existing coded copy or key")
    b.add_argument("--json", action="store_true", help="print JSON")
    u = sub.add_parser("unblind", help="decode a results table with the key")
    u.add_argument("--key", required=True, help="key file written by 'blind'")
    u.add_argument("--input", required=True, help="coded .tsv/.csv table")
    u.add_argument("--column", action="append", required=True,
                   help="column to decode, e.g. trial_type or events:trial_type (repeatable)")
    u.add_argument("--out", required=True, help="decoded copy to write (the input stays coded)")
    u.add_argument("--plan", action="append", help="plan/config file to compare with the hash recorded at blinding")
    u.add_argument("--log", help="append-only blinding log")
    u.add_argument("--force", action="store_true", help="overwrite --out")
    u.add_argument("--json", action="store_true", help="print JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return cmd_blind(args) if args.cmd == "blind" else cmd_unblind(args)
    except BlindError as e:
        print(f"blind_labels.py: error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"blind_labels.py: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
