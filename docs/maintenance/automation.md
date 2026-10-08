---
title: Maintenance Automation
---

# Maintenance Automation

Six GitHub Actions workflows maintain **neuroflow**. Three scheduled ones post reports to GitHub Discussions, a weekly canary tests the neuroflow mod against the newest Claude Code release, one validates every pull request and push to `main`, and one deploys the documentation site. The three report workflows read the repo's own specification files (skills, commands, agents, docs) as their ground truth ("Option A"), so their output is always grounded in what the repo actually contains.

---

## Workflows at a glance

| Workflow | Schedule | Discussion | Opens PRs? |
|---|---|---|---|
| Daily Maintainer Report | Daily 20:00 UTC | [#167](https://github.com/stanislavjiricek/neuroflow/discussions/167) | No |
| Sentinel-dev | Daily 20:00 UTC | [#168](https://github.com/stanislavjiricek/neuroflow/discussions/168) | Yes (auto-fixable only) |
| Research Radar | Weekly, Friday 20:00 UTC | [#169](https://github.com/stanislavjiricek/neuroflow/discussions/169) | No |
| Mod canary | Weekly, Monday 05:17 UTC | — (opens an issue when the mod breaks) | No |
| Validate | Every pull request and push to `main` | — | No |
| Deploy documentation | Every push to `main` | — | No |

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
  - cron: '0 20 * * *'   # change this
```

### How to change the target discussion

Change `--discussion-number 167` in the workflow's `run:` step.

---

## 2 — Sentinel-dev (`.github/workflows/sentinel-dev.yml`)

**Purpose:** Enforce internal consistency invariants in the plugin repo. Auto-fixes version drift by opening a PR; reports everything else.

**Repo context read:** All of `commands/`, `skills/`, `agents/`, `hooks/`, `docs/`, `mkdocs.yml`, `.claude-plugin/`, `README.md`, `.neuroflow/`.

**Script:** `scripts/automation/sentinel_check.py` — it runs the check registry in `scripts/automation/repo_checks.py`, the same one the per-PR validation runs. Each check is implemented once and keeps its id; the `sentinel-dev` agent cites the ids and adds the checks that need judgement.

### Checks performed

| Id | What it verifies |
|---|---|
| V1 | `plugin.json`, `marketplace.json` and `hooks/hooks.json` are valid JSON |
| V2 | Version sync across `plugin.json`, `marketplace.json`, `mkdocs.yml` `extra.version` and `.neuroflow/project_config.md` |
| V3 | Command frontmatter: `name`, `description`, canonical `phase`, `reads`, `writes`, `lifecycle`; `requires` / `produces` / `next` lists |
| V4 | Every `commands/*.md` has a `docs/commands/<name>.md` page |
| V5 | Skill and agent `name:` fields match their folder or file |
| V6 | `hooks/hooks.json`: structure, silent failure (`; true`), at most one hooks module and its path |
| V7 | Version bumped when substantive files changed (pull requests only) |
| V8 | Rule markers (`<!-- nf-rule: ID -->`) use known ids; every rule a mod guard enforces has one |
| V9 | No skill folder shares a command's name |
| V10 | Every command, skill and agent is in the README tables and the docs nav, each page listed once; no dead links |
| V11 | No dead `neuroflow:<name>` references in `SKILL.md` files |
| V12 | Release notes match the version (warning) |
| V13 | The repo's own `.neuroflow/` holds only `reasoning/` and `sessions/` (warning) |
| V14 | No private keys; emails and hardcoded secrets flagged for review |
| V15 | No stale flowie/hive paths or legacy field names (warning) |

### Auto-fixable issues (will create a PR)

- **V2:** `marketplace.json`, `mkdocs.yml` and `.neuroflow/project_config.md` out of sync with `plugin.json` — synced automatically (the same code as `bump_version.py --sync`). Only those files are committed.

### Running it locally

`python scripts/automation/sentinel_check.py --report-only` prints the report and never touches git or GitHub. Outside GitHub Actions the script refuses to commit, push or post.

### PR behaviour

- Branch name: `sentinel-dev/YYYY-MM-DD-auto-fix`
- PR title: `fix(sentinel): auto-fix consistency issues — YYYY-MM-DD`
- PR is linked in the Discussion comment

### How to change the schedule or target discussion

Same pattern as Daily Maintainer: edit `cron` and `--discussion-number` in the workflow file.

### Required permissions

The sentinel-dev workflow requires more permissions than the other report workflows:

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
  - cron: '0 20 * * 5'   # every Friday at 20:00 UTC
```

---

## 4 — Per-PR validation (`.github/workflows/validate.yml`)

**Purpose:** Catch structural mistakes before they merge. Runs on every pull request and every push to `main`, in two jobs.

**`validate` job:**

1. `python scripts/automation/validate_pr.py --base origin/<base branch>` — all checks V1–V15 from `repo_checks.py`. Findings marked `fail` fail the job; `warn` findings are printed for review. Exit codes: `0` no failures, `1` failures, `2` usage or internal error.
2. `python -m unittest discover -s tests -p "test_*.py" -v` — unit tests for the repo checks, `bump_version.py`, the pre-push hook, a smoke test that feeds simulated tool events into the `hooks/hooks.json` commands, and the skills' portable scripts. Runs even when step 1 failed.
3. `mkdocs build --strict` — the docs site builds without broken links.

**`mod` job** (the neuroflow mod): installs Claude Code 2.1.292, the version the mod is tested from, then runs

1. `claude plugin validate .` — the plugin manifest and its hooks module;
2. `claude plugin test .` — the mod's tests in `hooks/mod/tests/`;
3. `python scripts/automation/mod_policy.py` — compares the events the module hooks and the calls, environment variables and state the validator reports with the allowlist in `hooks/mod/policy.json`; anything new fails until a reviewer adds it.

Steps 2 and 3 run even when an earlier step failed.

The same validation runs locally from the repo root. To bump the version in all four places at once: `python scripts/automation/bump_version.py` (`--dry-run`, `--sync`, `--check`).

---

## 5 — Mod canary (`.github/workflows/mod-canary.yml`)

**Purpose:** Find out when a new Claude Code release breaks the neuroflow mod — function hooks are an early-access API that changes between releases — before users do.

**Schedule:** weekly, Monday 05:17 UTC (`cron: "17 5 * * 1"`).

**Steps:** installs the newest Claude Code (`@anthropic-ai/claude-code@latest`) and runs the `mod` job's three checks. When one fails, it opens an issue titled `mod canary: the neuroflow mod fails on Claude Code <version>`, unless an open issue with that title already exists.

---

## 6 — Deploy documentation (`.github/workflows/deploy-docs.yml`)

**Purpose:** Publish the documentation site. On every push to `main` it installs `requirements.txt`, runs `mkdocs build --strict` and deploys the result to GitHub Pages.

---

## Shared posting script

**File:** `scripts/automation/post_discussion.py`

The three report workflows use this script to post comments to GitHub Discussions via the GraphQL API.

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
- `validate` only reads (`contents: read`); `mod-canary` adds `issues: write` to open its issue; `deploy-docs` needs `pages: write` and `id-token: write` to publish the site.
- Every workflow installs its tools first — Python packages from PyPI, and Claude Code from npm where it is needed. At run time the report workflows call no external service except `api.github.com`, and the docs deploy publishes to GitHub Pages.

---

## Running workflows manually

Every workflow supports `workflow_dispatch`, so you can trigger it from the GitHub Actions UI without waiting for its schedule or a push:

1. Go to **Actions** in the repo
2. Click the workflow name
3. Click **Run workflow** → **Run workflow**

---

## Adding a new repo check

Add a function to `scripts/automation/repo_checks.py` that takes a `Context` and returns a list of `Finding`s, and register it in `CHECKS` under the next free id — never renumber or reuse an id, retire it instead. Add a test to `tests/automation/test_repo_checks.py` and a row to the check table in `agents/sentinel-dev.md`. `validate_pr.py` (every PR) and `sentinel_check.py` (daily) pick it up automatically. Use `severity=WARN` for heuristics that need a human, and `fix="version-sync"` only for drift the daily job may repair on its own.
