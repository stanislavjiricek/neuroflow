#!/usr/bin/env python3
"""PR-time validation for the neuroflow plugin repo.

Stdlib only — no external dependencies. Run from the repo root:

    python scripts/automation/validate_pr.py [--base origin/main]

Checks:
  V1  plugin.json / marketplace.json / hooks/hooks.json are valid JSON
  V2  version sync: plugin.json == marketplace.json == mkdocs.yml extra.version
  V3  every commands/*.md has frontmatter with name/description/phase/reads/writes,
      name matches the filename, and phase is in the canonical taxonomy
      (parsed live from skills/neuroflow-core/SKILL.md — single source of truth)
  V4  every commands/*.md has a docs page at docs/commands/<name>.md
  V5  every skills/*/SKILL.md frontmatter name matches its folder name
  V6  every hook command in hooks/hooks.json ends with error suppression
  V7  (with --base) if substantive files changed vs base, plugin.json version
      must be bumped — mirrors .githooks/pre-push, but enforced in CI

Exit code 0 = all passed, 1 = at least one failure.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAILURES: list[str] = []

# Files whose modification alone does not require a version bump (matches
# BUMP_FILES in pre_push_version_check.py plus CI/automation itself).
NO_BUMP_NEEDED = {
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "mkdocs.yml",
    "README.md",
    "docs/changelog.md",
}
NO_BUMP_PREFIXES = (".github/", "scripts/automation/", ".githooks/", ".neuroflow/")


def fail(check: str, msg: str) -> None:
    FAILURES.append(f"[{check}] {msg}")


def read_frontmatter(path: Path) -> dict[str, str] | None:
    """Parse simple `key: value` pairs from a leading --- block. Returns None if absent."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def check_json_files() -> dict[str, dict]:
    parsed = {}
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "hooks/hooks.json"):
        p = ROOT / rel
        if not p.exists():
            fail("V1", f"{rel} is missing")
            continue
        try:
            parsed[rel] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail("V1", f"{rel} is not valid JSON: {e}")
    return parsed


def check_version_sync(parsed: dict[str, dict]) -> None:
    plugin = parsed.get(".claude-plugin/plugin.json") or {}
    market = parsed.get(".claude-plugin/marketplace.json") or {}
    v_plugin = plugin.get("version")
    v_market = None
    plugins_list = market.get("plugins") or []
    if plugins_list:
        v_market = plugins_list[0].get("version")
    v_mkdocs = None
    mkdocs = ROOT / "mkdocs.yml"
    if mkdocs.exists():
        m = re.search(r"^\s*version:\s*[\"']?([\d.]+)", mkdocs.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            v_mkdocs = m.group(1)
    if not v_plugin:
        fail("V2", "plugin.json has no version field")
        return
    if v_market != v_plugin:
        fail("V2", f"marketplace.json version {v_market!r} != plugin.json {v_plugin!r}")
    if v_mkdocs != v_plugin:
        fail("V2", f"mkdocs.yml extra.version {v_mkdocs!r} != plugin.json {v_plugin!r}")


def canonical_phases() -> set[str]:
    core = ROOT / "skills/neuroflow-core/SKILL.md"
    text = core.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\*\*Valid `phase:` frontmatter values:\*\*(.+)", text)
    if not m:
        fail("V3", "could not find the canonical phase list in skills/neuroflow-core/SKILL.md")
        return set()
    return set(re.findall(r"`([a-z][\w-]*)`", m.group(1)))


def check_commands(phases: set[str]) -> None:
    required = ("name", "description", "phase", "reads", "writes")
    for cmd in sorted((ROOT / "commands").glob("*.md")):
        fm = read_frontmatter(cmd)
        rel = f"commands/{cmd.name}"
        if fm is None:
            fail("V3", f"{rel} has no frontmatter block")
            continue
        for key in required:
            if key not in fm:
                fail("V3", f"{rel} frontmatter is missing `{key}:`")
        name = fm.get("name")
        if name and name != cmd.stem:
            fail("V3", f"{rel} frontmatter name `{name}` != filename `{cmd.stem}`")
        phase = fm.get("phase")
        if phases and phase and phase not in phases:
            fail("V3", f"{rel} declares phase `{phase}` — not in the canonical taxonomy ({', '.join(sorted(phases))})")
        docs_page = ROOT / "docs" / "commands" / f"{cmd.stem}.md"
        if not docs_page.exists():
            fail("V4", f"{rel} has no docs page at docs/commands/{cmd.stem}.md")


def check_skills() -> None:
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fm = read_frontmatter(skill_md)
        folder = skill_md.parent.name
        if fm is None:
            fail("V5", f"skills/{folder}/SKILL.md has no frontmatter block")
            continue
        name = fm.get("name")
        if name and name != folder:
            fail("V5", f"skills/{folder}/SKILL.md frontmatter name `{name}` != folder `{folder}`")


def check_hooks(parsed: dict[str, dict]) -> None:
    hooks = parsed.get("hooks/hooks.json")
    if not hooks:
        return
    for event, groups in (hooks.get("hooks") or {}).items():
        for group in groups:
            for h in group.get("hooks", []):
                cmd = h.get("command", "")
                if not (cmd.rstrip().endswith("; true") or cmd.rstrip().endswith("|| true")):
                    fail("V6", f"{event} hook command does not end with `; true` or `|| true`: {cmd[:60]}…")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def check_version_bump(base: str) -> None:
    changed = [f for f in git("diff", "--name-only", f"{base}...HEAD").splitlines() if f]
    if not changed:
        return
    substantive = [
        f for f in changed
        if f not in NO_BUMP_NEEDED and not f.startswith(NO_BUMP_PREFIXES)
    ]
    if not substantive:
        return
    old_raw = git("show", f"{base}:.claude-plugin/plugin.json")
    try:
        old_version = json.loads(old_raw).get("version") if old_raw else None
    except json.JSONDecodeError:
        old_version = None
    try:
        new_version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        new_version = None
    if old_version and new_version and old_version == new_version:
        fail(
            "V7",
            f"{len(substantive)} substantive file(s) changed vs {base} but plugin.json version "
            f"is still {new_version} — bump the patch version (see neuroflow-develop release workflow)",
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="git ref to compare against for the version-bump check (e.g. origin/main)")
    args = ap.parse_args()

    parsed = check_json_files()
    check_version_sync(parsed)
    check_commands(canonical_phases())
    check_skills()
    check_hooks(parsed)
    if args.base:
        check_version_bump(args.base)

    if FAILURES:
        print(f"FAIL validate_pr: {len(FAILURES)} failure(s)\n")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print("OK validate_pr: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
