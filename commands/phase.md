---
name: phase
description: Show the current project phase and all phases worked on so far. Optionally switch to a different phase.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/
  - .neuroflow/timeline.md                # if it exists — deadlines under the map
  - .neuroflow/paper/paper-ledger.md      # only with paper_auto: on — the auto paper line
  - .neuroflow/paper/skeleton.md          # only with paper_auto: on — its sync date
  - .neuroflow/paper/gaps.md              # only with paper_auto: on
  - .neuroflow/*/runs.md                  # if any — long runs not yet reviewed
  - ~/.neuroflow/user.yaml                # personal default_mode, if set
  - ~/.neuroflow/local-projects.json      # flowie phase sync: which flowie project this folder is
  - commands/{active_phase}.md            # plugin file — its requires/produces/next frontmatter
writes:
  - .neuroflow/project_config.md          # active_phase only, when the person switches
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/reasoning/general.jsonl
  - ~/.neuroflow/flowie/projects/
lifecycle: light
---

# /phase

## What this command does

Shows a visual phase map of the project — current phase, visited phases, recommended phases, and untouched phases. Lets the user switch phase if they want.

With the neuroflow mod active, the mod answers `/neuroflow:phase` itself: the map with a picker you move through with the arrow keys and Enter (or a click), and the switch is written to `active_phase` in code. This file is the fallback for Claude Code without the mod, and it asks the same question with `AskUserQuestion`.

---

## Steps

1. Read `project_config.md` — from its frontmatter (`neuroflow:neuroflow-core` → **project_config.md — the config contract**; a legacy dialect is read as it is), open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (**Command lifecycle**, step 3), and extract:
   - `active_phase` (the current active phase)
   - `recommended_phases` (list suggested after the initial interview, if present)
   - `default_mode` (team default personality mode: `teacher`, `executor`, or `critic` — absent if not set)

   Also read `default_mode` from `~/.neuroflow/user.yaml` if it exists — a personal default overrides the team default.

2. Check which phase subfolders exist inside `.neuroflow/` — these are phases that have been worked on (a `.neuroflow/{phase}/` directory is present).

3. Check `sessions/` — find the most recent session log and note the date.

4. Print a visual phase map. Use these markers:

   - `◉` — current active phase
   - `●` — visited: a `.neuroflow/{phase}/` subfolder already exists (work has been done here)
   - `→` — recommended: suggested by neuroflow after the initial interview (listed in `recommended_phases` in `project_config.md`), but not yet visited
   - `○` — not started: no subfolder, not recommended

   The complete ordered list of phases is the **Phase taxonomy** in `neuroflow:neuroflow-core` — that section is canonical; if this file ever disagrees, core wins. Current canonical order:

   ```
   ideation → preregistration → grant-proposal → finance → experiment →
   tool-build → tool-validate → data → data-preprocess → data-analyze →
   brain-build → brain-optimize → brain-run → paper → review → poster →
   write-report → output   (+ notes — cadence-free, shown last)
   ```

   Print the map in order. Example output:

   ```
   Phase map — Last session: 2026-03-09

     ● ideation
     ◉ experiment          ← current
     → data-preprocess     ← recommended
     → data-analyze        ← recommended
     → paper               ← recommended
     ○ preregistration
     ○ grant-proposal
     ○ finance
     ○ tool-build
     ○ tool-validate
     ○ data
     ○ brain-build
     ○ brain-optimize
     ○ brain-run
     ○ review
     ○ poster
     ○ write-report
     ○ output
     ○ notes

   Legend: ◉ current  ● visited  → recommended  ○ not started
   ```

   Show visited and current phases first (in pipeline order), then recommended phases, then the rest.

   If `recommended_phases` is absent from `project_config.md`, omit the `→` entries and the legend entry for "recommended". Suggest running `/neuroflow` to set up the project and generate phase recommendations.

   **Below the phase map, render upcoming deadlines** from `.neuroflow/timeline.md` (if it exists and has entries): the next 3 entries with future dates, `⚠` on anything within 14 days, `❌ OVERDUE` on past dates that are not marked done:

   ```
   Deadlines:
     ⚠ 2026-08-25  SfN abstract deadline          (paper)
       2026-10-01  Ethics approval expires        (data)
   ```

   Skip the block silently if `timeline.md` is absent or empty.

   **Auto paper** — only when `paper_auto: on` in the frontmatter, print one line: `Auto paper: on | {n} facts ({m} final) | synced {date} | {g} gaps`. `{n}` = keys in `.neuroflow/paper/paper-ledger.md` (a later row with the same key supersedes earlier ones), `{m}` = keys whose latest row says `final`, `{date}` = the date in the first line of `skeleton.md`, `{g}` = gap rows in `gaps.md` (`neuroflow:phase-paper` → **Living paper skeleton**). Print nothing when `paper_auto` is off or absent, or when the files are missing.

   **Long runs** — if any `.neuroflow/*/runs.md` exists, run `python <neuroflow-core base dir>/../phase-brain-run/scripts/runs.py list --json` from the project root and print one line per run not yet reviewed: `Run {id}: {status} — {command}`. Print nothing when the list is empty, Python is unavailable or the script exits 2.

   Below that, print one line for the active personality mode and where it comes from:

   ```
   Personality mode: 🧐 Teacher (teacher, personal default)    [or ⚡ Executor (executor) / 🔍 Critic (critic); team default]
   ```

   If neither file sets `default_mode`, print: `Personality mode: not set (default: Executor — run /neuroflow to choose, or start any message with mode: <name>)`

   **Current phase checklist and next commands.** Read the frontmatter of the active phase's command in the plugin folder (`<neuroflow-core base dir>/../../commands/{active_phase}.md`). If it declares `requires:` or `produces:`, list each path with `[x]` when it exists and `[ ]` when it does not — information only, never a gate. If it declares `next:`, print `Next: /neuroflow:<name>` for each entry (at most three). Skip both silently when the keys are absent.

5. Ask with `AskUserQuestion` whether to switch:
   - **Stay in {active_phase}** — first option
   - up to three phase options: the phases after the current one in `recommended_phases`, in order (without that list, the next phases in the canonical order)
   - "Other" (added by the tool) — the person types any other phase; accept a canonical phase id from the Phase taxonomy and ask again if the answer matches none

6. If the user picks a different phase, set `active_phase` in the `project_config.md` frontmatter — that one key, in place (`neuroflow:neuroflow-core` → **project_config.md — the config contract**); `plugin_version` stays as it is, since only `/neuroflow:migrate` raises it. Nothing else follows the phase: the `.claude/CLAUDE.md` block is static and is never edited here, and no other instruction file is written. Then append `## HH:MM — [phase] Active phase: {old} → {new}` to `sessions/YYYY-MM-DD.md`, add a line to `reasoning/general.jsonl` (a phase change is a mandatory reasoning trigger — `neuroflow:neuroflow-core` → **Reasoning log**), and suggest the new phase's command.

7. **Flowie phase sync:** After updating `project_config.md`, check whether `flowie_profiles` is set and non-empty in `project_config.md`. If it is, and `~/.neuroflow/flowie/` exists as a git repo, use the first entry (`flowie_profiles[0]`). The person's own private flowie repo is a sync target they set up, so this sync asks nothing more (`neuroflow:neuroflow-core` → **Sharing tiers**); it runs only for a phase change the person chose in step 5 — never for one the model inferred. These are the steps of `/flowie` → **Phase sync**:

   - Pull (`/flowie` → Git operations pattern): skip the whole sync while `~/.neuroflow/flowie/.git/rebase-merge` or `rebase-apply` exists (a rebase the person has in progress). Otherwise `git -C ~/.neuroflow/flowie pull --rebase`; if it stops on a conflict, run `git -C ~/.neuroflow/flowie rebase --abort` — only the rebase this pull started — and skip the rest
   - Read `projects/projects.json` — find the linked project: the `name` of this repo's entry in `~/.neuroflow/local-projects.json`, else the `projects.json` entry whose `repos[].url` matches `git remote get-url origin`. If neither matches, skip the rest
   - Update `current_phase` to the new phase
   - Append to `visited_phases` if this phase is not already listed: `{ "phase": "{new_phase}", "entered": "{YYYY-MM-DD}" }`
   - Write updated `projects/projects.json`
   - Read `projects/{name}.md` — append a new row to the Phase timeline table: `| {new_phase} | {YYYY-MM-DD} |`
   - Commit, pull and push: `git -C ~/.neuroflow/flowie add projects/projects.json "projects/{name}.md" && git -C ~/.neuroflow/flowie commit -m "phase: {project} → {new_phase}" && git -C ~/.neuroflow/flowie pull --rebase && git -C ~/.neuroflow/flowie push || true` — if this pull stops on a conflict, abort it as above; the commit stays local for `/flowie --sync`

   If `~/.neuroflow/flowie/` does not exist, `flowie_profiles` is absent or empty, or any git operation fails, skip silently — never surface flowie errors to the user during a phase switch.
