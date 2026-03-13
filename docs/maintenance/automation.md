---
title: Maintenance Automation
---

# Maintenance Automation

Three scheduled GitHub Actions workflows provide automated repo maintenance for **neuroflow**. Each workflow reads the repo's own specification files (skills, commands, agents, docs) as its ground truth ("Option A"), so the output is always grounded in what the repo actually contains.

---

## Workflows at a glance

| Workflow | Schedule | Discussion | Opens PRs? |
|---|---|---|---|
| Daily Maintainer Report | Daily 07:00 UTC | [#167](https://github.com/stanislavjiricek/neuroflow/discussions/167) | No |
| Sentinel-dev | Daily 06:00 UTC | [#168](https://github.com/stanislavjiricek/neuroflow/discussions/168) | Yes (auto-fixable only) |
| Research Radar | Weekly, Monday 08:00 UTC | [#169](https://github.com/stanislavjiricek/neuroflow/discussions/169) | No |

All report comments begin with a status banner so you can stop reading immediately:

```
@stanislavjiricek ✅ ALL GOOD — YYYY-MM-DD
```
or
```
@stanislavjiricek ❌ NEEDS ATTENTION — YYYY-MM-DD (N actionable items)
```

---

## 1 — Daily Maintainer Report (`.github/workflows/daily-maintenance.yml`)

**Purpose:** Cluster open GitHub issues by theme, propose labels, and surface the top 3 recommended next actions.

**Repo context read:**

- `.neuroflow/project_config.md` — project overview and plugin version
- `docs/commands/index.md` — declared command surface
- `commands/**` — command spec files (counts + frontmatter)
- `skills/**` — skill files (counts)
- `agents/**` — agent files (counts)

**Script:** `scripts/automation/daily_maintenance.py`

### What it posts

- Plugin version, command/skill/agent counts
- Issues grouped by area: Commands/UX, Search/Literature, Memory/Architecture, Agents/Workflows, Data/Analysis, Docs/Repo
- Proposed labels for each issue (`type:feature`, `area:commands`, etc.)
- Top 3 recommended next actions sized as: quick win / medium / larger
- Stale issues (no update in ≥30 days)

### How to change the schedule

Edit the `cron` line in `.github/workflows/daily-maintenance.yml`:

```yaml
schedule:
  - cron: '0 7 * * *'   # change this
```

### How to change the target discussion

Change `--discussion-number 167` in the workflow's `run:` step.

---

## 2 — Sentinel-dev (`.github/workflows/sentinel-dev.yml`)

**Purpose:** Enforce internal consistency invariants in the plugin repo. Auto-fixes simple issues by opening a PR; reports everything else.

**Repo context read:** All of `commands/`, `skills/`, `agents/`, `hooks/hooks.json`, `mkdocs.yml`, `.claude-plugin/plugin.json`, `README.md`.

**Script:** `scripts/automation/sentinel_check.py`

### Checks performed

| Check | What it verifies |
|---|---|
| Check 1 | `name:` frontmatter matches folder/filename in `skills/`, `agents/`, `commands/` |
| Check 3 | `plugin.json` version matches `## What's new in X.Y.Z` heading in `README.md` |
| Check 4 | `neuroflow:some-skill` references in `SKILL.md` files point to real skills/commands |
| Check 6 | Every `commands/*.md` has required frontmatter fields (`name`, `description`) |
| Check 8 | `hooks/hooks.json` is valid JSON with required fields (`matcher`, `type`, `command`) |
| Check 9a | `mkdocs.yml` version matches `plugin.json` |
| Check 9b | Every `commands/*.md` has a corresponding `docs/commands/<name>.md` |
| Check 9c | Every `mkdocs.yml` nav entry points to a file that exists under `docs/` |

### Auto-fixable issues (will create a PR)

- **Check 9a:** `mkdocs.yml` version out of sync with `plugin.json` — updated automatically.

### PR behaviour

- Branch name: `sentinel-dev/YYYY-MM-DD-auto-fix`
- PR title: `fix(sentinel): auto-fix consistency issues — YYYY-MM-DD`
- PR is linked in the Discussion comment

### How to change the schedule or target discussion

Same pattern as Daily Maintainer: edit `cron` and `--discussion-number` in the workflow file.

### Required permissions

The sentinel-dev workflow requires more permissions than the others:

```yaml
permissions:
  contents: write       # to push fix branches
  discussions: write    # to post the report comment
  pull-requests: write  # to open the fix PR
```

These are set automatically in the workflow file. No additional secrets are needed; `GITHUB_TOKEN` is used.

---

## 3 — Research Radar (`.github/workflows/research-radar.yml`)

**Purpose:** Produce a weekly "Radar Brief" with new implementation ideas, detected capability gaps, and threats relevant to neuroflow's neuroscience/scientific workflow focus.

**Repo context read:** `commands/`, `skills/`, `agents/`, `README.md` changelog headings, `.claude-plugin/plugin.json`.

**Script:** `scripts/automation/research_radar.py`

### What it posts

- **New ideas** — emerging topics with priority ratings and suggested implementation locations
- **Detected capability gaps** — research domains with sparse coverage in current commands/skills
- **Threats / watchlist** — API changes, dependency risks, compliance notes
- **Proposed backlog entries** — ready-to-file feature or resilience tasks (no PRs opened)

!!! note "Web crawling"
    The current implementation is self-contained and deterministic — it does not make external web requests. The PubMed and bioRxiv MCP servers are already configured in `.claude-plugin/plugin.json` and can be wired in later to source live research signals.

### How to change the schedule

```yaml
schedule:
  - cron: '0 8 * * 1'   # every Monday at 08:00 UTC
```

---

## Shared posting script

**File:** `scripts/automation/post_discussion.py`

All three workflows use this script to post comments to GitHub Discussions via the GraphQL API.

**Usage:**

```bash
python scripts/automation/post_discussion.py \
  --repo owner/name \
  --discussion-number 167 \
  --body "Your markdown comment here"
```

**Requirements:**

- `GITHUB_TOKEN` environment variable must be set
- The token must have `discussions: write` permission (the default `GITHUB_TOKEN` in Actions has this)

**Error handling:**

- Exits with code 1 and a clear message if the token lacks permission (HTTP 401/403 or GraphQL `forbidden` error)
- Exits with code 1 if the discussion number is not found

---

## Permissions and security

- No secrets are stored in the repo — only `GITHUB_TOKEN` (auto-provided by Actions) is used.
- The `daily-maintenance` and `research-radar` workflows use minimal permissions (`contents: read`, `discussions: write`).
- The `sentinel-dev` workflow additionally needs `contents: write` and `pull-requests: write` to create fix branches and open PRs.
- No external services are called except `api.github.com`.

---

## Running workflows manually

All three workflows support `workflow_dispatch` so you can trigger them from the GitHub Actions UI without waiting for the schedule:

1. Go to **Actions** in the repo
2. Click the workflow name
3. Click **Run workflow** → **Run workflow**

---

## Adding new checks to sentinel-dev

Add a new function following the `check<N>_name()` pattern in `scripts/automation/sentinel_check.py` that returns `list[Issue]`. Then call it in `main()` alongside the existing checks. Mark issues as `fixable=True` and provide a `fix_description` if there's a straightforward programmatic fix to apply.
