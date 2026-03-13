#!/usr/bin/env python3
"""Research Radar — weekly brief for stanislavjiricek/neuroflow.

Reads the repo's changelog, docs, commands, and skills to detect
capability gaps and produce a structured ideas + threat brief.
Posts to Discussion #169.

Usage:
    python research_radar.py --repo owner/name --discussion-number 169
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from post_discussion import post_discussion_comment

REPO_ROOT = Path(__file__).parent.parent.parent

# ---------------------------------------------------------------------------
# Research-domain categories and ideas patterns
# ---------------------------------------------------------------------------

MIN_KEYWORD_COVERAGE_THRESHOLD = 2

CAPABILITY_AREAS = {
    "EEG / iEEG": ["eeg", "ieeg", "electrode", "epoch", "ica", "erp", "bci"],
    "fMRI": ["fmri", "bold", "spm", "freesurfer", "nilearn", "nibabel"],
    "Eye tracking": ["eye track", "gaze", "pupil", "fixation", "saccade"],
    "ECG / Physiology": ["ecg", "hrv", "heart rate", "physio", "emg"],
    "Brain simulation": ["brain-build", "brain-run", "neuron model", "network", "simulation"],
    "Literature / Search": ["pubmed", "biorxiv", "scholar", "literature", "paper"],
    "Statistics / ML": ["glm", "decoding", "classification", "connectivity", "regression"],
    "Data management": ["bids", "data", "format", "conversion", "validation"],
    "Writing / Publication": ["paper", "manuscript", "review", "grant"],
    "Workflow automation": ["pipeline", "orchestrat", "agent", "hook", "sentinel"],
}

# Emerging topics that are not yet well-covered → potential ideas
EMERGING_TOPICS = [
    {
        "topic": "LLM-assisted hypothesis generation",
        "relevance": "LLMs can now generate and critique scientific hypotheses; could extend `/ideation`",
        "suggested_location": "commands/ideation.md or new `/hypothesis` command",
        "priority": "high",
    },
    {
        "topic": "BIDS 2.0 support",
        "relevance": "BIDS 2.0 introduces new modalities and stricter validation rules",
        "suggested_location": "skills/phase-data/SKILL.md — add BIDS 2.0 validation guidance",
        "priority": "medium",
    },
    {
        "topic": "Automated preregistration syncing (OSF API)",
        "relevance": "OSF has a REST API; `/preregistration` could auto-submit instead of guiding manually",
        "suggested_location": "commands/preregistration.md — add `--submit` flag",
        "priority": "medium",
    },
    {
        "topic": "Reproducibility checks (code + data provenance)",
        "relevance": "Growing requirement from journals; DVC or DataLad integration could help",
        "suggested_location": "New `skills/phase-data/` section or `/data` command extension",
        "priority": "medium",
    },
    {
        "topic": "Multi-modal fusion (EEG+fMRI, EEG+eye tracking)",
        "relevance": "Multi-modal recording is increasingly common; neuroflow currently handles modalities separately",
        "suggested_location": "New `/fusion` command or extension to `/data-analyze`",
        "priority": "low",
    },
    {
        "topic": "Real-time feedback loop for BCI",
        "relevance": "Closed-loop BCI paradigms require tight latency; `/tool-build` could gain BCI-specific templates",
        "suggested_location": "commands/tool-build.md, skills/phase-tool-build/SKILL.md",
        "priority": "low",
    },
    {
        "topic": "NotebookLM / AI note-taking integration",
        "relevance": "Open issue #166 — community request; could be a new agent or `/notes` enhancement",
        "suggested_location": "agents/ or commands/notes.md",
        "priority": "high",
    },
]

THREATS = [
    {
        "threat": "PubMed E-utilities API rate limits",
        "description": "NCBI enforces 3 req/s without API key, 10/s with key; bulk `/search` runs may hit limits",
        "mitigation": "Add retry with backoff in scholar agent; surface API-key prompt in `/setup`",
    },
    {
        "threat": "bioRxiv MCP server availability",
        "description": "The `paper-search-mcp-nodejs` package is a community package; no SLA",
        "mitigation": "Add fallback to direct bioRxiv REST API (`https://api.biorxiv.org/`) if MCP fails",
    },
    {
        "threat": "Claude Code plugin API changes",
        "description": "Anthropic may change plugin format, hook events, or skill invocation between versions",
        "mitigation": "Pin plugin version in `.claude-plugin/plugin.json`; watch Anthropic changelog",
    },
    {
        "threat": "Markdown linting strictness (mkdocs-material)",
        "description": "`mkdocs build --strict` fails on warnings; new docs may break CI if not checked locally",
        "mitigation": "Add a pre-commit hook or local `mkdocs build --strict` alias in contributing docs",
    },
]


# ---------------------------------------------------------------------------
# Repo gap analysis
# ---------------------------------------------------------------------------

def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def get_command_names() -> list[str]:
    return sorted(p.stem for p in (REPO_ROOT / "commands").glob("*.md"))


def get_skill_names() -> list[str]:
    return sorted(p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md"))


def get_agent_names() -> list[str]:
    return sorted(p.stem for p in (REPO_ROOT / "agents").glob("*.md"))


def detect_capability_gaps(commands: list[str], skills: list[str]) -> list[str]:
    """Identify CAPABILITY_AREAS that are not well covered in current skills."""
    all_text = " ".join(commands + skills).lower()
    gaps = []
    for area, keywords in CAPABILITY_AREAS.items():
        covered = sum(1 for kw in keywords if kw in all_text)
        if covered < MIN_KEYWORD_COVERAGE_THRESHOLD:
            gaps.append(area)
    return gaps


def recent_changelog_items(n: int = 5) -> list[str]:
    """Extract the last N 'What's new' headings from README.md."""
    readme = read_file_safe(REPO_ROOT / "README.md")
    matches = re.findall(r"## What's new in ([0-9]+\.[0-9]+\.[0-9]+)", readme)
    return matches[:n]


def get_plugin_version() -> str:
    plugin_json = REPO_ROOT / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        return data.get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(run_date: str, week_label: str) -> str:
    commands = get_command_names()
    skills = get_skill_names()
    agents = get_agent_names()
    version = get_plugin_version()
    gaps = detect_capability_gaps(commands, skills)
    changelog = recent_changelog_items()

    lines = [
        f"## Research Radar Brief — {week_label}",
        "",
        f"_Generated {run_date} | neuroflow v{version} | "
        f"{len(commands)} commands · {len(skills)} skills · {len(agents)} agents_",
        "",
    ]

    # --- Recent changelog context ---
    lines.append("### Recent changes (context for gap analysis)")
    lines.append("")
    if changelog:
        lines.append(f"Most recent versions in changelog: {', '.join(changelog)}")
    else:
        lines.append("_No changelog data found._")
    lines.append("")

    # --- New ideas ---
    lines.append("### 💡 New ideas (implementation candidates)")
    lines.append("")
    for i, idea in enumerate(EMERGING_TOPICS, 1):
        prio = idea["priority"].upper()
        lines.append(f"**{i}. {idea['topic']}** `[{prio}]`")
        lines.append(f"> {idea['relevance']}")
        lines.append(f"> 📍 Suggested location: `{idea['suggested_location']}`")
        lines.append("")

    # --- Capability gaps ---
    if gaps:
        lines.append("### 🔍 Detected capability gaps")
        lines.append("")
        lines.append(
            "The following research domains have sparse coverage in current commands/skills:"
        )
        for gap in gaps:
            lines.append(f"- **{gap}**")
        lines.append("")

    # --- Threats ---
    lines.append("### ⚠️ Threats / watchlist")
    lines.append("")
    for threat in THREATS:
        lines.append(f"**{threat['threat']}**")
        lines.append(f"> {threat['description']}")
        lines.append(f"> Mitigation: {threat['mitigation']}")
        lines.append("")

    # --- Proposed backlog entries ---
    lines.append("### 📋 Proposed backlog entries")
    lines.append("")
    lines.append("_These are proposals only — no PRs will be opened by this workflow._")
    lines.append("")
    high_priority = [t for t in EMERGING_TOPICS if t["priority"] == "high"]
    for item in high_priority:
        lines.append(f"- `[feature]` **{item['topic']}** → `{item['suggested_location']}`")
    for threat in THREATS[:2]:
        lines.append(f"- `[resilience]` {threat['mitigation']}")
    lines.append("")

    lines.append(
        "<details><summary>How this report is generated</summary>\n\n"
        "This radar brief is generated deterministically from the repo's own content:\n"
        "commands, skills, agents, and the README changelog. "
        "It does not make external web requests. "
        "Web-sourced intel can be added later by wiring an MCP search server "
        "(PubMed / bioRxiv are already configured in `.claude-plugin/plugin.json`).\n\n"
        "</details>"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Research Radar Brief")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--discussion-number", type=int, required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    today = datetime.date.today()
    run_date = today.isoformat()

    # ISO week label
    iso_year, iso_week, _ = today.isocalendar()
    week_label = f"Week {iso_week}, {iso_year}"

    print(f"Building Research Radar for {week_label}…")
    report_body = build_report(run_date, week_label)

    banner = f"@stanislavjiricek ✅ ALL GOOD — {run_date} (Radar Brief ready)"
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
