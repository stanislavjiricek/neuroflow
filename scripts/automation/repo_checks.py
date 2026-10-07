#!/usr/bin/env python3
"""repo_checks - the one implementation of every mechanical check on the neuroflow plugin repo.

validate_pr.py runs this registry on every PR (CI) and locally; sentinel_check.py runs it
daily and posts the report; agents/sentinel-dev.md cites the same ids and adds only the
judgement checks. Stdlib only. Every check takes the repo root from a Context, so the tests
in tests/automation/ run them on fixture repos.

Ids are stable: never renumber or reuse one - retire it instead.

  V1   manifests are valid JSON (plugin.json, marketplace.json, hooks/hooks.json)
  V2   version sync: plugin.json = marketplace.json plugins[].version = mkdocs.yml extra.version
       = .neuroflow/project_config.md plugin_version (the four sites bump_version.py writes)
  V3   command frontmatter: name (= filename), description, phase (canonical), reads, writes,
       lifecycle (full | light | quiet); optional requires / produces / next lists, where
       next names existing commands; optional argument-hint
  V4   every command has a docs page docs/commands/<name>.md
  V5   skill folder = SKILL.md name; agent filename = agent name; boolean skill flags
  V6   hooks/hooks.json: hook structure; every command hook ends with `; true` or `|| true`;
       an optional `modules` key names exactly one existing hooks-module file
  V7   (needs a base ref) substantive changes bump the plugin.json version
  V8   rule markers: every <!-- nf-rule: ID --> uses an id from neuroflow-core's rule table,
       and every id a mod guard cites (hooks/mod/) has a marker in skills/ or commands/
  V9   name collisions: no skill folder shares a command's name (the command shadows it)
  V10  propagation: every command, skill and agent appears in README.md, the mkdocs nav and
       mind.js; README tables, nav and mind.js have no dead links
  V11  dead neuroflow:<name> references inside SKILL.md files
  V12  release notes (warn): README What's new, docs/changelog.md, docs/index.md sa-bar version
  V13  plugin-repo memory (warn): the repo's own .neuroflow/ holds only reasoning/ and sessions/
  V14  sensitive info: PEM private keys (fail); emails and hardcoded secrets (warn, human review)
  V15  path hygiene (warn): stale flowie/hive paths and legacy field names
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
CORE_SKILL = "skills/neuroflow-core/SKILL.md"
FAIL, WARN = "fail", "warn"
FIX_VERSION_SYNC = "version-sync"


def _load_nf_check():
    """Reuse the frontmatter parser and phase reader of nf_check.py (one parser, not three)."""
    path = Path(__file__).resolve().parents[2] / "skills" / "neuroflow-core" / "scripts" / "nf_check.py"
    name = "neuroflow_nf_check"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nf = _load_nf_check()


@dataclass(frozen=True)
class Finding:
    check: str
    message: str
    severity: str = FAIL
    fix: str = ""  # FIX_VERSION_SYNC when sentinel_check.py may apply it


@dataclass
class Context:
    root: Path
    base: str | None = None


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    func: Callable[[Context], list[Finding]]
    needs_base: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return nf._read(path)


def read_raw(path: Path) -> str:
    """Read keeping line endings as they are (writers must not turn LF into CRLF)."""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write_raw(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def read_frontmatter(path: Path) -> dict | None:
    return nf.split_frontmatter(_read(path))[0]


def command_names(root: Path) -> set[str]:
    return {p.stem for p in (root / "commands").glob("*.md")}


def skill_names(root: Path) -> set[str]:
    return {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}


def agent_names(root: Path) -> set[str]:
    return {p.stem for p in (root / "agents").glob("*.md")}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False).stdout.strip()


# ---------------------------------------------------------------------------
# Version sites (V2, bump_version.py, sentinel_check.py auto-fix)
# ---------------------------------------------------------------------------

PLUGIN_JSON = ".claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
MKDOCS_YML = "mkdocs.yml"
REPO_CONFIG = ".neuroflow/project_config.md"
VERSION_SITES = (PLUGIN_JSON, MARKETPLACE_JSON, MKDOCS_YML, REPO_CONFIG)
_SITE_FIELD = {
    PLUGIN_JSON: "version",
    MARKETPLACE_JSON: "plugins[].version",
    MKDOCS_YML: "extra.version",
    REPO_CONFIG: "plugin_version",
}
_JSON_VERSION_RE = re.compile(r'("version"\s*:\s*")([^"]*)(")')
_CONFIG_VERSION_RES = (
    re.compile(r"(?m)^(plugin_version:[ \t]*[\"']?)([^\"'\s#]+)"),
    re.compile(r"(\*\*Plugin version:\*\*[ \t]*)(\S+)"),
)


def _mkdocs_extra_version_span(text: str) -> tuple[int, int] | None:
    """Character span of the `extra:` -> `version:` value (never another `version:` key)."""
    m = re.search(r"(?m)^extra:[ \t]*$", text)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"(?m)^(?=\S)", text[start + 1:])
    end = start + 1 + nxt.start() if nxt else len(text)
    best = None
    for vm in re.finditer(r"(?m)^([ \t]+)version:[ \t]*[\"']?([^\"'\s#]+)", text[start:end]):
        if best is None or len(vm.group(1)) < len(best.group(1)):
            best = vm
    return (start + best.start(2), start + best.end(2)) if best else None


def site_versions(root: Path, rel: str) -> list[str] | None:
    """Versions recorded at one site; None when the file is absent, [] when none is found."""
    path = root / rel
    if not path.is_file():
        return None
    text = read_raw(path)
    if rel in (PLUGIN_JSON, MARKETPLACE_JSON):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        if rel == PLUGIN_JSON:
            v = data.get("version") if isinstance(data, dict) else None
            return [v] if isinstance(v, str) and v else []
        plugins = data.get("plugins") if isinstance(data, dict) else None
        return [str(e.get("version") or "") for e in plugins or [] if isinstance(e, dict)]
    if rel == MKDOCS_YML:
        span = _mkdocs_extra_version_span(text)
        return [text[span[0]:span[1]]] if span else []
    for rx in _CONFIG_VERSION_RES:
        m = rx.search(text)
        if m:
            return [m.group(2)]
    return []


def set_site_version(root: Path, rel: str, version: str) -> bool:
    """Rewrite only the version string at one site, keeping formatting. True if changed."""
    path = root / rel
    if not path.is_file():
        return False
    text = read_raw(path)
    if rel == PLUGIN_JSON:
        new = _JSON_VERSION_RE.sub(lambda m: m.group(1) + version + m.group(3), text, count=1)
    elif rel == MARKETPLACE_JSON:
        i = text.find('"plugins"')
        if i == -1:
            return False
        new = text[:i] + _JSON_VERSION_RE.sub(lambda m: m.group(1) + version + m.group(3), text[i:])
    elif rel == MKDOCS_YML:
        span = _mkdocs_extra_version_span(text)
        if not span:
            return False
        new = text[:span[0]] + version + text[span[1]:]
    else:
        new = text
        for rx in _CONFIG_VERSION_RES:
            if rx.search(text):
                new = rx.sub(lambda m: m.group(1) + version, text, count=1)
                break
    if new == text:
        return False
    write_raw(path, new)
    return True


def sync_versions(root: Path, version: str | None = None) -> list[str]:
    """Write `version` (default: plugin.json's) to every site that differs; return the changed sites."""
    if version is None:
        current = site_versions(root, PLUGIN_JSON) or []
        if not current:
            return []
        version = current[0]
    changed = []
    for rel in VERSION_SITES:
        found = site_versions(root, rel)
        if found is not None and any(v != version for v in found) and set_site_version(root, rel, version):
            changed.append(rel)
    return changed


# ---------------------------------------------------------------------------
# V1 - V7: structure, frontmatter, manifests, hooks, versions
# ---------------------------------------------------------------------------

MANIFESTS = (PLUGIN_JSON, MARKETPLACE_JSON, "hooks/hooks.json")
LIFECYCLES = ("full", "light", "quiet")
REQUIRED_COMMAND_KEYS = ("name", "description", "phase", "reads", "writes", "lifecycle")
OPTIONAL_LIST_KEYS = ("requires", "produces", "next")
BOOLEAN_SKILL_FLAGS = ("user-invocable", "disable-model-invocation")


def v1_json(ctx: Context) -> list[Finding]:
    out = []
    for rel in MANIFESTS:
        path = ctx.root / rel
        if not path.is_file():
            out.append(Finding("V1", f"{rel} is missing"))
            continue
        try:
            json.loads(_read(path))
        except json.JSONDecodeError as exc:
            out.append(Finding("V1", f"{rel} is not valid JSON: {exc}"))
    return out


def v2_versions(ctx: Context) -> list[Finding]:
    found = site_versions(ctx.root, PLUGIN_JSON)
    if found is None:
        return []  # V1 reports the missing manifest
    if not found:
        return [Finding("V2", f"{PLUGIN_JSON} has no version field")]
    want = found[0]
    out = []
    for rel in (MARKETPLACE_JSON, MKDOCS_YML, REPO_CONFIG):
        got = site_versions(ctx.root, rel)
        if got is None:
            if rel == MKDOCS_YML:
                out.append(Finding("V2", f"{rel} is missing"))
            continue  # V1 reports marketplace.json; the repo memory file is optional
        if not got:
            out.append(Finding("V2", f"{rel} records no {_SITE_FIELD[rel]}"))
        for v in got:
            if v != want:
                out.append(Finding("V2", f"{rel} {_SITE_FIELD[rel]} {v!r} != plugin.json {want!r} "
                                         "(python scripts/automation/bump_version.py --sync)", fix=FIX_VERSION_SYNC))
    return out


def v3_commands(ctx: Context) -> list[Finding]:
    out = []
    phases = nf.canonical_phases(ctx.root)
    if not phases:
        out.append(Finding("V3", f"could not find the canonical phase list (**Valid `phase:` frontmatter values:**) in {CORE_SKILL}"))
    commands = command_names(ctx.root)
    for cmd in sorted((ctx.root / "commands").glob("*.md")):
        rel = f"commands/{cmd.name}"
        fm = read_frontmatter(cmd)
        if fm is None:
            out.append(Finding("V3", f"{rel} has no frontmatter block"))
            continue
        for key in REQUIRED_COMMAND_KEYS:
            if key not in fm:
                hint = " (full | light | quiet - see neuroflow-core, Command frontmatter standard)" if key == "lifecycle" else ""
                out.append(Finding("V3", f"{rel} frontmatter is missing `{key}:`{hint}"))
        name = fm.get("name")
        if name and name != cmd.stem:
            out.append(Finding("V3", f"{rel} frontmatter name `{name}` != filename `{cmd.stem}`"))
        phase = fm.get("phase")
        if phases and phase and phase not in phases:
            out.append(Finding("V3", f"{rel} declares phase `{phase}` - not in the canonical taxonomy "
                                     f"({', '.join(sorted(phases))})"))
        lifecycle = fm.get("lifecycle")
        if "lifecycle" in fm and lifecycle not in LIFECYCLES:
            out.append(Finding("V3", f"{rel} has `lifecycle: {lifecycle}` - must be one of {', '.join(LIFECYCLES)}"))
        for key in OPTIONAL_LIST_KEYS:
            value = fm.get(key)
            if key not in fm or value is None:
                continue
            if not isinstance(value, list):
                out.append(Finding("V3", f"{rel} `{key}:` must be a list"))
            elif any(not isinstance(v, str) or not v.strip() for v in value):
                out.append(Finding("V3", f"{rel} `{key}:` entries must be non-empty strings"))
        next_list = fm.get("next") if isinstance(fm.get("next"), list) else []
        for target in next_list:
            if not isinstance(target, str) or not target.strip():
                continue
            bare = target.strip()
            if bare.startswith("/") or ":" in bare:
                out.append(Finding("V3", f"{rel} `next:` entry `{bare}` - use bare command names (no slash, no namespace)"))
            elif bare not in commands:
                out.append(Finding("V3", f"{rel} `next:` names `{bare}`, which is not a command"))
        hint = fm.get("argument-hint")
        if "argument-hint" in fm and (not isinstance(hint, str) or not hint.strip()):
            out.append(Finding("V3", f"{rel} `argument-hint:` must be a non-empty string"))
    return out


def v4_docs_pages(ctx: Context) -> list[Finding]:
    return [
        Finding("V4", f"commands/{name}.md has no docs page at docs/commands/{name}.md")
        for name in sorted(command_names(ctx.root))
        if not (ctx.root / "docs" / "commands" / f"{name}.md").is_file()
    ]


def v5_names(ctx: Context) -> list[Finding]:
    out = []
    for skill_md in sorted((ctx.root / "skills").glob("*/SKILL.md")):
        folder = skill_md.parent.name
        rel = f"skills/{folder}/SKILL.md"
        fm = read_frontmatter(skill_md)
        if fm is None:
            out.append(Finding("V5", f"{rel} has no frontmatter block"))
            continue
        name = fm.get("name")
        if not name:
            out.append(Finding("V5", f"{rel} frontmatter is missing `name:`"))
        elif name != folder:
            out.append(Finding("V5", f"{rel} frontmatter name `{name}` != folder `{folder}`"))
        for flag in BOOLEAN_SKILL_FLAGS:
            if flag in fm and str(fm[flag]).lower() not in ("true", "false"):
                out.append(Finding("V5", f"{rel} `{flag}: {fm[flag]}` must be true or false"))
    for agent in sorted((ctx.root / "agents").glob("*.md")):
        fm = read_frontmatter(agent) or {}
        name = fm.get("name")
        if not name:
            out.append(Finding("V5", f"agents/{agent.name} frontmatter is missing `name:`"))
        elif name != agent.stem:
            out.append(Finding("V5", f"agents/{agent.name} frontmatter name `{name}` != filename `{agent.stem}`"))
    return out


_SUPPRESSED_RE = re.compile(r"(;|\|\|)\s*true\s*$")
_MODULE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}


def v6_hooks(ctx: Context) -> list[Finding]:
    path = ctx.root / "hooks" / "hooks.json"
    try:
        data = json.loads(_read(path)) if path.is_file() else None
    except json.JSONDecodeError:
        return []  # V1 reports it
    if data is None:
        return []
    if not isinstance(data, dict):
        return [Finding("V6", "hooks/hooks.json must be a JSON object")]
    out = []
    unknown = sorted(set(data) - {"description", "hooks", "modules"})
    if unknown:
        out.append(Finding("V6", f"hooks/hooks.json has unknown top-level key(s): {', '.join(unknown)}", WARN))
    if "hooks" not in data and "modules" not in data:
        out.append(Finding("V6", "hooks/hooks.json needs `hooks`, `modules`, or both"))
    hooks = data.get("hooks") or {}
    if not isinstance(hooks, dict):
        out.append(Finding("V6", "`hooks` must map event names to lists"))
        hooks = {}
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            out.append(Finding("V6", f"`{event}` must be a list of hook groups"))
            continue
        for group in groups:
            if not isinstance(group, dict):
                out.append(Finding("V6", f"`{event}` has a hook group that is not an object"))
                continue
            if "matcher" in group and not isinstance(group["matcher"], str):
                out.append(Finding("V6", f"`{event}` matcher must be a string"))
            entries = group.get("hooks")
            if not isinstance(entries, list) or not entries:
                out.append(Finding("V6", f"`{event}` (matcher {group.get('matcher', '-')}) has an empty `hooks` list"))
                continue
            for hook in entries:
                if not isinstance(hook, dict) or "type" not in hook:
                    out.append(Finding("V6", f"`{event}` has a hook without `type`"))
                    continue
                if hook["type"] != "command":
                    continue
                cmd = hook.get("command")
                if not isinstance(cmd, str) or not cmd.strip():
                    out.append(Finding("V6", f"`{event}` command hook has no `command`"))
                elif not _SUPPRESSED_RE.search(cmd):
                    out.append(Finding("V6", f"`{event}` hook command does not end with `; true` or `|| true` "
                                             f"(hooks must fail silently): {cmd[:60]}..."))
    if "modules" in data:
        mods = data["modules"]
        if not isinstance(mods, list) or len(mods) != 1 or not isinstance(mods[0], str) or not mods[0].strip():
            out.append(Finding("V6", "`modules` must be a list with exactly one module path "
                                     "(Claude Code loads one hooks module per plugin and refuses a second entry)"))
        else:
            rel = mods[0].strip()
            candidates = (path.parent / rel, ctx.root / rel)
            target = next((c for c in candidates if c.is_file()), None)
            if target is None:
                out.append(Finding("V6", f"`modules` entry `{rel}` does not resolve to a file (relative to hooks/)"))
            elif target.suffix not in _MODULE_SUFFIXES:
                out.append(Finding("V6", f"`modules` entry `{rel}` is not a .ts/.tsx/.js module file", WARN))
    return out


NO_BUMP_FILES = frozenset({PLUGIN_JSON, MARKETPLACE_JSON, MKDOCS_YML, "README.md", "docs/changelog.md"})
NO_BUMP_PREFIXES = (".github/", "scripts/automation/", ".githooks/", ".neuroflow/", "tests/")


def substantive_changes(paths) -> list[str]:
    """Changed paths that need a version bump (shared with .githooks/pre-push)."""
    return [p for p in paths if p and p not in NO_BUMP_FILES and not p.startswith(NO_BUMP_PREFIXES)]


def v7_version_bump(ctx: Context) -> list[Finding]:
    changed = _git(ctx.root, "diff", "--name-only", f"{ctx.base}...HEAD").splitlines()
    substantive = substantive_changes(changed)
    if not substantive:
        return []
    try:
        old = json.loads(_git(ctx.root, "show", f"{ctx.base}:{PLUGIN_JSON}") or "{}").get("version")
    except (json.JSONDecodeError, AttributeError):
        old = None
    new = (site_versions(ctx.root, PLUGIN_JSON) or [None])[0]
    if old and new and old == new:
        return [Finding("V7", f"{len(substantive)} substantive file(s) changed vs {ctx.base} but plugin.json is still "
                              f"{new} - bump the patch version (python scripts/automation/bump_version.py)")]
    return []


# ---------------------------------------------------------------------------
# V8 - V11: rule markers, collisions, propagation, references
# ---------------------------------------------------------------------------

RULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
MARKER_RE = re.compile(r"<!--\s*nf-rule:\s*([A-Za-z0-9_-]+)\s*-->")
# A guard cites its rule as the literal `nf-rule: RULE-ID` (comment or reason string);
# placeholders such as `nf-rule: ID` in documentation are not ids.
GUARD_CITE_RE = re.compile(r"nf-rule:\s*([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")
# The initial rule set of the contracts; used only while neuroflow-core has no rule table.
C7_INITIAL_IDS = frozenset({
    "PREREG-FROZEN", "RAW-READONLY", "MEMORY-PURITY", "GIT-NO-SECRETS", "GIT-ALIAS-SCOPE",
    "ETHICS-GATE", "EGRESS-CONFIRM", "PARTICIPANT-ROUTE", "LOGIN-NODE",
})
_GUARD_SUFFIXES = _MODULE_SUFFIXES | {".json"}


def _heading_section(text: str, pattern: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,6})\s+(.*)$", line)
        if m and re.search(pattern, m.group(2), re.I):
            level = len(m.group(1))
            for j in range(i + 1, len(lines)):
                h = re.match(r"^(#{1,6})\s", lines[j])
                if h and len(h.group(1)) <= level:
                    return "\n".join(lines[i:j])
            return "\n".join(lines[i:])
    return ""


def rule_ids(root: Path) -> tuple[set[str], bool]:
    """Rule ids from neuroflow-core's rule-marker table: (ids, read_from_core)."""
    core = _read(root / CORE_SKILL)
    for text in (_heading_section(core, r"rule marker|nf-rule"), core):
        ids = {c.strip().strip("`*").strip() for c in nf.table_first_cells(text)}
        ids = {c for c in ids if RULE_ID_RE.match(c)}
        if ids:
            return ids, True
    return set(C7_INITIAL_IDS), False


def _prose_files(root: Path) -> list[Path]:
    files = sorted((root / "skills").rglob("*.md")) + sorted((root / "commands").glob("*.md"))
    return files + sorted((root / "agents").glob("*.md"))


def _markers(line: str) -> list[str]:
    """Marker ids on a prose line, skipping examples inside `inline code`."""
    return [m.group(1) for m in MARKER_RE.finditer(line) if line[:m.start()].count("`") % 2 == 0]


def v8_rule_markers(ctx: Context) -> list[Finding]:
    out = []
    ids, from_core = rule_ids(ctx.root)
    if not from_core:
        out.append(Finding("V8", f"no rule-marker table found in {CORE_SKILL}; checked against the initial rule set", WARN))
    marked: set[str] = set()
    for path in _prose_files(ctx.root):
        rel = path.relative_to(ctx.root).as_posix()
        lines = _read(path).splitlines()
        fenced = False
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
            if fenced:
                continue
            for rid in _markers(line):
                if rid not in ids:
                    out.append(Finding("V8", f"{rel}:{i + 1} marker uses unknown rule id `{rid}` "
                                             f"(known: {', '.join(sorted(ids))})"))
                    continue
                if not rel.startswith("agents/"):
                    marked.add(rid)
                if MARKER_RE.fullmatch(line.strip()) and (i + 1 >= len(lines) or not lines[i + 1].strip()):
                    out.append(Finding("V8", f"{rel}:{i + 1} marker `{rid}` must sit on the line before its rule", WARN))
    mod_dir = ctx.root / "hooks" / "mod"
    if mod_dir.is_dir():
        guard_files = (p for p in mod_dir.rglob("*") if p.is_file() and p.suffix in _GUARD_SUFFIXES
                       and "tests" not in p.relative_to(mod_dir).parts and ".test." not in p.name)
        for path in sorted(guard_files):
            rel = path.relative_to(ctx.root).as_posix()
            for rid in sorted(set(GUARD_CITE_RE.findall(_read(path)))):
                if rid not in ids:
                    out.append(Finding("V8", f"{rel} cites unknown rule id `{rid}`"))
                elif rid not in marked:
                    out.append(Finding("V8", f"{rel} enforces `{rid}`, but no `<!-- nf-rule: {rid} -->` marker exists in "
                                             "skills/ or commands/ (a guard may only enforce a rule the prose states)"))
    for rid in sorted(ids - marked):
        out.append(Finding("V8", f"rule `{rid}` has no marker in skills/ or commands/ yet", WARN))
    return out


def v9_collisions(ctx: Context) -> list[Finding]:
    skills, commands, agents = skill_names(ctx.root), command_names(ctx.root), agent_names(ctx.root)
    out = [
        Finding("V9", f"skills/{name}/ has the same name as commands/{name}.md - the command shadows the skill, so "
                      f"'read the neuroflow:{name} skill' loads the command (rename the skill folder)")
        for name in sorted(skills & commands)
    ]
    out += [
        Finding("V9", f"agents/{name}.md and skills/{name}/ share a name - confusing in references", WARN)
        for name in sorted(agents & skills)
    ]
    return out


def mkdocs_nav_paths(mkdocs_text: str) -> list[str]:
    lines = mkdocs_text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if re.match(r"^nav:\s*$", line))
    except StopIteration:
        return []
    paths = []
    for line in lines[start + 1:]:
        if line and not line[0].isspace() and not line.startswith("-"):
            break
        m = re.search(r"([A-Za-z0-9_./-]+\.md)[\"']?\s*$", line)
        if m:
            paths.append(m.group(1))
    return paths


def v10_propagation(ctx: Context) -> list[Finding]:
    out = []
    root = ctx.root
    commands, skills, agents = sorted(command_names(root)), sorted(skill_names(root)), sorted(agent_names(root))
    readme = _read(root / "README.md")
    for name in commands:
        if f"](commands/{name}.md)" not in readme:
            out.append(Finding("V10", f"commands/{name}.md has no link in README.md (Commands table row missing?)"))
    for name in skills:
        if f"](skills/{name}/SKILL.md)" not in readme:
            out.append(Finding("V10", f"skills/{name}/ has no link in README.md (Skills table row missing?)"))
    for name in agents:
        if f"](agents/{name}.md)" not in readme:
            out.append(Finding("V10", f"agents/{name}.md has no link in README.md (Agents table row missing?)"))
    # Only from "## Why neuroflow" on: the What's new history may link to removed files.
    region = readme[readme.find("## Why neuroflow"):] if "## Why neuroflow" in readme else readme
    for target in re.findall(r"\]\(((?:commands|skills|agents|\.github)/[^)#\s]+)\)", region):
        if not (root / target).exists():
            out.append(Finding("V10", f"README.md links to non-existent file `{target}`"))

    nav = mkdocs_nav_paths(_read(root / MKDOCS_YML))
    navset = set(nav)
    for name in commands:
        if f"commands/{name}.md" not in navset:
            out.append(Finding("V10", f"commands/{name}.md is not in the mkdocs.yml nav"))
    for name in skills:
        if f"skills/{name}/SKILL.md" not in navset:
            out.append(Finding("V10", f"skills/{name}/SKILL.md is not in the mkdocs.yml nav"))
    for name in agents:
        if f"agents/{name}.md" not in navset:
            out.append(Finding("V10", f"agents/{name}.md is not in the mkdocs.yml nav"))
    for path in sorted(navset):
        # skills/ and agents/ are copied into docs/ at build time (docs/hooks.py)
        full = root / path if path.startswith(("skills/", "agents/")) else root / "docs" / path
        if not full.exists():
            out.append(Finding("V10", f"mkdocs.yml nav references non-existent file `{path}`"))

    # mind.js is a curated concept map, not a 1:1 mirror: every command must be reachable
    # (`/name` or a commands/name/ url), every agent named, every url must resolve.
    mind = root / "docs" / "javascripts" / "mind.js"
    if mind.is_file():
        text = _read(mind)
        for name in commands:
            if f"/{name}" not in text and f"commands/{name}/" not in text:
                out.append(Finding("V10", f"commands/{name}.md is not referenced in docs/javascripts/mind.js "
                                          f"(no `/{name}` and no `commands/{name}/` url)"))
        for name in agents:
            if name not in text:
                out.append(Finding("V10", f"agents/{name}.md is not referenced in docs/javascripts/mind.js"))
        for url in re.findall(r'url:\s*"((?:commands|skills|agents)/[^"]+)"', text):
            path = url.rstrip("/")
            candidates = [root / f"{path}.md", root / path / "SKILL.md"]
            if path.endswith("/SKILL"):
                candidates.append(root / (path[:-6] + "/SKILL.md"))
            if not any(c.exists() for c in candidates):
                out.append(Finding("V10", f"docs/javascripts/mind.js url `{url}` does not resolve to a source file"))
    return out


_REF_RE = re.compile(r"neuroflow:([a-z0-9_-]+)")
_PLACEHOLDER_REFS = {"my-skill", "my-command", "skill-name", "command-name", "my-agent", "phase-"}


def v11_dead_refs(ctx: Context) -> list[Finding]:
    out = []
    known = skill_names(ctx.root) | command_names(ctx.root)
    for skill_md in sorted((ctx.root / "skills").glob("*/SKILL.md")):
        seen: set[str] = set()
        for ref in _REF_RE.findall(_read(skill_md)):
            if ref in seen or ref in _PLACEHOLDER_REFS:
                continue
            seen.add(ref)
            if ref not in known:
                out.append(Finding("V11", f"skills/{skill_md.parent.name}/SKILL.md references unknown skill/command "
                                          f"`neuroflow:{ref}`"))
    return out


# ---------------------------------------------------------------------------
# V12 - V15: release chores, repo memory, sensitive info, path hygiene
# ---------------------------------------------------------------------------


def v12_release_notes(ctx: Context) -> list[Finding]:
    found = site_versions(ctx.root, PLUGIN_JSON) or []
    if not found:
        return []
    v = found[0]
    out = []
    readme = ctx.root / "README.md"
    if readme.is_file() and f"## What's new in {v}" not in _read(readme):
        out.append(Finding("V12", f"README.md has no `## What's new in {v}` section", WARN))
    changelog = ctx.root / "docs" / "changelog.md"
    if changelog.is_file() and not re.search(rf"(?m)^##\s+v?{re.escape(v)}\b", _read(changelog)):
        out.append(Finding("V12", f"docs/changelog.md has no `## {v}` entry", WARN))
    index = ctx.root / "docs" / "index.md"
    if index.is_file():
        m = re.search(r'class="sa-bar-version">\s*v?([^<\s]+)\s*<', _read(index))
        if m and m.group(1) != v:
            out.append(Finding("V12", f"docs/index.md sa-bar-version is v{m.group(1)}, plugin is {v} - re-run the "
                                      "self-assessment for this version", WARN))
    return out


def v13_repo_memory(ctx: Context) -> list[Finding]:
    memory = ctx.root / ".neuroflow"
    if not memory.is_dir():
        return []
    skills = skill_names(ctx.root)
    out = []
    for sub in sorted(p for p in memory.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if sub.name in {"reasoning", "sessions"}:
            continue
        why = "matches a skill name - skills never create their own folders" if sub.name in skills else \
            "is not reasoning/ or sessions/ - is it intentional?"
        out.append(Finding("V13", f".neuroflow/{sub.name}/ {why}", WARN))
    return out


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SYNTHETIC_EMAIL_DOMAINS = (
    "example.com", "example.org", "test.com", "domain.com", "localhost",
    "users.noreply.github.com", "anthropic.com",
    "institution.edu", "university.edu", "inst.edu", "email.com",
)
# Files that DESCRIBE the patterns (the sentinel specs and the dev report) - self-referential noise.
_SELF_REFERENTIAL = {"agents/sentinel.md", "agents/sentinel-dev.md", ".neuroflow/sentinel-dev.md"}
# docs/agents/ and docs/skills/ are gitignored build-time copies made by docs/hooks.py.
_GENERATED_PREFIXES = ("docs/agents/", "docs/skills/")
_SECRET_KEY_RE = re.compile(r"(?i)\b(password|passwd|secret|api_key|token|private_key)\b\s*[:=]\s*(\S+)")
_PLACEHOLDER_VALUE_RE = re.compile(
    r"(?i)^[`\"'<{\[]*(?:[A-Z0-9_.-]+|.*(?:placeholder|example|changeme|your[_-]?|\.\.\.|…).*|\$\{?\w+\}?|dummy|none|null"
    r"|true|false|\*+)[`\"'>}\]]*[,;]?$"
)
_PEM_HEADER_RE = re.compile(r"^[\"'`]?-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_PEM_INLINE_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----(?:\\n|\s)+[A-Za-z0-9+/=]{40,}")
_BASE64_LINE_RE = re.compile(r"^[\"'`]?[A-Za-z0-9+/=]{40,}")
_SCAN_DIRS = ("agents", "commands", "skills", "docs", "hooks", "scripts", ".neuroflow")
_SCAN_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".js", ".sh", ".ps1", ".mjs", ".html"}


def _scan_files(root: Path, dirs: tuple[str, ...]) -> list[Path]:
    files = sorted(root.glob("*.md"))
    for d in dirs:
        base = root / d
        if base.is_dir():
            files.extend(sorted(p for p in base.rglob("*")
                                if p.is_file() and p.suffix in _SCAN_SUFFIXES and "__pycache__" not in p.parts))
    return files


def _mask_email(addr: str) -> str:
    local, _, domain = addr.partition("@")
    return f"{local[:1]}***@{domain[:3]}***"


def v14_sensitive(ctx: Context) -> list[Finding]:
    """CI subset of the sensitive-info audit. Real names and institutions need judgement and
    stay with the sentinel-dev agent."""
    out = []
    self_path = Path(__file__).resolve()
    for path in _scan_files(ctx.root, _SCAN_DIRS):
        if path.resolve() == self_path:
            continue
        rel = path.relative_to(ctx.root).as_posix()
        if rel in _SELF_REFERENTIAL or rel.startswith(_GENERATED_PREFIXES):
            continue
        lines = _read(path).splitlines()
        for lineno, line in enumerate(lines, 1):
            for m in _EMAIL_RE.finditer(line):
                if not m.group(0).lower().endswith(_SYNTHETIC_EMAIL_DOMAINS):
                    out.append(Finding("V14", f"{rel}:{lineno} contains an email address ({_mask_email(m.group(0))}) "
                                              "[needs human review]", WARN))
            sm = _SECRET_KEY_RE.search(line)
            value = sm.group(2) if sm else ""
            # Values with ( or { are code (os.environ.get(...), f-strings, dicts), not secrets,
            # and a secret has some substance (four or more letters or digits).
            if (sm and "(" not in value and "{" not in value and len(re.findall(r"[A-Za-z0-9]", value)) >= 4
                    and not _PLACEHOLDER_VALUE_RE.match(value)):
                out.append(Finding("V14", f"{rel}:{lineno} sets `{sm.group(1)}` to a non-placeholder value (***) "
                                          "[needs human review]", WARN))
            following = lines[lineno].strip() if lineno < len(lines) else ""
            # Key material, not a mention of the header (scanners hold the header in a regex).
            if _PEM_INLINE_RE.search(line) or (_PEM_HEADER_RE.match(line.strip()) and _BASE64_LINE_RE.match(following)):
                out.append(Finding("V14", f"{rel}:{lineno} contains PEM private-key material"))
    return out


# Files where legacy flowie/hive strings are historical or describe the patterns.
_PATH_HYGIENE_EXEMPT = {
    "docs/changelog.md", "README.md", "agents/sentinel-dev.md", ".neuroflow/sentinel-dev.md",
    "scripts/automation/repo_checks.py", "hooks/hooks.json",
}
_LEGACY_FIELDS = (
    (".neuroflow/.flowie/", "old dotted path - canonical is `~/.neuroflow/flowie/`"),
    ("flowie_profile:", "old scalar field - canonical is the `flowie_profiles:` list"),
    ("flowie_project:", "legacy scalar field - replaced by the `flowie_profiles:` list"),
    ("hive_member:", "legacy scalar field - removed"),
)
# A line that names a stale path to guard against it (.gitignore entries, migration notes).
_GUARD_CONTEXT_RE = re.compile(r"(?i)legacy|migrat|deprecated|gitignore|never commit")


def v15_path_hygiene(ctx: Context) -> list[Finding]:
    out = []
    for path in _scan_files(ctx.root, _SCAN_DIRS + (".github",)):
        rel = path.relative_to(ctx.root).as_posix()
        if rel in _PATH_HYGIENE_EXEMPT or rel in _SELF_REFERENTIAL or rel.startswith(_GENERATED_PREFIXES):
            continue
        for lineno, line in enumerate(_read(path).splitlines(), 1):
            guarded = bool(_GUARD_CONTEXT_RE.search(line))
            for pattern, note in _LEGACY_FIELDS:
                if pattern in line and not guarded:
                    out.append(Finding("V15", f"{rel}:{lineno} contains stale `{pattern}` - {note}", WARN))
            for stale in (".neuroflow/flowie/", ".neuroflow/hive/"):
                if guarded:
                    continue
                idx = 0
                while (idx := line.find(stale, idx)) != -1:
                    prefix = line[max(0, idx - 1):idx]
                    context = line[max(0, idx - 40):idx]
                    # Only a path INTO the folder is a stale instruction; a bare mention of the
                    # folder is a guard (.gitignore entries, export exclusion lists).
                    inside = re.match(r"[A-Za-z0-9_{.-]", line[idx + len(stale):idx + len(stale) + 1])
                    if inside and prefix not in ("/", "\\", "~") and "USERPROFILE" not in context and "$HOME" not in context:
                        canonical = "~/.neuroflow/flowie/" if "flowie" in stale else "~/.neuroflow/hives/{org-repo}/"
                        out.append(Finding("V15", f"{rel}:{lineno} uses project-level `{stale}` - canonical is "
                                                  f"`{canonical}`", WARN))
                    idx += len(stale)
    return out


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CHECKS: tuple[Check, ...] = (
    Check("V1", "Manifests are valid JSON", v1_json),
    Check("V2", "Version sync (four sites)", v2_versions),
    Check("V3", "Command frontmatter", v3_commands),
    Check("V4", "Command docs pages", v4_docs_pages),
    Check("V5", "Skill and agent names", v5_names),
    Check("V6", "hooks.json", v6_hooks),
    Check("V7", "Version bump vs base", v7_version_bump, needs_base=True),
    Check("V8", "Rule markers", v8_rule_markers),
    Check("V9", "Name collisions", v9_collisions),
    Check("V10", "Propagation (README, nav, mind map)", v10_propagation),
    Check("V11", "Dead skill/command references", v11_dead_refs),
    Check("V12", "Release notes sync", v12_release_notes),
    Check("V13", "Plugin-repo memory", v13_repo_memory),
    Check("V14", "Sensitive info", v14_sensitive),
    Check("V15", "Path hygiene", v15_path_hygiene),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


def run(root: Path = ROOT, base: str | None = None, only: set[str] | None = None) -> list[Finding]:
    """Run the registry (V7 only with a base ref) and return every finding."""
    ctx = Context(root=root, base=base)
    findings: list[Finding] = []
    for check in CHECKS:
        if only and check.id not in only:
            continue
        if check.needs_base and not base:
            continue
        findings.extend(check.func(ctx))
    return findings
