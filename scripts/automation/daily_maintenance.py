#!/usr/bin/env python3
"""Daily Maintainer Report for stanislavjiricek/neuroflow.

Reads repo context (project_config.md, commands, skills, agents) and
GitHub issues, then posts a clustered report to Discussion #167.

Usage:
    python daily_maintenance.py --repo owner/name --discussion-number 167
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

# Add automation scripts directory to path for shared module
sys.path.insert(0, str(Path(__file__).parent))
from post_discussion import post_discussion_comment

REPO_ROOT = Path(__file__).parent.parent.parent

# ---------------------------------------------------------------------------
# Keyword-based issue clustering
# ---------------------------------------------------------------------------

CLUSTERS = {
    "Commands / UX": [
        "command", "slash", "ux", "interface", "chatting", "personality",
        "mode", "notebooklm", "cli", "entry",
    ],
    "Search / Literature": [
        "search", "scholar", "journal", "literature", "pubmed", "biorxiv",
        "paper", "expert", "knowledge",
    ],
    "Memory / Architecture": [
        "memory", "hive", "flow", "neuroflow", "project", "config",
        "session", "context",
    ],
    "Agents / Workflows": [
        "agent", "workflow", "pipeline", "orchestrat", "sentinel",
        "flowie", "ideation", "experiment",
    ],
    "Data / Analysis": [
        "data", "analysis", "preprocess", "analyze", "eeg", "fmri",
        "bids", "epoch", "artifact",
    ],
    "Docs / Repo": [
        "doc", "readme", "github", "branch", "protection", "setting",
        "label", "issue", "ci", "workflow",
    ],
}

STALE_THRESHOLD_DAYS = 30

LABEL_SUGGESTIONS = {
    "Commands / UX": "area:commands",
    "Search / Literature": "area:search",
    "Memory / Architecture": "area:memory",
    "Agents / Workflows": "area:agents",
    "Data / Analysis": "area:data",
    "Docs / Repo": "area:repo",
}

TYPE_KEYWORDS = {
    "type:bug": ["bug", "error", "broken", "fail", "crash", "wrong", "fix"],
    "type:feature": [
        "feature", "add", "new", "implement", "support", "allow", "enable",
        "request",
    ],
    "type:docs": ["doc", "readme", "documentation", "typo", "spelling"],
    "type:chore": ["chore", "setting", "cleanup", "refactor", "ci", "action"],
}


def guess_cluster(title: str, body: str) -> str:
    text = (title + " " + (body or "")).lower()
    scores = {cluster: 0 for cluster in CLUSTERS}
    for cluster, keywords in CLUSTERS.items():
        for kw in keywords:
            if kw in text:
                scores[cluster] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def guess_type(title: str, body: str) -> str:
    text = (title + " " + (body or "")).lower()
    for label, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return label
    return "type:feature"


# ---------------------------------------------------------------------------
# GitHub REST helpers
# ---------------------------------------------------------------------------

def github_get(token: str, path: str) -> list | dict:
    """Paginate a GitHub REST endpoint and return all results."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = "https://api.github.com"
    url = f"{base}{path}&per_page=100" if "?" in path else f"{base}{path}?per_page=100"
    results = []
    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                link_header = resp.headers.get("Link", "")
        except urllib.error.HTTPError as exc:
            print(f"ERROR: GitHub API {exc.code} on {url}", file=sys.stderr)
            sys.exit(1)
        if isinstance(data, list):
            results.extend(data)
        else:
            return data
        # Follow pagination
        next_url = None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                match = re.search(r"<([^>]+)>", part)
                if match:
                    next_url = match.group(1)
        url = next_url
    return results


def fetch_issues(token: str, owner: str, name: str) -> list:
    """Return all open issues (excluding pull requests)."""
    raw = github_get(token, f"/repos/{owner}/{name}/issues?state=open")
    return [i for i in raw if "pull_request" not in i]


# ---------------------------------------------------------------------------
# Repo context reading
# ---------------------------------------------------------------------------

def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def count_commands() -> int:
    return len(list((REPO_ROOT / "commands").glob("*.md")))


def count_skills() -> int:
    return len(list((REPO_ROOT / "skills").glob("*/SKILL.md")))


def count_agents() -> int:
    return len(list((REPO_ROOT / "agents").glob("*.md")))


def get_plugin_version() -> str:
    plugin_json = REPO_ROOT / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        return data.get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(issues: list, run_date: str) -> tuple[str, bool]:
    """Return (markdown_report, has_actionable_items)."""
    lines: list[str] = []

    # Cluster issues
    clustered: dict[str, list] = {}
    for issue in issues:
        cluster = guess_cluster(issue["title"], issue.get("body") or "")
        clustered.setdefault(cluster, []).append(issue)

    # Count stale issues (no update in 30+ days)
    today = datetime.date.today()
    stale = []
    for issue in issues:
        updated = issue.get("updated_at", "")[:10]
        if updated:
            try:
                delta = today - datetime.date.fromisoformat(updated)
                if delta.days >= STALE_THRESHOLD_DAYS:
                    stale.append(issue)
            except ValueError:
                pass

    actionable = bool(issues)  # any open issue is worth noting

    # --- Repo context summary ---
    version = get_plugin_version()
    n_commands = count_commands()
    n_skills = count_skills()
    n_agents = count_agents()

    lines.append(f"## Daily Maintainer Report — {run_date}")
    lines.append("")
    lines.append("### Repo snapshot")
    lines.append(f"- Plugin version: **{version}**")
    lines.append(f"- Commands: {n_commands} | Skills: {n_skills} | Agents: {n_agents}")
    lines.append(f"- Open issues: **{len(issues)}**")
    if stale:
        lines.append(f"- Stale issues (≥{STALE_THRESHOLD_DAYS} days, no update): **{len(stale)}**")
    lines.append("")

    if not issues:
        lines.append("_No open issues — nothing to triage today._")
        return "\n".join(lines), False

    # --- Issue clusters ---
    lines.append("### Issue clusters")
    lines.append("")
    for cluster, cluster_issues in sorted(clustered.items()):
        area_label = LABEL_SUGGESTIONS.get(cluster, "area:other")
        lines.append(f"**{cluster}**")
        for iss in cluster_issues:
            num = iss["number"]
            title = iss["title"]
            type_label = guess_type(title, iss.get("body") or "")
            existing_labels = [lb["name"] for lb in iss.get("labels", [])]
            proposed = []
            if type_label not in existing_labels:
                proposed.append(type_label)
            if area_label not in existing_labels:
                proposed.append(area_label)
            proposed_str = f" — propose labels: `{'`, `'.join(proposed)}`" if proposed else ""
            lines.append(f"- #{num} {title}{proposed_str}")
        lines.append("")

    # --- Stale issues ---
    if stale:
        lines.append(f"### Stale issues (no activity in ≥{STALE_THRESHOLD_DAYS} days)")
        for iss in stale:
            lines.append(
                f"- #{iss['number']} {iss['title']} — last updated {iss.get('updated_at','')[:10]}"
            )
        lines.append("")

    # --- Recommended next actions ---
    lines.append("### Recommended next actions")
    lines.append("")

    # Top 3 actionable suggestions based on clusters
    suggestions = []
    if "Docs / Repo" in clustered:
        iss = clustered["Docs / Repo"][0]
        suggestions.append(
            f"1. **Quick win (~10 min)** — Add labels and triage #{iss['number']} "
            f"(_\"{iss['title']}_\")"
        )
    if "Commands / UX" in clustered or "Agents / Workflows" in clustered:
        pool = clustered.get("Commands / UX", []) + clustered.get("Agents / Workflows", [])
        iss = pool[0]
        suggestions.append(
            f"2. **Medium (~30 min)** — Write a spec or design note for #{iss['number']} "
            f"(_\"{iss['title']}_\")"
        )
    if "Search / Literature" in clustered or "Memory / Architecture" in clustered:
        pool = (
            clustered.get("Search / Literature", [])
            + clustered.get("Memory / Architecture", [])
        )
        iss = pool[0]
        suggestions.append(
            f"3. **Larger (~1–2 h)** — Implement or prototype #{iss['number']} "
            f"(_\"{iss['title']}_\")"
        )

    if not suggestions:
        # Fallback to top 3 issues
        for i, iss in enumerate(issues[:3], 1):
            suggestions.append(
                f"{i}. Review and triage #{iss['number']} (_\"{iss['title']}_\")"
            )

    lines.extend(suggestions)
    lines.append("")
    lines.append(
        "_Labels are proposed only — apply via GitHub Labels UI or `gh issue edit`._"
    )
    lines.append("")
    lines.append(
        "<details><summary>Repo constitution grounding</summary>\n\n"
        f"This report was generated by reading `.neuroflow/project_config.md`, "
        f"`docs/commands/index.md`, `commands/` ({n_commands} files), "
        f"`skills/` ({n_skills} skills), and `agents/` ({n_agents} agents).\n\n"
        "</details>"
    )

    return "\n".join(lines), actionable


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Maintainer Report")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--discussion-number", type=int, required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    owner, name = args.repo.split("/")
    run_date = datetime.date.today().isoformat()

    print(f"Fetching open issues for {args.repo}…")
    issues = fetch_issues(token, owner, name)
    print(f"Found {len(issues)} open issues.")

    report_body, actionable = build_report(issues, run_date)

    n_actionable = len(issues)
    if not actionable:
        banner = f"@stanislavjiricek ✅ ALL GOOD — {run_date}"
    else:
        banner = (
            f"@stanislavjiricek ❌ NEEDS ATTENTION — {run_date} "
            f"({n_actionable} actionable items)"
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
