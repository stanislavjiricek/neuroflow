#!/usr/bin/env python3
"""Going-public audit of a project's whole git history (phase-output).

Making a repository public publishes every commit reachable from its refs, not
just the current files: memory that was deleted later, credentials, participant
recordings and full-text PDFs are all still there. Run this before a repository
goes public (for example for a code DOI through a public repository) and before
pushing history to any new shared remote.

Classes:
    sensitive-path   a path that must not become public: local-tier memory
                     (sessions/, review/, integrations.json, flowie/,
                     paper/xray-*, wiki/.pending/), fails/, finance/, ethics/
                     files outside the non-identifying allowlist, credential
                     files (rules from export.py)
    data-file        raw recordings or images (participant data)
    paper-pdf        PDFs under a papers/ folder (full texts may not be redistributable)
    large-file       blobs larger than --large-mb (default 50)
    secret           token or private-key patterns in file content (pii_scan.py)
    personal-data    emails, phone numbers, configured ID patterns, roster names
                     in file content (pii_scan.py)
    incomplete-history  a shallow clone: older commits were not checked

Output never shows matched values - only class, path, the commit where the path
or content first appears, and a count. History cannot be cleaned automatically
and existing clones keep it; the safe route for publication is a fresh
repository built from an export.

Usage:
    python <phase-output skill base dir>/scripts/history_audit.py [--root DIR]
        [--large-mb N] [--max-scan-mb N] [--config FILE] [--roster FILE] [--json]

Exit codes:
    0  clean
    1  findings
    2  not a git repository, git failed, or bad arguments

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

DATA_SUFFIXES = (
    ".edf", ".bdf", ".gdf", ".eeg", ".vhdr", ".vmrk", ".fif", ".fif.gz", ".set", ".fdt",
    ".cnt", ".xdf", ".snirf", ".mff", ".nii", ".nii.gz", ".dcm", ".mgz",
)
BINARY_SUFFIXES = (
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".tar", ".npy", ".npz", ".mat",
    ".pkl", ".h5", ".hdf5", ".docx", ".xlsx", ".pptx", ".mp3", ".mp4", ".wav",
)
FIND_OBJECT_LIMIT = 30


class AuditError(Exception):
    """Exit code 2."""


def _sibling(name: str):
    mod_name = f"_nf_phase_output_{name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, Path(__file__).with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    try:
        out = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root,
                             input=stdin, capture_output=True, check=False)
    except OSError as e:
        raise AuditError(f"git is not available: {e}") from e
    if out.returncode != 0:
        raise AuditError(f"git {args[0]} failed: {out.stderr.decode('utf-8', 'replace').strip()}")
    return out.stdout


def path_history(root: Path) -> dict[str, list]:
    """path -> [oldest commit touching it, number of commits touching it]."""
    out = git(root, "log", "--all", "--no-renames", "--name-only", "--format=%x01%h")
    hist: dict[str, list] = {}
    current = None
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("\x01"):
            current = line[1:].strip()
        elif line.strip():
            entry = hist.setdefault(line, [current, 0])
            entry[0] = current  # git log runs newest to oldest: the last one seen is the oldest
            entry[1] += 1
    return hist


def blob_list(root: Path) -> list[tuple[str, int, str]]:
    """(sha, size, path) for every blob reachable from any ref."""
    objs = git(root, "rev-list", "--all", "--objects")
    check = git(root, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)", stdin=objs)
    blobs = []
    for line in check.decode("utf-8", "replace").splitlines():
        parts = line.split(" ", 3)
        if len(parts) == 4 and parts[1] == "blob":
            blobs.append((parts[0], int(parts[2]), parts[3]))
    return blobs


def read_blobs(root: Path, shas: list[str]):
    """Yield (sha, bytes) for each sha via one `git cat-file --batch` process."""
    if not shas:
        return
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def feed():
        try:
            proc.stdin.write("".join(f"{s}\n" for s in shas).encode())
        finally:
            proc.stdin.close()

    writer = threading.Thread(target=feed, daemon=True)
    writer.start()
    try:
        for _ in shas:
            header = proc.stdout.readline().split()
            if len(header) < 3:
                break
            size = int(header[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)  # trailing newline
            yield header[0].decode(), data
    finally:
        writer.join()
        proc.stdout.close()
        proc.wait()


def first_commit_of_blob(root: Path, sha: str) -> str | None:
    try:
        out = git(root, "log", "--all", "--format=%h", f"--find-object={sha}")
    except AuditError:
        return None
    lines = out.decode().split()
    return lines[-1] if lines else None


def lower_suffix(path: str) -> str:
    name = path.lower()
    for double in (".nii.gz", ".fif.gz"):
        if name.endswith(double):
            return double
    dot = name.rfind(".")
    return name[dot:] if dot > name.rfind("/") else ""


def audit(root: Path, large_mb: float, max_scan_mb: float, scanner) -> dict:
    rules = _sibling("export")
    git(root, "rev-parse", "--git-dir")
    try:
        head = git(root, "rev-parse", "HEAD").decode().strip()
    except AuditError:
        head = None
    shallow = git(root, "rev-parse", "--is-shallow-repository").decode().strip() == "true"
    commits = int(git(root, "rev-list", "--all", "--count").decode().strip() or 0)
    findings: list[dict] = []
    if shallow:
        findings.append({"kind": "incomplete-history", "path": "-", "first_commit": None, "count": 0,
                         "detail": "shallow clone - fetch the full history (git fetch --unshallow) and run again"})

    hist = path_history(root)
    for path, (first, count) in sorted(hist.items()):
        reason = rules.classify(path)
        suffix = lower_suffix(path)
        if reason:
            findings.append({"kind": "sensitive-path", "path": path, "first_commit": first, "count": count,
                             "detail": reason})
        elif suffix in DATA_SUFFIXES:
            findings.append({"kind": "data-file", "path": path, "first_commit": first, "count": count,
                             "detail": "recording or image file - participant data"})
        elif suffix == ".pdf" and "papers/" in f"/{path.lower()}":
            findings.append({"kind": "paper-pdf", "path": path, "first_commit": first, "count": count,
                             "detail": "full-text PDF - may not be redistributable"})

    blobs = blob_list(root)
    large = large_mb * 1024 * 1024
    max_scan = max_scan_mb * 1024 * 1024
    to_scan: dict[str, str] = {}
    for sha, size, path in blobs:
        if size > large:
            findings.append({"kind": "large-file", "path": path, "first_commit": hist.get(path, [None])[0],
                             "count": 1, "detail": f"{size / 1024 / 1024:.1f} MB blob"})
        suffix = lower_suffix(path)
        if size <= max_scan and suffix not in DATA_SUFFIXES and suffix not in BINARY_SUFFIXES:
            to_scan[sha] = path

    content: dict[tuple[str, str], list] = {}
    for sha, data in read_blobs(root, list(to_scan)):
        if b"\0" in data[:8192]:
            continue
        path = to_scan[sha]
        for _line, kind in scanner.scan_text(data.decode("utf-8", errors="replace")):
            cls = "secret" if kind.startswith("secret:") else "personal-data"
            entry = content.setdefault((cls, path), [sha, {}])
            entry[1][kind] = entry[1].get(kind, 0) + 1
    lookups = 0
    for (cls, path), (sha, kinds) in sorted(content.items()):
        first = None
        if lookups < FIND_OBJECT_LIMIT:
            first = first_commit_of_blob(root, sha)
            lookups += 1
        findings.append({"kind": cls, "path": path, "first_commit": first or hist.get(path, [None])[0],
                         "count": sum(kinds.values()),
                         "detail": ", ".join(f"{k} x{v}" for k, v in sorted(kinds.items()))})

    order = ["incomplete-history", "secret", "sensitive-path", "data-file", "personal-data", "large-file", "paper-pdf"]
    findings.sort(key=lambda f: (order.index(f["kind"]), f["path"]))
    memory = sum(1 for p in hist if rules.memory_part(p) is not None and not rules.classify(p))
    notes = []
    if memory:
        notes.append(f"{memory} team-tier .neuroflow/ paths in the history become public too "
                     "(reasoning, tasks, meetings, wiki) - the person reviews and confirms that")
    return {"head": head, "shallow": shallow, "commits": commits, "paths": len(hist), "blobs": len(blobs),
            "findings": findings, "notes": notes}


def print_human(rep: dict) -> None:
    head = rep["head"][:12] if rep["head"] else "(no commits)"
    print(f"History audit - HEAD {head}, {rep['commits']} commits, {rep['paths']} paths, "
          f"{rep['blobs']} blobs: {len(rep['findings'])} findings (values are never shown)")
    current = None
    for f in rep["findings"]:
        if f["kind"] != current:
            current = f["kind"]
            print(f"\n{current}")
        first = f" first in {f['first_commit']}" if f["first_commit"] else ""
        print(f"  {f['path']} {first} - {f['detail']}")
    for note in rep["notes"]:
        print(f"\nNote: {note}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Audit the whole git history before a repository goes public.")
    ap.add_argument("--root", default=".", help="repository folder (default: current folder)")
    ap.add_argument("--large-mb", type=float, default=50.0, help="report blobs larger than this (default 50)")
    ap.add_argument("--max-scan-mb", type=float, default=2.0,
                    help="scan the content of text blobs up to this size (default 2)")
    ap.add_argument("--config", help="pii_scan.py config (id_patterns, allow_emails, roster)")
    ap.add_argument("--roster", help="salted-hash roster from pii_scan.py --build-roster")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    pii = _sibling("pii_scan")

    def fail(msg: str) -> int:
        if args.json:
            print(json.dumps({"error": msg}, indent=2))
        else:
            print(f"history_audit: {msg}", file=sys.stderr)
        return 2

    if args.large_mb <= 0 or args.max_scan_mb < 0:
        return fail("--large-mb must be positive and --max-scan-mb not negative")
    try:
        config = pii.load_config(Path(args.config).expanduser() if args.config else None)
        scanner = pii.scanner_from_args(config, args.roster, [], root)
        rep = audit(root, args.large_mb, args.max_scan_mb, scanner)
    except (AuditError, pii.ConfigError) as e:
        return fail(str(e))
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_human(rep)
    return 1 if rep["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
