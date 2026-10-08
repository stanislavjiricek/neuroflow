#!/usr/bin/env python3
"""Find every place a participant ID reached — for an erasure request (neuroflow /ethics --erase).

The sweep only FINDS and REPORTS. It never deletes, moves or rewrites anything, and
it never prints file contents or the matching lines: only locations and counts.
The person decides what to delete. Run it in your own terminal, not through
Claude Code, so the ID and the hit list do not land in a new session transcript.

Searched:
  project       every file under the project root (path names and contents; .git/ is
                covered by the git-history check instead); large files are scanned
                in their first --head-kb only (binary headers such as EDF patient fields)
  git history   commits on all branches that add or remove the ID (git log --all -S)
  claude-code   Claude Code's local data: ~/.claude (or CLAUDE_CONFIG_DIR, plus every
                --config-dir): transcripts in projects/, history.jsonl, file-history/,
                paste-cache/, debug/, plans/, tasks/, uploads/, backups/ ...; ~/.claude.json;
                Claude Code's temp folder (session scratchpads, pasted images)
  neuroflow     ~/.neuroflow (flowie profile, personal wiki and tasks, hive caches)
  extra         every --extra DIR (exports, a server share, the acquisition PC copy)

Not searchable from here (check by hand; listed in the report): remote git hosts and
collaborators' clones, cloud drives and sync folders outside these roots, external
services (whiteboards, notebook tools, cloud documents), backups, and copies held by
the model provider under your organisation's agreement with it.

Usage:
    python <phase-data base dir>/scripts/erasure_sweep.py --id sub-07 [--id P07 ...]
        [--root DIR] [--extra DIR ...] [--config-dir DIR ...] [--no-claude]
        [--no-neuroflow-home] [--no-git] [--case-sensitive] [--max-full-mb 20]
        [--head-kb 1024] [--list-limit 200] [--json]

Matching: an ID matches when it is not glued to other letters or digits, so `sub-07`
does not match `sub-070`. Case-insensitive by default. Non-ASCII IDs (names) are also
searched in their JSON-escaped form, as they appear inside transcripts.

Exit codes:
    0  no occurrence found in any searched location
    1  occurrences found (the report lists where)
    2  usage or runtime error (no ID, an ID shorter than 3 characters, missing root)

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHUNK = 1024 * 1024
SKIP_DIRS_PROJECT = {".git"}
SKIP_DIRS_CONFIG = {"plugins"}
NOT_SEARCHED = [
    "remote git hosts (origin and other remotes, forks) and collaborators' clones",
    "the personal flowie and team hive remotes on the git host (the local caches were searched)",
    "cloud drives, sync folders and network shares outside the searched roots",
    "external services the project used (whiteboards, notebook tools, cloud documents, chat)",
    "backups and archives (institutional backup, external disks, published deposits)",
    "copies held by the model provider - governed by your organisation's agreement with it",
    "the identity key (ID-to-name list) and signed consent forms, wherever they are kept",
]


def build_patterns(ids: list[str], case_sensitive: bool) -> list[re.Pattern[bytes]]:
    flags = 0 if case_sensitive else re.IGNORECASE
    variants: set[bytes] = set()
    for ident in ids:
        variants.add(ident.encode("utf-8"))
        escaped = json.dumps(ident)[1:-1]  # \uXXXX form used inside JSON transcripts
        variants.add(escaped.encode("ascii"))
    patterns = []
    for variant in sorted(variants):
        patterns.append(re.compile(rb"(?<![A-Za-z0-9])" + re.escape(variant) + rb"(?![A-Za-z0-9])", flags))
    return patterns


def scan_file(path: Path, patterns, max_full: int | None, head: int, overlap: int) -> tuple[int, bool]:
    """Return (occurrences, head_only).

    Reads in chunks. Each chunk is searched together with the tail of the previous one,
    so a match across a chunk edge is found once, with the byte before it in view for
    the boundary check. Files larger than max_full are scanned in their first `head`
    bytes only; max_full=None scans every file in full.
    """
    size = path.stat().st_size
    head_only = max_full is not None and size > max_full
    limit = head if head_only else size
    total = 0
    carry = b""
    skip = 0  # matches starting before this index of `data` were counted in the previous round
    read = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(min(CHUNK, limit - read)) if read < limit else b""
            read += len(block)
            data = carry + block
            if not block or read >= limit:
                total += sum(1 for p in patterns for m in p.finditer(data) if m.start() >= skip)
                break
            if len(data) <= overlap + 1:
                carry = data
                continue
            cut = len(data) - overlap
            total += sum(1 for p in patterns for m in p.finditer(data) if skip <= m.start() < cut)
            carry = data[cut - 1 :]
            skip = 1
    return total, head_only


def path_matches(rel: str, patterns) -> bool:
    raw = rel.encode("utf-8", errors="replace")
    return any(p.search(raw) for p in patterns)


def sweep_tree(
    root: Path,
    scope: str,
    patterns,
    args,
    skip_dirs: set[str],
    only: list[str] | None = None,
    full_scan: bool = False,
) -> dict:
    """Search one location. full_scan=True reads every file completely (text stores such as transcripts)."""
    result = {"scope": scope, "root": str(root), "files": [], "unreadable": [], "scanned": 0, "partial": 0}
    max_full = None if full_scan else args.max_full_mb * CHUNK
    overlap = max(256, max(len(p.pattern) for p in patterns) + 2)
    if not root.exists():
        result["missing"] = True
        return result
    entries = [root / name for name in only] if only else [root]
    for entry in entries:
        if entry.is_file():
            walker = [(str(entry.parent), [], [entry.name])]
        elif entry.is_dir():
            walker = os.walk(entry, followlinks=False)
        else:
            continue
        for dirpath, dirnames, filenames in walker:
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for name in filenames:
                path = Path(dirpath) / name
                try:
                    rel = path.relative_to(root).as_posix()
                except ValueError:
                    rel = path.as_posix()
                if path.is_symlink():
                    continue
                try:
                    hits, partial = scan_file(path, patterns, max_full, args.head_kb * 1024, overlap)
                except OSError:
                    result["unreadable"].append(rel)
                    continue
                result["scanned"] += 1
                result["partial"] += int(partial)
                named = path_matches(rel, patterns)
                if hits or named:
                    result["files"].append(
                        {"path": rel, "occurrences": hits, "path_match": named, "head_only": partial}
                    )
    result["files"].sort(key=lambda f: f["path"])
    return result


def git_history(repo: Path, ids: list[str]) -> dict:
    """Count commits on all branches of `repo` that add or remove an ID (git pickaxe, case-sensitive)."""
    info = {"repo": str(repo), "available": False, "commits": 0}
    if not shutil.which("git"):
        info["reason"] = "git not found"
        return info
    probe = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, check=False
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        info["reason"] = "not a git repository"
        return info
    info["available"] = True
    commits: set[str] = set()
    for ident in ids:
        proc = subprocess.run(
            ["git", "-C", str(repo), "log", "--all", "--format=%H", f"-S{ident}"],
            capture_output=True,
            text=True,
            check=False,
        )
        commits.update(line for line in proc.stdout.splitlines() if line.strip())
    info["commits"] = len(commits)
    return info


def git_repos(root: Path, include_home: bool) -> list[Path]:
    repos = [root]
    if include_home:
        home = Path.home() / ".neuroflow"
        candidates = [home / "flowie"]
        if (home / "hives").is_dir():
            candidates += sorted(p for p in (home / "hives").iterdir() if p.is_dir())
        repos += [c for c in candidates if (c / ".git").exists()]
    return repos


def claude_roots(args) -> list[tuple[Path, list[str] | None]]:
    roots: list[tuple[Path, list[str] | None]] = []
    seen: set[str] = set()
    candidates = [Path.home() / ".claude"]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        candidates.append(Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser())
    candidates += [Path(d).expanduser() for d in args.config_dir]
    for cand in candidates:
        key = str(cand.resolve()) if cand.exists() else str(cand)
        if key in seen:
            continue
        seen.add(key)
        roots.append((cand, None))
    # ~/.claude.json sits next to ~/.claude and keeps per-project entries (history included).
    home_json = Path.home() / ".claude.json"
    if home_json.is_file():
        roots.append((home_json.parent, [home_json.name]))
    tmp_base = os.environ.get("CLAUDE_CODE_TMPDIR") or tempfile.gettempdir()
    tmp = Path(tmp_base) / "claude"
    if tmp.is_dir() and str(tmp.resolve()) not in seen:
        roots.append((tmp, None))
    return roots


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find (never delete) every location that mentions a participant ID, for an erasure request.",
    )
    parser.add_argument("--id", dest="ids", action="append", required=True,
                        help="participant ID to search for (repeat for aliases, e.g. --id sub-07 --id P07)")
    parser.add_argument("--root", help="project root (default: nearest folder with .neuroflow/, else the cwd)")
    parser.add_argument("--extra", action="append", default=[], help="another folder to search (repeatable)")
    parser.add_argument("--config-dir", action="append", default=[],
                        help="another Claude Code config dir to search (repeatable)")
    parser.add_argument("--no-claude", action="store_true", help="skip Claude Code's local data")
    parser.add_argument("--no-neuroflow-home", action="store_true", help="skip ~/.neuroflow")
    parser.add_argument("--no-git", action="store_true", help="skip the git-history check")
    parser.add_argument("--case-sensitive", action="store_true", help="match the exact case only")
    parser.add_argument("--max-full-mb", type=int, default=20, help="scan whole files up to this size (default 20)")
    parser.add_argument("--head-kb", type=int, default=1024, help="scan this much of larger files (default 1024)")
    parser.add_argument("--list-limit", type=int, default=200, help="max paths listed per location in text output")
    parser.add_argument("--allow-short", action="store_true", help="accept IDs shorter than 3 characters")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".neuroflow").is_dir():
            return candidate
    return start


def render_text(report: dict, limit: int) -> list[str]:
    lines = [
        f"Participant erasure sweep - {report['id_count']} ID(s), "
        f"{'case-sensitive' if report['case_sensitive'] else 'case-insensitive'}",
        "Locations and counts only; contents are never printed. Nothing was deleted.",
        "",
    ]
    for loc in report["locations"]:
        head = f"[{loc['scope']}] {loc['root']}"
        if loc.get("missing"):
            lines.append(f"{head}: not found")
            continue
        hits = loc["files"]
        occ = sum(f["occurrences"] for f in hits)
        named = sum(1 for f in hits if f["path_match"])
        lines.append(
            f"{head}: {len(hits)} file(s) mention an ID ({occ} occurrence(s) in contents, {named} path(s) "
            f"name one); {loc['scanned']} scanned, {loc['partial']} head-only"
        )
        for f in hits[:limit]:
            tags = []
            if f["occurrences"]:
                tags.append(f"{f['occurrences']}x")
            if f["path_match"]:
                tags.append("path")
            if f["head_only"]:
                tags.append("head-only")
            lines.append(f"    {f['path']}  ({', '.join(tags)})")
        if len(hits) > limit:
            lines.append(f"    ... {len(hits) - limit} more (use --json for the full list)")
        if loc["unreadable"]:
            lines.append(f"    {len(loc['unreadable'])} unreadable file(s) - check them by hand")
    for git in report["git"]:
        if git["available"]:
            lines.append(f"[git history] {git['repo']}: {git['commits']} commit(s) on any branch add or remove "
                         "an ID (exact case; rewriting history is a separate, deliberate step)")
        else:
            lines.append(f"[git history] {git['repo']}: not checked - {git.get('reason')}")
    lines.append("")
    lines.append("Not searched - check by hand:")
    lines += [f"  - {item}" for item in report["not_searched"]]
    lines.append("")
    lines.append(f"Total: {report['total_files']} file(s), {report['total_occurrences']} occurrence(s), "
                 f"{report['total_commits']} commit(s)")
    return lines


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    ids = [i.strip() for i in args.ids if i and i.strip()]
    if not ids:
        print("error: give at least one --id", file=sys.stderr)
        return 2
    short = [i for i in ids if len(i) < 3]
    if short and not args.allow_short:
        print("error: IDs shorter than 3 characters match almost everything; use the full ID "
              "(e.g. sub-07) or pass --allow-short", file=sys.stderr)
        return 2
    root = Path(args.root) if args.root else find_root(Path.cwd())
    if not root.is_dir():
        print(f"error: project root not found: {root}", file=sys.stderr)
        return 2
    patterns = build_patterns(ids, args.case_sensitive)
    locations = [sweep_tree(root, "project", patterns, args, SKIP_DIRS_PROJECT)]
    for extra in args.extra:
        locations.append(sweep_tree(Path(extra).expanduser(), "extra", patterns, args, set()))
    if not args.no_claude:
        for croot, only in claude_roots(args):
            locations.append(sweep_tree(croot, "claude-code", patterns, args, SKIP_DIRS_CONFIG, only, full_scan=True))
    if not args.no_neuroflow_home:
        home = Path.home() / ".neuroflow"
        if home.exists():
            locations.append(sweep_tree(home, "neuroflow", patterns, args, {".git"}, full_scan=True))
    gits = [] if args.no_git else [git_history(r, ids) for r in git_repos(root, not args.no_neuroflow_home)]
    total_files = sum(len(loc["files"]) for loc in locations)
    total_occ = sum(f["occurrences"] for loc in locations for f in loc["files"])
    total_commits = sum(g["commits"] for g in gits)
    report = {
        "id_count": len(ids),
        "case_sensitive": args.case_sensitive,
        "locations": locations,
        "git": gits,
        "not_searched": NOT_SEARCHED,
        "total_files": total_files,
        "total_occurrences": total_occ,
        "total_commits": total_commits,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n".join(render_text(report, args.list_limit)))
    return 1 if (total_files or total_commits) else 0


if __name__ == "__main__":
    sys.exit(main())
