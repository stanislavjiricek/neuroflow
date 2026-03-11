---
title: /git
---

# `/neuroflow:git`

**Context-aware git utility with smart shorthand aliases.**

`/git` reads the current repo state — branch, staged changes, commit history, remote sync status — and suggests or executes the most appropriate git action. Works in any repo, not only neuroflow projects.

---

## When to use it

- You want to commit, push, or pull with minimal typing
- You want a suggested commit message based on your changes
- You want to create a branch or open a pull request
- You're not sure whether to push or pull

---

## Shorthand aliases

| Invocation | What it does |
|---|---|
| `/git` | Read context and suggest the most appropriate next action |
| `/git p` | **Smart push/pull** — reads context to decide (see rules below) |
| `/git pl` | Pull from remote |
| `/git ps` | Push to remote |
| `/git a` | Stage all changes (`git add .`) |
| `/git c` | Commit staged changes with a suggested message |
| `/git ac` | Stage + commit |
| `/git acp` | Stage + commit + push |
| `/git b` | Branch — show current, list, or create a new one |
| `/git pr` | Open a pull request — push if needed, then generate PR title and body |

---

## Smart push/pull logic (`/git p`)

| Context | Action |
|---|---|
| Has unpushed local commits | Push |
| Local is behind remote and no unpushed commits | Pull |
| Both unpushed commits and behind remote | Warn user, ask whether to push first or pull and rebase |
| Nothing to push or pull | Tell user the branch is in sync |

---

## Commit message generation

When staging and committing, `/git` reads the diff and suggests a commit message in imperative mood that describes the actual change — not a generic placeholder. You can accept it, edit it, or provide your own.

---

## Pull request creation (`/git pr`)

Claude:

1. Checks if the current branch is pushed to remote — pushes first if needed
2. Reads the commit log since the base branch to understand what changed
3. Generates a pull request title (imperative mood, short) and body (what changed and why)
4. Runs `gh pr create` with the generated content
5. Returns the PR URL

Requires `gh` CLI to be installed and authenticated.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md` (if they exist) |
| Writes | `.neuroflow/sessions/YYYY-MM-DD.md` (if `.neuroflow/` exists) |

---

## Related commands

- [`/phase`](phase.md) — check or switch the active research phase before committing
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency before pushing
