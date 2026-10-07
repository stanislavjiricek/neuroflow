#!/usr/bin/env python3
"""Migrate neuroflow's memory to the current contracts (neuroflow-core), level by level.

Dry run by default: prints the plan (with a diff of project_config.md) and writes
nothing. --apply writes the plan. Idempotent: a migrated level has nothing to do.

The project (the default; found by walking up from --root):
  - project_config.md: the legacy dialects (`key: value` lines, `**Bold:**` labels,
    or a mix) -> YAML frontmatter (nf_schema 1) followed by the free markdown body;
    plugin_version -> the running plugin's version when it is older or missing (never lowered)
  - personal fields (auto_issue_reporting, researcher name, writing_style, zotero,
    notification / wellbeing settings) -> ~/.neuroflow/user.yaml, only with --move-personal
  - reasoning/*.json arrays -> *.jsonl, one element per line; the old file is kept as *.json.bak
  - missing .gitattributes (merge=union) and .gitignore (local tier) lines
  - the project's .claude/CLAUDE.md neuroflow block -> the static block, when it names a phase
  Only reports (never edits):
  - neuroflow blocks in ~/.claude/CLAUDE.md, .github/copilot-instructions.md and AGENTS.md

Your flowie (--flowie) and team hives (--hive NAME, --hives), instead of the project:
  - task files in a legacy form (flat tasks/{id}-{slug}.md, or id / assignee / responsible /
    level keys) -> tasks/{column}/{slug}.md with the keys commands/tasks.md defines; a slug /tasks
    accepts is kept as it is, and blocked_by entries follow a task whose name changes
  - .gitignore: integrations.json (flowie) or sync.json (hive) added when it is missing
  Only reports (never edits): integrations.json or sync.json tracked by git; a task file that is
  not UTF-8, holds conflict markers or names more than one person as its owner; a blocked_by entry
  that could now mean two tasks; a cached hive without .git/ (the copied-file cache that
  /hive --init replaces with a clone).
  With --apply in a git repository, tracked task files move with `git mv` (history follows
  them) and every changed path is staged; the result lists the paths to commit. It never
  commits or pushes.

Usage:
  python <neuroflow-core base dir>/scripts/migrate.py [--root DIR] [--apply]
      [--move-personal] [--set KEY=VALUE ...] [--json]
  python <neuroflow-core base dir>/scripts/migrate.py [--flowie] [--hive NAME ... | --hives]
      [--apply] [--json]

Exit codes:
  0  nothing to do (already current), or --apply finished with nothing left to report
  1  findings: changes to apply, decisions needed (--set), personal fields still in the
     project file, or report-only items; with --apply and a blocking item, nothing is written
  2  refused or failed: nf_schema newer than this script knows, no project found, an
     unknown --hive name, unreadable files, a failed git command, bad arguments

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("nf_scaffold", Path(__file__).with_name("scaffold.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sc = _load_scaffold()

KNOWN_SCHEMA = sc.SCHEMA_VERSION

FRONTMATTER_ORDER = [
    "nf_schema", "project_name", "active_phase", "default_mode", "target_journal",
    "recommended_phases", "raw_roots", "paper_auto", "hive_repo", "ethics", "collaborators",
    "flowie_profiles", "plugin_version",
]
SETTABLE = {"project_name", "active_phase", "default_mode", "target_journal", "recommended_phases",
            "raw_roots", "paper_auto", "hive_repo"}
LIST_KEYS = {"recommended_phases", "raw_roots"}
RECORD_KEYS = {"collaborators", "flowie_profiles"}
RAW_EMIT_KEYS = {"active_phase", "default_mode", "paper_auto"}
MODES = {"teacher", "executor", "critic"}

# Legacy spellings (normalised: lowercase, non-alphanumerics -> "_") -> contract key.
KEY_ALIASES = {
    "nf_schema": "nf_schema",
    "project_name": "project_name", "project": "project_name", "project_title": "project_name",
    "active_phase": "active_phase", "phase": "active_phase", "current_phase": "active_phase",
    "default_mode": "default_mode", "personality_mode": "default_mode",
    "target_journal": "target_journal", "journal": "target_journal",
    "recommended_phases": "recommended_phases",
    "raw_roots": "raw_roots",
    "paper_auto": "paper_auto",
    "hive_repo": "hive_repo", "hive": "hive_repo",
    "ethics": "ethics",  # `ethics: not-applicable` (see /ethics) keeps working as a frontmatter fact
    "collaborators": "collaborators",
    "flowie_profiles": "flowie_profiles",
    "plugin_version": "plugin_version",
}
# Personal fields (C1): legacy key -> key in ~/.neuroflow/user.yaml.
PERSONAL_KEYS = {
    "auto_issue_reporting": "auto_issue_reporting",
    "researcher": "name", "researcher_name": "name",
    "writing_style": "writing_style",
    "zotero": "zotero",  # the /ideation answer: whether this person uses Zotero
}
PERSONAL_PREFIXES = ("notification", "wellbeing")
YES_NO_KEYS = {"auto_issue_reporting", "zotero"}

KV_RE = re.compile(r"^(?P<key>[a-z_][a-z0-9_]*):(?:[ \t]+(?P<value>.*?))?[ \t]*$")
BOLD_RE = re.compile(r"^(?:[-*+][ \t]+)?\*\*(?P<label>[^*\n]+?)[ \t]*:?[ \t]*\*\*[ \t]*:?[ \t]*(?P<value>.*?)[ \t]*$")
ITEM_KV_RE = re.compile(r"^(?P<key>[A-Za-z_][\w-]*):(?:[ \t]+(?P<value>.*))?$")
CONFLICT_RE = re.compile(r"^(<{7}|>{7})( |$)", re.MULTILINE)


# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------


def norm_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def personal_target(key: str) -> str | None:
    if key in PERSONAL_KEYS:
        return PERSONAL_KEYS[key]
    if key.startswith(PERSONAL_PREFIXES):
        return key
    return None


def clean_scalar(value: str, yaml: bool = True) -> str:
    """Strip quotes, inline YAML comments (yaml=True only) and markdown backticks from a scalar."""
    value = value.strip()
    if value[:1] in ('"', "'"):
        quote = value[0]
        end = value.find(quote, 1)
        while quote == '"' and end > 0 and value[end - 1] == "\\":
            end = value.find(quote, end + 1)
        if end > 0:
            inner = value[1:end]
            return inner.replace('\\"', '"').replace("\\\\", "\\") if quote == '"' else inner.replace("''", "'")
    if yaml:
        value = re.split(r"[ \t]#", value, maxsplit=1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        value = value[1:-1].strip()
    return value


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    parts = re.split(r"\s*(?:→|->|,)\s*", value)
    return [clean_scalar(p) for p in parts if clean_scalar(p)]


def parse_block(block: list[str]) -> list | None:
    """A YAML block list of scalars or flat mappings; None when it is anything else."""
    items: list = []
    current: dict | None = None
    base: int | None = None
    for line in block:
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped == "-" or stripped.startswith(("- ", "-\t")):
            if base is None:
                base = indent
            if indent != base:
                return None
            content = stripped[1:].strip()
            kv = ITEM_KV_RE.match(content)
            if kv:
                current = {kv.group("key"): clean_scalar(kv.group("value") or "")}
                items.append(current)
            else:
                current = None
                items.append(clean_scalar(content))
            continue
        kv = ITEM_KV_RE.match(stripped)
        if kv and current is not None and base is not None and indent > base:
            current[kv.group("key")] = clean_scalar(kv.group("value") or "")
            continue
        return None
    return items


def take_block(lines: list[str], i: int) -> int:
    """Index just past the indented / list lines directly below the key on line i-1."""
    j = i
    while j < len(lines):
        line = lines[j]
        if line.strip() and (line.startswith((" ", "\t")) or line == "-" or line.startswith(("- ", "-\t"))):
            j += 1
            continue
        break
    return j


def canonical_phases() -> set[str]:
    """Phase ids from the neuroflow-core Phase taxonomy (plus `setup`, the scaffold placeholder)."""
    fallback = {"ideation", "preregistration", "grant-proposal", "finance", "experiment", "tool-build",
                "tool-validate", "data", "data-preprocess", "data-analyze", "brain-build", "brain-optimize",
                "brain-run", "paper", "review", "poster", "notes", "write-report", "output"}
    try:
        text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
        m = re.search(r"\*\*Valid `phase:` frontmatter values:\*\*(.+)", text)
        phases = set(re.findall(r"`([a-z][\w-]*)`", m.group(1))) if m else set()
    except OSError:
        phases = set()
    phases = (phases or fallback) - {"utility"}
    return phases | {"setup"}


def norm_phase(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().lower())


def version_key(value: str) -> tuple[int, ...]:
    """A dotted version as numbers; a part that is not a number counts as 0."""
    return tuple(int(part) if part.isdigit() else 0 for part in re.split(r"[.+-]", value.strip()))


def is_older(recorded: str, running: str) -> bool:
    """True when `recorded` is older than `running`, compared number by number (0.2.9 < 0.2.10)."""
    a, b = version_key(recorded), version_key(running)
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) < b + (0,) * (width - len(b))


def recorded_version(recorded: str | None, running: str | None) -> str | None:
    """The plugin_version a migration leaves: the running version when the recorded one is older or missing.
    Never lower: a newer recorded version (a teammate's newer neuroflow migrated the project) stays."""
    if running and (not recorded or is_older(recorded, running)):
        return running
    return recorded


# ---------------------------------------------------------------------------
# Value normalisation and validation
# ---------------------------------------------------------------------------


class Problems:
    def __init__(self) -> None:
        self.blocking: list[str] = []
        self.notes: list[str] = []


def normalise(key: str, value, phases: set[str], problems: Problems, origin: str):
    """Contract value for `key`, or None when it cannot be used (a problem is recorded)."""
    if key == "active_phase":
        phase = norm_phase(str(value)) if isinstance(value, str) else ""
        if phase in phases:
            return phase
        problems.blocking.append(
            f"active_phase: {value!r} ({origin}) is not a phase id. Ask the person which phase "
            "applies and rerun with --set active_phase=<id>.")
        return None
    if key == "recommended_phases":
        items = value if isinstance(value, list) else parse_inline_list(str(value))
        if any(isinstance(x, dict) for x in items):
            problems.blocking.append(f"recommended_phases ({origin}) is not a list of phase ids.")
            return None
        ids = [norm_phase(x) for x in items]
        bad = [orig for orig, pid in zip(items, ids) if pid not in phases or pid == "setup"]
        if bad:
            problems.blocking.append(
                f"recommended_phases ({origin}) holds values that are not phase ids: {', '.join(map(repr, bad))}. "
                "Rerun with --set recommended_phases=<id>,<id>,...")
            return None
        return ids
    if key == "raw_roots":
        items = value if isinstance(value, list) else parse_inline_list(str(value))
        if any(isinstance(x, dict) for x in items):
            problems.blocking.append(f"raw_roots ({origin}) is not a list of folders.")
            return None
        return [str(x) for x in items]
    if key == "default_mode":
        mode = str(value).strip().lower()
        if mode in MODES:
            return mode
        problems.notes.append(f"default_mode {value!r} ({origin}) is not teacher, executor or critic; "
                              "left in the notes.")
        return None
    if key == "paper_auto":
        flag = str(value).strip().lower()
        if flag in {"on", "yes", "true"}:
            return "on"
        if flag in {"off", "no", "false"}:
            return "off"
        problems.notes.append(f"paper_auto {value!r} ({origin}) is not on or off; left in the notes.")
        return None
    if key in RECORD_KEYS:
        if isinstance(value, list) and all(isinstance(x, dict) for x in value):
            return value
        problems.notes.append(f"{key} ({origin}) could not be read as a list of entries; left in the notes. "
                              "Move it into the frontmatter by hand.")
        return None
    if isinstance(value, list):
        problems.notes.append(f"{key} ({origin}) is a list where a single value is expected; left in the notes.")
        return None
    return str(value).strip()


def personal_value(target: str, value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if target in YES_NO_KEYS:
        low = text.strip().lower()
        if low in {"yes", "true", "on", "y"}:
            return "yes"
        if low in {"no", "false", "off", "n"}:
            return "no"
    return text.strip()


# ---------------------------------------------------------------------------
# YAML emission
# ---------------------------------------------------------------------------


def emit_key(key: str, value) -> list[str]:
    if key == "nf_schema":
        return [f"nf_schema: {value}"]
    if isinstance(value, list):
        if value and all(isinstance(x, dict) for x in value):
            out = [f"{key}:"]
            for record in value:
                for n, (k2, v2) in enumerate(record.items()):
                    out.append(f"{'  - ' if n == 0 else '    '}{k2}: {sc.yaml_scalar(str(v2))}")
            return out
        return [f"{key}: [" + ", ".join(sc.yaml_scalar(str(x), in_flow=True) for x in value) + "]"]
    text = str(value)
    return [f"{key}: {text if key in RAW_EMIT_KEYS else sc.yaml_scalar(text)}"]


def emit_frontmatter(facts: dict) -> list[str]:
    out: list[str] = []
    for key in FRONTMATTER_ORDER + [k for k in facts if k not in FRONTMATTER_ORDER]:
        if key in facts:
            out += emit_key(key, facts[key])
    return out


# ---------------------------------------------------------------------------
# Reading project_config.md
# ---------------------------------------------------------------------------


def scan_legacy(lines: list[str]) -> list[dict]:
    """Known `key: value` / `**Label:** value` entries outside code fences."""
    entries: list[dict] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        style = None
        m = KV_RE.match(line)
        if m:
            style, raw_key, value = "kv", m.group("key"), (m.group("value") or "")
        else:
            m = BOLD_RE.match(line)
            if m:
                style, raw_key, value = "bold", norm_key(m.group("label")), m.group("value")
        if style is None:
            i += 1
            continue
        start, i = i, i + 1
        block: list[str] = []
        if not value.strip() and style == "kv":
            end = take_block(lines, i)
            block, i = lines[i:end], end
        key = KEY_ALIASES.get(raw_key)
        target = personal_target(raw_key)
        if key or target:
            entries.append({"raw_key": raw_key, "key": key, "personal": target, "value": value,
                            "block": block, "start": start, "end": i, "style": style})
    return entries


def entry_value(entry: dict):
    if entry["block"]:
        return parse_block(entry["block"])
    return clean_scalar(entry["value"], yaml=False)


def segment_frontmatter(fm_lines: list[str]) -> list[list]:
    """[[key or None, [lines]], ...] for a frontmatter block."""
    segs: list[list] = []
    for line in fm_lines:
        m = re.match(r"^([A-Za-z_][\w-]*):(?:[ \t]|$)", line)
        if m:
            segs.append([m.group(1), [line]])
        elif segs:
            segs[-1][1].append(line)
        else:
            segs.append([None, [line]])
    return segs


def segment_value(lines: list[str]):
    m = re.match(r"^[A-Za-z_][\w-]*:[ \t]*(.*)$", lines[0])
    first = m.group(1) if m else ""
    if first.strip():
        if first.strip().startswith("["):
            return parse_inline_list(first)
        return clean_scalar(first)
    return parse_block(lines[1:])


NOT_UTF8 = ("is not UTF-8; convert it (from the encoding it was saved in), then rerun: rewriting it now would "
            "replace every character that could not be read")


def read_utf8(path: Path) -> str | None:
    """A file's text with its own line endings, decoded strictly as UTF-8; None when it does not decode. Every
    file this script rewrites is read this way: one that does not decode is reported, never written back."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            return fh.read()
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------------------
# The migration plan
# ---------------------------------------------------------------------------


class Plan:
    def __init__(self, root: Path, home: Path) -> None:
        self.root, self.home = root, home
        self.dialect = "current"
        self.changes: list[dict] = []
        self.writes: list[tuple[Path, str, str]] = []
        self.renames: list[tuple[Path, Path]] = []
        self.problems = Problems()
        self.personal: list[dict] = []
        self.user_yaml_add: list[str] = []
        self.report: list[dict] = []
        self.warnings: list[str] = []

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def write(self, path: Path, text: str, summary: str, newline: str = "\n", diff_from: str | None = None) -> None:
        diff = None
        if diff_from is not None:
            diff = "".join(difflib.unified_diff(
                diff_from.replace("\r\n", "\n").splitlines(keepends=True),
                text.splitlines(keepends=True),
                fromfile=f"a/{self.rel(path)}", tofile=f"b/{self.rel(path)}"))
        self.writes.append((path, text, newline))
        self.changes.append({"path": self.rel(path), "action": "write", "summary": summary, "diff": diff})

    def rename(self, src: Path, dst: Path, summary: str) -> None:
        self.renames.append((src, dst))
        self.changes.append({"path": self.rel(src), "action": "rename", "summary": summary, "diff": None})


def plan_config(plan: Plan, config: Path, overrides: dict, move_personal: bool, version: str | None,
                phases: set[str]) -> None:
    original = read_utf8(config)
    if original is None:
        plan.problems.blocking.append(f"{plan.rel(config)} {NOT_UTF8}.")
        return
    if CONFLICT_RE.search(original):
        plan.problems.blocking.append(f"{plan.rel(config)} contains merge-conflict markers; resolve them first.")
        return
    newline = sc.detect_newline(original)
    text = original.replace("\r\n", "\n")
    split = sc.split_frontmatter(text)
    if split is not None and not any(re.match(r"^[A-Za-z_][\w-]*:(?:[ \t]|$)", line) for line in split[0]):
        split = None  # a leading --- horizontal rule, not a YAML frontmatter block
    problems = plan.problems

    if split is not None:
        fm_lines, body = split
        segs = segment_frontmatter(fm_lines)
        keys = {seg[0] for seg in segs if seg[0]}
        schema = sc.schema_of(text)
        if isinstance(schema, int) and schema > KNOWN_SCHEMA:
            raise RefusedError(f"project_config.md has nf_schema {schema}, newer than this script knows "
                               f"({KNOWN_SCHEMA}). Nothing written; update the neuroflow plugin.")
        if schema is not None and not isinstance(schema, int):
            problems.blocking.append(f"nf_schema {schema!r} is not an integer; fix it by hand.")
            return
        plan.dialect = "current" if schema == KNOWN_SCHEMA else "frontmatter without nf_schema"
        changed = False
        for seg in segs:
            key = seg[0]
            if not key:
                continue
            target = personal_target(key)
            if target:
                value = personal_value(target, segment_value(seg[1]))
                plan.personal.append({"key": key, "value": value, "target": target})
                if move_personal:
                    seg[0], seg[1] = None, []
                    changed = True
                continue
            canon = KEY_ALIASES.get(key)
            if canon and canon != key and canon not in keys:
                value = normalise(canon, segment_value(seg[1]), phases, problems, f"frontmatter `{key}`")
                if value is not None:
                    seg[0], seg[1] = canon, emit_key(canon, value)
                    keys.add(canon)
                    changed = True
        if "nf_schema" not in keys:
            segs.insert(0, ["nf_schema", [f"nf_schema: {KNOWN_SCHEMA}"]])
            changed = True
        for key, value in overrides.items():
            emitted = emit_key(key, value)
            for seg in segs:
                if seg[0] == key:
                    if seg[1] != emitted:
                        seg[1] = emitted
                        changed = True
                    break
            else:
                insert_at = next((n for n, seg in enumerate(segs) if seg[0] == "plugin_version"), len(segs))
                segs.insert(insert_at, [key, emitted])
                keys.add(key)
                changed = True
        if "project_name" not in keys:
            segs.insert(1, ["project_name", emit_key("project_name", plan.root.name)])
            problems.notes.append(f"project_name taken from the folder name ({plan.root.name!r}); "
                                  "change it with --set project_name=<name>.")
            changed = True
        if "recommended_phases" not in keys:  # contract key; empty until /neuroflow or /phase suggests a sequence
            insert_at = next((n for n, seg in enumerate(segs) if seg[0] == "plugin_version"), len(segs))
            segs.insert(insert_at, ["recommended_phases", ["recommended_phases: []"]])
            changed = True
        current = {seg[0]: segment_value(seg[1]) for seg in segs if seg[0] in ("active_phase", "recommended_phases")}
        if "active_phase" not in current:
            problems.blocking.append("project_config.md has no active_phase. Ask the person which phase applies "
                                     "and rerun with --set active_phase=<id>.")
        else:
            normalise("active_phase", current["active_phase"], phases, problems, "frontmatter")
        if "recommended_phases" in current:
            normalise("recommended_phases", current["recommended_phases"], phases, problems, "frontmatter")
        # The version the project was last brought up to date to (what the version notice compares): raised to the
        # running version when it is older or missing, never lowered — a teammate's newer plugin may have recorded it.
        recorded = next((segment_value(seg[1]) for seg in segs if seg[0] == "plugin_version"), None)
        recorded = recorded if isinstance(recorded, str) and recorded else None
        behind = recorded_version(recorded, version) != recorded
        summary_text = "update the frontmatter"
        if behind and not changed:
            summary_text = (f"record neuroflow {version} as the version the project is up to date with "
                            f"(was {recorded or 'not recorded'})")
        if behind:
            emitted = emit_key("plugin_version", version)
            for seg in segs:
                if seg[0] == "plugin_version":
                    seg[1] = emitted
                    break
            else:
                segs.append(["plugin_version", emitted])
            changed = True
        if changed:
            fm = [line for seg in segs for line in seg[1]]
            new_text = "\n".join(["---", *fm, "---"]) + ("\n" + body if body else "\n")
            plan.write(config, new_text, summary_text, newline, diff_from=original)
        return

    # Legacy dialects: no frontmatter.
    lines = text.split("\n")
    entries = scan_legacy(lines)
    styles = {e["style"] for e in entries}
    plan.dialect = {frozenset(): "unrecognised", frozenset({"kv"}): "key: value lines",
                    frozenset({"bold"}): "bold labels"}.get(frozenset(styles), "mixed")
    facts: dict = {"nf_schema": KNOWN_SCHEMA}
    consumed: set[int] = set()
    legacy_version: str | None = None
    for entry in entries:
        value = entry_value(entry)
        origin = f"line {entry['start'] + 1}"
        if entry["personal"]:
            if value is None or isinstance(value, list):
                problems.notes.append(f"{entry['raw_key']} ({origin}) is not a single value; left in the notes.")
                continue
            target = entry["personal"]
            plan.personal.append({"key": entry["raw_key"], "value": personal_value(target, value), "target": target})
            if move_personal:
                consumed.update(range(entry["start"], entry["end"]))
            continue
        key = entry["key"]
        if key in ("nf_schema", "plugin_version"):
            if key == "plugin_version" and isinstance(value, str) and value:
                legacy_version = value
            consumed.update(range(entry["start"], entry["end"]))
            continue
        if key in facts:
            problems.notes.append(f"{key} appears more than once; the first value is used and line "
                                  f"{entry['start'] + 1} stays in the notes.")
            continue
        if value is None:
            problems.notes.append(f"{key} ({origin}) could not be parsed; left in the notes.")
            continue
        if key in overrides:
            consumed.update(range(entry["start"], entry["end"]))
            continue
        normalised = normalise(key, value, phases, problems, origin)
        if normalised is None:
            continue
        facts[key] = normalised
        consumed.update(range(entry["start"], entry["end"]))
    facts.update(overrides)
    facts.setdefault("recommended_phases", [])
    if "project_name" not in facts:
        facts["project_name"] = plan.root.name
        problems.notes.append(f"project_name taken from the folder name ({plan.root.name!r}); "
                              "change it with --set project_name=<name>.")
    if "active_phase" not in facts and not any("active_phase" in b for b in problems.blocking):
        problems.blocking.append("project_config.md names no phase. Ask the person which phase applies and "
                                 "rerun with --set active_phase=<id>.")
    kept_version = recorded_version(legacy_version, version)
    if kept_version:
        facts["plugin_version"] = kept_version
    body_lines = [line for n, line in enumerate(lines) if n not in consumed]
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(body_lines)).strip("\n")
    new_text = "\n".join(["---", *emit_frontmatter(facts), "---", ""]) + ("\n" + body + "\n" if body else "")
    plan.write(config, new_text, f"convert {plan.dialect} to frontmatter (nf_schema {KNOWN_SCHEMA})",
               newline, diff_from=original)


class RefusedError(Exception):
    pass


def plan_reasoning(plan: Plan) -> None:
    folder = plan.root / ".neuroflow" / "reasoning"
    if not folder.is_dir():
        return
    renamed: list[str] = []
    for src in sorted(folder.glob("*.json")):
        text = read_utf8(src)
        rel = plan.rel(src)
        if text is None:
            plan.problems.blocking.append(f"{rel} {NOT_UTF8}.")
            continue
        if CONFLICT_RE.search(text):
            plan.problems.blocking.append(f"{rel} contains merge-conflict markers; resolve them first.")
            continue
        try:
            data = json.loads(text) if text.strip() else []
        except ValueError as exc:
            plan.problems.blocking.append(f"{rel} is not valid JSON ({exc}); fix or remove it, then rerun.")
            continue
        if not isinstance(data, list):
            plan.problems.blocking.append(f"{rel} is not a JSON array; convert it by hand.")
            continue
        dst = src.with_suffix(".jsonl")
        seen: set[str] = set()
        existing = read_utf8(dst) if dst.exists() else ""
        if existing is None:
            plan.problems.blocking.append(f"{plan.rel(dst)} {NOT_UTF8}.")
            continue
        if CONFLICT_RE.search(existing):
            plan.problems.blocking.append(f"{plan.rel(dst)} contains merge-conflict markers; resolve them first.")
            continue
        for n, line in enumerate(existing.splitlines(), 1):
            if line.strip():
                try:
                    seen.add(json.dumps(json.loads(line), sort_keys=True, ensure_ascii=False))
                except ValueError:
                    plan.problems.blocking.append(f"{plan.rel(dst)} line {n} is not valid JSON; fix it first.")
                    break
        new_lines = []
        for element in data:
            key = json.dumps(element, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                new_lines.append(json.dumps(element, ensure_ascii=False))
        bak = src.with_name(src.name + ".bak")
        n = 1
        while bak.exists():
            bak = src.with_name(f"{src.name}.bak.{n}")
            n += 1
        body = existing.replace("\r\n", "\n")
        if body and not body.endswith("\n"):
            body += "\n"
        if new_lines or not dst.exists():
            plan.write(dst, body + "".join(line + "\n" for line in new_lines),
                       f"{len(new_lines)} entr{'y' if len(new_lines) == 1 else 'ies'} from {src.name} "
                       f"as JSON Lines" + (" (appended)" if dst.exists() else ""))
        plan.rename(src, bak, f"keep the old array as {bak.name}")
        renamed.append((src.name, bak.name))
    if not renamed:
        return
    index = folder / "flow.md"
    original = read_utf8(index) if index.is_file() else ""
    if original is None:
        plan.problems.blocking.append(f"{plan.rel(index)} {NOT_UTF8}.")
        return
    updated = original.replace("\r\n", "\n")
    for name, _ in renamed:
        updated = re.sub(rf"\b{re.escape(name)}\b(?!\.bak)", name + "l", updated)
    listed = {cell.strip().strip("`") for cell in re.findall(r"^\|([^|\n]*)\|", updated, re.MULTILINE)}
    today = date.today().isoformat()
    rows = []
    for name, bak_name in renamed:
        if name + "l" not in listed:
            rows.append(f"| {name}l | Decision log (JSON Lines). | {today} |")
        if bak_name not in listed:
            rows.append(f"| {bak_name} | Legacy JSON array kept by /neuroflow:migrate; no longer written. | {today} |")
    if not updated.strip():
        updated = "| File / Folder | Description | Last changed |\n|---|---|---|\n"
    if rows:
        updated = (updated if updated.endswith("\n") else updated + "\n") + "\n".join(rows) + "\n"
    if updated != original.replace("\r\n", "\n"):
        plan.write(index, updated, "index the .jsonl logs and the kept .json.bak files",
                   sc.detect_newline(original or None))


def plan_git_files(plan: Plan) -> None:
    for rel, header, wanted in ((".gitattributes", sc.GITATTRIBUTES_HEADER, sc.GITATTRIBUTES_LINES),
                                (".gitignore", sc.GITIGNORE_HEADER, sc.GITIGNORE_LINES)):
        target = plan.root / rel
        missing = sc.missing_lines(target, wanted)
        if missing:
            existing = read_utf8(target) if target.exists() else None
            if target.exists() and existing is None:
                plan.problems.blocking.append(f"{rel} {NOT_UTF8}.")
                continue
            plan.write(target, sc.append_lines_text(existing, header, missing),
                       f"add {len(missing)} line(s): {', '.join(missing)}", sc.detect_newline(existing))


def plan_instruction_blocks(plan: Plan) -> None:
    claude = plan.root / ".claude" / "CLAUDE.md"
    if not claude.exists():
        plan.write(claude, sc.CLAUDE_BLOCK, "create the static neuroflow instruction block")
    elif (original := read_utf8(claude)) is None:
        plan.problems.blocking.append(f"{plan.rel(claude)} {NOT_UTF8}.")
    else:
        text = original.replace("\r\n", "\n")
        span = sc.neuroflow_block_span(text)
        if span is None:
            body = text if not text or text.endswith("\n") else text + "\n"
            plan.write(claude, body + ("\n" if body else "") + sc.CLAUDE_BLOCK,
                       "append the static neuroflow instruction block", sc.detect_newline(original),
                       diff_from=original)
        elif sc.block_is_stale(text[span[0]:span[1]]):
            tail = text[span[1]:]
            new_block = sc.CLAUDE_BLOCK + ("\n" if tail else "")
            plan.write(claude, text[:span[0]] + new_block + tail,
                       "replace the neuroflow block that names a phase with the static block",
                       sc.detect_newline(original), diff_from=original)
    for path in (plan.home / ".claude" / "CLAUDE.md",
                 plan.root / ".github" / "copilot-instructions.md",
                 plan.root / "AGENTS.md"):
        if not path.is_file():
            continue
        text = sc.read_text(path).replace("\r\n", "\n")
        span = sc.neuroflow_block_span(text)
        if span is None:
            continue
        first = text.count("\n", 0, span[0]) + 1
        last = first + text[span[0]:span[1]].rstrip("\n").count("\n")
        where = ("your global ~/.claude/CLAUDE.md" if path == plan.home / ".claude" / "CLAUDE.md"
                 else "a mirror file neuroflow no longer writes")
        plan.report.append({"path": str(path), "lines": [first, last], "block": text[span[0]:span[1]].rstrip("\n"),
                            "message": f"neuroflow block in {where}; offer to remove it (show the block, ask first)"})


def plan_legacy_status(plan: Plan) -> None:
    """Report (never convert) a table-only ethics status: approval values need a person's confirmation."""
    status = plan.root / ".neuroflow" / "ethics" / "status.md"
    if not status.is_file():
        return
    split = sc.split_frontmatter(sc.read_text(status))
    if split is None or not any(re.match(r"^[A-Za-z_][\w-]*:(?:[ \t]|$)", line) for line in split[0]):
        plan.report.append({"path": plan.rel(status),
                            "message": "legacy ethics status without frontmatter; run /ethics --status, which shows "
                                       "the frontmatter and writes it only after the person confirms the values"})


def plan_personal(plan: Plan, move_personal: bool) -> None:
    if not plan.personal or not move_personal:
        return
    user_yaml = plan.home / ".neuroflow" / "user.yaml"
    existing: dict[str, str] = {}
    original = read_utf8(user_yaml) if user_yaml.is_file() else None
    if user_yaml.is_file() and original is None:
        plan.problems.blocking.append(f"~/.neuroflow/user.yaml {NOT_UTF8}.")
        return
    if original is not None:
        for line in original.splitlines():
            m = re.match(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*))?$", line)
            if m:
                existing[m.group(1)] = clean_scalar(m.group(2) or "")
    additions: list[str] = []
    for item in plan.personal:
        target, value = item["target"], item["value"]
        if target in existing:
            item["status"] = ("already in user.yaml" if existing[target] == value
                              else f"user.yaml keeps its own value {existing[target]!r}; the project value is dropped")
        elif any(line.startswith(f"{target}:") for line in additions):
            item["status"] = "duplicate in the project file; the first value is moved"
        else:
            plain = target in YES_NO_KEYS and value in {"yes", "no"}
            additions.append(f"{target}: {value if plain else sc.yaml_scalar(value)}")
            item["status"] = "moved to ~/.neuroflow/user.yaml"
    if additions:
        header = f"# moved from a project_config.md by /neuroflow:migrate on {date.today().isoformat()}"
        plan.write(user_yaml, sc.append_lines_text(original, header, additions),
                   f"add {len(additions)} personal field(s)", sc.detect_newline(original))


def build_plan(root: Path, home: Path, overrides: dict, move_personal: bool, version: str | None) -> Plan:
    plan = Plan(root, home)
    phases = canonical_phases()
    plan_config(plan, root / ".neuroflow" / "project_config.md", overrides, move_personal, version, phases)
    plan_reasoning(plan)
    plan_git_files(plan)
    plan_instruction_blocks(plan)
    plan_legacy_status(plan)
    plan_personal(plan, move_personal)
    return plan


def apply_plan(plan: Plan) -> None:
    # project_config.md last: it records plugin_version, so a run that stops part-way keeps the version notice.
    config = plan.root / ".neuroflow" / "project_config.md"
    for path, text, newline in [write for write in plan.writes if write[0] != config]:
        sc.write_text(path, text, newline)
    for src, dst in plan.renames:
        src.rename(dst)
    for path, text, newline in [write for write in plan.writes if write[0] == config]:
        sc.write_text(path, text, newline)


def parse_overrides(pairs: list[str], phases: set[str]) -> dict:
    overrides: dict = {}
    problems = Problems()
    for pair in pairs:
        if "=" not in pair:
            raise RefusedError(f"--set expects KEY=VALUE, got {pair!r}")
        key, value = (part.strip() for part in pair.split("=", 1))
        if key not in SETTABLE:
            raise RefusedError(f"--set {key}: not a settable key ({', '.join(sorted(SETTABLE))})")
        normalised = normalise(key, parse_inline_list(value) if key in LIST_KEYS else value, phases, problems, "--set")
        if normalised is None or problems.blocking or problems.notes:
            raise RefusedError("; ".join(problems.blocking + problems.notes) or f"--set {key}: invalid value")
        overrides[key] = normalised
    return overrides


def summary(plan: Plan, applied: bool, move_personal: bool) -> dict:
    pending_personal = [p for p in plan.personal if not move_personal]
    return {
        "root": str(plan.root),
        "dialect": plan.dialect,
        "applied": applied,
        "changes": plan.changes,
        "blocking": plan.problems.blocking,
        "notes": plan.problems.notes,
        "personal": plan.personal,
        "personal_pending": bool(pending_personal),
        "report": plan.report,
        "warnings": plan.warnings,
    }


def print_human(result: dict) -> None:
    mode = "applied" if result["applied"] else "dry run, nothing written"
    print(f"neuroflow migrate ({mode}): {result['root']}")
    print(f"  project_config.md dialect: {result['dialect']}")
    if result["changes"]:
        print("  changes:" if result["applied"] else "  planned changes:")
        for change in result["changes"]:
            print(f"    - {change['path']}: {change['summary']}")
            if change.get("diff") and not result["applied"]:
                for line in change["diff"].rstrip("\n").splitlines():
                    print(f"        {line}")
    else:
        print("  no changes needed")
    if result["blocking"]:
        print("  needs a decision (nothing is written while these remain):")
        for item in result["blocking"]:
            print(f"    - {item}")
    if result["personal"]:
        print("  personal fields (C1: they belong in ~/.neuroflow/user.yaml):")
        for item in result["personal"]:
            status = item.get("status") or "stays in the project file; rerun with --move-personal after asking"
            print(f"    - {item['key']}: {item['value']!r} -> {item['target']} ({status})")
    for note in result["notes"]:
        print(f"  note: {note}")
    for item in result["report"]:
        where = f" lines {item['lines'][0]}-{item['lines'][1]}" if item.get("lines") else ""
        print(f"  report only: {item['path']}{where}: {item['message']}")
    for warning in result["warnings"]:
        print(f"  warning: {warning}")
    if not result["applied"] and result["changes"] and not result["blocking"]:
        print("  run again with --apply to write these changes")


# ---------------------------------------------------------------------------
# Your flowie and team hives (--flowie, --hive NAME, --hives)
# ---------------------------------------------------------------------------

TASK_COLUMNS = ["inbox", "ready", "active", "review", "meeting", "done", "archive"]
LEGACY_TASK_KEYS = {"id", "assignee", "responsible", "level"}
NOT_TASK_FILES = {"flow.md", "readme.md", "index.md"}
SLUG_MAX = 40
# A legacy slug /tasks would accept as it is: kept verbatim, whatever its length (a slug is never renamed).
VALID_SLUG = re.compile(r"[a-z0-9-]*[a-z0-9][a-z0-9-]*")
FM_KEY_LINE = re.compile(r"^[A-Za-z_][\w-]*:(?:[ \t]|$)")
TASK_PROBLEMS = {
    "conflict": "merge-conflict markers; resolve them, then rerun",
    "not-utf8": "not UTF-8 — convert it, then rerun",
}
# The file each level keeps on this machine: listed in its .gitignore, never committed.
KEEP_LOCAL = {
    "flowie": ("integrations.json", "# neuroflow: settings that stay on this machine, never synced"),
    "hive": ("sync.json", "# neuroflow: each member's sync state stays on their machine"),
}
TRACKED = {
    "flowie": ("tracked by git, so it travels with your flowie; it belongs on this machine. "
               "`git -C {root} rm --cached integrations.json` and a commit stop tracking it. Older commits keep "
               "their copies: if one ever held a key, revoke that key; rewriting the history is your call"),
    "hive": ("tracked by the hive repository, so every member's sync state is shared. Agree with the team, then "
             "`git -C {root} rm --cached sync.json`, commit, and push after your yes"),
}
SYNC_HINT = {"flowie": "/flowie --sync", "hive": "/hive --sync"}


class GitError(OSError):
    pass


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(f"git {args[0]} could not run in {root}: {exc}") from exc


def git_ok(root: Path, *args: str) -> None:
    proc = git(root, *args)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed in {root}: {(proc.stderr or proc.stdout).strip()}")


def slugify(text: str) -> str:
    """The /tasks slug: lowercase ASCII, accents dropped, other runs -> '-', at most 40 characters."""
    folded = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
    if len(slug) > SLUG_MAX:
        cut = slug[:SLUG_MAX]
        if "-" in cut[SLUG_MAX // 2:]:
            cut = cut[:cut.rfind("-")]
        slug = cut.strip("-")
    return slug or "task"


def task_columns(tasks_dir: Path) -> tuple[list[str], str, str | None, str | None]:
    """(column ids in board order, the column of a task without status, the archive column, a note)."""
    columns: list[str] = []
    default = archive = note = None
    config = tasks_dir / "config.json"
    if config.is_file():
        try:
            entries = json.loads(sc.read_text(config)).get("columns", [])
        except (ValueError, AttributeError):
            entries, note = [], "tasks/config.json is not valid JSON; the default columns apply"
        for entry in entries if isinstance(entries, list) else []:
            cid = entry.get("id") if isinstance(entry, dict) else None
            if isinstance(cid, str) and cid.strip():
                columns.append(cid.strip())
                if entry.get("default") is True and default is None:
                    default = cid.strip()
                if entry.get("archive") is True and archive is None:
                    archive = cid.strip()
    columns = columns or list(TASK_COLUMNS)
    default = default or ("inbox" if "inbox" in columns else columns[0])
    archive = archive or ("archive" if "archive" in columns else None)
    return columns, default, archive, note


def column_for(status, columns: list[str], default: str, archive: str | None) -> str | None:
    """The column a legacy `status` names (`archived` = the archive column); None when it names none."""
    if not isinstance(status, str) or not status.strip():
        return default
    wanted = status.strip().lower()
    if wanted == "archived" and archive:
        return archive
    return next((column for column in columns if column.lower() == wanted), None)


def read_task(path: Path) -> dict | None:
    """A task file's frontmatter segments and body; None without a frontmatter block.

    `problem` names what keeps the file from being migrated (TASK_PROBLEMS). The file is decoded strictly as
    UTF-8: one that does not decode is never rewritten, since writing it back would replace every character
    that could not be read."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except UnicodeDecodeError:
        return {"problem": "not-utf8"}
    bom = "﻿" if raw.startswith("﻿") else ""
    text = raw[len(bom):].replace("\r\n", "\n")
    if CONFLICT_RE.search(text):
        return {"problem": "conflict"}
    split = sc.split_frontmatter(text)
    if split is None or not any(FM_KEY_LINE.match(line) for line in split[0]):
        return None
    segs = segment_frontmatter(split[0])
    return {"problem": None, "bom": bom, "segs": segs, "body": split[1], "newline": sc.detect_newline(raw),
            "values": {seg[0]: segment_value(seg[1]) for seg in segs if seg[0]}}


def handles_in(value) -> list[str]:
    """The people an `owner` / `assignee` / `responsible` value names: roster handles without the @."""
    items = value if isinstance(value, list) else [value]
    handles = [item.strip().lstrip("@").strip() for item in items if isinstance(item, str)]
    return [handle for handle in handles if handle]


def task_owners(task: dict) -> list[str]:
    """Each person the task names in `owner`, `assignee` or `responsible` (in that order), once."""
    people: dict[str, str] = {}
    for key in ("owner", "assignee", "responsible"):
        for seg_key, lines in task["segs"]:
            if seg_key == key:
                for handle in handles_in(segment_value(lines)):
                    people.setdefault(handle.lower(), handle)
    return list(people.values())


def blocked_by_of(task: dict) -> list[str] | None:
    """The `blocked_by` entries (slugs at the same level); None when the key is absent or not a list of slugs."""
    seg = next((seg for seg in task["segs"] if seg[0] == "blocked_by"), None)
    if seg is None:
        return None
    value = segment_value(seg[1])
    items = value if isinstance(value, list) else [value] if isinstance(value, str) and value else []
    return items if all(isinstance(item, str) for item in items) else None


def set_updated(out: list[list], today: str) -> None:
    """`updated` is set on every change, moves included (commands/tasks.md)."""
    updated = next((seg for seg in out if seg[0] == "updated"), None)
    if updated is None:
        after_created = next((n + 1 for n, seg in enumerate(out) if seg[0] == "created"), len(out))
        out.insert(after_created, ["updated", [f"updated: {today}"]])
    else:
        updated[1] = [f"updated: {today}"]


def task_text(task: dict, out: list[list]) -> str:
    fm = [line for seg in out for line in seg[1]]
    body = task["body"]
    return task["bom"] + "\n".join(["---", *fm, "---"]) + ("\n" + body if body else "\n")


def retargeted(old: list[str], new: list[str]) -> str:
    return "blocked_by: " + ", ".join(f"{a} -> {b}" for a, b in zip(old, new) if a != b)


def current_task_text(task: dict, column: str, today: str,
                      blocked_by: list[str] | None = None) -> tuple[str, list[str]]:
    """The task file with the keys /tasks defines (status = its column, owner, updated), and what changed.

    The caller has checked that the task names at most one person (task_owners): that person becomes `owner`.
    `blocked_by`, when given, replaces that key's entries (slugs this migration renamed)."""
    owners = task_owners(task)
    # An owner key counts only when it names someone: an empty one gives way to the legacy key's person.
    has_owner = any(key == "owner" and handles_in(segment_value(lines)) for key, lines in task["segs"])
    out: list[list] = []
    changed: list[str] = []
    for key, lines in task["segs"]:
        if key == "owner" and owners and not handles_in(segment_value(lines)):
            changed.append("empty owner dropped")
            continue
        if key in ("id", "level"):
            changed.append(f"{key} dropped")
            continue
        if key in ("assignee", "responsible"):
            if has_owner or not owners:  # the person is already the owner, or the key names nobody
                changed.append(f"{key} dropped")
                continue
            out.append(["owner", emit_key("owner", owners[0])])
            has_owner = True
            changed.append(f"{key} -> owner")
            continue
        if key == "blocked_by" and blocked_by is not None:
            changed.append(retargeted(blocked_by_of(task) or [], blocked_by))
            out.append([key, emit_key(key, blocked_by)])
            continue
        out.append([key, list(lines)])
    status = next((seg for seg in out if seg[0] == "status"), None)
    if status is None:
        after_title = next((n + 1 for n, seg in enumerate(out) if seg[0] == "title"), 0)
        out.insert(after_title, ["status", [f"status: {column}"]])
        changed.append(f"status: {column}")
    else:  # the folder is the column; an old comment listing the legacy values goes too
        if segment_value(status[1]) != column:
            changed.append(f"status: {segment_value(status[1]) or '(empty)'} -> {column}")
        status[1] = [f"status: {column}"]
    set_updated(out, today)
    return task_text(task, out), changed


def retargeted_task_text(task: dict, blocked_by: list[str], today: str) -> str:
    """A current task file with only its `blocked_by` entries (and `updated`) changed."""
    out = [[key, emit_key(key, blocked_by) if key == "blocked_by" else list(lines)] for key, lines in task["segs"]]
    set_updated(out, today)
    return task_text(task, out)


class LevelPlan:
    """One user-level folder (~/.neuroflow/flowie or a cached hive) and what migrating it changes."""

    def __init__(self, level: str, root: Path, home: Path, name: str | None = None) -> None:
        self.level, self.root, self.name = level, root, name
        try:
            self.shown = "~/" + root.relative_to(home).as_posix()
        except ValueError:
            self.shown = root.as_posix()
        self.is_repo = (root / ".git").exists()
        self.git = self.is_repo and shutil.which("git") is not None
        self.changes: list[dict] = []
        self.moves: list[tuple[Path, Path, str, str]] = []  # (src, dst, text, newline); dst == src: in place
        self.writes: list[tuple[Path, str, str]] = []
        self.blocking: list[str] = []
        self.report: list[dict] = []
        self.notes: list[str] = []
        self.commit_paths: list[str] = []

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def move(self, src: Path, dst: Path, text: str, newline: str, summary: str) -> None:
        self.moves.append((src, dst, text, newline))
        change = {"path": self.rel(src), "action": "write" if dst == src else "move", "summary": summary}
        if dst != src:
            change["to"] = self.rel(dst)
        self.changes.append(change)

    def write(self, path: Path, text: str, newline: str, summary: str) -> None:
        self.writes.append((path, text, newline))
        self.changes.append({"path": self.rel(path), "action": "write", "summary": summary})


def one_owner_or_report(plan: LevelPlan, path: Path, task: dict) -> bool:
    """True when the task names at most one person. /tasks gives a task one `owner` (a roster handle), so a legacy
    file naming several (assignee and responsible, or either beside an owner) is reported, never rewritten:
    migrating it must not drop a person."""
    people = task_owners(task)
    if len(people) <= 1:
        return True
    plan.report.append({"path": plan.rel(path), "message": (
        f"names {len(people)} people in owner / assignee / responsible ({', '.join(people)}), but a task has one "
        "owner (/tasks); choose who owns it (the others can go into the notes), then rerun")})
    return False


def plan_tasks(plan: LevelPlan, today: str) -> None:
    """Legacy task files -> tasks/{column}/{slug}.md with the current keys (commands/tasks.md).

    A slug is never renamed once written: a legacy file keeps its slug when /tasks would accept it as it is,
    whatever its length, and only a name /tasks would not write becomes a new slug. When a move cannot keep the
    name (invalid characters, a -N collision, or a legacy id the file no longer carries), the `blocked_by` entries
    at this level that name the task follow it; an entry that could now mean two tasks is reported instead."""
    tasks_dir = plan.root / "tasks"
    if not tasks_dir.is_dir():
        return
    columns, default, archive, note = task_columns(tasks_dir)
    if note:
        plan.notes.append(note)
    # The slugs at this level after the migration (lowercase -> as written); the slug is the task's id here.
    slugs = {path.stem.lower(): path.stem for folder in tasks_dir.iterdir() if folder.is_dir()
             for path in folder.glob("*.md")}
    entries: list[dict] = []  # the task files this run rewrites or moves, in the order they are planned
    held: list[tuple[Path, dict]] = []  # legacy files left as they are (reported), still checked for blocked_by
    for column in columns:  # files in their column folder: the folder is the column
        folder = tasks_dir / column
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            task = read_task(path)
            if task is None:
                continue
            if task["problem"]:
                plan.report.append({"path": plan.rel(path), "message": TASK_PROBLEMS[task["problem"]]})
                continue
            legacy = bool(LEGACY_TASK_KEYS & set(task["values"]))
            if legacy and not one_owner_or_report(plan, path, task):
                held.append((path, task))
                continue
            legacy_id = task["values"].get("id") if legacy and isinstance(task["values"].get("id"), str) else ""
            was = [legacy_id] if legacy_id and legacy_id.lower() != path.stem.lower() else []  # the dropped id
            entries.append({"path": path, "dst": path, "task": task, "column": column, "legacy": legacy, "was": was})
    for path in sorted(p for p in tasks_dir.glob("*.md") if p.is_file()):  # flat {id}-{slug}.md files
        if path.name.lower() in NOT_TASK_FILES:
            continue
        task = read_task(path)
        if task is None or task["problem"]:
            message = (TASK_PROBLEMS[task["problem"]] if task else
                       "not a task file (no frontmatter), so the board does not show it; move or remove it")
            plan.report.append({"path": plan.rel(path), "message": message})
            continue
        values = task["values"]
        column = column_for(values.get("status"), columns, default, archive)
        if column is None:
            plan.report.append({"path": plan.rel(path), "message": f"status {values.get('status')!r} is not a column "
                                f"of this board ({', '.join(columns)}); ask which column it belongs in, then "
                                "/tasks --move moves it"})
            continue
        if not one_owner_or_report(plan, path, task):
            held.append((path, task))
            continue
        legacy_id = values.get("id") if isinstance(values.get("id"), str) else ""
        stem = path.stem
        if legacy_id and stem.lower().startswith(legacy_id.lower() + "-"):
            stem = stem[len(legacy_id) + 1:]
        elif legacy_id and stem.lower() == legacy_id.lower():
            stem = ""
        title = values.get("title") if isinstance(values.get("title"), str) else ""
        base = stem if VALID_SLUG.fullmatch(stem) else slugify(stem or title)
        slug, n = base, 2
        while slug.lower() in slugs:
            slug, n = f"{base}-{n}", n + 1
        slugs[slug.lower()] = slug
        was = [name for name in dict.fromkeys([stem, legacy_id, path.stem]) if name and name != slug]
        entries.append({"path": path, "dst": tasks_dir / column / f"{slug}.md", "task": task, "column": column,
                        "legacy": True, "was": was})

    # The names a moved task leaves behind: each follows it, unless it may also name another task now.
    meanings: dict[str, set[str]] = {}
    for entry in entries:
        for name in entry["was"]:
            meanings.setdefault(name.lower(), set()).add(entry["dst"].stem)
    renamed: dict[str, str] = {}
    unclear: dict[str, list[str]] = {}
    for name, targets in meanings.items():
        if name in slugs and name not in {target.lower() for target in targets}:
            targets = targets | {slugs[name]}  # a task at this level still carries that slug
        if len(targets) == 1:
            renamed[name] = next(iter(targets))
        else:
            unclear[name] = sorted(targets)

    def follow(path: Path, task: dict) -> list[str] | None:
        """The task's blocked_by with renamed slugs followed (None: nothing to change); unclear entries reported."""
        items = blocked_by_of(task)
        if not items:
            return None
        for item in items:
            if item.lower() in unclear:
                plan.report.append({"path": plan.rel(path), "message": (
                    f"blocked_by names {item!r}, which may now mean {' or '.join(unclear[item.lower()])} (slugs changed "
                    "in this migration); check which task it means and edit the entry")})
        followed = [renamed.get(item.lower(), item) for item in items]
        return followed if followed != items else None

    for path, task in held:  # left as they are: say what their blocked_by should become
        followed = follow(path, task)
        if followed is not None:
            plan.report.append({"path": plan.rel(path), "message": (
                f"{retargeted(blocked_by_of(task) or [], followed)} (those tasks moved): edit the entries when you "
                "fix this file")})
    for entry in entries:
        path, task, column = entry["path"], entry["task"], entry["column"]
        followed = follow(path, task)
        if entry["legacy"]:
            text, changed = current_task_text(task, column, today, followed)
            if entry["dst"] == path:
                summary = "current task keys: " + "; ".join(changed)
            else:
                summary = "; ".join(["into its column folder", *changed])
            plan.move(path, entry["dst"], text, task["newline"], summary)
        elif followed is not None:
            plan.move(path, path, retargeted_task_text(task, followed, today), task["newline"],
                      retargeted(blocked_by_of(task) or [], followed))


def is_ignored(plan: LevelPlan, name: str) -> bool:
    if plan.git:
        code = git(plan.root, "check-ignore", "-q", "--no-index", "--", name).returncode
        if code in (0, 1):
            return code == 0
    ignore = plan.root / ".gitignore"
    return ignore.is_file() and not sc.missing_lines(ignore, [name])


def plan_level(plan: LevelPlan, today: str) -> None:
    if plan.level == "hive" and not plan.is_repo:
        # An older cache of copied files (phase-hive → Local hive cache): read-only here, and /hive --init
        # replaces it with a clone after the person confirms. Nothing is planned for it.
        plan.report.append({"path": plan.shown, "message": "not a git clone — /hive --init replaces it with a clone"})
        return
    if not plan.is_repo:
        plan.notes.append("not a git repository: changes are written in place, there is nothing to commit")
    elif not plan.git:
        plan.notes.append("git is not installed: task files move without git mv and nothing is staged")
    else:
        git_dir = plan.root / ".git"
        if any((git_dir / marker).exists() for marker in ("rebase-merge", "rebase-apply", "MERGE_HEAD")):
            plan.blocking.append(f"a rebase or merge is in progress; finish or abort it first ({SYNC_HINT[plan.level]})")
            return
    plan_tasks(plan, today)
    name, header = KEEP_LOCAL[plan.level]
    if not is_ignored(plan, name):
        ignore = plan.root / ".gitignore"
        existing = read_utf8(ignore) if ignore.exists() else None
        if ignore.exists() and existing is None:
            plan.report.append({"path": ".gitignore", "message": f"{NOT_UTF8}, so {name} is not added to it"})
        else:
            plan.write(ignore, sc.append_lines_text(existing, header, [name]), sc.detect_newline(existing),
                       f"add {name}: it stays on this machine")
    if plan.git and git(plan.root, "ls-files", "--error-unmatch", "--", name).returncode == 0:
        plan.report.append({"path": name, "message": TRACKED[plan.level].format(root=plan.shown)})


def build_levels(home: Path, flowie: bool, hive_names: list[str], all_hives: bool,
                 today: str) -> tuple[list[LevelPlan], list[str]]:
    base = home / ".neuroflow"
    plans: list[LevelPlan] = []
    notes: list[str] = []
    if flowie:
        if (base / "flowie").is_dir():
            plans.append(LevelPlan("flowie", base / "flowie", home))
        else:
            notes.append("no flowie at ~/.neuroflow/flowie - nothing to migrate there (/flowie sets one up)")
    hives_dir = base / "hives"
    cached = sorted(p.name for p in hives_dir.iterdir() if p.is_dir()) if hives_dir.is_dir() else []
    names: list[str] = []
    for name in hive_names:
        if name not in cached:
            raise RefusedError(f"no cached hive {name!r} under ~/.neuroflow/hives/ (cached: {', '.join(cached) or 'none'})")
        names.append(name)
    if all_hives:
        if not cached:
            notes.append("no cached hive under ~/.neuroflow/hives - nothing to migrate there (/hive --init joins one)")
        names += cached
    for name in dict.fromkeys(names):
        plans.append(LevelPlan("hive", hives_dir / name, home, name))
    for plan in plans:
        plan_level(plan, today)
    return plans, notes


def stage(plan: LevelPlan, path: Path) -> None:
    if plan.git:
        git_ok(plan.root, "add", "--", plan.rel(path))
        plan.commit_paths.append(plan.rel(path))


def apply_level(plan: LevelPlan) -> None:
    """Writes the plan; in a git repository tracked task files move with git mv and every change is staged."""
    for src, dst, text, newline in plan.moves:
        if dst != src:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if plan.git and git(plan.root, "ls-files", "--error-unmatch", "--", plan.rel(src)).returncode == 0:
                git_ok(plan.root, "mv", "--", plan.rel(src), plan.rel(dst))
                plan.commit_paths.append(plan.rel(src))
            else:
                src.rename(dst)
        sc.write_text(dst, text, newline)
        stage(plan, dst)
    for path, text, newline in plan.writes:
        sc.write_text(path, text, newline)
        stage(plan, path)


def level_summary(plan: LevelPlan) -> dict:
    return {"level": plan.level, "name": plan.name, "root": str(plan.root), "shown": plan.shown, "git": plan.git,
            "changes": plan.changes, "blocking": plan.blocking, "report": plan.report, "notes": plan.notes,
            "commit_paths": plan.commit_paths}


def print_levels(result: dict) -> None:
    mode = "applied" if result["applied"] else "dry run, nothing written"
    print(f"neuroflow migrate ({mode}): your flowie and team hives")
    for note in result["notes"]:
        print(f"  note: {note}")
    for level in result["levels"]:
        title = "flowie" if level["level"] == "flowie" else f"hive {level['name']}"
        print(f"  {title} ({level['shown']}):")
        if level["changes"]:
            print("    changes:" if result["applied"] else "    planned changes:")
            for change in level["changes"]:
                target = f" -> {change['to']}" if change.get("to") else ""
                print(f"      - {change['path']}{target}: {change['summary']}")
        else:
            print("    no changes needed")
        for item in level["blocking"]:
            print(f"    needs attention (nothing is written while it remains): {item}")
        for item in level["report"]:
            print(f"    report only: {item['path']}: {item['message']}")
        for note in level["notes"]:
            print(f"    note: {note}")
        if level["commit_paths"]:
            paths = " ".join(f'"{path}"' if " " in path else path for path in level["commit_paths"])
            print(f"    staged, not committed - commit exactly these paths (commit_paths in --json): {paths}")
    levels = result["levels"]
    if not result["applied"] and any(lv["changes"] for lv in levels) and not any(lv["blocking"] for lv in levels):
        print("  run again with --apply to write these changes (git changes are staged, never committed or pushed)")


def run_levels(args: argparse.Namespace, home: Path, fail) -> int:
    try:
        plans, notes = build_levels(home, args.flowie, args.hive, args.hives, date.today().isoformat())
    except RefusedError as exc:
        return fail(str(exc))
    except OSError as exc:
        return fail(f"could not read your flowie or hive: {exc}")
    blocked = any(plan.blocking for plan in plans)
    applied = False
    if args.apply and not blocked and any(plan.changes for plan in plans):
        try:
            for plan in plans:
                apply_level(plan)
        except OSError as exc:
            return fail(f"write failed part-way: {exc}. Rerun the dry run to see what is left.")
        applied = True
    has_report = any(plan.report for plan in plans)
    if applied:
        code = 1 if has_report else 0
    else:
        code = 1 if (blocked or has_report or any(plan.changes for plan in plans)) else 0
    result = {"levels": [level_summary(plan) for plan in plans], "applied": applied, "notes": notes,
              "exit_code": code}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_levels(result)
    return code


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()  # paths and task titles in any script survive a Windows pipe (the prose reads --json)
    ap = argparse.ArgumentParser(description="Migrate neuroflow's memory to the current contracts: the project "
                                             "(default), or your flowie and team hives. Dry run unless --apply.")
    ap.add_argument("--root", default=".", help="folder inside the project (default: current directory)")
    ap.add_argument("--apply", action="store_true", help="write the planned changes")
    ap.add_argument("--move-personal", action="store_true",
                    help="move personal fields to ~/.neuroflow/user.yaml (ask the person first)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="set a frontmatter value the person chose (repeatable)")
    ap.add_argument("--plugin-version", help="override the version read from the installed plugin.json")
    ap.add_argument("--flowie", action="store_true",
                    help="check your flowie (~/.neuroflow/flowie) instead of the project")
    ap.add_argument("--hive", action="append", default=[], metavar="NAME",
                    help="check the cached hive ~/.neuroflow/hives/NAME instead of the project (repeatable)")
    ap.add_argument("--hives", action="store_true",
                    help="check every cached hive under ~/.neuroflow/hives/ instead of the project")
    ap.add_argument("--home", help="the home folder that holds .neuroflow/ (default: your home directory)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    home = Path(args.home) if args.home else Path.home()

    def fail(message: str) -> int:
        if args.json:
            print(json.dumps({"error": message, "exit_code": 2}, indent=2))
        else:
            print(f"neuroflow migrate: refused: {message}")
        return 2

    if args.flowie or args.hive or args.hives:
        if args.set or args.move_personal:
            return fail("--set and --move-personal apply to the project; run them without --flowie, --hive or --hives")
        return run_levels(args, home, fail)

    root = sc.find_project_root(Path(args.root), home)
    if root is None:
        return fail(f"no .neuroflow/project_config.md found from {Path(args.root).resolve()} up to the "
                    "repository root. Run /neuroflow to set up a project.")
    version = args.plugin_version or sc.installed_plugin_version()
    try:
        overrides = parse_overrides(args.set, canonical_phases())
        plan = build_plan(root, home, overrides, args.move_personal, version)
    except RefusedError as exc:
        return fail(str(exc))
    except OSError as exc:
        return fail(f"could not read the project: {exc}")
    if version is None:
        plan.warnings.append("could not read the plugin version; plugin_version not updated")

    applied = False
    if args.apply and plan.changes and not plan.problems.blocking:
        try:
            apply_plan(plan)
        except OSError as exc:
            return fail(f"write failed part-way: {exc}. Rerun the dry run to see what is left.")
        applied = True
    result = summary(plan, applied, args.move_personal)
    pending = bool(result["blocking"] or result["personal_pending"] or result["report"] or result["notes"])
    if applied:
        code = 1 if pending else 0
    else:
        code = 1 if (plan.changes or pending) else 0
    result["exit_code"] = code
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_human(result)
    return code


if __name__ == "__main__":
    sys.exit(main())
