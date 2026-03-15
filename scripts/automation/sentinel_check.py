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

    return issues


def check4_dead_skill_references() -> list[Issue]:
    """Check 4: dead references to skills/commands inside SKILL.md files."""
    issues = []
    skill_names = {p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    command_names = {p.stem for p in (REPO_ROOT / "commands").glob("*.md")}

    ref_pattern = re.compile(r"neuroflow:([a-z0-9_-]+)")

    # Placeholder tokens used as examples in developer-facing docs — skip these
    PLACEHOLDER_TOKENS = {"my-skill", "my-command", "skill-name", "command-name", "my-agent"}

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
            "Check 3 — Version sync",
            "Check 4 — Dead skill/command references",
            "Check 6 — Command frontmatter completeness",
            "Check 8 — hooks.json validity",
            "Check 9 — Docs website sync",
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
        "Check 3": "Version sync",
        "Check 4": "Dead skill/command references",
        "Check 6": "Command frontmatter completeness",
        "Check 8": "hooks.json validity",
        "Check 9a": "mkdocs.yml version sync",
        "Check 9b": "Command docs completeness",
        "Check 9c": "Nav dead links",
    }
    all_checks = ["Check 1", "Check 3", "Check 4", "Check 6", "Check 8", "Check 9a", "Check 9b", "Check 9c"]
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
    all_issues.extend(check3_version_sync())
    all_issues.extend(check4_dead_skill_references())
    all_issues.extend(check6_command_frontmatter())
    all_issues.extend(check8_hooks_json())
    all_issues.extend(check9_docs_sync())

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
