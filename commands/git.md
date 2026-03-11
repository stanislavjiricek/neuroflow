---
name: git
description: Context-aware git utility — reads the current repo state and suggests or executes the most appropriate git action. Supports shorthand aliases (p, pl, ps, a, c, ac, acp, b, pr) so you can commit, push, pull, branch, or open a PR with minimal typing.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /git

Read the `neuroflow:phase-git` skill first. Then read `project_config.md` and `flow.md` if they exist (they may not — `/git` works in any repo, not only neuroflow projects).

## What this command does

A context-aware git utility that reads the current repo state — branch name, staged/unstaged changes, commit history, remote sync status — and suggests or executes the most appropriate git action. Designed to minimize typing with sensible shorthand aliases.

---

## Shorthand aliases

| Invocation | Resolved action |
|---|---|
| `/git` | Read context and suggest the most appropriate next action |
| `/git p` | **Smart push/pull** — context decides (see rules below) |
| `/git pl` | Pull from remote |
| `/git ps` | Push to remote |
| `/git a` | Stage all changes (`git add .`) |
| `/git c` | Commit staged changes with a suggested message |
| `/git ac` | Stage + commit |
| `/git acp` | Stage + commit + push |
| `/git b` | Branch — show current branch, list branches, or create a new one |
| `/git pr` | Open a pull request — push if needed, then generate PR title and body |

---

## Steps

### 1 — Read repo state

Before taking any action, run the following to understand context:

```bash
git status --short
git log --oneline -5
git branch --show-current
git remote -v
git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null || echo "no upstream"
```

Extract from this:
- **Branch**: current branch name
- **On main/master**: boolean — is this `main` or `master`?
- **Has uncommitted changes**: boolean — any modified or untracked files
- **Has staged changes**: boolean — anything in the staging area
- **Unpushed commits**: number of local commits ahead of remote
- **Behind remote**: number of commits the local branch is behind the remote

### 2 — Apply alias rules

**`/git p` — smart push/pull:**

| Context | Action |
|---|---|
| Has unpushed local commits | → push |
| Local is behind remote AND no unpushed commits | → pull |
| Both unpushed commits AND behind remote | → warn user, ask whether to push first or pull and rebase |
| Nothing to push or pull | → tell the user the branch is in sync |

**`/git pl` — pull:**
Always pull from remote. Warn if there are uncommitted changes first and ask whether to stash.

**`/git ps` — push:**
Push to remote. If no upstream is set, run `git push --set-upstream origin <branch>`.

**`/git a` — add:**
Run `git add .` and confirm what was staged.

**`/git c` — commit:**
1. Show what is staged.
2. Suggest a concise commit message based on the diff (use `git diff --cached --stat` and `git diff --cached` to understand changes).
3. Confirm with the user or let them edit the message.
4. Run `git commit -m "<message>"`.

**`/git ac` — add + commit:**
Run `git add .` then follow the commit flow above.

**`/git acp` — add + commit + push:**
Run `git add .`, commit (with suggested message), then push.

**`/git b` — branch:**
1. Show current branch.
2. List all local branches (`git branch`).
3. Ask: "Create a new branch, switch to an existing one, or just checking?"
4. Execute based on response.

**`/git pr` — pull request:**
1. Push the current branch if there are unpushed commits.
2. Generate a PR title from the branch name (e.g. `feat/eeg-preprocessing` → "feat: eeg preprocessing").
3. Generate a PR body summarising commits since the branch diverged from main/master (`git log main..HEAD --oneline`).
4. Show the generated title + body and ask the user to confirm or edit.
5. If GitHub CLI (`gh`) is available, run `gh pr create --title "..." --body "..."`.
6. If not, display the title and body and prompt the user to open the PR manually.

### 3 — `/git` with no arguments — suggest mode

Read context and output a short status summary:

```
Branch: feature/my-analysis
Changes: 3 files modified, 1 untracked
Commits ahead of origin: 2
Commits behind origin: 0

Suggested action: /git ps  (push your 2 unpushed commits)
```

Then offer the shorthand aliases table and ask what the user wants to do.

---

## Context rules

- **On `main` or `master`**: before staging or committing, warn the user they are on the default branch and ask if they meant to be on a feature branch.
- **No remote configured**: skip push/pull steps and tell the user.
- **Detached HEAD**: warn the user and refuse to commit until they check out a branch.
- **Merge conflict markers detected** (`git status` shows "both modified"): surface the conflicted files and guide the user to resolve before continuing.

---

## At end

- If `.neuroflow/` exists in the working directory, append a one-line entry to `.neuroflow/sessions/YYYY-MM-DD.md`: timestamp + what git action was taken.
- Do **not** write to any phase subfolder.
- Do **not** log a reasoning entry unless the user made a significant branching or merge decision.
