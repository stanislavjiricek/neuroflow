#!/usr/bin/env python3
"""Sentinel-dev: repo consistency checker for stanislavjiricek/neuroflow.

Runs the checks defined in agents/sentinel-dev.md against the plugin repo
itself, generates a report, optionally creates a branch + PR with auto-fixes,
and posts the report to Discussion #168.

Usage:
    python sentinel_check.py --repo owner/name --discussion-number 168
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent))
from post_discussion import post_discussion_comment

REPO_ROOT = Path(__file__).parent.parent.parent

# Regex for matching the Plugin version line in .neuroflow/project_config.md
_PROJECT_CONFIG_VERSION_RE = re.compile(
    r"(\*\*Plugin version:\*\*\s*)([0-9]+\.[0-9]+\.[0-9]+)"
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Issue(NamedTuple):
    check: str
    description: str
    fixable: bool
    fix_description: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter fields (name, description, phase …)."""
    fm: dict = {}
    if not content.startswith("---"):
        return fm
    end = content.find("---", 3)
    if end == -1:
        return fm
    block = content[3:end].strip()
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def get_plugin_version() -> str:
    plugin_json = REPO_ROOT / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        return data.get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check1_frontmatter_names() -> list[Issue]:
    """Check 1: folder/file name vs frontmatter name field."""
    issues = []

    # skills/*/SKILL.md — name must match folder name
    for skill_file in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        folder = skill_file.parent.name
        fm = parse_frontmatter(read_file_safe(skill_file))
        name = fm.get("name", "").strip()
        if not name:
            issues.append(Issue(
                "Check 1",
                f"`skills/{folder}/SKILL.md` is missing `name:` in frontmatter",
                fixable=False,
            ))
        elif name != folder:
            issues.append(Issue(
                "Check 1",
                f"`skills/{folder}/SKILL.md` has `name: {name}` but folder is `{folder}`",
                fixable=False,
            ))

    # agents/*.md — name must match filename (without .md)
    for agent_file in sorted((REPO_ROOT / "agents").glob("*.md")):
        stem = agent_file.stem
        fm = parse_frontmatter(read_file_safe(agent_file))
        name = fm.get("name", "").strip()
        if not name:
            issues.append(Issue(
                "Check 1",
                f"`agents/{agent_file.name}` is missing `name:` in frontmatter",
                fixable=False,
            ))
        elif name != stem:
            issues.append(Issue(
                "Check 1",
                f"`agents/{agent_file.name}` has `name: {name}` but filename is `{stem}`",
                fixable=False,
            ))

    # commands/*.md — name must match filename (without .md)
    for cmd_file in sorted((REPO_ROOT / "commands").glob("*.md")):
        stem = cmd_file.stem
        fm = parse_frontmatter(read_file_safe(cmd_file))
        name = fm.get("name", "").strip()
        if not name:
            issues.append(Issue(
                "Check 1",
                f"`commands/{cmd_file.name}` is missing `name:` in frontmatter",
                fixable=False,
            ))
        elif name != stem:
            issues.append(Issue(
                "Check 1",
                f"`commands/{cmd_file.name}` has `name: {name}` but filename is `{stem}`",
                fixable=False,
            ))

    return issues


def check3_version_sync() -> list[Issue]:
    """Check 3: version in plugin.json vs README.md heading and marketplace.json."""
    issues = []
    version = get_plugin_version()
    if version == "unknown":
        return issues

    readme = read_file_safe(REPO_ROOT / "README.md")
    heading = f"## What's new in {version}"
    if heading not in readme:
        issues.append(Issue(
            "Check 3",
            f"README.md is missing heading `{heading}` (plugin.json version is `{version}`)",
            fixable=False,
        ))

    # 3b: marketplace.json version must match plugin.json
    marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if marketplace_path.exists():
        try:
            marketplace_data = json.loads(marketplace_path.read_text(encoding="utf-8"))
            plugins = marketplace_data.get("plugins", [])
            for entry in plugins:
                mp_version = entry.get("version", "unknown")
                if mp_version != version:
                    issues.append(Issue(
                        "Check 3b",
                        f"`marketplace.json` version `{mp_version}` differs from "
                        f"`plugin.json` version `{version}`",
                        fixable=True,
                        fix_description=f"Update `marketplace.json` plugins[].version to `{version}`",
                    ))
        except (json.JSONDecodeError, OSError):
            pass

    # 3c: .neuroflow/project_config.md plugin_version must match plugin.json
    project_config_path = REPO_ROOT / ".neuroflow" / "project_config.md"
    if project_config_path.exists():
        config_content = read_file_safe(project_config_path)
        version_match = _PROJECT_CONFIG_VERSION_RE.search(config_content)
        if version_match:
            config_version = version_match.group(2)
            if config_version != version:
                issues.append(Issue(
                    "Check 3c",
                    f"`.neuroflow/project_config.md` `Plugin version: {config_version}` differs from "
                    f"`plugin.json` version `{version}`",
                    fixable=True,
                    fix_description=f"Update `.neuroflow/project_config.md` Plugin version to `{version}`",
                ))
        else:
            issues.append(Issue(
                "Check 3c",
                "`.neuroflow/project_config.md` is missing `**Plugin version:**` line",
                fixable=False,
            ))

    return issues


def check6_command_frontmatter() -> list[Issue]:
    """Check 6: required frontmatter fields in command files."""
    REQUIRED = {"name", "description"}
    issues = []
    for cmd_file in sorted((REPO_ROOT / "commands").glob("*.md")):
        content = read_file_safe(cmd_file)
        fm = parse_frontmatter(content)
        missing = REQUIRED - set(fm.keys())
        if missing:
            issues.append(Issue(
                "Check 6",
                f"`commands/{cmd_file.name}` is missing frontmatter fields: "
                + ", ".join(sorted(missing)),
                fixable=False,
            ))
    return issues


def check8_hooks_json() -> list[Issue]:
    """Check 8: hooks.json audit."""
    issues = []
    hooks_path = REPO_ROOT / "hooks" / "hooks.json"
    if not hooks_path.exists():
        issues.append(Issue(
            "Check 8",
            "`hooks/hooks.json` does not exist",
            fixable=False,
        ))
        return issues

    try:
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(Issue(
            "Check 8",
            f"`hooks/hooks.json` is invalid JSON: {exc}",
            fixable=False,
        ))
        return issues

    hooks_section = data.get("hooks", {})
    for event, entries in hooks_section.items():
        if not isinstance(entries, list):
            issues.append(Issue(
                "Check 8",
                f"`hooks/hooks.json` event `{event}` is not a list",
                fixable=False,
            ))
            continue
        for entry in entries:
            if "matcher" not in entry:
                issues.append(Issue(
                    "Check 8",
                    f"`hooks/hooks.json` entry under `{event}` is missing `matcher`",
                    fixable=False,
                ))
            hook_list = entry.get("hooks", [])
            if not hook_list:
                issues.append(Issue(
                    "Check 8",
                    f"`hooks/hooks.json` entry under `{event}` has empty `hooks` list",
                    fixable=False,
                ))
            for h in hook_list:
                if "type" not in h or "command" not in h:
                    issues.append(Issue(
                        "Check 8",
                        f"`hooks/hooks.json` hook is missing `type` or `command` field",
                        fixable=False,
                    ))
                    continue
                # Check 8b: hook commands must have error suppression so they
                # fail silently and never surface noise to the user.
                cmd = h.get("command", "")
                has_suppression = bool(
                    re.search(r";\s*true\b", cmd)
                    or re.search(r"\|\|\s*true\b", cmd)
                    or "2>/dev/null" in cmd
                    or re.search(r"\btry\s*:", cmd)
                )
                if not has_suppression:
                    issues.append(Issue(
                        "Check 8b",
                        f"`hooks/hooks.json` hook command under `{event}` "
                        f"(matcher: {entry.get('matcher','?')}) has no error "
                        f"suppression — add `; true`, `|| true`, or `2>/dev/null`, "
                        f"or wrap in try/except",
                        fixable=False,
                    ))
    return issues


def check9_docs_sync() -> list[Issue]:
    """Check 9: docs website sync."""
    issues = []

    # 9a: version in mkdocs.yml vs plugin.json
    plugin_version = get_plugin_version()
    mkdocs_content = read_file_safe(REPO_ROOT / "mkdocs.yml")
    extra_version_match = re.search(r"version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+)['\"]?", mkdocs_content)
    if extra_version_match:
        mkdocs_version = extra_version_match.group(1)
        if mkdocs_version != plugin_version:
            issues.append(Issue(
                "Check 9a",
                f"`mkdocs.yml` version `{mkdocs_version}` differs from "
                f"`plugin.json` version `{plugin_version}`",
                fixable=True,
                fix_description=f"Update `mkdocs.yml` version to `{plugin_version}`",
            ))

    # 9b: every commands/*.md has a docs/commands/<name>.md
    for cmd_file in sorted((REPO_ROOT / "commands").glob("*.md")):
        stem = cmd_file.stem
        doc_path = REPO_ROOT / "docs" / "commands" / f"{stem}.md"
        if not doc_path.exists():
            issues.append(Issue(
                "Check 9b",
                f"`commands/{stem}.md` has no docs page at `docs/commands/{stem}.md`",
                fixable=False,
            ))

    # 9c: nav dead links — check that nav files exist
    # Note: skills/ and agents/ are copied into docs/ by docs/hooks.py at build time;
    # check them against REPO_ROOT/<path> instead of docs/<path>.
    HOOK_SYNCED = ("skills/", "agents/")
    nav_paths = re.findall(
        r'["\']?[^:\n]+["\']?:\s+([a-zA-Z0-9_/.-]+\.md)',
        mkdocs_content,
    )
    for nav_path in nav_paths:
        nav_path = nav_path.strip()
        if any(nav_path.startswith(prefix) for prefix in HOOK_SYNCED):
            full = REPO_ROOT / nav_path
        else:
            full = REPO_ROOT / "docs" / nav_path
        if not full.exists():
            issues.append(Issue(
                "Check 9c",
                f"`mkdocs.yml` nav references non-existent file `{nav_path}`",
                fixable=False,
            ))

    # 9d: mind map staleness — mind.js is a CURATED CONCEPT MAP (24 concept
    # nodes), not a 1:1 mirror of skills/commands/agents. What we can enforce:
    #   - every command is reachable: "/<name>" appears somewhere (a label or a
    #     `commands:` array entry) OR a node urls to commands/<name>/
    #   - every agent file stem appears somewhere in the map text
    #   - no dead urls: every commands/skills/agents url in mind.js resolves
    # Per-skill nodes are intentionally NOT required — concepts cover them.
    mind_js_path = REPO_ROOT / "docs" / "javascripts" / "mind.js"
    if mind_js_path.exists():
        mind_js_content = mind_js_path.read_text(encoding="utf-8")
        for cmd_file in sorted((REPO_ROOT / "commands").glob("*.md")):
            stem = cmd_file.stem
            if f"/{stem}" not in mind_js_content and f"commands/{stem}/" not in mind_js_content:
                issues.append(Issue(
                    "Check 9d",
                    f"`commands/{cmd_file.name}` is not referenced anywhere in `docs/javascripts/mind.js` "
                    f"(no `/{stem}` mention and no `commands/{stem}/` url)",
                    fixable=False,
                ))
        for agent_file in sorted((REPO_ROOT / "agents").glob("*.md")):
            stem = agent_file.stem
            if stem not in mind_js_content:
                issues.append(Issue(
                    "Check 9d",
                    f"`agents/{agent_file.name}` is not referenced anywhere in `docs/javascripts/mind.js`",
                    fixable=False,
                ))
        for url in re.findall(r'url:\s*"((?:commands|skills|agents)/[^"]+)"', mind_js_content):
            path = url.rstrip("/")
            candidates = [
                REPO_ROOT / f"{path}.md",
                REPO_ROOT / path / "SKILL.md" if not path.endswith("SKILL") else REPO_ROOT / f"{path}.md",
                REPO_ROOT / (path[:-6] + "/SKILL.md") if path.endswith("/SKILL") else None,
            ]
            if not any(c is not None and c.exists() for c in candidates):
                issues.append(Issue(
                    "Check 9d",
                    f"`docs/javascripts/mind.js` url `{url}` does not resolve to a source file",
                    fixable=False,
                ))

    return issues


def check4_dead_skill_references() -> list[Issue]:
    """Check 4: dead references to skills/commands inside SKILL.md files."""
    issues = []
    skill_names = {p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    command_names = {p.stem for p in (REPO_ROOT / "commands").glob("*.md")}

    ref_pattern = re.compile(r"neuroflow:([a-z0-9_-]+)")

    # Placeholder tokens used as examples in developer-facing docs — skip these
    PLACEHOLDER_TOKENS = {"my-skill", "my-command", "skill-name", "command-name", "my-agent", "phase-"}

    for skill_file in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        content = read_file_safe(skill_file)
        seen_refs: set[str] = set()
        for match in ref_pattern.finditer(content):
            ref = match.group(1)
            if ref in seen_refs or ref in PLACEHOLDER_TOKENS:
                continue
            seen_refs.add(ref)
            if ref not in skill_names and ref not in command_names:
                issues.append(Issue(
                    "Check 4",
                    f"`skills/{skill_file.parent.name}/SKILL.md` references "
                    f"unknown skill/command `neuroflow:{ref}`",
                    fixable=False,
                ))
    return issues


def check2_readme_tables() -> list[Issue]:
    """Check 2: every command/skill/agent has a README link, and README links resolve."""
    issues = []
    readme = read_file_safe(REPO_ROOT / "README.md")

    for cmd_file in sorted((REPO_ROOT / "commands").glob("*.md")):
        if f"](commands/{cmd_file.name})" not in readme:
            issues.append(Issue(
                "Check 2",
                f"`commands/{cmd_file.name}` has no link in README.md (Commands table row missing?)",
                fixable=False,
            ))
    for skill_md in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        folder = skill_md.parent.name
        if f"](skills/{folder}/SKILL.md)" not in readme:
            issues.append(Issue(
                "Check 2",
                f"`skills/{folder}/` has no link in README.md (Skills table row missing?)",
                fixable=False,
            ))
    for agent_file in sorted((REPO_ROOT / "agents").glob("*.md")):
        if f"](agents/{agent_file.name})" not in readme:
            issues.append(Issue(
                "Check 2",
                f"`agents/{agent_file.name}` has no link in README.md (Agents table row missing?)",
                fixable=False,
            ))

    # Reverse direction: every repo-relative README link must resolve.
    # Scan only from "## Why neuroflow" onward — the "What's new" changelog
    # above it legitimately links to files that were later removed.
    tables_region = readme[readme.find("## Why neuroflow"):] if "## Why neuroflow" in readme else readme
    for target in re.findall(r"\]\(((?:commands|skills|agents|\.github)/[^)#]+)\)", tables_region):
        if not (REPO_ROOT / target).exists():
            issues.append(Issue(
                "Check 2",
                f"README.md links to non-existent file `{target}`",
                fixable=False,
            ))
    return issues


# Same-name skill/command/agent pairs that are intentional by design.
INTENTIONAL_NAME_PAIRS = {"setup", "wiki", "autoresearch", "sentinel", "sentinel-dev", "flowie"}


def check5_naming_overlaps() -> list[Issue]:
    """Check 5: new identical names across skills, commands, and agents.

    Heuristic guard: `phase-{command}` skills and the known intentional pairs
    are by design; anything else sharing a name is flagged for human review.
    """
    issues = []
    skills = {p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    commands = {p.stem for p in (REPO_ROOT / "commands").glob("*.md")}
    agents = {p.stem for p in (REPO_ROOT / "agents").glob("*.md")}

    for name in sorted((skills & commands) - INTENTIONAL_NAME_PAIRS):
        issues.append(Issue(
            "Check 5",
            f"Skill `{name}` and command `{name}` share a name and are not a known intentional pair "
            f"[needs human review]",
            fixable=False,
        ))
    for name in sorted((agents & skills) - INTENTIONAL_NAME_PAIRS):
        issues.append(Issue(
            "Check 5",
            f"Agent `{name}` and skill `{name}` share a name and are not a known intentional pair "
            f"[needs human review]",
            fixable=False,
        ))
    return issues


def check7_neuroflow_purity() -> list[Issue]:
    """Check 7: the plugin repo's own .neuroflow/ may only contain reasoning/ and sessions/."""
    issues = []
    nf = REPO_ROOT / ".neuroflow"
    if not nf.is_dir():
        return issues
    PERMITTED = {"reasoning", "sessions"}
    skills = {p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    for sub in sorted(p for p in nf.iterdir() if p.is_dir()):
        if sub.name in PERMITTED:
            continue
        if sub.name in skills:
            issues.append(Issue(
                "Check 7",
                f"`.neuroflow/{sub.name}/` matches a skill name — skills must never create "
                f"their own subfolders in `.neuroflow/`",
                fixable=False,
            ))
        else:
            issues.append(Issue(
                "Check 7",
                f"`.neuroflow/{sub.name}/` is not a permitted subfolder in the plugin repo "
                f"(only `reasoning/` and `sessions/`) — is it intentional?",
                fixable=False,
            ))
    return issues


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SYNTHETIC_EMAIL_DOMAINS = (
    "example.com", "example.org", "test.com", "domain.com", "localhost",
    "users.noreply.github.com", "anthropic.com",
    "institution.edu", "university.edu", "inst.edu", "email.com",
)
# Files that legitimately DESCRIBE sensitive-info / legacy-path patterns
# (the sentinel specs and the sentinel's own report) — self-referential noise.
_SELF_REFERENTIAL = {"agents/sentinel.md", "agents/sentinel-dev.md", ".neuroflow/sentinel-dev.md"}
# docs/agents/ and docs/skills/ are gitignored build-time copies made by
# docs/hooks.py — scan the sources instead, never the copies.
_GENERATED_PREFIXES = ("docs/agents/", "docs/skills/")
_SECRET_KEY_RE = re.compile(
    r"(?i)\b(password|passwd|secret|api_key|token|private_key)\b\s*[:=]\s*(\S+)"
)
_PLACEHOLDER_VALUE_RE = re.compile(
    r"(?i)^[`\"'<{\[]*(?:[A-Z0-9_.-]+|.*(?:placeholder|example|changeme|your[_-]?|\.\.\.|…).*|\$\{?\w+\}?|dummy|none|null|true|false|\*+)[`\"'>}\]]*[,;]?$"
)
_SCAN_DIRS_CHECK10 = ("agents", "commands", "skills", "docs", "hooks", "scripts", ".neuroflow")
_SCAN_EXTS_CHECK10 = {".md", ".json", ".py", ".yml", ".yaml", ".js", ".sh", ".ps1", ".mjs", ".html"}


def _mask_email(addr: str) -> str:
    local, _, dom = addr.partition("@")
    return f"{local[:1]}***@{dom[:3]}***"


def check10_sensitive_info() -> list[Issue]:
    """Check 10 (CI subset): emails, hardcoded secrets, and PEM private keys.

    Real-name / institution detection stays in the sentinel-dev agent audit —
    it needs human judgment and would drown CI in false positives.
    """
    issues = []
    files: list[Path] = [REPO_ROOT / "README.md", REPO_ROOT / "AGENTS.md"]
    for d in _SCAN_DIRS_CHECK10:
        base = REPO_ROOT / d
        if base.exists():
            files.extend(p for p in base.rglob("*") if p.is_file() and p.suffix in _SCAN_EXTS_CHECK10)

    self_path = Path(__file__).resolve()
    for path in files:
        if path.resolve() == self_path or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in _SELF_REFERENTIAL or rel.startswith(_GENERATED_PREFIXES):
            continue
        text = read_file_safe(path)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in _EMAIL_RE.finditer(line):
                addr = m.group(0)
                if addr.lower().endswith(_SYNTHETIC_EMAIL_DOMAINS):
                    continue
                issues.append(Issue(
                    "Check 10",
                    f"`{rel}:{lineno}` contains an email address ({_mask_email(addr)}) [needs human review]",
                    fixable=False,
                ))
            sm = _SECRET_KEY_RE.search(line)
            # Values containing ( or { are code expressions (os.environ.get(...),
            # f-strings, dict literals), not hardcoded secrets.
            if sm and "(" not in sm.group(2) and "{" not in sm.group(2) and not _PLACEHOLDER_VALUE_RE.match(sm.group(2)):
                issues.append(Issue(
                    "Check 10",
                    f"`{rel}:{lineno}` sets `{sm.group(1)}` to a non-placeholder value (***) [needs human review]",
                    fixable=False,
                ))
            if "-----BEGIN" in line and "PRIVATE" in line.upper():
                issues.append(Issue(
                    "Check 10",
                    f"`{rel}:{lineno}` contains PEM private-key material",
                    fixable=False,
                ))
    return issues


# Files where legacy flowie/hive path strings are historical or intentional:
# changelog + README record history; the sentinel spec and this script describe
# the patterns; hooks.json uses a path-suffix matcher that must keep the
# un-anchored form to match the global path on every platform.
_CHECK12_EXEMPT = {
    "docs/changelog.md",
    "README.md",
    "agents/sentinel-dev.md",
    ".neuroflow/sentinel-dev.md",
    "scripts/automation/sentinel_check.py",
    "hooks/hooks.json",
}
_CHECK12_PATTERNS = (
    (".neuroflow/.flowie/", "old dotted path — canonical is `~/.neuroflow/flowie/`"),
    ("flowie_profile:", "old scalar field — canonical is `flowie_profiles:` list"),
    ("flowie_project:", "legacy scalar field — replaced by `flowie_profiles:` list"),
    ("hive_member:", "legacy scalar field — removed"),
)


def check12_path_hygiene() -> list[Issue]:
    """Check 12: stale flowie/hive paths and legacy field names."""
    issues = []
    files = [
        p for d in ("agents", "commands", "skills", "docs", "hooks", "scripts", ".neuroflow", ".github")
        for p in (REPO_ROOT / d).rglob("*")
        if p.is_file() and p.suffix in _SCAN_EXTS_CHECK10 and "__pycache__" not in p.parts
    ]
    files.extend([REPO_ROOT / "README.md", REPO_ROOT / "AGENTS.md"])

    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in _CHECK12_EXEMPT or rel in _SELF_REFERENTIAL or rel.startswith(_GENERATED_PREFIXES):
            continue
        text = read_file_safe(path)
        for lineno, line in enumerate(text.splitlines(), 1):
            lowered = line.lower()
            # Migration instructions legitimately name the legacy fields they replace.
            is_migration_context = "legacy" in lowered or "migrat" in lowered
            for pattern, note in _CHECK12_PATTERNS:
                if pattern in line and not is_migration_context:
                    issues.append(Issue(
                        "Check 12",
                        f"`{rel}:{lineno}` contains stale `{pattern}` — {note}",
                        fixable=False,
                    ))
            # Project-level `.neuroflow/flowie/` or `.neuroflow/hive/` (deprecated) —
            # only when NOT part of the global `~/.neuroflow/...` form (which always
            # has a path separator, `~`, or env-var expansion right before it).
            for stale in (".neuroflow/flowie/", ".neuroflow/hive/"):
                idx = 0
                while (idx := line.find(stale, idx)) != -1:
                    prefix = line[max(0, idx - 1):idx]
                    context = line[max(0, idx - 40):idx]
                    is_global = prefix in ("/", "\\", "~") or "USERPROFILE" in context or "$HOME" in context
                    if not is_global:
                        canonical = "~/.neuroflow/flowie/" if "flowie" in stale else "~/.neuroflow/hives/{org-repo}/"
                        issues.append(Issue(
                            "Check 12",
                            f"`{rel}:{lineno}` uses project-level `{stale}` — canonical is `{canonical}`",
                            fixable=False,
                        ))
                    idx += len(stale)
    return issues


# ---------------------------------------------------------------------------
# Auto-fix: version in mkdocs.yml
# ---------------------------------------------------------------------------

def fix_mkdocs_version(plugin_version: str) -> bool:
    """Update version in mkdocs.yml to match plugin.json. Returns True if changed."""
    mkdocs_path = REPO_ROOT / "mkdocs.yml"
    content = mkdocs_path.read_text(encoding="utf-8")
    new_content, n = re.subn(
        r"(version:\s*['\"]?)([0-9]+\.[0-9]+\.[0-9]+)(['\"]?)",
        lambda m: f"{m.group(1)}{plugin_version}{m.group(3)}",
        content,
    )
    if n == 0:
        return False
    mkdocs_path.write_text(new_content, encoding="utf-8")
    return True


def fix_marketplace_version(plugin_version: str) -> bool:
    """Update plugins[].version in marketplace.json to match plugin.json. Returns True if changed."""
    marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    try:
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    changed = False
    for entry in data.get("plugins", []):
        if entry.get("version") != plugin_version:
            entry["version"] = plugin_version
            changed = True
    if not changed:
        return False
    marketplace_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True


def fix_project_config_version(plugin_version: str) -> bool:
    """Update Plugin version line in .neuroflow/project_config.md. Returns True if changed."""
    config_path = REPO_ROOT / ".neuroflow" / "project_config.md"
    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError:
        return False
    new_content, n = _PROJECT_CONFIG_VERSION_RE.subn(
        lambda m: f"{m.group(1)}{plugin_version}",
        content,
    )
    if n == 0:
        return False
    config_path.write_text(new_content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def github_api(token: str, method: str, path: str, data: dict | None = None) -> dict:
    url = f"https://api.github.com{path}"
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"ERROR: GitHub API {method} {path} → {exc.code}: {body}", file=sys.stderr)
        return {}


def get_default_branch(token: str, owner: str, name: str) -> str:
    resp = github_api(token, "GET", f"/repos/{owner}/{name}")
    return resp.get("default_branch", "main")


def create_pr(
    token: str,
    owner: str,
    name: str,
    branch: str,
    base: str,
    title: str,
    body: str,
) -> str:
    """Create a PR and return its HTML URL."""
    resp = github_api(
        token,
        "POST",
        f"/repos/{owner}/{name}/pulls",
        {
            "title": title,
            "body": body,
            "head": branch,
            "base": base,
        },
    )
    return resp.get("html_url", "")


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(
    issues: list[Issue],
    run_date: str,
    pr_url: str = "",
) -> tuple[str, bool]:
    lines = [f"## Sentinel-dev Report — {run_date}", ""]

    if not issues and not pr_url:
        lines.append("### Checks")
        lines.append("")
        for check_name in [
            "Check 1 — Frontmatter name consistency",
            "Check 2 — README tables",
            "Check 3 — Version sync",
            "Check 3b — marketplace.json version sync",
            "Check 3c — project_config.md version sync",
            "Check 4 — Dead skill/command references",
            "Check 5 — Naming overlaps",
            "Check 6 — Command frontmatter completeness",
            "Check 7 — .neuroflow purity",
            "Check 8 — hooks.json validity",
            "Check 8b — Hook error suppression",
            "Check 9 — Docs website sync",
            "Check 9d — Mind map staleness",
            "Check 10 — Sensitive info (emails/secrets/keys)",
            "Check 12 — Flowie/hive path hygiene",
        ]:
            lines.append(f"- ✅ {check_name}")
        lines.append("")
        lines.append("_All checks passed — no issues found._")
        return "\n".join(lines), False

    # Group by check
    by_check: dict[str, list[Issue]] = {}
    for iss in issues:
        by_check.setdefault(iss.check, []).append(iss)

    lines.append("### Checks")
    lines.append("")
    check_names = {
        "Check 1": "Frontmatter name consistency",
        "Check 2": "README tables",
        "Check 3": "Version sync",
        "Check 3b": "marketplace.json version sync",
        "Check 3c": "project_config.md version sync",
        "Check 4": "Dead skill/command references",
        "Check 5": "Naming overlaps",
        "Check 6": "Command frontmatter completeness",
        "Check 7": ".neuroflow purity",
        "Check 8": "hooks.json validity",
        "Check 8b": "Hook error suppression",
        "Check 9a": "mkdocs.yml version sync",
        "Check 9b": "Command docs completeness",
        "Check 9c": "Nav dead links",
        "Check 9d": "Mind map staleness",
        "Check 10": "Sensitive info (emails/secrets/keys)",
        "Check 12": "Flowie/hive path hygiene",
    }
    all_checks = ["Check 1", "Check 2", "Check 3", "Check 3b", "Check 3c", "Check 4", "Check 5", "Check 6", "Check 7", "Check 8", "Check 8b", "Check 9a", "Check 9b", "Check 9c", "Check 9d", "Check 10", "Check 12"]
    for check in all_checks:
        label = check_names.get(check, check)
        if check in by_check:
            lines.append(f"- ❌ **{check} — {label}** ({len(by_check[check])} issue(s))")
            for iss in by_check[check]:
                lines.append(f"  - {iss.description}")
        else:
            lines.append(f"- ✅ {check} — {label}")
    lines.append("")

    fixable = [i for i in issues if i.fixable]
    if fixable:
        lines.append("### Auto-fix plan")
        lines.append("")
        for iss in fixable:
            lines.append(f"- {iss.fix_description}")
        lines.append("")

    if pr_url:
        lines.append("### PR opened")
        lines.append("")
        lines.append(f"- {pr_url}")
        lines.append("")

    non_fixable = [i for i in issues if not i.fixable]
    if non_fixable:
        lines.append("### Manual action required")
        lines.append("")
        lines.append(
            f"{len(non_fixable)} issue(s) require manual attention (not auto-fixable)."
        )

    return "\n".join(lines), True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel-dev consistency check")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--discussion-number", type=int, required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    owner, name = args.repo.split("/")
    run_date = datetime.date.today().isoformat()

    print("Running sentinel checks…")

    all_issues: list[Issue] = []
    all_issues.extend(check1_frontmatter_names())
    all_issues.extend(check2_readme_tables())
    all_issues.extend(check3_version_sync())
    all_issues.extend(check4_dead_skill_references())
    all_issues.extend(check5_naming_overlaps())
    all_issues.extend(check6_command_frontmatter())
    all_issues.extend(check7_neuroflow_purity())
    all_issues.extend(check8_hooks_json())
    all_issues.extend(check9_docs_sync())
    all_issues.extend(check10_sensitive_info())
    all_issues.extend(check12_path_hygiene())

    print(f"Found {len(all_issues)} issues.")

    pr_url = ""
    fixable = [i for i in all_issues if i.fixable]

    if fixable:
        plugin_version = get_plugin_version()
        branch_name = f"sentinel-dev/{run_date}-auto-fix"
        print(f"Auto-fixable issues found. Creating branch `{branch_name}`…")

        # Apply fixes locally
        fixed_descriptions = []
        for iss in fixable:
            if "mkdocs.yml" in iss.fix_description:
                if fix_mkdocs_version(plugin_version):
                    fixed_descriptions.append(iss.fix_description)
                    print(f"Fixed: {iss.fix_description}")
            elif "marketplace.json" in iss.fix_description:
                if fix_marketplace_version(plugin_version):
                    fixed_descriptions.append(iss.fix_description)
                    print(f"Fixed: {iss.fix_description}")
            elif "project_config.md" in iss.fix_description:
                if fix_project_config_version(plugin_version):
                    fixed_descriptions.append(iss.fix_description)
                    print(f"Fixed: {iss.fix_description}")

        if fixed_descriptions:
            # Configure git
            subprocess.run(
                ["git", "config", "user.name", "sentinel-dev[bot]"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "sentinel-dev[bot]@users.noreply.github.com"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )

            # Create or reset the branch (handles re-runs on the same day)
            subprocess.run(
                ["git", "checkout", "-B", branch_name],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "add", "-A"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"fix(sentinel): auto-fix {run_date}"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            result = subprocess.run(
                ["git", "push", "--force-with-lease", "origin", branch_name],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"WARNING: git push failed: {result.stderr}", file=sys.stderr)
            else:
                default_branch = get_default_branch(token, owner, name)
                pr_body = (
                    f"## Sentinel-dev auto-fix — {run_date}\n\n"
                    "Auto-generated by the sentinel-dev workflow.\n\n"
                    "### Changes\n\n"
                    + "\n".join(f"- {d}" for d in fixed_descriptions)
                )
                pr_url = create_pr(
                    token,
                    owner,
                    name,
                    branch_name,
                    default_branch,
                    f"fix(sentinel): auto-fix consistency issues — {run_date}",
                    pr_body,
                )
                if pr_url:
                    print(f"PR created: {pr_url}")
                else:
                    print(
                        "NOTE: PR already exists for this branch or creation returned "
                        "no URL — check repository pull requests.",
                        file=sys.stderr,
                    )

    report_body, has_issues = build_report(all_issues, run_date, pr_url)

    n_issues = len(all_issues)
    if not has_issues:
        banner = f"@stanislavjiricek ✅ ALL GOOD — {run_date}"
    else:
        extra = " — PR opened" if pr_url else ""
        banner = (
            f"@stanislavjiricek ❌ NEEDS ATTENTION — {run_date} "
            f"({n_issues} issue(s){extra})"
        )

    body = f"{banner}\n\n{report_body}"

    print(f"Posting to Discussion #{args.discussion_number}…")
    url = post_discussion_comment(
        repo=args.repo,
        discussion_number=args.discussion_number,
        body=body,
        token=token,
    )
    print(f"Posted: {url}")


if __name__ == "__main__":
    main()
