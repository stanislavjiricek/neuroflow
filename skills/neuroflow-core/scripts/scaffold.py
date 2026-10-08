#!/usr/bin/env python3
"""Idempotent neuroflow project scaffold (neuroflow-core).

Creates the `.neuroflow/` project memory tree with the project_config.md
frontmatter contract, the merge-safety `.gitattributes` lines, the sharing-tier
`.gitignore` lines and the project instruction block in `.claude/CLAUDE.md`.
It never overwrites an existing file: it only creates what is missing, appends
missing lines, and reports everything it did.

Usage:
    python <neuroflow-core base dir>/scripts/scaffold.py [--root DIR]
        [--project-name NAME] [--plugin-version X.Y.Z] [--dry-run] [--json]

Exit codes:
    0  scaffold complete (created what was missing, or nothing to do)
    1  complete, but something needs the person's attention: a legacy
       project_config.md dialect or an older neuroflow block in
       .claude/CLAUDE.md (offer /neuroflow:migrate)
    2  refused or failed: home directory, filesystem root, nested project,
       config written by a newer neuroflow, unwritable path, bad arguments

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SCHEMA_VERSION = 1

# Contract C4: union merge for append-only project memory.
GITATTRIBUTES_LINES = [
    ".neuroflow/reasoning/*.jsonl merge=union",
    ".neuroflow/sessions/*.md merge=union",
    ".neuroflow/fails/*.md merge=union",
    ".neuroflow/preregistration/deviations.md merge=union",
    ".neuroflow/data-analyze/multiverse.md merge=union",
]
GITATTRIBUTES_HEADER = "# neuroflow: union merge for append-only project memory (neuroflow-core, Merge safety)"

# Contract C5: local-tier paths are never committed.
GITIGNORE_LINES = [
    ".neuroflow/sessions/",
    ".neuroflow/review/",
    ".neuroflow/integrations.json",
    ".neuroflow/flowie/",
    ".neuroflow/paper/xray-*",
    ".neuroflow/wiki/.pending/",
]
GITIGNORE_HEADER = "# neuroflow: local-only project memory, never committed (neuroflow-core, Sharing tiers)"

# Contract C12: the static project instruction block. It must stay identical to the
# block under "Project instruction block" in skills/neuroflow-core/SKILL.md (a test checks it).
CLAUDE_BLOCK = """## neuroflow

This project uses neuroflow, a Claude Code plugin. Project memory is in `.neuroflow/`.

- Read `.neuroflow/project_config.md` (its frontmatter holds `active_phase` and the other project facts) and `.neuroflow/flow.md` at the start of every session.
- Record project decisions in `.neuroflow/reasoning/`, not in Claude's auto-memory.
- Keep this block static: no phase or other changing facts here.
"""

NEUROFLOW_BLOCK_RE = re.compile(r"^##\s+neuroflow\s*$", re.IGNORECASE | re.MULTILINE)
STALE_BLOCK_RE = re.compile(r"^\s*[-*]?\s*(\*\*)?active[ _]phase(\*\*)?\s*:", re.IGNORECASE | re.MULTILINE)

WIKI_PAGE_DIRS = ["concepts", "entities", "sources", "synthesis", "methods"]


# ---------------------------------------------------------------------------
# Helpers shared with migrate.py (one home per helper, contract C10)
# ---------------------------------------------------------------------------


def plugin_root() -> Path:
    """The installed plugin folder: <plugin>/skills/neuroflow-core/scripts/scaffold.py."""
    return Path(__file__).resolve().parents[3]


def installed_plugin_version() -> str | None:
    """Version from the installed plugin's manifest, or None if it cannot be read."""
    manifest = plugin_root() / ".claude-plugin" / "plugin.json"
    try:
        version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        return None
    return version if isinstance(version, str) and version else None


def _resolve(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path.expanduser().absolute()


def find_project_root(start: Path, home: Path) -> Path | None:
    """Walk up from `start` to the first folder whose .neuroflow/ holds project_config.md.

    Stops at the git repository root and never looks at or above the home
    directory: `~/.neuroflow/` is the user-level folder, never project memory.
    """
    current, home = _resolve(start), _resolve(home)
    while True:
        if current == home:
            return None
        if (current / ".neuroflow" / "project_config.md").is_file():
            return current
        if (current / ".git").exists() or current.parent == current:
            return None
        current = current.parent


def ancestor_project(root: Path, home: Path) -> Path | None:
    """A project that already encloses `root` (scaffolding here would nest a second one)."""
    root = _resolve(root)
    if (root / ".git").exists() or root.parent == root:
        return None
    return find_project_root(root.parent, home)


def read_text(path: Path) -> str:
    """File text with its original line endings (callers detect CRLF and keep it)."""
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def detect_newline(text: str | None) -> str:
    return "\r\n" if text and "\r\n" in text else "\n"


def write_text(path: Path, text: str, newline: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n")
    if newline != "\n":
        text = text.replace("\n", newline)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def missing_lines(path: Path, wanted: list[str]) -> list[str]:
    """Lines of `wanted` not yet present (exact match after stripping) in `path`."""
    if not path.exists():
        return list(wanted)
    present = {line.strip() for line in read_text(path).splitlines()}
    return [line for line in wanted if line not in present]


def append_lines_text(existing: str | None, header: str, lines: list[str]) -> str:
    """The file text with a header comment and `lines` appended (LF; write_text restores CRLF)."""
    body = (existing or "").replace("\r\n", "\n")
    if body and not body.endswith("\n"):
        body += "\n"
    if body:
        body += "\n"
    return body + "\n".join([header, *lines]) + "\n"


def neuroflow_block_span(text: str) -> tuple[int, int] | None:
    """(start, end) offsets of the `## neuroflow` block (up to the next # or ## heading), or None."""
    m = NEUROFLOW_BLOCK_RE.search(text)
    if not m:
        return None
    nxt = re.compile(r"^#{1,2}\s", re.MULTILINE).search(text, m.end())
    return m.start(), (nxt.start() if nxt else len(text))


def block_is_stale(block: str) -> bool:
    """An older neuroflow block names an active phase, a volatile fact the static block never holds."""
    return STALE_BLOCK_RE.search(block) is not None


def split_frontmatter(text: str) -> tuple[list[str], str] | None:
    """(frontmatter lines, body) when the text opens with a --- block, else None."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None


def schema_of(text: str) -> int | str | None:
    """nf_schema from the frontmatter: int, the raw string if it is not an integer, or None."""
    split = split_frontmatter(text)
    if split is None:
        return None
    for line in split[0]:
        m = re.match(r"^nf_schema:\s*(.*?)\s*(#.*)?$", line)
        if m:
            raw = m.group(1).strip("'\"")
            return int(raw) if raw.isdigit() else raw
    return None


def yaml_scalar(value: str, in_flow: bool = False) -> str:
    """Quote a string for YAML only when a plain scalar would be misread."""
    if value == "":
        return '""'
    specials = {"true", "false", "yes", "no", "on", "off", "null", "~", "y", "n"}
    needs = (
        value != value.strip()
        or value[0] in "-?:,[]{}#&*!|>'\"%@`"
        or ": " in value
        or value.endswith(":")
        or " #" in value
        or value.lower() in specials
        or re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", value) is not None
        or (in_flow and any(ch in value for ch in ",[]{}"))
    )
    if not needs:
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def config_text(project_name: str, plugin_version: str | None) -> str:
    lines = [
        "---",
        f"nf_schema: {SCHEMA_VERSION}",
        f"project_name: {yaml_scalar(project_name)}",
        "active_phase: setup",
        "recommended_phases: []",
    ]
    if plugin_version:
        lines.append(f"plugin_version: {yaml_scalar(plugin_version)}")
    lines += [
        "---",
        "",
        "# Project config",
        "",
        "Setup in progress: `/neuroflow` fills in the facts above and the notes below after its interview.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------


def plan_files(project_name: str, plugin_version: str | None, today: str) -> dict[str, str]:
    """Relative path -> content for every file the scaffold creates when it is missing."""
    files = {
        ".neuroflow/project_config.md": config_text(project_name, plugin_version),
        ".neuroflow/flow.md": (
            "| File / Folder | Description | Last changed |\n"
            "|---|---|---|\n"
            f"| project_config.md | Project facts (frontmatter) and notes. | {today} |\n"
            f"| sessions/ | Daily session logs (local only, gitignored). | {today} |\n"
            f"| reasoning/ | Per-phase decision logs (JSON Lines). | {today} |\n"
            f"| tasks/ | Project task board, one file per task (see /tasks). | {today} |\n"
            f"| wiki/ | Project wiki scaffold (initialised by /wiki). | {today} |\n"
        ),
        ".neuroflow/sessions/.gitkeep": "",
        ".neuroflow/tasks/.gitkeep": "",
        ".neuroflow/reasoning/flow.md": (
            "| File / Folder | Description | Last changed |\n"
            "|---|---|---|\n"
            f"| general.jsonl | Project-level decision log (JSON Lines). | {today} |\n"
        ),
        ".neuroflow/reasoning/general.jsonl": "",
        ".neuroflow/wiki/index.md": "",
        ".neuroflow/wiki/log.md": "",
        ".neuroflow/wiki/schema.md": "",
        ".neuroflow/wiki/raw/.gitkeep": "",
    }
    for sub in WIKI_PAGE_DIRS:
        files[f".neuroflow/wiki/pages/{sub}/.gitkeep"] = ""
    return files


def scaffold(root: Path, home: Path, project_name: str | None, plugin_version: str | None,
             dry_run: bool = False) -> dict:
    report: dict = {"root": str(_resolve(root)), "dry_run": dry_run, "created": [], "appended": {},
                    "existing": [], "notes": [], "warnings": [], "errors": []}

    def refuse(msg: str) -> dict:
        report["errors"].append(msg)
        report["exit_code"] = 2
        return report

    if not root.is_dir():
        return refuse(f"{root} is not a directory")
    if _resolve(root) == _resolve(home):
        return refuse("refusing to scaffold in the home directory: ~/.neuroflow/ there is the "
                      "user-level folder, not a project. Run from the project folder.")
    if _resolve(root).parent == _resolve(root):
        return refuse("refusing to scaffold at the filesystem root. Run from the project folder.")
    outer = ancestor_project(root, home)
    if outer is not None:
        return refuse(f"{outer} already holds .neuroflow/ project memory and encloses this folder. "
                      "Work from that project instead of nesting a second one.")
    nf = root / ".neuroflow"
    if nf.exists() and not nf.is_dir():
        return refuse(".neuroflow exists but is not a folder")

    config = nf / "project_config.md"
    if config.is_file():
        schema = schema_of(read_text(config))
        if isinstance(schema, int) and schema > SCHEMA_VERSION:
            return refuse(f"project_config.md has nf_schema {schema}, newer than this neuroflow knows "
                          f"({SCHEMA_VERSION}); nothing written. Update the neuroflow plugin.")
        if schema is None:
            report["notes"].append("project_config.md uses a legacy dialect (no nf_schema frontmatter); "
                                   "left untouched. Offer /neuroflow:migrate.")
    if plugin_version is None:
        report["warnings"].append("could not read the plugin version; plugin_version left out of a new "
                                  "project_config.md")

    today = date.today().isoformat()
    try:
        for rel, content in plan_files(project_name or "(setup in progress)", plugin_version, today).items():
            target = root / rel
            if target.exists():
                report["existing"].append(rel)
                continue
            report["created"].append(rel)
            if not dry_run:
                write_text(target, content)

        for rel, header, wanted in ((".gitattributes", GITATTRIBUTES_HEADER, GITATTRIBUTES_LINES),
                                    (".gitignore", GITIGNORE_HEADER, GITIGNORE_LINES)):
            target = root / rel
            missing = missing_lines(target, wanted)
            if not missing:
                report["existing"].append(rel)
                continue
            existing = read_text(target) if target.exists() else None
            if existing is None:
                report["created"].append(rel)
            else:
                report["appended"][rel] = len(missing)
            if not dry_run:
                write_text(target, append_lines_text(existing, header, missing), detect_newline(existing))

        claude, rel = root / ".claude" / "CLAUDE.md", ".claude/CLAUDE.md"
        if not claude.exists():
            report["created"].append(rel)
            if not dry_run:
                write_text(claude, CLAUDE_BLOCK)
        else:
            text = read_text(claude)
            span = neuroflow_block_span(text)
            if span is None:
                report["appended"][rel] = CLAUDE_BLOCK.count("\n")
                if not dry_run:
                    body = text.replace("\r\n", "\n")
                    if body and not body.endswith("\n"):
                        body += "\n"
                    write_text(claude, body + ("\n" if body else "") + CLAUDE_BLOCK, detect_newline(text))
            else:
                report["existing"].append(rel)
                if block_is_stale(text[span[0]:span[1]]):
                    report["notes"].append(".claude/CLAUDE.md has an older neuroflow block that names a phase; "
                                           "left untouched. Offer /neuroflow:migrate, which replaces it.")
    except OSError as exc:
        return refuse(f"write failed: {exc}")

    report["exit_code"] = 1 if report["notes"] else 0
    return report


def print_human(report: dict) -> None:
    head = "neuroflow scaffold" + (" (dry run, nothing written)" if report["dry_run"] else "")
    print(f"{head}: {report['root']}")
    for err in report["errors"]:
        print(f"  refused: {err}")
    if report["errors"]:
        return
    for rel in report["created"]:
        print(f"  {'would create' if report['dry_run'] else 'created'}: {rel}")
    for rel, n in report["appended"].items():
        print(f"  {'would append' if report['dry_run'] else 'appended'}: {rel} (+{n} lines)")
    if report["existing"]:
        print(f"  already present, left untouched: {len(report['existing'])} item(s)")
    for note in report["notes"]:
        print(f"  attention: {note}")
    for warning in report["warnings"]:
        print(f"  warning: {warning}")
    if not report["created"] and not report["appended"]:
        print("  nothing to do: the scaffold is complete")


def utf8_stdio() -> None:
    """Make stdout and stderr UTF-8, so a path in any script survives a Windows pipe."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(
        description="Create the neuroflow project scaffold. Never overwrites an existing file.")
    ap.add_argument("--root", default=".", help="project folder (default: current directory)")
    ap.add_argument("--project-name", help="project_name written into a new project_config.md")
    ap.add_argument("--plugin-version", help="override the version read from the installed plugin.json")
    ap.add_argument("--home", help=argparse.SUPPRESS)  # tests only: stands in for the home directory
    ap.add_argument("--dry-run", action="store_true", help="show what would be created; write nothing")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    home = Path(args.home) if args.home else Path.home()
    version = args.plugin_version or installed_plugin_version()
    report = scaffold(Path(args.root).expanduser(), home, args.project_name, version, args.dry_run)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
