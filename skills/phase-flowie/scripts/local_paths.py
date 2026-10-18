#!/usr/bin/env python3
"""Find machine-local absolute paths in flowie files before they sync to every machine (phase-flowie → Write rules).

A flowie syncs to every machine the person uses, so a folder on one of them (C:\\Users\\…, /home/…, ~/projects/…)
means nothing on the others and tells the hosting service where the person keeps their data. Local folders live
only in ~/.neuroflow/local-projects.json, which never syncs. The flowie auto-sync hook, /flowie --sync and
/neuroflow:migrate run this check; it reports and never edits.

Flagged: a Windows drive path (C:\\… or C:/…), a UNC path (\\\\server\\share), a home or mount folder (/home/,
/Users/, /mnt/, /media/, /scratch/, /gpfs/, /lustre/, /storage/, /data/, /work/, /srv/, /net/, /nfs/, /tmp/),
a ~/ path outside ~/.neuroflow/, and any other absolute path of two or more parts inside a code span or a table
row. URLs, relative paths, slash commands (/flowie --sync) and example patterns (/storage/.../data,
~/{project}) are not paths here.

usage:
  python local_paths.py FILE [FILE ...]      check these files
  python local_paths.py --flowie DIR         check every text file of a flowie clone
  add --json for a machine-readable result

exit codes: 0 nothing found · 1 machine-local paths found · 2 usage or read error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".txt", ".csv", ".tsv", ".flow", ""}
# Files that stay on the machine (gitignored) or are git's own: never synced, so never checked.
SKIP_NAMES = {"integrations.json"}
SKIP_DIRS = {".git"}

MOUNTS = "home|Users|mnt|media|scratch|gpfs|lustre|storage|data|work|srv|net|nfs|tmp"
ALWAYS = [
    ("windows path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s|`'\")\]<>]*")),
    ("network share", re.compile(r"(?<![\\\w])\\\\[A-Za-z0-9._-]+\\[^\s|`'\")\]<>]+")),
    ("home or mount folder", re.compile(rf"(?<![\w.:/~-])/(?:{MOUNTS})/[^\s|`'\")\]<>]+")),
    ("home folder (~/)", re.compile(r"(?<![\w.:/~-])~/(?!\.neuroflow(?:/|\b))[^\s|`'\")\]<>]+")),
]
# Inside a code span or a table row, a whole token that is an absolute path of two or more parts counts.
ABSOLUTE = re.compile(r"/[^/\s]+(?:/[^/\s]+)+/?")
TOKEN_EDGES = re.compile(r"[\s|`'\"()\[\],;]+")
CODE_SPAN = re.compile(r"`([^`]+)`")
URL = re.compile(r"[a-z][a-z0-9+.-]*://\S+", re.I)
# A pattern shown as an example (/storage/.../data, ~/{project}, C:\Users\<name>), not a folder anyone has.
PLACEHOLDER = re.compile(r"\.\.\.|…|[<>{}$*]")


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def findings_in_text(text: str) -> list[dict]:
    """Every machine-local path in `text`, one entry per hit: line number, kind and the path as written."""
    out: list[dict] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = URL.sub(" ", raw)
        hits: list[tuple[str, str]] = []
        for kind, pattern in ALWAYS:
            hits += [(kind, match.group(0)) for match in pattern.finditer(line)]
        scopes = [match.group(1) for match in CODE_SPAN.finditer(line)]
        if line.lstrip().startswith("|"):
            scopes.append(line)
        for scope in scopes:
            tokens = [token.rstrip(".:") for token in TOKEN_EDGES.split(scope)]
            hits += [("absolute path", token) for token in tokens if ABSOLUTE.fullmatch(token) and ":" not in token]
        seen: set[str] = set()
        for kind, path in hits:
            if PLACEHOLDER.search(path):
                continue
            path = path.rstrip(".,;:")
            if any(path in other or other in path for other in seen):
                continue
            seen.add(path)
            out.append({"line": number, "kind": kind, "path": path})
    return out


def flowie_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or any(part in SKIP_DIRS for part in rel.parts) or path.name in SKIP_NAMES:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def check(paths: list[Path], base: Path | None) -> tuple[list[dict], list[str]]:
    results: list[dict] = []
    errors: list[str] = []
    for path in paths:
        if path.name in SKIP_NAMES:
            continue
        try:
            text = path.read_bytes().decode("utf-8", errors="replace")
        except OSError as error:
            errors.append(f"{path}: {error.strerror or error}")
            continue
        shown = path.relative_to(base).as_posix() if base is not None else path.as_posix()
        for hit in findings_in_text(text):
            results.append({"file": shown, **hit})
    return results, errors


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path, help="files to check")
    parser.add_argument("--flowie", type=Path, metavar="DIR", help="check every text file of this flowie clone")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    if args.flowie is None and not args.files:
        parser.print_usage(sys.stderr)
        print("local_paths: name files to check, or --flowie DIR", file=sys.stderr)
        return 2
    if args.flowie is not None and not args.flowie.is_dir():
        print(f"local_paths: no folder {args.flowie}", file=sys.stderr)
        return 2
    paths = flowie_files(args.flowie) if args.flowie is not None else list(args.files)
    results, errors = check(paths, args.flowie)
    if args.json:
        print(json.dumps({"findings": results, "errors": errors, "checked": len(paths)}, ensure_ascii=False, indent=2))
    else:
        for hit in results:
            print(f"{hit['file']}:{hit['line']}: {hit['kind']}: {hit['path']}")
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        if results:
            print(f"{len(results)} machine-local path(s): they belong in ~/.neuroflow/local-projects.json, which never syncs")
    if errors and not results:
        return 2
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
