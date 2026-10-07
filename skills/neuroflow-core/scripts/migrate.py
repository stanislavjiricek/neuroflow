#!/usr/bin/env python3
"""Migrate a neuroflow project to the current project-memory contract (neuroflow-core).

Dry run by default: prints the plan (with a diff of project_config.md) and writes
nothing. --apply writes the plan. Idempotent: a migrated project has nothing to do.

Converts:
  - project_config.md: the legacy dialects (`key: value` lines, `**Bold:**` labels,
    or a mix) -> YAML frontmatter (nf_schema 1) followed by the free markdown body
  - personal fields (auto_issue_reporting, researcher name, writing_style,
    notification / wellbeing settings) -> ~/.neuroflow/user.yaml, only with --move-personal
  - reasoning/*.json arrays -> *.jsonl, one element per line; the old file is kept as *.json.bak
  - missing .gitattributes (merge=union) and .gitignore (local tier) lines
  - the project's .claude/CLAUDE.md neuroflow block -> the static block, when it names a phase
Only reports (never edits):
  - neuroflow blocks in ~/.claude/CLAUDE.md, .github/copilot-instructions.md and AGENTS.md

Usage:
  python <neuroflow-core base dir>/scripts/migrate.py [--root DIR] [--apply]
      [--move-personal] [--set KEY=VALUE ...] [--json]

Exit codes:
  0  nothing to do (already current), or --apply finished with nothing left to report
  1  findings: changes to apply, decisions needed (--set), personal fields still in the
     project file, or report-only items; with --apply and a blocking item, nothing is written
  2  refused or failed: nf_schema newer than this script knows, no project found,
     unreadable files, bad arguments

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import re
import sys
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
}
PERSONAL_PREFIXES = ("notification", "wellbeing")

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
    if target == "auto_issue_reporting":
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
    original = sc.read_text(config)
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
        if changed and version:
            emitted = emit_key("plugin_version", version)
            for seg in segs:
                if seg[0] == "plugin_version":
                    seg[1] = emitted
                    break
            else:
                segs.append(["plugin_version", emitted])
        if changed:
            fm = [line for seg in segs for line in seg[1]]
            new_text = "\n".join(["---", *fm, "---"]) + ("\n" + body if body else "\n")
            plan.write(config, new_text, "update the frontmatter", newline, diff_from=original)
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
    if version or legacy_version:
        facts["plugin_version"] = version or legacy_version
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
        text = sc.read_text(src)
        rel = plan.rel(src)
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
        existing = sc.read_text(dst) if dst.exists() else ""
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
    original = sc.read_text(index) if index.is_file() else ""
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
            existing = sc.read_text(target) if target.exists() else None
            plan.write(target, sc.append_lines_text(existing, header, missing),
                       f"add {len(missing)} line(s): {', '.join(missing)}", sc.detect_newline(existing))


def plan_instruction_blocks(plan: Plan) -> None:
    claude = plan.root / ".claude" / "CLAUDE.md"
    if not claude.exists():
        plan.write(claude, sc.CLAUDE_BLOCK, "create the static neuroflow instruction block")
    else:
        original = sc.read_text(claude)
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
    if user_yaml.is_file():
        for line in sc.read_text(user_yaml).splitlines():
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
            plain = target == "auto_issue_reporting" and value in {"yes", "no"}
            additions.append(f"{target}: {value if plain else sc.yaml_scalar(value)}")
            item["status"] = "moved to ~/.neuroflow/user.yaml"
    if additions:
        original = sc.read_text(user_yaml) if user_yaml.exists() else None
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
    for path, text, newline in plan.writes:
        sc.write_text(path, text, newline)
    for src, dst in plan.renames:
        src.rename(dst)


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Migrate a neuroflow project to the current memory contract. "
                                             "Dry run unless --apply.")
    ap.add_argument("--root", default=".", help="folder inside the project (default: current directory)")
    ap.add_argument("--apply", action="store_true", help="write the planned changes")
    ap.add_argument("--move-personal", action="store_true",
                    help="move personal fields to ~/.neuroflow/user.yaml (ask the person first)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="set a frontmatter value the person chose (repeatable)")
    ap.add_argument("--plugin-version", help="override the version read from the installed plugin.json")
    ap.add_argument("--home", help=argparse.SUPPRESS)  # tests only: stands in for the home directory
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
