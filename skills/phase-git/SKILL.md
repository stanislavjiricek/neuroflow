---
name: phase-git
description: Phase guidance for /git — context-aware git shorthand rules, smart push/pull logic, commit message generation, branch management, and PR creation workflow.
---

# phase-git

Guides the `/git` command to read repository state accurately and apply context-aware rules before executing any git action.

## Core principle

**Never act blindly.** Always read repo state first. The value of `/git` is that it understands context — so every alias resolves to the right action given the current branch, staged files, commit history, and remote sync status.

## Reading repo state

Always run all four checks before acting:

```bash
git status --short                                        # staged and unstaged changes
git log --oneline -5                                      # recent commits
git branch --show-current                                 # current branch
git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null  # ahead/behind remote
```

Parse the output to determine:

| Signal | Meaning |
|---|---|
| `M ` (staged modified) or `A ` (staged add) in `git status` | Has staged changes |
| ` M` or `??` in `git status` | Has unstaged or untracked changes |
| Right count > 0 from `rev-list` | Has unpushed commits |
| Left count > 0 from `rev-list` | Is behind remote |
| Branch is `main` or `master` | Warn before any write operation |
| `fatal:` or `no upstream` from `rev-list` | No upstream tracking branch set — skip push/pull and inform the user to run `git push --set-upstream origin <branch>` first |

## Smart push/pull logic (`/git p`)

| Condition | Action |
|---|---|
| Unpushed commits AND not behind remote | Push |
| Behind remote AND no unpushed commits | Pull |
| Unpushed commits AND behind remote | Warn — ask user: push first or pull & rebase? |
| Neither ahead nor behind | Report: "Branch is in sync with remote." |

## Commit message generation

When generating a commit message (`/git c`, `/git ac`, `/git acp`):

1. Run `git diff --cached --stat` to see which files changed and how many lines.
2. Run `git diff --cached` (first 200 lines is enough) to read actual changes.
3. Generate a message following the Conventional Commits format:
   - `feat:` for new functionality
   - `fix:` for bug fixes
   - `docs:` for documentation only changes
   - `refactor:` for refactoring without feature/fix
   - `chore:` for build, config, or tooling changes
4. Keep the subject line under 72 characters.
5. Show the proposed message to the user and ask: "Use this message, or edit it?"

## Branch operations (`/git b`)

Present this menu:
1. Show current branch + list all local branches
2. Create a new branch (ask for name, then `git checkout -b <name>`)
3. Switch to an existing branch (`git checkout <name>`)
4. Delete a local branch (warn if not merged)

Branch naming guidance to offer if creating a new branch:
- `feat/<short-description>` for new features
- `fix/<short-description>` for bug fixes
- `docs/<short-description>` for documentation
- `chore/<short-description>` for maintenance

## PR creation (`/git pr`)

1. Push branch if there are unpushed commits.
2. Derive PR title from branch name:
   - Strip prefix type if present (`feat/`, `fix/`, etc.)
   - Replace hyphens/underscores with spaces
   - Capitalise first letter
   - Re-add the prefix as a Conventional Commits type: `feat: <title>`
3. Generate PR body:
   - Run `git log main..HEAD --oneline` (or `master..HEAD`) to list commits
   - Group into a short summary paragraph + bullet list of commits
4. Check for `gh` CLI availability (`which gh`):
   - If available: run `gh pr create --title "..." --body "..."`
   - If not: display title + body for manual copy-paste with a link hint to GitHub's PR page

## Safety rules

- **On main/master:** before any `add`, `commit`, or `push`, show a yellow warning:
  > "⚠️ You are on the `main` branch. Did you mean to work on a feature branch?"
  Ask before proceeding.
- **Detached HEAD:** refuse to commit. Say: "You're in detached HEAD state. Check out a branch first: `git checkout -b <name>`"
- **Merge conflicts present** (`UU` or `AA` in `git status`): surface the conflicted files and say:
  > "Merge conflicts detected in: [files]. Resolve those before committing."
- **No remote:** skip push/pull; inform the user: "No remote configured. Add one with `git remote add origin <url>`."
- **Uncommitted changes before pull:** warn and offer `git stash` before pulling.

## Tone

Be brief and direct. This is a utility command — the user wants fast feedback and fast execution. Use short status lines, not paragraphs. Only explain when something is ambiguous or risky.
