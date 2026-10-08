#!/usr/bin/env python3
"""Sentinel-dev: daily repo consistency report for stanislavjiricek/neuroflow.

Runs the check registry in repo_checks.py (the same checks validate_pr.py runs on every
PR; agents/sentinel-dev.md cites their ids), auto-fixes version drift on a branch + PR,
and posts the report to Discussion #168.

Usage:
    python sentinel_check.py --repo owner/name --discussion-number 168   # GitHub Actions only
    python sentinel_check.py --report-only                              # anywhere: print, no side effects
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import repo_checks  # noqa: E402
from post_discussion import post_discussion_comment  # noqa: E402

REPO_ROOT = repo_checks.ROOT
Finding = repo_checks.Finding


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
    issues: list[Finding],
    run_date: str,
    pr_url: str = "",
) -> tuple[str, bool]:
    lines = [f"## Sentinel-dev Report — {run_date}", ""]
    checks = [c for c in repo_checks.CHECKS if not c.needs_base]

    if not issues and not pr_url:
        lines.append("### Checks")
        lines.append("")
        for check in checks:
            lines.append(f"- ✅ {check.id} — {check.title}")
        lines.append("")
        lines.append("_All checks passed — no issues found._")
        return "\n".join(lines), False

    by_check: dict[str, list[Finding]] = {}
    for iss in issues:
        by_check.setdefault(iss.check, []).append(iss)

    lines.append("### Checks")
    lines.append("")
    for check in checks:
        found = by_check.get(check.id)
        if found:
            lines.append(f"- ❌ **{check.id} — {check.title}** ({len(found)} issue(s))")
            for iss in found:
                tag = " (warn)" if iss.severity == repo_checks.WARN else ""
                lines.append(f"  - {iss.message}{tag}")
        else:
            lines.append(f"- ✅ {check.id} — {check.title}")
    lines.append("")

    fixable = [i for i in issues if i.fix == repo_checks.FIX_VERSION_SYNC]
    if fixable:
        lines.append("### Auto-fix plan")
        lines.append("")
        lines.append("- Sync every version site to `plugin.json` (`bump_version.py --sync`)")
        lines.append("")

    if pr_url:
        lines.append("### PR opened")
        lines.append("")
        lines.append(f"- {pr_url}")
        lines.append("")

    manual = [i for i in issues if i.fix != repo_checks.FIX_VERSION_SYNC]
    if manual:
        lines.append("### Manual action required")
        lines.append("")
        lines.append(
            f"{len(manual)} issue(s) require manual attention (not auto-fixable)."
        )

    return "\n".join(lines), True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Sentinel-dev consistency check")
    parser.add_argument("--repo", help="owner/name")
    parser.add_argument("--discussion-number", type=int)
    parser.add_argument("--report-only", action="store_true",
                        help="print the report and exit 0/1; no git, no GitHub (safe on any machine)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):  # the report carries emoji; local consoles may not encode them
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    run_date = datetime.date.today().isoformat()
    all_issues = repo_checks.run(REPO_ROOT)

    if args.report_only:
        print(build_report(all_issues, run_date)[0])
        return 1 if all_issues else 0
    if not (args.repo and args.discussion_number):
        parser.error("--repo and --discussion-number are required (or use --report-only)")
    # The fix path resets a branch, stages everything and force-pushes: CI only.
    if os.environ.get("GITHUB_ACTIONS") != "true":
        print("Refusing to commit, push or post outside GitHub Actions. "
              "Run validate_pr.py or sentinel_check.py --report-only instead.", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        return 1

    owner, name = args.repo.split("/")
    print(f"Ran sentinel checks: {len(all_issues)} issue(s).")

    pr_url = ""
    fixable = [i for i in all_issues if i.fix == repo_checks.FIX_VERSION_SYNC]

    if fixable:
        branch_name = f"sentinel-dev/{run_date}-auto-fix"
        print(f"Auto-fixable issues found. Creating branch `{branch_name}`…")

        changed = repo_checks.sync_versions(REPO_ROOT)
        fixed_descriptions = [f"Sync `{rel}` to the plugin.json version" for rel in changed]
        for desc in fixed_descriptions:
            print(f"Fixed: {desc}")

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
                ["git", "add", "--", *changed],
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
