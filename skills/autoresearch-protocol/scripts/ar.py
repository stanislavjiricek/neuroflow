#!/usr/bin/env python3
"""Transaction bookkeeping for a neuroflow autoresearch loop.

Each bookkeeping step of an iteration is one call, so the snapshots in history/,
the results.md table and the __thetask__.md counters never drift apart.

    python ar.py init    LOOP [--column NAME ...]
    python ar.py begin   LOOP
    python ar.py status  LOOP
    python ar.py keep    LOOP --iter N --delta D [--focus TEXT] [--value V ...]
    python ar.py revert  LOOP --iter N --verdict WORSE|"NO CHANGE" --delta D [--focus TEXT] [--value V ...]
    python ar.py restore LOOP
    python ar.py adopt   LOOP --iter N [--focus TEXT] [--value V ...]

LOOP is the loop folder ({name}_autoresearch/). Tracked files come from its
__thetask__.md, caps from the "## Loop configuration" block of its program.md.
Add --json to any subcommand for machine-readable output.

Every file is replaced atomically (written to a temporary file, then renamed),
snapshots are built in a temporary folder and renamed into place, and running
the same keep/revert/adopt call again (same --iter) is safe: finished steps are
detected and skipped, and a recorded iteration is never touched twice.

Exit codes: 0 = done / nothing to report, 1 = findings (status: a cap is reached
or the loop state needs attention), 2 = usage or runtime error (the call was
refused; nothing was half-written).

Stdlib only, Python 3.10+. Part of the neuroflow autoresearch-protocol skill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path, PurePosixPath

PLATEAU_REVERTS = 5  # REVERTED rows in a row that signal a plateau: change approach, never stop
LOCK_WAIT_SECONDS = 10.0
LOCK_STALE_SECONDS = 300.0
MANIFEST = ".ar-manifest.json"
DASH = "—"  # em dash, as results.md uses it
BASE_COLUMNS = ["#", "Verdict", "Δ", "Running", "Decision", "Next focus"]
NO_CAP = {"", "none", "n/a", "na", "off", "no", "-", DASH, "unlimited"}
REVERT_VERDICTS = ("WORSE", "NO CHANGE")
UNIT = re.compile(r"(d|days?|h|hrs?|hours?|m|mins?|minutes?|s|secs?|seconds?)?")
UNIT_SECONDS = {"d": 86400.0, "h": 3600.0, "m": 60.0, "s": 1.0, "": 3600.0}  # a bare number means hours


class ArError(Exception):
    """The call was refused or failed (exit code 2)."""


def finding(kind: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "detail": detail}


# --------------------------------------------------------------------------- files


def read_text(path: Path) -> tuple[str, str]:
    """Return the file's text with '\\n' newlines, and the newline style it uses."""
    raw = path.read_bytes().decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), eol


def replace_path(src: Path, dst: Path) -> None:
    """os.replace with retries: on Windows an editor, indexer or antivirus may hold dst briefly."""
    for attempt in range(6):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == 5:
                raise ArError(f"could not replace {dst}: it is in use - close it and run the same call again") from None
            time.sleep(0.1 * 2**attempt)


def write_text(path: Path, text: str, eol: str = "\n") -> None:
    """Atomically replace path with text, written with the given newline style."""
    tmp = path.with_name(f".{path.name}.ar-tmp")
    tmp.write_bytes(text.replace("\n", eol).encode("utf-8"))
    try:
        replace_path(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def copy_file(src: Path, dst: Path) -> None:
    """Atomically replace dst with a byte-exact copy of src (binary-safe, keeps the timestamp)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.ar-tmp")
    shutil.copy2(src, tmp)
    try:
        replace_path(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return stamp if stamp.tzinfo else stamp.astimezone()


def fmt_seconds(seconds: float) -> str:
    hours, minutes = divmod(int(seconds // 60), 60)
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"


class LoopLock:
    """history/.ar-lock - one bookkeeping call at a time per loop (mkdir is atomic)."""

    def __init__(self, history: Path) -> None:
        self.path = history / ".ar-lock"

    def __enter__(self) -> LoopLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                pass
            try:
                age = time.time() - self.path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > LOCK_STALE_SECONDS:  # left behind by a call that was killed
                try:
                    os.rmdir(self.path)
                    continue
                except OSError:
                    pass
            if time.monotonic() >= deadline:
                raise ArError(
                    "another ar.py call is working on this loop (history/.ar-lock) - wait for it, "
                    "or delete that folder if no ar.py is running"
                )
            time.sleep(0.2)

    def __exit__(self, *exc: object) -> None:
        try:
            os.rmdir(self.path)
        except OSError:
            pass


# --------------------------------------------------------------------------- markdown

HEADING = re.compile(r"^#{1,2}\s")
TABLE_LINE = re.compile(r"^\s*\|")
CONFIG_LINE = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$")


def find_section(lines: list[str], heading: str) -> tuple[int, int] | None:
    """(first, end) line indices of the body under a '## heading' line; end is exclusive."""
    want = heading.strip().lower()
    for i, line in enumerate(lines):
        if line.strip().lower() == want:
            j = i + 1
            while j < len(lines) and not HEADING.match(lines[j]):
                j += 1
            return i + 1, j
    return None


def section_body(text: str, heading: str) -> list[str] | None:
    lines = text.split("\n")
    span = find_section(lines, heading)
    return None if span is None else lines[span[0] : span[1]]


def first_value(body: list[str] | None) -> str | None:
    for line in body or []:
        value = line.strip().strip("`").strip()
        if value and not value.startswith("<!--"):
            return value
    return None


def set_section(text: str, heading: str, body: list[str]) -> str:
    """Replace the whole body under heading; append the section if it is missing."""
    lines = text.split("\n")
    span = find_section(lines, heading)
    if span is None:
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join([*lines, "", heading, *body, ""])
    first, end = span
    lines[first:end] = [*body, ""]
    return "\n".join(lines)


def set_value(text: str, heading: str, value: str) -> str:
    """Replace the first value line under heading, keeping anything else in the section."""
    lines = text.split("\n")
    span = find_section(lines, heading)
    if span is None:
        return set_section(text, heading, [value])
    first, end = span
    for i in range(first, end):
        line = lines[i].strip()
        if line and not line.startswith("<!--"):
            lines[i] = value
            return "\n".join(lines)
    lines.insert(first, value)
    return "\n".join(lines)


def split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", inner)]


def clean_cell(text: str) -> str:
    text = " ".join(str(text).replace("|", "/").split())
    return text or DASH


def fmt_delta(delta: int) -> str:
    return "0" if delta == 0 else f"{delta:+d}"


# --------------------------------------------------------------------------- loop files


def normalize_tracked(entry: str) -> str:
    entry = entry.strip().replace("\\", "/")
    while entry.startswith("./"):
        entry = entry[2:]
    return entry


def parse_tracked(thetask_text: str) -> list[str]:
    body = section_body(thetask_text, "## Tracked files")
    if body is None:
        raise ArError("__thetask__.md has no '## Tracked files' section")
    tracked: list[str] = []
    for line in body:
        item = line.strip()
        if not item.startswith(("-", "*")):
            continue
        item = item[1:].strip()
        quoted = re.search(r"`([^`]+)`", item)
        path = normalize_tracked(quoted.group(1) if quoted else re.split(rf"\s+(?:{DASH}|#)\s*", item)[0])
        if path and path not in tracked:
            tracked.append(path)
    if not tracked:
        raise ArError("no tracked files listed under '## Tracked files' in __thetask__.md")
    return tracked


def normalize_snapshot(value: str | None) -> str | None:
    found = re.search(r"(?:^|/)(v\d+)(?:/|\b)", (value or "").replace("\\", "/"))
    return f"history/{found.group(1)}/" if found else None


def read_counters(thetask_text: str) -> dict[str, object]:
    best = normalize_snapshot(first_value(section_body(thetask_text, "## Current best snapshot")))
    iterations = re.match(r"\s*(\d+)", first_value(section_body(thetask_text, "## Iterations run")) or "")
    run: dict[str, str] = {}
    for line in section_body(thetask_text, "## Current run") or []:
        pair = re.match(r"^\s*[-*]?\s*([A-Za-z ]+?)\s*:\s*(.+?)\s*$", line)
        if pair:
            run[pair.group(1).lower()] = pair.group(2)
    return {
        "best": best,
        "iterations": int(iterations.group(1)) if iterations else None,
        "run_started": run.get("started"),
        "run_iterations_at_start": run.get("iterations at start"),
    }


def loop_config(program_text: str) -> dict[str, str]:
    config: dict[str, str] = {}
    for line in section_body(program_text, "## Loop configuration") or []:
        pair = CONFIG_LINE.match(line)
        if pair:
            config[pair.group(1).lower()] = re.split(r"\s+#", pair.group(2), maxsplit=1)[0].strip()
    return config


def parse_count(value: str) -> int | None:
    """'50' -> 50; 'none' -> None (no cap)."""
    text = value.strip().lower()
    if text in NO_CAP:
        return None
    count = int(text)
    if count <= 0:
        raise ValueError(value)
    return count


def parse_duration(value: str) -> float | None:
    """'8h', '90m', '2h30m', '1.5h', '45 min', '1d' -> seconds; a bare number means hours; 'none' -> None."""
    text = value.strip().lower()
    if text in NO_CAP:
        return None
    compact = re.sub(r"\s+", "", text)
    parts = re.findall(r"(\d+(?:\.\d+)?)([a-z]*)", compact)
    if "".join(number + unit for number, unit in parts) != compact or not parts:
        raise ValueError(value)
    if len(parts) > 1 and any(unit == "" for _, unit in parts):
        raise ValueError(value)  # '2h30' is ambiguous
    total = 0.0
    for number, unit in parts:
        if not UNIT.fullmatch(unit):
            raise ValueError(value)
        total += float(number) * UNIT_SECONDS[unit[:1]]
    if total <= 0:
        raise ValueError(value)
    return total


class Results:
    """The iteration table in results.md."""

    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise ArError("results.md not found - run ar.py init first")
        self.path = path
        text, self.eol = read_text(path)
        self.lines = text.split("\n")
        header = next(
            (i for i, line in enumerate(self.lines) if TABLE_LINE.match(line) and split_row(line)[0] == "#"),
            None,
        )
        if header is None:
            raise ArError("results.md has no iteration table (a header row starting with '| # |')")
        self.columns = split_row(self.lines[header])
        if len(self.columns) < len(BASE_COLUMNS):
            raise ArError(f"the results.md table needs at least the columns {' | '.join(BASE_COLUMNS)}")
        self.rows: list[list[str]] = []
        i = header + 1
        while i < len(self.lines) and TABLE_LINE.match(self.lines[i]):
            cells = split_row(self.lines[i])
            if cells and cells[0].isdigit():
                self.rows.append(cells)
            i += 1
        self.end = i

    def row(self, number: int) -> list[str] | None:
        return next((cells for cells in self.rows if int(cells[0]) == number), None)

    def last_number(self) -> int:
        return max((int(cells[0]) for cells in self.rows), default=-1)

    def last_running(self) -> int:
        if not self.rows:
            return 0
        cells = max(self.rows, key=lambda c: int(c[0]))
        try:
            return int(cells[3].replace("−", "-"))
        except (IndexError, ValueError):
            raise ArError(f"results.md row {cells[0]}: the Running value is not a number") from None

    def last_kept(self) -> int | None:
        kept = [int(c[0]) for c in self.rows if len(c) > 4 and c[4].upper().startswith("KEPT")]
        return max(kept) if kept else None

    def reverts_in_a_row(self) -> int:
        count = 0
        for cells in sorted(self.rows, key=lambda c: int(c[0]), reverse=True):
            if len(cells) <= 4 or not cells[4].upper().startswith("REVERT"):
                break
            count += 1
        return count

    def append(self, cells: list[str]) -> None:
        if len(cells) > len(self.columns):
            raise ArError(f"results.md has {len(self.columns)} columns, got {len(cells)} values - check --value")
        cells = [*cells, *([DASH] * (len(self.columns) - len(cells)))]
        self.lines.insert(self.end, "| " + " | ".join(cells) + " |")
        self.end += 1
        self.rows.append(cells)
        write_text(self.path, "\n".join(self.lines), self.eol)


class Loop:
    def __init__(self, folder: str) -> None:
        self.dir = Path(folder)
        self.thetask = self.dir / "__thetask__.md"
        if not self.thetask.is_file():
            raise ArError(f"{self.thetask} not found - LOOP must be a loop folder ({{name}}_autoresearch)")
        self.results = self.dir / "results.md"
        self.program = self.dir / "program.md"
        self.history = self.dir / "history"
        self.tracked = parse_tracked(read_text(self.thetask)[0])

    def path_of(self, tracked: str) -> Path:
        return Path(os.path.normpath(os.path.join(self.dir, tracked)))

    def config(self) -> dict[str, str]:
        return loop_config(read_text(self.program)[0]) if self.program.is_file() else {}

    def name(self) -> str:
        configured = self.config().get("loop_name", "")
        folder = self.dir.resolve().name
        return configured or (folder[: -len("_autoresearch")] if folder.endswith("_autoresearch") else folder)

    def counters(self) -> dict[str, object]:
        return read_counters(read_text(self.thetask)[0])

    def set_counters(self, iterations: int, best: str | None = None) -> None:
        text, eol = read_text(self.thetask)
        current = read_counters(text)
        updated = text
        if best is not None and current["best"] != best:
            updated = set_value(updated, "## Current best snapshot", best)
        if current["iterations"] != iterations:
            updated = set_value(updated, "## Iterations run", f"{iterations} (last: {datetime.now().date()})")
        if updated != text:
            write_text(self.thetask, updated, eol)


# --------------------------------------------------------------------------- snapshots


def vname(number: int) -> str:
    return f"v{number:03d}"


def stored_name(tracked: str) -> str:
    path = re.sub(r"^[A-Za-z]:", "", tracked.replace("\\", "/"))
    parts = [part for part in path.split("/") if part not in ("", ".", "..")]
    if not parts:
        raise ArError(f"tracked entry {tracked!r} does not name a file")
    return "/".join(parts)


def storage_plan(tracked: list[str]) -> dict[str, str]:
    """Where each tracked file goes inside a snapshot: its path without '..' parts, made unique."""
    used: set[str] = set()
    plan: dict[str, str] = {}
    for entry in tracked:
        base = stored_name(entry)
        name, k = base, 2
        while name.lower() in used or name == MANIFEST:
            name, k = f"_{k}/{base}", k + 1
        used.add(name.lower())
        plan[entry] = name
    return plan


def read_manifest(snapshot: Path) -> dict | None:
    path = snapshot / MANIFEST
    if not path.is_file():
        return None  # a snapshot made by hand, before ar.py
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ArError(f"{path} is unreadable: {exc}") from None


def snapshot_source(snapshot: Path, tracked: str, manifest: dict | None) -> tuple[Path | None, str | None]:
    """Where a tracked file sits inside a snapshot, and its recorded sha256 (None in hand-made snapshots)."""
    if manifest is not None:
        for entry in manifest.get("files", []):
            if normalize_tracked(entry.get("tracked", "")) == tracked:
                return snapshot / entry["stored"], entry.get("sha256")
        return None, None
    for candidate in (stored_name(tracked), PurePosixPath(tracked).name):
        if (snapshot / candidate).is_file():
            return snapshot / candidate, None
    return None, None


def compare(loop: Loop, snapshot: Path) -> dict[str, str]:
    """State of each tracked file against a snapshot: same | differs | missing | not-in-snapshot."""
    manifest = read_manifest(snapshot)
    states: dict[str, str] = {}
    for entry in loop.tracked:
        current = loop.path_of(entry)
        source, recorded = snapshot_source(snapshot, entry, manifest)
        if not current.is_file():
            states[entry] = "missing"
        elif source is None or not source.is_file():
            states[entry] = "not-in-snapshot"
        else:
            states[entry] = "same" if sha256(current) == (recorded or sha256(source)) else "differs"
    return states


def take_snapshot(loop: Loop, number: int) -> tuple[str, bool]:
    """Copy the tracked files into history/vNNN/. Returns (relative path, created)."""
    rel = f"history/{vname(number)}/"
    final = loop.history / vname(number)
    absent = [entry for entry in loop.tracked if not loop.path_of(entry).is_file()]
    if absent:
        raise ArError(
            f"tracked file(s) missing or not files: {', '.join(absent)} - fix __thetask__.md "
            "(ar.py tracks files, not folders); nothing was written"
        )
    if final.exists():
        if all(state == "same" for state in compare(loop, final).values()):
            return rel, False
        raise ArError(f"{rel} already exists and differs from the tracked files - refusing to overwrite a snapshot")
    tmp = loop.history / f".{vname(number)}.ar-tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    plan = storage_plan(loop.tracked)
    files = []
    for entry in loop.tracked:
        target = tmp / plan[entry]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(loop.path_of(entry), target)
        files.append({"tracked": entry, "stored": plan[entry], "sha256": sha256(target)})
    manifest = {"format": 1, "snapshot": vname(number), "created": now_iso(), "files": files}
    (tmp / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        replace_path(tmp, final)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    return rel, True


def restore(loop: Loop, snapshot_rel: str) -> list[str]:
    """Put the tracked files back to a snapshot. Every source is checked before any file is touched."""
    snapshot = loop.dir / snapshot_rel
    if not snapshot.is_dir():
        raise ArError(f"snapshot {snapshot_rel} not found - nothing was restored")
    manifest = read_manifest(snapshot)
    plan = []
    for entry in loop.tracked:
        source, recorded = snapshot_source(snapshot, entry, manifest)
        if source is None or not source.is_file():
            raise ArError(
                f"{entry} is not in {snapshot_rel} - nothing was restored "
                "(restore it by hand, or adopt the current files)"
            )
        if recorded and sha256(source) != recorded:
            raise ArError(f"{source} no longer matches its manifest (the snapshot was edited) - nothing was restored")
        plan.append((entry, source))
    changed = []
    for entry, source in plan:
        target = loop.path_of(entry)
        if target.is_file() and sha256(target) == sha256(source):
            continue
        copy_file(source, target)
        changed.append(entry)
    return changed


def best_snapshot(loop: Loop, results: Results | None, counters: dict[str, object]) -> str:
    """The best snapshot named in __thetask__.md, else the one of the last KEPT row."""
    candidates = [str(counters["best"])] if counters.get("best") else []
    if results is not None and results.last_kept() is not None:
        candidates.append(f"history/{vname(results.last_kept())}/")
    for candidate in candidates:
        if (loop.dir / candidate).is_dir():
            return candidate
    raise ArError(
        "no best snapshot found (__thetask__.md names none that exists, and no KEPT row has a history/ folder)"
        " - run ar.py init first"
    )


# --------------------------------------------------------------------------- caps


def evaluate_caps(loop: Loop, iterations: int) -> tuple[dict[str, object], list[dict[str, str]]]:
    """The caps from program.md, the current run from __thetask__.md, and every cap that is reached."""
    config, counters = loop.config(), loop.counters()
    findings: list[dict[str, str]] = []
    limits: dict[str, float | None] = {}
    for key, parse, form in (
        ("max_iterations", parse_count, "a whole number"),
        ("max_wall_clock", parse_duration, "a duration such as 8h or 90m"),
    ):
        try:
            limits[key] = parse(config.get(key, ""))
        except ValueError:
            limits[key] = None
            findings.append(finding("cap-unreadable", f"{key}: {config[key]!r} is not {form} or none"))
    if not findings and limits["max_iterations"] is None and limits["max_wall_clock"] is None:
        findings.append(
            finding(
                "no-cap",
                "program.md sets no cap (max_iterations, max_wall_clock) - ask the human for caps "
                "before the next iteration; a loop without a cap is never run",
            )
        )
    caps: dict[str, object] = {
        "max_iterations": limits["max_iterations"],
        "max_wall_clock": config.get("max_wall_clock") or None,
        "max_wall_clock_seconds": limits["max_wall_clock"],
        "max_cost": config.get("max_cost") or "n/a",
        "max_consecutive_errors": config.get("max_consecutive_errors") or "3",
        "run": None,
    }
    started = counters.get("run_started")
    try:
        start = parse_iso(str(started)) if started else None
        at_start = int(str(counters.get("run_iterations_at_start") or "0"))
    except ValueError:
        start = None
    if start is None:
        findings.append(finding("no-run", "no readable run start - run ar.py begin when the loop starts or resumes"))
        return caps, findings
    elapsed = (datetime.now().astimezone() - start).total_seconds()
    this_run = max(iterations - at_start, 0)
    caps["run"] = {"started": str(started), "iterations": this_run, "elapsed_seconds": int(elapsed)}
    max_iterations, max_wall_clock = limits["max_iterations"], limits["max_wall_clock"]
    if max_iterations is not None and this_run >= max_iterations:
        findings.append(
            finding("cap", f"max_iterations reached ({this_run} of {int(max_iterations)} this run) - stop the loop")
        )
    if max_wall_clock is not None and elapsed >= max_wall_clock:
        reached = f"{fmt_seconds(elapsed)} of {fmt_seconds(max_wall_clock)} this run"
        findings.append(finding("cap", f"max_wall_clock reached ({reached}) - stop the loop"))
    return caps, findings


def caps_line(caps: dict[str, object]) -> str:
    return (
        f"max_iterations {caps['max_iterations'] or 'none'}, max_wall_clock {caps['max_wall_clock'] or 'none'}, "
        f"max_cost {caps['max_cost']} (not measured by ar.py), "
        f"max_consecutive_errors {caps['max_consecutive_errors']}"
    )


# --------------------------------------------------------------------------- commands


def check_delta(delta: int) -> None:
    if not -5 <= delta <= 5:
        raise ArError(f"--delta {delta} is outside -5..+5")


def check_next(results: Results, number: int) -> None:
    expected = results.last_number() + 1
    if number != expected:
        raise ArError(
            f"--iter {number:03d} does not follow the last recorded iteration ({expected - 1:03d}); "
            f"the next one is {expected:03d}"
        )


def record_kept(loop: Loop, args: argparse.Namespace, verdict: str, delta: int, decision: str) -> dict[str, object]:
    """Snapshot -> row -> counters, each step skipped when a previous identical call already did it."""
    number, adopt = args.iter, args.command == "adopt"
    results = Results(loop.results)
    rel = f"history/{vname(number)}/"
    existing = results.row(number)
    if existing is not None:
        if not existing[4].upper().startswith("KEPT"):
            raise ArError(f"iteration {number:03d} is already recorded as {existing[4]} - not changing it")
        if not (loop.dir / rel).is_dir():
            raise ArError(f"iteration {number:03d} is recorded as KEPT but {rel} is missing")
        loop.set_counters(results.last_number(), rel if number == results.last_kept() else None)
        return {"iter": number, "snapshot": rel, "running": results.last_running(), "already_recorded": True}
    check_next(results, number)
    if adopt:
        best = best_snapshot(loop, results, loop.counters())
        if all(state == "same" for state in compare(loop, loop.dir / best).values()):
            raise ArError(f"the tracked files already equal the best snapshot {best} - nothing to adopt")
    rel, _ = take_snapshot(loop, number)
    running = results.last_running() + delta
    cells = [f"{number:03d}", verdict, fmt_delta(delta), str(running), decision, clean_cell(args.focus)]
    results.append([*cells, *map(clean_cell, args.value)])
    loop.set_counters(number, rel)
    return {"iter": number, "snapshot": rel, "running": running, "already_recorded": False}


def already(out: dict[str, object]) -> str:
    return " (already recorded - nothing changed)" if out["already_recorded"] else ""


def cmd_init(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        if loop.results.is_file() and Results(loop.results).last_number() > 0:
            raise ArError("this loop is past its baseline already - use status, keep or revert")
        rel, created = take_snapshot(loop, 0)
        if not loop.results.is_file():
            columns = BASE_COLUMNS + [clean_cell(name) for name in args.column]
            header = "| " + " | ".join(columns) + " |\n|" + "|".join("---" for _ in columns) + "|"
            started = datetime.now().strftime("%Y-%m-%d %H:%M")
            write_text(loop.results, f"# Autoresearch Results {DASH} {loop.name()}\nStarted: {started}\n\n{header}\n")
        results = Results(loop.results)
        if results.row(0) is None:
            results.append(["000", DASH, "0", "0", "KEPT (baseline)", DASH])
        loop.set_counters(0, rel)
    state = "created" if created else "already there"
    text = [f"baseline {rel} {state} - row 000 in results.md - best {rel}"]
    return {"snapshot": rel, "created": created, "text": text}, 0


def cmd_begin(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        iterations = max(Results(loop.results).last_number(), 0)
        text, eol = read_text(loop.thetask)
        started = now_iso()
        run = [f"started: {started}", f"iterations at start: {iterations}"]
        write_text(loop.thetask, set_section(text, "## Current run", run), eol)
    caps, findings = evaluate_caps(loop, iterations)
    text = [f"run started {started} at iteration {iterations:03d} - caps: {caps_line(caps)}"]
    text += [f"FINDING {f['kind']}: {f['detail']}" for f in findings]
    out = {"started": started, "iterations_at_start": iterations, "caps": caps, "findings": findings, "text": text}
    return out, 1 if findings else 0


def cmd_status(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    loop = Loop(args.loop)
    findings: list[dict[str, str]] = []
    notes: list[str] = []
    results = None
    try:
        results = Results(loop.results)
    except ArError as exc:
        findings.append(finding("not-initialized", str(exc)))
    counters = loop.counters()
    iterations = max(results.last_number(), 0) if results else int(counters["iterations"] or 0)
    best, states = None, {}
    try:
        best = best_snapshot(loop, results, counters)
        states = compare(loop, loop.dir / best)
    except ArError as exc:
        findings.append(finding("best-missing", str(exc)))
    for entry, state in states.items():
        if state == "missing":
            detail = f"tracked file {entry} is missing - halt and ask the human to restore it or fix __thetask__.md"
            findings.append(finding("missing", detail))
        elif state == "not-in-snapshot":
            detail = f"{entry} is not in {best} - ask the human, then ar.py adopt or fix __thetask__.md"
            findings.append(finding("not-in-best", detail))
    differs = [entry for entry, state in states.items() if state == "differs"]
    if differs:
        detail = (
            f"tracked file(s) differ from {best}: {', '.join(differs)} - before a new iteration this means one was "
            "cut off, or someone edited them: ask the human, then ar.py restore or ar.py adopt"
        )
        findings.append(finding("dirty", detail))
    last_kept = results.last_kept() if results else None
    if best and last_kept is not None and best != f"history/{vname(last_kept)}/":
        notes.append(f"best is {best}, the last KEPT row is {last_kept:03d} - fine after a deliberate re-branch")
    if results and counters["iterations"] is not None and counters["iterations"] != iterations:
        notes.append(
            f"__thetask__.md says {counters['iterations']} iterations, results.md has {iterations} - "
            "run the last keep/revert call again to sync"
        )
    caps, cap_findings = evaluate_caps(loop, iterations)
    findings.extend(cap_findings)
    reverts = results.reverts_in_a_row() if results else 0
    plateau = reverts >= PLATEAU_REVERTS
    running = results.last_running() if results else 0
    run = caps["run"]
    if isinstance(run, dict):
        this_run = f"{run['iterations']} iteration(s) in {fmt_seconds(run['elapsed_seconds'])} (since {run['started']})"
    else:
        this_run = "not started (ar.py begin)"
    clean = bool(states) and all(state == "same" for state in states.values())
    text = [
        f"loop        {loop.name()}  ({loop.dir})",
        f"iterations  {iterations} run - next {iterations + 1:03d} - best {best or 'none'} - running {running}",
        f"this run    {this_run}",
        f"caps        {caps_line(caps)}",
        f"reverts     {reverts} in a row"
        + (" - PLATEAU: change approach (a plateau is never a reason to stop)" if plateau else ""),
        f"tracked     {len(loop.tracked)} file(s)" + (" - all equal to best" if clean else ""),
        *(f"note        {note}" for note in notes),
        f"findings    {len(findings) or 'none'}",
        *(f"- {f['kind']}: {f['detail']}" for f in findings),
    ]
    out = {
        "loop": loop.name(),
        "iterations": iterations,
        "next_iter": iterations + 1,
        "best": best,
        "running": running,
        "caps": caps,
        "reverts_in_a_row": reverts,
        "plateau": plateau,
        "tracked": [{"path": entry, "state": states.get(entry, "unknown")} for entry in loop.tracked],
        "notes": notes,
        "findings": findings,
        "text": text,
    }
    return out, 1 if findings else 0


def cmd_keep(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    check_delta(args.delta)
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        out = record_kept(loop, args, "BETTER", args.delta, "KEPT")
    summary = f"snapshot {out['snapshot']} - running {out['running']}"
    out["text"] = [f"iteration {args.iter:03d} KEPT - {summary}{already(out)}"]
    return out, 0


def cmd_adopt(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        out = record_kept(loop, args, DASH, 0, "KEPT (outside edit)")
    out["text"] = [f"iteration {args.iter:03d} KEPT (outside edit) - new best {out['snapshot']}{already(out)}"]
    return out, 0


def cmd_revert(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    """Restore -> row -> counters; a recorded iteration is never restored again (newer work stays)."""
    check_delta(args.delta)
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        results = Results(loop.results)
        existing = results.row(args.iter)
        if existing is not None:
            if not existing[4].upper().startswith("REVERT"):
                raise ArError(f"iteration {args.iter:03d} is already recorded as {existing[4]} - not changing it")
            loop.set_counters(results.last_number())
            best, restored, recorded = loop.counters().get("best"), [], True
        else:
            check_next(results, args.iter)
            best = best_snapshot(loop, results, loop.counters())
            restored, recorded = restore(loop, best), False
            running = str(results.last_running())
            cells = [f"{args.iter:03d}", args.verdict, fmt_delta(args.delta), running, "REVERTED"]
            results.append([*cells, clean_cell(args.focus), *map(clean_cell, args.value)])
            loop.set_counters(args.iter)
    out: dict[str, object] = {
        "iter": args.iter,
        "best": best,
        "restored": restored,
        "running": results.last_running(),
        "already_recorded": recorded,
    }
    summary = f"restored {len(restored)} file(s) from {best} - running {out['running']}"
    out["text"] = [f"iteration {args.iter:03d} REVERTED - {summary}{already(out)}"]
    return out, 0


def cmd_restore(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    loop = Loop(args.loop)
    with LoopLock(loop.history):
        results = Results(loop.results) if loop.results.is_file() else None
        best = best_snapshot(loop, results, loop.counters())
        restored = restore(loop, best)
    detail = f": {', '.join(restored)}" if restored else " (already equal)"
    return {"best": best, "restored": restored, "text": [f"restored {len(restored)} file(s) from {best}{detail}"]}, 0


# --------------------------------------------------------------------------- cli


def verdict_arg(value: str) -> str:
    verdict = " ".join(value.replace("-", " ").replace("_", " ").upper().split())
    verdict = "NO CHANGE" if verdict == "NOCHANGE" else verdict
    if verdict not in REVERT_VERDICTS:
        raise argparse.ArgumentTypeError("use WORSE or 'NO CHANGE'")
    return verdict


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("loop", help="the loop folder ({name}_autoresearch/)")
    common.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser = argparse.ArgumentParser(
        prog="ar.py",
        description="Transaction bookkeeping for a neuroflow autoresearch loop: snapshots, restores, "
        "the results.md table, the __thetask__.md counters, and the caps.",
        epilog="Exit codes: 0 = done / nothing to report, 1 = findings (status), 2 = usage or runtime error.",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    init = sub.add_parser("init", parents=[common], help="baseline: history/v000/, row 000, counters")
    init.add_argument("--column", action="append", default=[], metavar="NAME", help="extra results.md column")
    init.set_defaults(func=cmd_init)
    begin = sub.add_parser("begin", parents=[common], help="a run starts (new loop or resume); caps count from here")
    begin.set_defaults(func=cmd_begin)
    status = sub.add_parser("status", parents=[common], help="caps, plateau, best snapshot, tracked files vs best")
    status.set_defaults(func=cmd_status)
    for name, func, summary in (
        ("keep", cmd_keep, "BETTER: snapshot to history/vNNN/, KEPT row, counters"),
        ("revert", cmd_revert, "WORSE / NO CHANGE: restore from the best snapshot, REVERTED row"),
        ("adopt", cmd_adopt, "keep outside edits as the new best (KEPT (outside edit) row)"),
    ):
        command = sub.add_parser(name, parents=[common], help=summary)
        command.add_argument("--iter", type=int, required=True, metavar="N", help="this iteration (status: 'next')")
        if name == "revert":
            command.add_argument("--verdict", type=verdict_arg, required=True, help="WORSE or 'NO CHANGE'")
        if name != "adopt":
            command.add_argument("--delta", type=int, required=True, metavar="D", help="judged delta, -5..+5")
        command.add_argument("--focus", default="", help="the Next focus column")
        command.add_argument("--value", action="append", default=[], metavar="V", help="extra column value, in order")
        command.set_defaults(func=func)
    restore_cmd = sub.add_parser("restore", parents=[common], help="put the tracked files back to the best snapshot")
    restore_cmd.set_defaults(func=cmd_restore)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        out, code = args.func(args)
    except Exception as exc:  # any failure is exit 2 - never 1, which means "findings"
        message = str(exc) if isinstance(exc, ArError) else f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps({"ok": False, "command": args.command, "error": message}))
        else:
            print(f"ar.py {args.command}: error: {message}", file=sys.stderr)
        return 2
    text = out.pop("text", [])
    if args.json:
        print(json.dumps({"ok": True, "command": args.command, **out}, indent=2))
    else:
        print("\n".join(text))
    return code


if __name__ == "__main__":
    sys.exit(main())
