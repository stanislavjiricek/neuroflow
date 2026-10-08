#!/usr/bin/env python3
"""Seeded allocation and counterbalancing ledger for non-clinical studies (/experiment).

NOT for clinical trials. A trial that needs allocation concealment under good clinical
practice uses a validated randomisation system run by the trial unit, not this script.

`generate` builds the whole schedule once from a recorded seed and refuses to overwrite
an existing one. `next` hands out the next slot to one participant and appends it to an
append-only ledger; it never reassigns a slot. A replacement participant takes over the
slot (and the order) of the person they replace. `verify` proves the schedule is the
one the seed produces, that it has not changed since allocation started, and reports
the balance so far.

Schemes:
    williams  balanced Latin square for order (first-order carry-over balanced; for an
              odd number of conditions the square plus its mirror, 2n orders)
    latin     cyclic Latin square (each condition once per position)
    full      every permutation of the conditions (up to 6 conditions)
    block     between-subjects groups in randomised blocks (permuted-block randomisation)
Condition labels are assigned to the square in a seeded random order, and orders are
handed out in a seeded random sequence within each complete cycle.

Usage:
    python <phase-experiment base dir>/scripts/allocation.py generate --scheme williams
        --conditions A B C D --participants 24 --seed 20261007 --out paradigm/allocation/schedule.csv
    python <phase-experiment base dir>/scripts/allocation.py generate --scheme block
        --groups control training --block-size 4 --participants 40 --seed 7 --out schedule.csv
    python <phase-experiment base dir>/scripts/allocation.py next --schedule schedule.csv
        --ledger ledger.csv --participant sub-07 [--replaces sub-03]
    python <phase-experiment base dir>/scripts/allocation.py verify --schedule schedule.csv
        --ledger ledger.csv [--expect-sha256 HASH]
All subcommands take --json. Participant IDs must be pseudonyms (e.g. sub-07), never names.

Files: schedule.csv (slot,assignment), schedule.csv.json (scheme, seed and the CSV's
SHA-256, LF-normalised), ledger.csv (allocated_at,slot,participant,assignment,kind,
replaces,schedule_sha256). Record the seed and the SHA-256 in the experiment plan and
the preregistration; log replacements and skipped slots as deviations.

Exit codes:
    0  done: schedule written, participant allocated, or verify found no problem
    1  findings / refusals: participant already allocated, schedule exhausted, schedule
       changed or not reproducible from its seed, ledger out of order
    2  usage or runtime error: bad arguments, file exists or is missing, ID looks like a name

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import platform
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

GENERATOR = "neuroflow allocation.py 1"
LEDGER_FIELDS = ["allocated_at", "slot", "participant", "assignment", "kind", "replaces", "schedule_sha256"]
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,63}$")
SEP = ">"


class UsageError(Exception):
    pass


class Refusal(Exception):
    """A refusal or finding: exit code 1."""


# ------------------------------------------------------------------ designs


def williams_rows(n: int) -> list[list[int]]:
    first = [0] + [((j + 1) // 2) if j % 2 else n - j // 2 for j in range(1, n)]
    rows = [[(x + i) % n for x in first] for i in range(n)]
    if n % 2:
        rows += [list(reversed(r)) for r in rows]
    return rows


def latin_rows(n: int) -> list[list[int]]:
    return [[(j + i) % n for j in range(n)] for i in range(n)]


def full_rows(n: int) -> list[list[int]]:
    if n > 6:
        raise UsageError("full counterbalancing of more than 6 conditions needs over 5000 orders; use williams")
    return [list(p) for p in itertools.permutations(range(n))]


def build_schedule(params: dict) -> list[str]:
    rng = random.Random(params["seed"])
    n_participants = params["participants"]
    if params["scheme"] == "block":
        groups = params["groups"]
        size = params["block_size"]
        out: list[str] = []
        while len(out) < n_participants:
            block = [g for g in groups for _ in range(size // len(groups))]
            rng.shuffle(block)
            out += block
        return out[:n_participants]
    conditions = list(params["conditions"])
    labels = conditions[:]
    rng.shuffle(labels)  # which condition plays which role in the square
    n = len(conditions)
    rows = {"williams": williams_rows, "latin": latin_rows, "full": full_rows}[params["scheme"]](n)
    out = []
    while len(out) < n_participants:
        cycle = rows[:]
        rng.shuffle(cycle)
        out += [SEP.join(labels[i] for i in row) for row in cycle]
    return out[:n_participants]


# ------------------------------------------------------------------ files


def schedule_csv(assignments: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["slot", "assignment"])
    for slot, assignment in enumerate(assignments, start=1):
        writer.writerow([slot, assignment])
    return buf.getvalue()


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_schedule(path: Path) -> list[str]:
    if not path.is_file():
        raise UsageError(f"schedule not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    out = []
    for expected, row in enumerate(rows, start=1):
        if str(row.get("slot", "")).strip() != str(expected):
            raise Refusal(f"schedule slots are not 1..N in order (row {expected}): it was edited by hand")
        out.append(row["assignment"])
    return out


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_ledger(path: Path, row: dict) -> None:
    new = not path.exists() or path.stat().st_size == 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        if new:
            writer.writeheader()
        writer.writerow(row)


def sidecar_path(schedule: Path) -> Path:
    return schedule.with_name(schedule.name + ".json")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_id(participant: str) -> None:
    if not ID_RE.match(participant):
        raise UsageError(
            f"{participant!r} does not look like a pseudonymous ID (letters, digits, '-' or '_', no spaces); "
            "never use names in the ledger"
        )


# ------------------------------------------------------------------ subcommands


def cmd_generate(args) -> dict:
    out = Path(args.out)
    side = sidecar_path(out)
    if out.exists() or side.exists():
        raise UsageError(f"{out} (or its .json) already exists: a schedule is generated once; use a new file name")
    if args.participants < 1:
        raise UsageError("--participants must be at least 1")
    params: dict = {"scheme": args.scheme, "participants": args.participants, "seed": args.seed}
    if args.scheme == "block":
        groups = args.groups or []
        if len(groups) < 2:
            raise UsageError("--scheme block needs --groups with at least two group names")
        size = args.block_size or 2 * len(groups)
        if size % len(groups):
            raise UsageError("--block-size must be a multiple of the number of groups")
        params.update({"groups": groups, "block_size": size})
        labels = groups
    else:
        conditions = args.conditions or []
        if len(conditions) < 2:
            raise UsageError(f"--scheme {args.scheme} needs --conditions with at least two names")
        params["conditions"] = conditions
        labels = conditions
    if len(set(labels)) != len(labels) or any(not lab.strip() or SEP in lab or "," in lab for lab in labels):
        raise UsageError(f"labels must be unique and must not contain ',' or '{SEP}'")
    assignments = build_schedule(params)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(schedule_csv(assignments), encoding="utf-8", newline="\n")
    digest = sha256_text(out)
    meta = dict(params, generator=GENERATOR, python=platform.python_version(), created_at=now_utc(), sha256=digest)
    side.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"schedule": out.as_posix(), "sidecar": side.as_posix(), "sha256": digest, "slots": len(assignments),
            "message": f"wrote {len(assignments)} slot(s) to {out.as_posix()} (sha256 {digest}); record the seed "
                       "and this hash in the experiment plan and the preregistration"}


def load_checked(args) -> tuple[list[str], str, list[dict]]:
    schedule_path = Path(args.schedule)
    schedule = read_schedule(schedule_path)
    digest = sha256_text(schedule_path)
    side = sidecar_path(schedule_path)
    if side.exists():
        meta = json.loads(side.read_text(encoding="utf-8"))
        if meta.get("sha256") != digest:
            raise Refusal("the schedule changed after it was generated (hash differs from schedule.csv.json)")
    ledger = read_ledger(Path(args.ledger))
    stale = {r.get("schedule_sha256") for r in ledger} - {digest}
    if stale:
        raise Refusal("the schedule changed after allocation started (ledger rows carry another schedule hash)")
    return schedule, digest, ledger


def cmd_next(args) -> dict:
    check_id(args.participant)
    schedule, digest, ledger = load_checked(args)
    existing = [r for r in ledger if r["participant"] == args.participant]
    if existing:
        row = existing[-1]
        raise Refusal(
            f"{args.participant} is already allocated: slot {row['slot']} ({row['assignment']}); "
            "nothing new was allocated"
        )
    if args.replaces:
        old = [r for r in ledger if r["participant"] == args.replaces]
        if not old:
            raise UsageError(f"{args.replaces} is not in the ledger, so there is no slot to take over")
        slot, assignment, kind = int(old[-1]["slot"]), old[-1]["assignment"], "replacement"
    else:
        used = [int(r["slot"]) for r in ledger if r["kind"] == "new"]
        slot = (max(used) if used else 0) + 1
        if slot > len(schedule):
            raise Refusal(f"schedule exhausted: all {len(schedule)} slot(s) are allocated")
        assignment, kind = schedule[slot - 1], "new"
    row = {"allocated_at": now_utc(), "slot": slot, "participant": args.participant, "assignment": assignment,
           "kind": kind, "replaces": args.replaces or "", "schedule_sha256": digest}
    append_ledger(Path(args.ledger), row)
    note = f" (replaces {args.replaces}; log the replacement as a deviation)" if args.replaces else ""
    return {"participant": args.participant, "slot": slot, "assignment": assignment, "kind": kind,
            "message": f"{args.participant} -> slot {slot}: {assignment}{note}"}


def cmd_verify(args) -> dict:
    findings: list[str] = []
    schedule_path = Path(args.schedule)
    schedule = read_schedule(schedule_path)
    digest = sha256_text(schedule_path)
    side = sidecar_path(schedule_path)
    reproducible = None
    if side.exists():
        meta = json.loads(side.read_text(encoding="utf-8"))
        if meta.get("sha256") != digest:
            findings.append("schedule hash differs from the one recorded at generation")
        params = {k: meta[k] for k in ("scheme", "participants", "seed", "conditions", "groups", "block_size")
                  if k in meta}
        try:
            reproducible = build_schedule(params) == schedule
        except (KeyError, UsageError):
            reproducible = False
        if not reproducible:
            findings.append("the schedule is not what its recorded scheme and seed produce")
    else:
        findings.append("no schedule.csv.json next to the schedule: seed and generation hash are not recorded")
    if args.expect_sha256 and args.expect_sha256.lower() != digest:
        findings.append("schedule hash differs from --expect-sha256 (the hash recorded in the plan/preregistration)")
    ledger = read_ledger(Path(args.ledger)) if args.ledger else []
    seen: set[str] = set()
    occupant: dict[int, str] = {}
    expected_slot = 1
    for row in ledger:
        if row.get("schedule_sha256") != digest:
            findings.append(f"ledger row for {row.get('participant')} carries another schedule hash")
        if row["participant"] in seen:
            findings.append(f"{row['participant']} appears twice in the ledger")
        seen.add(row["participant"])
        slot = int(row["slot"])
        if slot < 1 or slot > len(schedule) or row["assignment"] != schedule[slot - 1]:
            findings.append(f"ledger slot {slot} for {row['participant']} does not match the schedule")
        if row["kind"] == "new":
            if slot != expected_slot:
                findings.append(f"slot {slot} handed out where slot {expected_slot} was next (skipped or reused)")
            expected_slot = max(expected_slot, slot) + 1
        elif row["kind"] == "replacement":
            if row.get("replaces") not in seen:
                findings.append(f"{row['participant']} replaces {row.get('replaces')!r}, who was never allocated")
        occupant[slot] = row["participant"]
    counts: dict[str, int] = {}
    for slot in occupant:
        assignment = schedule[slot - 1] if 0 < slot <= len(schedule) else "?"
        counts[assignment] = counts.get(assignment, 0) + 1
    return {"sha256": digest, "slots": len(schedule), "allocated_slots": len(occupant),
            "reproducible_from_seed": reproducible, "counts": counts, "findings": findings}


# ------------------------------------------------------------------ main


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser = argparse.ArgumentParser(
        description="Seeded allocation and counterbalancing ledger for non-clinical studies (not for clinical trials).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", parents=[common], help="build the whole schedule once from a seed")
    gen.add_argument("--scheme", required=True, choices=["williams", "latin", "full", "block"])
    gen.add_argument("--conditions", nargs="+", help="condition labels (order schemes)")
    gen.add_argument("--groups", nargs="+", help="group labels (block scheme)")
    gen.add_argument("--block-size", type=int, help="block size for --scheme block (default 2 x groups)")
    gen.add_argument("--participants", type=int, required=True, help="number of slots to generate")
    gen.add_argument("--seed", type=int, required=True, help="integer seed - record it")
    gen.add_argument("--out", required=True, help="schedule CSV path (must not exist)")
    nxt = sub.add_parser("next", parents=[common], help="allocate the next slot to one participant")
    nxt.add_argument("--schedule", required=True)
    nxt.add_argument("--ledger", required=True)
    nxt.add_argument("--participant", required=True, help="pseudonymous ID, e.g. sub-07")
    nxt.add_argument("--replaces", help="pseudonymous ID of the participant this one replaces (takes over the slot)")
    ver = sub.add_parser("verify", parents=[common], help="check schedule, seed and ledger; report balance")
    ver.add_argument("--schedule", required=True)
    ver.add_argument("--ledger")
    ver.add_argument("--expect-sha256", help="hash recorded in the plan or preregistration")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            result = cmd_generate(args)
        elif args.command == "next":
            result = cmd_next(args)
        else:
            result = cmd_verify(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Refusal as exc:
        if args.json:
            print(json.dumps({"refused": str(exc)}, indent=2))
        else:
            print(f"refused: {exc}")
        return 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.command == "verify":
        print(f"schedule sha256 {result['sha256']} - {result['allocated_slots']}/{result['slots']} slot(s) allocated")
        print(f"reproducible from its seed: {result['reproducible_from_seed']}")
        for assignment, count in sorted(result["counts"].items()):
            print(f"  {assignment}: {count}")
        for finding in result["findings"]:
            print(f"FINDING {finding}")
        if not result["findings"]:
            print("no problems found")
    else:
        print(result["message"])
    return 1 if args.command == "verify" and result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
