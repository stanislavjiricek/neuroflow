---
name: phase-flowie
description: Phase guidance for the neuroflow /flowie command. Covers how to read and use the flowie profile for personalization, write rules for .neuroflow/.flowie/, GitHub sync protocol, and profile-aware assistance across all phases.
---

# phase-flowie

The `/flowie` command manages the user's personal identity layer — a private GitHub repository containing their research profile. This skill defines how Claude should read, update, and apply that profile across all neuroflow phases.

## What the flowie profile contains

The flowie profile lives in `.neuroflow/.flowie/` and consists of three files:

| File | Contents |
|---|---|
| `profile.md` | Research identity: name, domain, methodological preferences, writing style, stances, key beliefs |
| `ideas.md` | Ongoing ideas and hypotheses that span multiple projects |
| `sync.json` | GitHub repo URL, last sync timestamp, list of linked projects |

The profile is private by design. It lives in a private GitHub repository and is never included in project exports or any output intended for external readers.

## Reading the profile

At the start of any command session, if `.neuroflow/.flowie/profile.md` exists and the current project is linked to flowie (indicated by a `flowie_profile` field in `project_config.md`), read the profile silently.

Do not announce that you are reading the profile. Do not quote it back verbatim. Use it to inform the quality and character of your assistance without drawing attention to the mechanism.

If the profile does not exist or the project is not linked, proceed as normal — flowie is optional.

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

## Write rules for .neuroflow/.flowie/

These rules apply whenever the `/flowie` command or any other command writes to `.neuroflow/.flowie/`:

1. **Never overwrite without showing a diff first.** Before writing to `profile.md` or `ideas.md`, show the proposed changes as a diff and wait for explicit confirmation.
2. **Always read before writing.** Load the current file content before computing the new version.
3. **Do not truncate.** When updating a section, preserve all other sections exactly as they are.
4. **Log every write.** Every file write to `.neuroflow/.flowie/` must be followed by a session log entry.
5. **Never write to .flowie/ from a non-flowie command.** Other phase commands may read the profile, but only `/flowie` may write to `.neuroflow/.flowie/`.

## GitHub sync protocol

The flowie profile is mirrored to a private GitHub repository. The sync protocol is:

1. **Always pull before push.** Never push local changes without first checking for remote updates.
2. **Show the diff before applying.** When a pull brings in changes, show what changed and ask for confirmation before applying.
3. **Handle merge conflicts explicitly.** If local and remote have diverged, show both versions side by side. Do not silently pick one. Ask the user to resolve each conflict.
4. **Update `last_synced` only on success.** If the push fails (auth error, network issue), do not update the timestamp. Report the error clearly.
5. **Never push to any repo other than the one in `sync.json`.** Confirm the repo URL before any push operation.
6. **Respect `gh` CLI availability.** Prefer `gh` CLI for auth and repo operations. Fall back to raw git + PAT if `gh` is not installed.

## Privacy rules

- The profile is stored in a **private** GitHub repository. Never suggest making it public.
- Profile data must never appear in outputs intended for external readers — papers, reports, grant proposals, talk slides.
- When generating any external-facing document, treat profile data as context only — do not quote stances or beliefs in the output.
- If a project is being exported (via `/export`), `.neuroflow/.flowie/` is excluded by default. Confirm explicitly before including it.

## Slash command

When this skill is invoked directly (without `/flowie`), run the full `/flowie` workflow — show the mode menu and proceed from there. Mention `/neuroflow:flowie` at the end.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:phase-output` — flowie directory is excluded from exports by default
