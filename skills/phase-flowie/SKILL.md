---
name: phase-flowie
description: Phase guidance for the neuroflow /flowie command. Covers how to read and use the flowie profile for personalization, write rules for ~/.neuroflow/flowie/, GitHub sync protocol, and profile-aware assistance across all phases.
---

# phase-flowie

The `/flowie` command manages the user's personal identity layer — a private GitHub repository containing their research profile. This skill defines how Claude should read, update, and apply that profile across all neuroflow phases.

## What the flowie profile contains

The flowie profile lives in `~/.neuroflow/flowie/` and consists of three files:

| File | Contents |
|---|---|
| `profile.md` | Research identity: name, email, domain, methodological preferences, writing style, stances, key beliefs |
| `ideas.md` | Ongoing ideas and hypotheses that span multiple projects |
| `sync.json` | GitHub repo URL, last sync timestamp, list of linked projects |

`profile.md` includes `email:` and `hives:` fields under `## Identity`:

```markdown
## Identity
name: {name}
email: {email}
research_domain: {domain}
hives: [acme-neuroscience/hive-lab, another-org/hive-research]
```

- `email:` — used by `/meeting` as the organizer address for calendar invites
- `hives:` — list of Hive repos this person is a member of (`{org}/{repo}` format). Used by `/hive --init` to suggest pre-filling the hive repo URL when connecting a new project. Lets Claude know which teams the researcher belongs to across all their projects.

The profile is private by design. It lives in a private GitHub repository and is never included in project exports or any output intended for external readers.

## Reading the profile

At the start of any command session, if `~/.neuroflow/flowie/profile.md` exists and the current project is linked to flowie (indicated by a non-empty `flowie_profiles` list in `project_config.md`), read the profile silently.

Do not announce that you are reading the profile. Do not quote it back verbatim. Use it to inform the quality and character of your assistance without drawing attention to the mechanism.

If the profile does not exist or the project is not linked, proceed as normal — flowie is optional.

With the neuroflow mod active and the project linked, a digest of the profile is already in the system prompt (its identity, contact and wellbeing sections left out, capped in length); read `profile.md` itself when a task needs more than the digest.

## Using the profile in other phases

When assisting in any neuroflow phase, apply the profile as follows:

### In /ideation

- Frame suggestions around the user's known research domain and beliefs
- If a proposed idea conflicts with a stated stance, flag it explicitly rather than suppressing it
- Use the `ideas.md` file as a starting point — the user's cross-project hypotheses may be relevant

### In /paper

- Apply the user's documented writing style throughout — density, hedging patterns, register
- Do not override the user's voice with generic academic prose
- If a section sounds unlike the user, say so and ask whether to adjust

### In /data-analyze

- Apply the user's known methodological preferences — e.g. if they prefer Bayesian inference, frame statistical options Bayesian-first
- If a method conflicts with a documented stance, note the tension and ask before proceeding

### In /experiment

- Use the user's preferred paradigm and recording modality as defaults when not specified
- Do not assume — confirm — but use profile context to suggest sensible starting points

### In all phases

- Match the user's register and level of technical density in your responses
- If a stated belief or stance is relevant to the current decision, surface it: *"Your profile notes that you prefer preregistration before data collection — does that apply here?"*
- Never be sycophantic about it. Surface it once, do not repeat.

## 3-tier task model

Tasks in neuroflow exist at three levels with one file format and one board spec, both defined in `/tasks` (`commands/tasks.md`): `tasks/{column}/{slug}.md` with `status`, `owner`, `updated` and the other keys listed there.

| Level | Location | Who sees it | When to use |
|-------|----------|-------------|-------------|
| `flowie` | `~/.neuroflow/flowie/tasks/` | Owner only | Personal todos, private research tasks |
| `project` | `.neuroflow/tasks/` | All project collaborators | Sprint work, analysis steps, paper milestones |
| `hive` | `~/.neuroflow/hives/{org-repo}/tasks/` | Whole team | Shared deliverables, joint deadlines |

When a user runs `/flowie --tasks`, default to `flowie` level. If they pass `--level project` or `--level hive`, read/write from the corresponding location. Show `[level: flowie|project|hive]` at the bottom of every board display.

`~/.neuroflow/flowie/` is gitignored from project repos — each collaborator has their own private flowie. `.neuroflow/tasks/` is git-tracked and shared across the team.

## Write rules for ~/.neuroflow/flowie/

These rules apply whenever the `/flowie` command or any other command writes to `~/.neuroflow/flowie/`:

1. **Never overwrite without showing a diff first.** Before writing to `profile.md` or `ideas.md`, show the proposed changes as a diff and wait for explicit confirmation.
2. **Always read before writing.** Load the current file content before computing the new version.
3. **Do not truncate.** When updating a section, preserve all other sections exactly as they are.
4. **Log every write.** Every file write to `~/.neuroflow/flowie/` must be followed by a session log entry.
5. **Only documented writers.** Only `/flowie` writes `profile.md`, `ideas.md`, `sync.json` and `projects/` (including the phase sync `/phase` triggers). Other commands write only their own documented flowie paths: `/tasks` and `/meeting` at `--level flowie` (`tasks/`, `meetings/`), `/notes` (`notes/`, and raw ideas to `ideas-inbox.md` via `--idea`), and wiki ingests through `neuroflow:wiki` (`wiki/`). Every other phase command may read the profile but never writes here.
6. **No machine-local paths.** Never write absolute local paths (`C:/Users/…`, `/home/…`) into a flowie file — the repo syncs to every machine. Where each project lives on this machine is kept in `~/.neuroflow/local-projects.json`, outside the repo and never synced (written by `/flowie --link`).

## GitHub sync protocol

The flowie profile is mirrored to a private GitHub repository. The sync protocol is:

1. **Always pull before push.** `git -C ~/.neuroflow/flowie pull --rebase` before every push. If the rebase stops on a conflict, run `git -C ~/.neuroflow/flowie rebase --abort` at once — never leave the repo mid-rebase — and resolve it with the person (rule 3).
2. **Show what a pull brought in.** `/flowie --sync` summarises incoming changes before pushing; nothing pulled is ever silently overwritten.
3. **Handle merge conflicts explicitly.** If local and remote have diverged, show both versions side by side. Do not silently pick one. Ask the user to resolve each conflict.
<!-- nf-rule: GIT-NO-SECRETS -->
4. **Stage explicit paths only.** Commit exactly the files the operation changed (`git add -- {paths}`, `git commit -- {paths}`) — never `git add -A`, never `integrations.json` (it is listed in the repo's `.gitignore`).
5. **Record failures, don't swallow them.** A push or pull that fails for network or auth reasons never blocks the person: say so once per session, keep the local commit (git is the outbox — the next successful push sends everything in order), and do not retry in a loop. The flowie auto-sync hook (below) appends each failure to `~/.neuroflow/flowie-sync.log`; `/flowie --sync` reports the log and empties it once a pull and a push have both succeeded.
6. **Update `last_synced` only on success.** If the push fails (auth error, network issue), do not update the timestamp. Report the error clearly.
7. **Never push to any repo other than the one in `sync.json`.** Confirm the repo URL before any push operation.
8. **Respect `gh` CLI availability.** Use the following order for auth and fetch operations: (1) try `gh auth status` — if authenticated, use `gh` CLI; (2) if not, try `git clone --depth 1` directly (works when the user has standard git credentials configured); (3) if both fail, never ask for a token in chat: the person signs in with `gh auth login` (or stores a GitHub credential for git, e.g. with `git credential approve`) in their own terminal, then retry once. Do not attempt additional `gh` diagnostics between steps 1 and 2.

**Flowie auto-sync hook.** The plugin ships a `PostToolUse` hook for Edit/Write on files under `~/.neuroflow/flowie/`. It commits that one file, pulls with rebase (aborting at once on a conflict), then pushes. It skips `integrations.json`, gitignored files and anything while a rebase or merge is in progress, and it never blocks: each failure becomes one line `{UTC timestamp} {what failed}: {path}` (e.g. `pull failed`, `push failed`, `skipped (rebase or merge in progress)`) in `~/.neuroflow/flowie-sync.log` (machine-local, never synced). The hook is a convenience, not the protocol — commands still run their own Sync step (`/flowie` → Git operations pattern), so everything works with hooks disabled, and changes made through Bash (`git mv`, deletions) are committed only by that step.

## Privacy rules

- The profile is stored in a **private** GitHub repository. Never suggest making it public.
- Profile data must never appear in outputs intended for external readers — papers, reports, grant proposals, talk slides.
- When generating any external-facing document, treat profile data as context only — do not quote stances or beliefs in the output.
- If a project is being exported (via `/output`), `~/.neuroflow/flowie/` is excluded by default. Confirm explicitly before including it.

## Wellbeing tracking

The flowie repo contains a `wellbeing/` folder for daily self-assessments. The feature is opt-in (`collect: false` by default) and enabled either during `--init` or via `/flowie --assess`. Entries are pushed to the private flowie repo like every other flowie file; they are never shared with collaborators, the hive or any export.

**Self-reported only.** Wellbeing data is what the person types in `--assess` — nothing else. Never infer mood, stress, energy or wellbeing from messages, typing, timing or work patterns; never write an inferred value to `wellbeing/` or anywhere else; never mention scores outside `/flowie --assess` unless the person asks. Passive issue monitoring (neuroflow-core) logs problems with the plugin's behavior — never an assessment of the person.

**Structure:**
- `wellbeing/config.json` — `collect` flag, metric definitions (anxiety/energy/happiness 1–10), `prompt_on_sync` flag
- `wellbeing/YYYY-MM-DD.json` — one entry per day with integer scores and optional free-text notes

**When to prompt:** On any write operation (`--sync`, `--link`, `--tasks --add`, `--projects --add`), check if `collect: true` and today's entry is missing. If so, run `--assess` inline before proceeding. Do NOT prompt during read-only modes (`--view`, `--identify`, `--credentials`).

**Scale:** 1–10 with 5 as the neutral baseline. For anxiety: 10=very high anxiety. For energy and happiness: 10=very high.

**Enabling mid-session:** Running `/flowie --assess` when `collect: false` will offer to enable tracking before collecting the entry.

## Notes sync

After every `/notes` session, the command offers to copy the formatted note to `~/.neuroflow/flowie/notes/` (default: yes, controlled by `sync_to_flowie` in `.neuroflow/notes/config.json`). The flowie auto-sync hook commits and pushes it. The `notes/` folder in flowie acts as a cross-project note archive.

`/notes --idea "…"` appends raw ideas to `~/.neuroflow/flowie/ideas-inbox.md` (one timestamped line each). The inbox is not curated: moving an idea into `ideas.md` follows write rule 1 (show the diff, wait for confirmation).

## Personal wiki

The flowie repo also contains a `wiki/` folder — a Karpathy-style personal knowledge base maintained by the LLM. All wiki operations are handled by the `neuroflow:wiki` skill, which defines page formats, ingest/query/lint/add workflows, and neuroflow-specific integrations.

**When to surface the wiki:** wiki ingest offers and ambient wiki lookups are handled automatically by `neuroflow-core`'s `## Wiki ambient behavior` rules — crystallization detection fires at the end of every command, and pre-query lookup runs silently on domain questions. Do not duplicate those prompts here. The flowie-level wiki is a target for any crystallization that matches the **flowie** routing preconditions (personal insight, cross-project method, insight spanning multiple projects).

**Wiki structure (at a glance):**

```
~/.neuroflow/flowie/wiki/
├── index.md       ← catalog of all pages
├── log.md         ← append-only operation log
├── schema.md      ← LLM operating guide for this wiki
├── raw/           ← immutable source documents
└── pages/
    ├── concepts/  ← topic pages
    ├── entities/  ← people, tools, datasets
    ├── sources/   ← one page per ingested source
    ├── synthesis/ ← cross-source analysis
    └── methods/   ← protocols, pipelines, analysis methods
```

For full wiki behavior, always load `neuroflow:wiki` when handling `--wiki-*` modes.

## Slash command

When this skill is invoked directly (without `/flowie`), run the full `/flowie` workflow — show the mode menu and proceed from there. Mention `/neuroflow:flowie` at the end.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:wiki` — full wiki behavior for all `--wiki-*` modes
- `neuroflow:phase-output` — flowie directory is excluded from exports by default
