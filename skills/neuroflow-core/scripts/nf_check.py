#!/usr/bin/env python3
"""nf_check - deterministic audit of a neuroflow project's memory (.neuroflow/).

The sentinel agent (/sentinel) runs this first and spends its own reading only on
the judgement checks; a mod, a git hook or CI may run the same file. It never
writes anything.

    python <plugin root>/skills/neuroflow-core/scripts/nf_check.py [--project DIR] [--json]

Exit codes: 0 = clean, 1 = findings, 2 = usage or runtime error.

Check ids are stable (agents/sentinel.md cites them):
  NF1  flow.md index: root flow.md lists every folder; each folder's flow.md lists its files
  NF2  project_config.md: frontmatter contract, nf_schema, phases, plugin_version, no personal
       keys (they belong in ~/.neuroflow/user.yaml)
  NF3  integrity status: status.md files; frozen-file hashes re-checked by
       skills/phase-preregistration/scripts/freeze.py verify; ethics approval and expiry
  NF4  reasoning logs: reasoning/*.jsonl holds one JSON object per line
  NF5  merge-conflict markers anywhere under .neuroflow/
  NF6  memory structure: only the root files and folders neuroflow-core documents
  NF7  instruction block: .claude/CLAUDE.md points at project_config.md; no stale copies
  NF8  sensitive data: delegates to skills/phase-output/scripts/pii_scan.py when installed

The documented structure, the phase list and the command names are read live from
the plugin (skills/neuroflow-core/SKILL.md and commands/*.md), so the prose stays the
source of truth. Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SUPPORTED_NF_SCHEMA = 1

CHECKS: dict[str, str] = {
    "NF1": "flow.md index",
    "NF2": "project_config.md contract",
    "NF3": "integrity status files",
    "NF4": "reasoning logs",
    "NF5": "merge-conflict markers",
    "NF6": "memory structure",
    "NF7": "instruction block",
    "NF8": "sensitive data",
}

ERROR, WARN, INFO = "error", "warn", "info"

# Folders with their own structure instead of a flow.md index: daily logs (local
# tier), the task board's columns, the wiki (index.md is its index), dated meeting files.
FLOW_EXEMPT = {"sessions", "tasks", "wiki", "meetings"}
# Always-known root entries that the root tables may not list (sharing tiers: local).
EXTRA_ROOT_FILES = {"integrations.json"}
EXTRA_ROOT_FOLDERS = {"review"}
LEGACY_ROOT_FILES = {
    "linked_flows.md": "removed in 0.2.17; cross-project links live in the flowie project registry",
    "team.md": "removed in 0.2.17; collaborators belong in project_config.md (`collaborators:`)",
}
REQUIRED_CONFIG_KEYS = ("nf_schema", "project_name", "active_phase", "recommended_phases", "plugin_version")
PERSONAL_CONFIG_KEYS = {"auto_issue_reporting", "writing_style", "researcher", "zotero"}
MODES = {"teacher", "executor", "critic"}
PREREG_STATUSES = {"draft", "frozen"}
ETHICS_STATUSES = {"none", "pending", "approved", "expired", "withdrawn"}
AI_PROCESSING = {"none", "pseudonymised", "identifiable"}
SET_BY = {"person", "model"}
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".csv", ".tsv", ".tex", ".bib", ".py", ".r", ".m"}
MAX_PER_FILE = 5


@dataclass
class Finding:
    check: str
    severity: str
    path: str
    message: str
    line: int | None = None
    fix: str = ""


# ---------------------------------------------------------------------------
# Frontmatter: a small YAML subset (scalars, inline and block lists, nested
# mappings, folded/literal blocks). Values stay strings; callers convert.
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"^(?P<key>[^\s#][^:]*?)\s*:(?:[ \t]+(?P<val>.*))?$")
_BLOCK_SCALARS = {">", "|", ">-", "|-", ">+", "|+"}


def _strip_comment(s: str) -> str:
    quote = None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " \t[,"):
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def _split_inline(s: str) -> list[str]:
    parts, buf, quote = [], [], None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _scalar(raw: str):
    s = _strip_comment(raw.strip())
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(p) for p in _split_inline(s[1:-1])]
    if s == "{}":
        return {}
    return s


def _yaml_lines(block: str) -> list[tuple[int, str]]:
    out = []
    for raw in block.splitlines():
        line = raw.replace("\t", "    ").rstrip()
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#"):
            out.append((len(line) - len(stripped), stripped))
    return out


def _is_item(text: str) -> bool:
    return text == "-" or text.startswith("- ")


def _parse_node(lines: list[tuple[int, str]]):
    if not lines:
        return None
    if _is_item(lines[0][1]):
        return _parse_seq(lines, lines[0][0])
    return _parse_map(lines, lines[0][0])


def _parse_map(lines: list[tuple[int, str]], base: int) -> dict:
    out: dict = {}
    i, n = 0, len(lines)
    while i < n:
        indent, text = lines[i]
        m = _KEY_RE.match(text) if indent == base and not _is_item(text) else None
        if not m:
            i += 1
            continue
        key = m.group("key").strip()
        if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
            key = key[1:-1]
        val = _strip_comment(m.group("val") or "")
        j, children = i + 1, []
        while j < n:
            ind, t = lines[j]
            if ind > base or (ind == base and not val and _is_item(t)):
                children.append(lines[j])
                j += 1
            else:
                break
        if val in _BLOCK_SCALARS:
            out[key] = (" " if val.startswith(">") else "\n").join(t for _, t in children)
        elif val:
            out[key] = _scalar(val)
        else:
            out[key] = _parse_node(children)
        i = j
    return out


def _parse_seq(lines: list[tuple[int, str]], base: int) -> list:
    out: list = []
    i, n = 0, len(lines)
    while i < n:
        indent, text = lines[i]
        if indent != base or not _is_item(text):
            i += 1
            continue
        item = text[1:].strip()
        j, children = i + 1, []
        while j < n and lines[j][0] > base:
            children.append(lines[j])
            j += 1
        if item and item[0] not in "\"'[" and _KEY_RE.match(item):
            child_indent = children[0][0] if children else base + 2
            out.append(_parse_map([(child_indent, item)] + children, child_indent))
        elif item:
            out.append(_scalar(item))
        else:
            out.append(_parse_node(children))
        i = j
    return out


def parse_yaml_subset(block: str) -> dict:
    lines = _yaml_lines(block)
    return _parse_map(lines, lines[0][0]) if lines else {}


def split_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Return (frontmatter or None when absent, body, error or None)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text, None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            body = "".join(lines[idx + 1:])
            return parse_yaml_subset("".join(lines[1:idx])), body, None
    return None, text, "frontmatter opens with --- but is never closed"


# ---------------------------------------------------------------------------
# What the plugin documents (read live - the prose is the source of truth)
# ---------------------------------------------------------------------------

_PHASES_RE = re.compile(r"\*\*Valid `phase:` frontmatter values:\*\*(.+)")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def canonical_phases(plugin_root: Path) -> set[str]:
    """Phase ids from neuroflow-core's phase taxonomy (empty set when not found)."""
    m = _PHASES_RE.search(_read(plugin_root / "skills" / "neuroflow-core" / "SKILL.md"))
    return set(re.findall(r"`([a-z][\w-]*)`", m.group(1))) if m else set()


def table_first_cells(text: str) -> list[str]:
    cells = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 2:
            first = s.strip("|").split("|")[0].strip()
            if first and set(first) - set("-: "):
                cells.append(first)
    return cells


def _memory_section(core: str) -> str:
    """The project `.neuroflow/` section of neuroflow-core (not the global ~/.neuroflow/ one)."""
    lines = core.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m and ".neuroflow/" in m.group(2) and "~" not in m.group(2):
            level = len(m.group(1))
            end = len(lines)
            for j in range(i + 1, len(lines)):
                h = re.match(r"^(#{1,6})\s", lines[j])
                if h and len(h.group(1)) <= level:
                    end = j
                    break
            return "\n".join(lines[i:end])
    return ""


def commands_info(plugin_root: Path) -> tuple[set[str], set[str], set[str]]:
    """(command names, .neuroflow/ folders and root files named in command frontmatter)."""
    names, folders, files = set(), set(), set()
    for path in sorted((plugin_root / "commands").glob("*.md")):
        names.add(path.stem)
        fm, _, _ = split_frontmatter(_read(path))
        for key in ("reads", "writes", "requires", "produces"):
            values = (fm or {}).get(key)
            for v in values if isinstance(values, list) else [values] if isinstance(values, str) else []:
                if not isinstance(v, str):
                    continue
                m = re.match(r"^\.neuroflow/([A-Za-z0-9_.-]+)(/?)", v.strip())
                if m:
                    (folders if m.group(2) else files).add(m.group(1))
    return names, folders, files


def documented_structure(plugin_root: Path) -> dict:
    core = _read(plugin_root / "skills" / "neuroflow-core" / "SKILL.md")
    section = _memory_section(core) or core
    files, folders = set(), set()
    for cell in table_first_cells(section):
        m = re.fullmatch(r"`([A-Za-z0-9_.-]+)(/?)`", cell)
        if not m:
            continue
        name, slash = m.groups()
        if slash:
            folders.add(name)
        elif "." in name:
            files.add(name)
    commands, cmd_folders, cmd_files = commands_info(plugin_root)
    skills = {p.parent.name for p in (plugin_root / "skills").glob("*/SKILL.md")}
    return {
        "source": "skills/neuroflow-core/SKILL.md + commands/*.md",
        "documented": bool(files or folders),
        "root_files": sorted(files | cmd_files | EXTRA_ROOT_FILES),
        "root_folders": sorted(folders | cmd_folders | EXTRA_ROOT_FOLDERS),
        "phase_folders": sorted(commands),
        "skills": sorted(skills),
        "flow_exempt": sorted(FLOW_EXEMPT),
    }


def plugin_version(plugin_root: Path) -> str | None:
    try:
        return json.loads(_read(plugin_root / ".claude-plugin" / "plugin.json")).get("version")
    except (json.JSONDecodeError, AttributeError):
        return None


def _vtuple(v) -> tuple[int, ...] | None:
    m = re.match(r"^\s*v?(\d+)\.(\d+)\.(\d+)", str(v or ""))
    return tuple(int(x) for x in m.groups()) if m else None


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


@dataclass
class Context:
    project: Path
    plugin_root: Path
    home: Path
    today: _dt.date
    run_pii: bool = True

    @property
    def nf(self) -> Path:
        return self.project / ".neuroflow"

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.project).as_posix()
        except ValueError:
            try:
                return "~/" + path.relative_to(self.home).as_posix()
            except ValueError:
                return path.as_posix()


def _same_path(a: Path, b: Path) -> bool:
    try:
        return os.path.normcase(str(a.resolve())) == os.path.normcase(str(b.resolve()))
    except OSError:
        return False


def find_project(start: Path, home: Path) -> Path | None:
    """Walk up from start to the folder holding .neuroflow/; never the home folder
    (there ~/.neuroflow/ is the global, per-user home, not project memory)."""
    start = start.resolve()
    for d in [start, *start.parents]:
        if _same_path(d, home):
            return None
        if (d / ".neuroflow").is_dir():
            return d
    return None


# ---------------------------------------------------------------------------
# NF1 - flow.md index completeness
# ---------------------------------------------------------------------------

_HEADER_CELLS = {"file / folder", "file/folder", "file", "folder", "files", "name", "path", "entry"}
_PATHLIKE_RE = re.compile(r"(\.[A-Za-z0-9]{1,6}|/)$")


def _clean_cell(cell: str) -> str:
    m = re.fullmatch(r"\[([^\]]*)\]\(([^)\s]+)\)", cell.strip())
    if m:
        cell = m.group(1) if m.group(2).startswith(("http://", "https://")) else m.group(2)
    cell = cell.strip().strip("`*").strip()
    return cell[2:] if cell.startswith("./") else cell


def parse_flow(text: str) -> tuple[list[tuple[str, int]], int]:
    """Return (index entries with line numbers, number of other tables).

    An index table has a `File / Folder`-style header, or first cells that look like
    paths. Any other table is narrative, which flow.md must not hold (neuroflow-core)."""
    blocks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 2:
            current.append((lineno, s.strip("|").split("|")[0].strip()))
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    entries: list[tuple[str, int]] = []
    other = 0
    for block in blocks:
        rows = [(n, _clean_cell(c)) for n, c in block if c and set(c) - set("-: ")]
        if not rows:
            continue
        header = rows[0][1].lower() in _HEADER_CELLS
        data = rows[1:] if header else rows
        data = [(n, c) for n, c in data if c and c not in {"-", "--"} and not c.startswith("(")]
        pathlike = sum(1 for _, c in data if _PATHLIKE_RE.search(c))
        if header or (data and pathlike * 2 >= len(data)):
            entries.extend((c, n) for n, c in data)
        else:
            other += 1
    return entries, other


def parse_flow_entries(text: str) -> list[tuple[str, int]]:
    return parse_flow(text)[0]


def _entry_candidates(entry: str, folder_rel: str) -> list[str]:
    e = entry.rstrip("/")
    cands = [e]
    if e.startswith(".neuroflow/"):
        e2 = e[len(".neuroflow/"):]
        cands.append(e2)
        if folder_rel and e2.startswith(folder_rel + "/"):
            cands.append(e2[len(folder_rel) + 1:])
    if folder_rel and e.startswith(folder_rel + "/"):
        cands.append(e[len(folder_rel) + 1:])
    return cands


def _is_listed(child: str, entries: list[tuple[str, int]], folder_rel: str) -> bool:
    for entry, _ in entries:
        for c in _entry_candidates(entry, folder_rel):
            if c == child or c.startswith(child + "/"):
                return True
    return False


def _children(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if not p.name.startswith(".") and p.name != "flow.md"
    )


def _check_flow_file(ctx: Context, folder: Path, out: list[Finding], depth: int) -> None:
    folder_rel = folder.relative_to(ctx.nf).as_posix() if folder != ctx.nf else ""
    flow = folder / "flow.md"
    shown = ctx.rel(flow)
    entries, other_tables = parse_flow(_read(flow))
    is_root = folder == ctx.nf
    if other_tables:
        out.append(Finding("NF1", WARN, shown,
                           f"holds {other_tables} table(s) that are not the file index - flow.md is a pure index",
                           fix="move the narrative into its own .md file in the folder and list that file"))
    for child in _children(folder):
        if is_root and child.is_file():
            continue  # the root index lists folders; root files are documented in neuroflow-core
        if not _is_listed(child.name, entries, folder_rel):
            kind = "folder" if child.is_dir() else "file"
            out.append(Finding("NF1", WARN, shown,
                               f"{kind} `{child.name}{'/' if child.is_dir() else ''}` exists but is not listed",
                               fix=f"add a row for `{child.name}{'/' if child.is_dir() else ''}`"))
    for entry, lineno in entries:
        if any(ch in entry for ch in "*{}<>") or "://" in entry:
            continue
        bases = [folder, ctx.nf, ctx.project]
        if not any((b / entry.rstrip("/")).exists() for b in bases):
            out.append(Finding("NF1", WARN, shown, f"lists `{entry}`, which does not exist", lineno,
                               fix="remove the row, or restore the file"))
    if depth < 3 and not is_root:  # level-1 folders are walked by check_nf1 itself
        for sub in _children(folder):
            if sub.is_dir() and (sub / "flow.md").is_file():
                _check_flow_file(ctx, sub, out, depth + 1)


def check_nf1(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    root_flow = ctx.nf / "flow.md"
    if not root_flow.is_file():
        out.append(Finding("NF1", WARN, ".neuroflow/flow.md", "the root index flow.md is missing",
                           fix="create it with one row per folder"))
    else:
        _check_flow_file(ctx, ctx.nf, out, 0)
    for folder in sorted(p for p in ctx.nf.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if folder.name in FLOW_EXEMPT:
            continue
        if not (folder / "flow.md").is_file():
            out.append(Finding("NF1", WARN, ctx.rel(folder) + "/", "folder has no flow.md index",
                               fix="create flow.md with one row per file"))
            continue
        _check_flow_file(ctx, folder, out, 1)
    return out


# ---------------------------------------------------------------------------
# NF2 - project_config.md contract
# ---------------------------------------------------------------------------


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def legacy_config_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*]\s+)?\*\*([^*]+?):?\*\*:?\s*(.+?)\s*$", line)
        if m:
            fields.setdefault(_slug(m.group(1)), m.group(2))
            continue
        m = re.match(r"^\s*([a-z_][a-z0-9_]*)\s*:\s*(\S.*?)\s*$", line)
        if m:
            fields.setdefault(m.group(1), m.group(2))
    return fields


def _as_list(v) -> list:
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [v]


def check_nf2(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    path = ctx.nf / "project_config.md"
    shown = ctx.rel(path)
    if not path.is_file():
        return [Finding("NF2", ERROR, shown, "project_config.md is missing", fix="run /neuroflow")]
    text = _read(path)
    fm, _, err = split_frontmatter(text)
    if err:
        out.append(Finding("NF2", ERROR, shown, err))
    current = plugin_version(ctx.plugin_root)
    if fm is None:
        fields = legacy_config_fields(text)
        out.append(Finding("NF2", WARN, shown,
                           "legacy dialect (no YAML frontmatter) - readers accept it, nothing rewrites it silently",
                           fix="run /neuroflow:migrate, which shows the diff and asks before writing"))
        recorded = fields.get("plugin_version")
    else:
        recorded = fm.get("plugin_version")
        schema = fm.get("nf_schema")
        if schema is None:
            pass  # reported with the other required keys
        elif not str(schema).isdigit():
            out.append(Finding("NF2", WARN, shown, f"`nf_schema: {schema}` is not an integer"))
        elif int(schema) > SUPPORTED_NF_SCHEMA:
            out.append(Finding("NF2", ERROR, shown,
                               f"written with nf_schema {schema}; this plugin knows {SUPPORTED_NF_SCHEMA} - do not write "
                               "this file", fix="update the neuroflow plugin"))
        missing = [k for k in REQUIRED_CONFIG_KEYS if k not in fm]
        if missing:
            out.append(Finding("NF2", WARN, shown, "frontmatter is missing " + ", ".join(f"`{k}`" for k in missing),
                               fix="run /neuroflow:migrate"))
        phases = canonical_phases(ctx.plugin_root) - {"utility"}
        active = fm.get("active_phase")
        if isinstance(active, str) and active:
            if active == "setup":
                out.append(Finding("NF2", WARN, shown, "`active_phase: setup` - project setup never finished",
                                   fix="re-run /neuroflow to finish the interview"))
            elif phases and active not in phases:
                out.append(Finding("NF2", WARN, shown, f"`active_phase: {active}` is not a canonical phase"))
        recommended = fm.get("recommended_phases")
        if recommended not in (None, "") and not isinstance(recommended, list):
            out.append(Finding("NF2", WARN, shown, "`recommended_phases` must be a list"))
        elif phases:
            unknown = [p for p in _as_list(recommended) if isinstance(p, str) and p not in phases]
            if unknown:
                out.append(Finding("NF2", WARN, shown, "`recommended_phases` has unknown phase(s): " + ", ".join(unknown)))
        mode = fm.get("default_mode")
        if mode not in (None, "") and mode not in MODES:
            out.append(Finding("NF2", WARN, shown, f"`default_mode: {mode}` is not one of teacher, executor, critic"))
        auto = fm.get("paper_auto")
        if auto not in (None, "") and str(auto).lower() not in ("on", "off"):
            out.append(Finding("NF2", WARN, shown, f"`paper_auto: {auto}` must be on or off"))
        for root in _as_list(fm.get("raw_roots")):
            r = str(root)
            if r.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", r) or ".." in Path(r).parts:
                out.append(Finding("NF2", WARN, shown, f"`raw_roots` entry `{r}` must be relative to the project root"))
        personal = sorted(k for k in fm if k in PERSONAL_CONFIG_KEYS or k.startswith(("notification", "wellbeing")))
        if personal:
            out.append(Finding("NF2", WARN, shown,
                               "personal field(s) in the shared project file: " + ", ".join(f"`{k}`" for k in personal),
                               fix="move them to ~/.neuroflow/user.yaml (/neuroflow:migrate does this)"))
        if "wiki_auto" in fm:
            # Each person's own opt-in to wiki capture (it reads their sessions): never moved for them.
            out.append(Finding("NF2", WARN, shown,
                               "`wiki_auto` in the shared project file is ignored - it is each person's own opt-in, "
                               "read only from ~/.neuroflow/user.yaml; the project's policy is `wiki_capture: allow | forbid`",
                               fix="remove it here; whoever wants wiki capture runs /wiki --auto ask"))
    if not recorded:
        out.append(Finding("NF2", WARN, shown, "no plugin_version recorded",
                           fix="run /neuroflow:migrate - it brings the project, your flowie and the hive up to date "
                               "and then records the version"))
    elif current and _vtuple(recorded) and _vtuple(current):
        if _vtuple(recorded) < _vtuple(current):
            out.append(Finding("NF2", WARN, shown,
                               f"plugin_version {recorded} is older than the installed plugin {current} - "
                               "structure changes may apply",
                               fix="run /neuroflow:migrate - it brings the project, your flowie and the hive up to date "
                                   "and then records the version"))
        elif _vtuple(recorded) > _vtuple(current):
            out.append(Finding("NF2", WARN, shown,
                               f"plugin_version {recorded} is newer than the installed plugin {current}",
                               fix="update the neuroflow plugin"))
    return out


# ---------------------------------------------------------------------------
# NF3 - integrity status files
# ---------------------------------------------------------------------------


FREEZE_SCRIPT = "skills/phase-preregistration/scripts/freeze.py"
PII_SCRIPT = "skills/phase-output/scripts/pii_scan.py"
# freeze.py verify finding kinds -> severity (it is the one home of the hash lock)
FREEZE_SEVERITY = {"changed": ERROR, "missing": ERROR, "banner-missing": WARN, "unconfirmed-freeze": WARN,
                   "no-files": WARN}


def run_plugin_script(ctx: Context, rel: str, args: list[str], timeout: int = 180) -> tuple[int | None, object, str]:
    """Run another plugin script - the single executable home of its check.
    Returns (exit code or None when not installed, parsed JSON or None, last output line)."""
    script = ctx.plugin_root / rel
    if not script.is_file():
        return None, None, "not installed"
    try:
        proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True,
                              timeout=timeout, cwd=str(ctx.project), encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 2, None, str(exc)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = None
    tail = ((proc.stderr or proc.stdout).strip().splitlines() or ["no output"])[-1]
    return proc.returncode, data, tail[:200]


def _date(v) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(str(v).strip()[:10])
    except ValueError:
        return None


def _schema_too_new(fm: dict, shown: str, check: str) -> list[Finding]:
    s = fm.get("nf_schema")
    if s is not None and str(s).isdigit() and int(s) > SUPPORTED_NF_SCHEMA:
        return [Finding(check, ERROR, shown, f"written with nf_schema {s}; this plugin knows {SUPPORTED_NF_SCHEMA}",
                        fix="update the neuroflow plugin")]
    return []


def _check_prereg(ctx: Context, out: list[Finding]) -> None:
    path = ctx.nf / "preregistration" / "status.md"
    if not path.is_file():
        return
    shown = ctx.rel(path)
    fm, _, err = split_frontmatter(_read(path))
    if fm is None:
        out.append(Finding("NF3", WARN, shown, err or "status.md has no frontmatter - the freeze state cannot be read"))
        return
    out.extend(_schema_too_new(fm, shown, "NF3"))
    status = str(fm.get("status") or "")
    if status not in PREREG_STATUSES:
        out.append(Finding("NF3", WARN, shown, f"`status: {status or '(missing)'}` must be draft or frozen"))
        return
    if status != "frozen":
        return
    if not fm.get("frozen_at"):
        out.append(Finding("NF3", WARN, shown, "frozen but `frozen_at` is missing"))
    # The hash re-check has one home: the preregistration freeze script.
    code, data, tail = run_plugin_script(ctx, FREEZE_SCRIPT, ["verify", "--root", str(ctx.project), "--json"])
    if code is None or code not in (0, 1):
        why = "is not installed" if code is None else f"could not run ({tail})"
        out.append(Finding("NF3", INFO, shown, f"freeze.py {why} - frozen files were not re-hashed; compare them by hand"))
        return
    items = data.get("findings", []) if isinstance(data, dict) else []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "finding")
        fix = {"changed": "restore the file; record the change in deviations.md",
               "missing": "restore it from git; record any change in deviations.md",
               "unconfirmed-freeze": "a person confirms the freeze in /preregistration"}.get(kind, "")
        out.append(Finding("NF3", FREEZE_SEVERITY.get(kind, WARN), str(item.get("path") or shown),
                           f"{kind}: {item.get('detail') or 'see freeze.py verify'}", fix=fix))
    if code == 1 and not items:
        out.append(Finding("NF3", WARN, shown, f"freeze.py verify reported findings: {tail}"))


def _legacy_ethics(text: str) -> dict[str, str]:
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^\s*\|\s*\**\s*(Status|Expires|Approved)\s*\**\s*\|\s*([^|]*?)\s*\|", line, re.I) or \
            re.match(r"^\s*(?:[-*]\s+)?\*\*(Status|Expires|Approved):?\*\*:?\s*(.+?)\s*$", line, re.I)
        if m:
            fields.setdefault(m.group(1).lower(), m.group(2).strip().strip("`*").lower())
    return fields


def _check_ethics(ctx: Context, out: list[Finding]) -> None:
    path = ctx.nf / "ethics" / "status.md"
    if not path.is_file():
        return
    shown = ctx.rel(path)
    text = _read(path)
    fm, _, err = split_frontmatter(text)
    legacy = fm is None
    if legacy:
        out.append(Finding("NF3", WARN, shown, err or "legacy ethics status format (no frontmatter)",
                           fix="run /ethics --status, which writes the frontmatter after a person confirms the values"))
        fm = _legacy_ethics(text)
        fm.setdefault("set_by", "person")  # the old format did not record who set it
        words = re.findall(r"[a-z]+", str(fm.get("status") or ""))
        fm["status"] = words[0] if words else ""
    else:
        out.extend(_schema_too_new(fm, shown, "NF3"))
    status = str(fm.get("status") or "").lower()
    if status and status not in ETHICS_STATUSES and not legacy:
        out.append(Finding("NF3", WARN, shown, f"`status: {status}` is not one of {', '.join(sorted(ETHICS_STATUSES))}"))
    if status == "approved" and str(fm.get("set_by") or "") != "person":
        out.append(Finding("NF3", WARN, shown,
                           "approved with `set_by` other than person - readers treat it as not approved",
                           fix="a person confirms the approval in /ethics"))
    expires = fm.get("expires")
    if expires not in (None, ""):
        d = _date(expires)
        if d is None:
            out.append(Finding("NF3", WARN, shown, f"`expires: {expires}` is not an ISO date (YYYY-MM-DD)"))
        elif status == "approved" and d < ctx.today:
            out.append(Finding("NF3", ERROR, shown, f"ethics approval expired on {d.isoformat()}",
                               fix="renew the approval; record it with /ethics"))
    ai = fm.get("ai_processing")
    if ai not in (None, "") and str(ai) not in AI_PROCESSING:
        out.append(Finding("NF3", WARN, shown, f"`ai_processing: {ai}` must be none, pseudonymised or identifiable"))


def check_nf3(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    _check_prereg(ctx, out)
    _check_ethics(ctx, out)
    return out


# ---------------------------------------------------------------------------
# NF4 - reasoning logs
# ---------------------------------------------------------------------------

_REASONING_KEYS = ("statement", "source", "reasoning")


def _entry_problem(obj) -> str | None:
    if not isinstance(obj, dict):
        return "is not a JSON object"
    missing = [k for k in _REASONING_KEYS if not str(obj.get(k) or "").strip()]
    return "lacks " + ", ".join(f"`{k}`" for k in missing) if missing else None


def check_nf4(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    folder = ctx.nf / "reasoning"
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.jsonl")):
        shown, reported = ctx.rel(path), 0
        for lineno, line in enumerate(_read(path).splitlines(), 1):
            if not line.strip():
                continue
            try:
                problem = _entry_problem(json.loads(line))
                severity = WARN
            except json.JSONDecodeError:
                problem, severity = "is not valid JSON (a hand-merged conflict?)", ERROR
            if problem:
                reported += 1
                if reported <= MAX_PER_FILE:
                    out.append(Finding("NF4", severity, shown, f"line {problem}", lineno))
        if reported > MAX_PER_FILE:
            out.append(Finding("NF4", WARN, shown, f"... and {reported - MAX_PER_FILE} more line(s) with problems"))
    for path in sorted(folder.glob("*.json")):
        shown = ctx.rel(path)
        try:
            data = json.loads(_read(path) or "null")
        except json.JSONDecodeError as exc:
            out.append(Finding("NF4", ERROR, shown, f"not valid JSON ({exc.msg}, line {exc.lineno}) - often a hand-merged conflict"))
            continue
        out.append(Finding("NF4", WARN, shown, "legacy JSON-array log - the current format is one object per line in .jsonl",
                           fix="run /neuroflow:migrate"))
        if path.with_suffix(".jsonl").exists():
            out.append(Finding("NF4", WARN, shown, f"both {path.name} and {path.stem}.jsonl exist",
                               fix="/neuroflow:migrate merges them"))
        entries = data if isinstance(data, list) else [] if data is None else [data]
        bad = [i for i, e in enumerate(entries) if _entry_problem(e)]
        if bad:
            out.append(Finding("NF4", WARN, shown, f"{len(bad)} entr{'y' if len(bad) == 1 else 'ies'} lack "
                                                   "statement/source/reasoning"))
    return out


# ---------------------------------------------------------------------------
# NF5 - merge-conflict markers
# ---------------------------------------------------------------------------

_CONFLICT_RE = re.compile(r"^(<{7}|>{7})(\s|$)")


def check_nf5(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    for path in sorted(ctx.nf.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > 5_000_000:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:8192]:
            continue
        for lineno, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            if _CONFLICT_RE.match(line):
                out.append(Finding("NF5", ERROR, ctx.rel(path), "merge-conflict marker", lineno,
                                   fix="resolve the merge by hand; append-only logs keep both sides"))
    return out


# ---------------------------------------------------------------------------
# NF6 - memory structure (MEMORY-PURITY)
# ---------------------------------------------------------------------------


def check_nf6(ctx: Context, structure: dict) -> list[Finding]:
    out: list[Finding] = []
    files = set(structure["root_files"])
    folders = set(structure["root_folders"]) | set(structure["phase_folders"])
    skills = set(structure["skills"])
    if not structure["documented"]:
        out.append(Finding("NF6", INFO, ".neuroflow/",
                           "could not read the documented structure from neuroflow-core; only command folders are known"))
    for entry in sorted(ctx.nf.iterdir()):
        name, shown = entry.name, ctx.rel(entry) + ("/" if entry.is_dir() else "")
        if name.startswith("."):
            if name == ".flowie" and entry.is_dir():
                out.append(Finding("NF6", WARN, shown, "old dotted flowie folder - flowie lives at ~/.neuroflow/flowie/"))
            continue
        if entry.is_dir():
            if name in folders:
                continue
            if name == "flowie":
                msg = "flowie never lives inside a project - it is the global clone at ~/.neuroflow/flowie/"
            elif name == "hive":
                msg = "hive caches never live inside a project - they are at ~/.neuroflow/hives/{org-repo}/"
            elif name in skills:
                msg = "folder named after a skill - skills write into the active command's phase folder"
            else:
                msg = "folder is not part of the documented structure (neuroflow-core -> .neuroflow/ folder)"
            out.append(Finding("NF6", WARN, shown, msg, fix="move its files to the right phase folder, then remove it"))
        elif name not in files:
            msg = LEGACY_ROOT_FILES.get(name)
            out.append(Finding("NF6", WARN, shown,
                               f"legacy file - {msg}" if msg else "file is not part of the documented root files",
                               fix="move it into a phase folder (or the project root if it is a deliverable)"))
    return out


# ---------------------------------------------------------------------------
# NF7 - project instruction block
# ---------------------------------------------------------------------------


def _neuroflow_block(text: str) -> str | None:
    m = re.search(r"(?ms)^##\s+neuroflow\s*$(.*?)(?=^#{1,2}\s|\Z)", text)
    return m.group(1) if m else None


def check_nf7(ctx: Context) -> list[Finding]:
    out: list[Finding] = []
    claude_md = ctx.project / ".claude" / "CLAUDE.md"
    shown = ctx.rel(claude_md)
    if not claude_md.is_file():
        out.append(Finding("NF7", WARN, shown, "missing - Claude Code is not pointed at the project memory",
                           fix="add the static block from neuroflow-core (Project instruction block)"))
    else:
        text = _read(claude_md)
        block = _neuroflow_block(text)
        if "project_config.md" not in (block if block is not None else text):
            out.append(Finding("NF7", WARN, shown, "does not point at .neuroflow/project_config.md",
                               fix="add the static block from neuroflow-core (Project instruction block)"))
        if block and re.search(r"(?im)^\s*[-*]?\s*(\*\*)?active[ _]phase(\*\*)?\s*:", block):
            out.append(Finding("NF7", WARN, shown,
                               "the neuroflow block holds an `Active phase` line - it goes stale; the phase lives in "
                               "project_config.md", fix="remove the line"))
    global_md = ctx.home / ".claude" / "CLAUDE.md"
    if global_md.is_file() and _neuroflow_block(_read(global_md)) is not None:
        out.append(Finding("NF7", WARN, ctx.rel(global_md),
                           "a neuroflow block in the global CLAUDE.md is injected into every session, in every folder",
                           fix="remove it after the person confirms (only the project's .claude/CLAUDE.md carries it)"))
    for mirror in (ctx.project / ".github" / "copilot-instructions.md", ctx.project / "AGENTS.md"):
        if mirror.is_file() and _neuroflow_block(_read(mirror)) is not None:
            out.append(Finding("NF7", WARN, ctx.rel(mirror),
                               "stale neuroflow block - neuroflow is a Claude Code plugin and no longer maintains this copy",
                               fix="remove the neuroflow block (keep the rest of the file)"))
    return out


# ---------------------------------------------------------------------------
# NF8 - sensitive data (delegated)
# ---------------------------------------------------------------------------


def check_nf8(ctx: Context) -> tuple[list[Finding], str]:
    """Return (findings, status) where status is pass | warn | skipped.

    pii_scan.py scans the team-tier files of .neuroflow/ (local-tier memory never leaves
    the machine) and reports path, line and class - never the value."""
    if not ctx.run_pii:
        return [], "skipped"
    code, data, tail = run_plugin_script(ctx, PII_SCRIPT, ["--root", str(ctx.project), "--json"])
    if code is None:
        return [Finding("NF8", INFO, ".neuroflow/",
                        "pii_scan.py is not installed - the sentinel agent scans by reading (agents/sentinel.md S5)")], "skipped"
    if code == 0:
        return [], "pass"
    if code != 1:
        return [Finding("NF8", INFO, ".neuroflow/", f"pii_scan.py exited {code} ({tail}) - scan by reading")], "skipped"
    out: list[Finding] = []
    items = data.get("findings", []) if isinstance(data, dict) else data
    if isinstance(items, list) and items:
        for item in items:
            if not isinstance(item, dict):
                continue
            msg = item.get("message") or item.get("kind") or item.get("rule") or "possible personal data"
            raw = Path(str(item.get("path") or ctx.nf))
            path = ctx.rel(raw if raw.is_absolute() else ctx.project / raw)
            line = item.get("line") if isinstance(item.get("line"), int) else None
            out.append(Finding("NF8", WARN, path, f"{msg} [needs human review]", line))
    else:
        out.append(Finding("NF8", WARN, ".neuroflow/", f"pii_scan.py: {tail} [needs human review]"))
    return out, "warn"


# ---------------------------------------------------------------------------
# Runner and CLI
# ---------------------------------------------------------------------------


def run_checks(ctx: Context, only: set[str] | None = None) -> tuple[list[Finding], dict[str, str]]:
    structure = documented_structure(ctx.plugin_root)
    findings: list[Finding] = []
    statuses: dict[str, str] = {}
    runners = {
        "NF1": lambda: check_nf1(ctx),
        "NF2": lambda: check_nf2(ctx),
        "NF3": lambda: check_nf3(ctx),
        "NF4": lambda: check_nf4(ctx),
        "NF5": lambda: check_nf5(ctx),
        "NF6": lambda: check_nf6(ctx, structure),
        "NF7": lambda: check_nf7(ctx),
    }
    for cid in CHECKS:
        if only and cid not in only:
            continue
        if cid == "NF8":
            found, status = check_nf8(ctx)
        else:
            found = runners[cid]()
            severities = {f.severity for f in found}
            status = ERROR if ERROR in severities else WARN if WARN in severities else "pass"
        findings.extend(found)
        statuses[cid] = status
    return findings, statuses


def exit_code(findings: list[Finding], fail_on: str) -> int:
    counted = {ERROR} if fail_on == ERROR else {ERROR, WARN}
    return 1 if any(f.severity in counted for f in findings) else 0


def render_text(ctx: Context, findings: list[Finding], statuses: dict[str, str], code: int) -> str:
    version = plugin_version(ctx.plugin_root) or "unknown"
    lines = [f"nf_check {ctx.project.as_posix()}  (plugin {version}, nf_schema {SUPPORTED_NF_SCHEMA})"]
    for cid, status in statuses.items():
        own = [f for f in findings if f.check == cid]
        counted = [f for f in own if f.severity != INFO]
        lines.append(f"[{cid}] {CHECKS[cid]}: {status}" + (f" ({len(counted)})" if counted else ""))
        for f in own:
            where = f.path + (f":{f.line}" if f.line else "")
            lines.append(f"  {f.severity:5}  {where}  {f.message}" + (f"  -> {f.fix}" if f.fix else ""))
    totals = {s: sum(1 for f in findings if f.severity == s) for s in (ERROR, WARN, INFO)}
    lines.append(f"Summary: {totals[ERROR]} error, {totals[WARN]} warn, {totals[INFO]} info (exit {code})")
    return "\n".join(lines)


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
        prog="nf_check",
        description="Deterministic audit of a neuroflow project's .neuroflow/ memory (read-only).",
    )
    ap.add_argument("--project", default=".", help="project folder, or any folder below it (default: .)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("--only", help="comma-separated check ids, e.g. NF1,NF4")
    ap.add_argument("--fail-on", choices=[WARN, ERROR], default=WARN,
                    help="lowest severity that makes the exit code 1 (default: warn)")
    ap.add_argument("--no-pii", action="store_true", help="skip NF8 (the delegated sensitive-data scan)")
    ap.add_argument("--structure", action="store_true",
                    help="print the documented .neuroflow/ structure (the NF6 whitelist) as JSON and exit")
    ap.add_argument("--plugin-root", type=Path, default=PLUGIN_ROOT, help=argparse.SUPPRESS)
    ap.add_argument("--home", type=Path, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--today", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # paths may hold characters the console cannot encode
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    plugin_root = args.plugin_root.resolve()
    if args.structure:
        print(json.dumps(documented_structure(plugin_root), indent=2))
        return 0
    only = None
    if args.only:
        only = {c.strip().upper() for c in args.only.split(",") if c.strip()}
        unknown = only - set(CHECKS)
        if unknown:
            print(f"nf_check: unknown check id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
    home = (args.home or Path.home()).resolve()
    project = find_project(Path(args.project), home)
    if project is None:
        print(f"nf_check: no project .neuroflow/ found in {Path(args.project).resolve()} or its parents "
              "(the global ~/.neuroflow/ is not project memory) - run /neuroflow first", file=sys.stderr)
        return 2
    today = _date(args.today) if args.today else _dt.date.today()
    if today is None:
        print(f"nf_check: --today {args.today!r} is not an ISO date", file=sys.stderr)
        return 2
    ctx = Context(project=project, plugin_root=plugin_root, home=home, today=today, run_pii=not args.no_pii)
    try:
        findings, statuses = run_checks(ctx, only)
    except Exception as exc:  # report, never guess
        print(f"nf_check: internal error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2
    code = exit_code(findings, args.fail_on)
    if args.json:
        print(json.dumps({
            "tool": "nf_check",
            "project": project.as_posix(),
            "plugin_root": plugin_root.as_posix(),
            "plugin_version": plugin_version(plugin_root),
            "checks": [{"id": c, "title": CHECKS[c], "status": s} for c, s in statuses.items()],
            "findings": [asdict(f) for f in findings],
            "summary": {s: sum(1 for f in findings if f.severity == s) for s in (ERROR, WARN, INFO)},
            "exit_code": code,
        }, indent=2))
    else:
        print(render_text(ctx, findings, statuses, code))
    return code


if __name__ == "__main__":
    sys.exit(main())
