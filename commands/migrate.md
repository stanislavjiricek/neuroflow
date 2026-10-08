---
name: migrate
description: Bring neuroflow's memory up to the installed version after a plugin update — the project (project_config.md frontmatter, JSON Lines reasoning logs, merge-safe .gitattributes, local-only .gitignore lines, the static instruction block), your flowie and the team hive (task files in the current format, local-only files kept out of git). Shows the plan first and writes only after you agree.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/reasoning/
  - .claude/CLAUDE.md
  - .gitattributes
  - .gitignore
  - ~/.neuroflow/user.yaml
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/flowie/.gitignore
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - ~/.neuroflow/hives/{org-repo}/.gitignore
  - ~/.claude/CLAUDE.md                   # report only
  - .github/copilot-instructions.md       # report only
  - AGENTS.md                             # report only
writes:
  - .neuroflow/project_config.md
  - .neuroflow/reasoning/
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .claude/CLAUDE.md
  - .gitattributes
  - .gitignore
  - ~/.neuroflow/user.yaml                # personal fields, only after the person agrees
  - ~/.neuroflow/flowie/tasks/            # committed and pushed: the person's own repository
  - ~/.neuroflow/flowie/.gitignore
  - ~/.neuroflow/hives/{org-repo}/tasks/  # written, committed and pushed only after the person's yes
  - ~/.neuroflow/hives/{org-repo}/.gitignore
lifecycle: light
produces:
  - .neuroflow/project_config.md
next:
  - phase
  - git
---

# /migrate

Bring neuroflow's memory up to the version that is running, level by level: the project (`neuroflow:neuroflow-core` → **project_config.md — the config contract**, **Reasoning log**, **Merge safety**, **Sharing tiers**, **Project instruction block**), then your flowie and the team hive (task files as `/tasks` → **Task file format** defines them, local-only files kept out of git). Nothing is written until the person has seen the plan and agreed.

Read the `neuroflow:neuroflow-core` skill first: the script ships in its `scripts/` folder, and Claude Code shows the skill's base directory when it loads.

---

## When to run it

- **after a plugin update** — the main reason. Every command compares the version the project was last brought up to date to (`plugin_version`) with the running one and, when the project is behind, names this command in one line (`neuroflow:neuroflow-core` → **Command lifecycle**, the version notice); with the neuroflow mod, the band above the prompt shows the same line. Only this command (and the scaffold of a new project) writes `plugin_version`, so the line stays until the project is migrated
- `/neuroflow`, `/phase` or another command reported a legacy `project_config.md` dialect (no `nf_schema` frontmatter)
- reasoning logs are still JSON arrays (`reasoning/*.json`)
- `.claude/CLAUDE.md` holds an older neuroflow block that names a phase
- flowie or hive task files still sit flat in `tasks/` or carry `id` / `assignee` / `responsible` / `level` keys

---

## Step 1 — Dry run

```bash
python <neuroflow-core base dir>/scripts/migrate.py --root .
```

Use `python3` where `python` is not on the PATH. The script walks up to the project root, writes nothing, and prints the plan: a diff of `project_config.md` (with `plugin_version` raised to the running version when the project's is older or missing — never lowered: a newer one, recorded by a teammate's newer neuroflow, stays), the reasoning conversions, the `.gitattributes` / `.gitignore` lines to add, the instruction-block fix, the decisions it needs, personal fields, and report-only findings. Add `--json` when you need the plan as data.

| Exit code | Meaning | What to do |
|---|---|---|
| `0` | Already current, nothing to report | Say so and go to Step 5. |
| `1` | Findings | Continue with Step 2. |
| `2` | Refused or failed — `nf_schema` newer than this plugin knows, no project found, unreadable file, bad argument | Show the message and stop. A newer schema means: update the plugin — never edit the file by hand to get past it. No project here: say so in one line and go to Step 5 — the flowie and the hive need no project. |

**If Python is unavailable**, do the same conversion by hand, following the contract sections named above: show each change as an edit (Claude Code's own diff is the preview) and ask before each file.

---

## Step 2 — Show the plan and collect decisions

Show the plan in short form — the config diff as printed, then one line per other change. Then settle what the script cannot decide, each with `AskUserQuestion`:

1. **Needs a decision** — e.g. a phase value that is not a phase id (`active development`, `writing / review`). Offer the likeliest canonical phases (`neuroflow:neuroflow-core` → **Phase taxonomy**) as options; "Other" takes any phase id. Each answer becomes a `--set` argument: `--set active_phase=paper`, `--set recommended_phases=ideation,data,paper`.
2. **Personal fields** (`auto_issue_reporting`, researcher name, `writing_style`, `zotero`, notification or wellbeing settings) — they belong in `~/.neuroflow/user.yaml`, not in the shared project file. Ask: **Move them to my user.yaml** / **Leave them**. Moving never overwrites a value already in `user.yaml`; the plan says which values are kept.
3. **Apply?** — **Apply these changes** / **Cancel**. On Cancel nothing in the project is written: go on with Step 4 and Step 5.

---

## Step 3 — Apply

```bash
python <neuroflow-core base dir>/scripts/migrate.py --root . --apply [--move-personal] [--set key=value ...]
```

The script writes nothing while a decision is still open. It keeps every old reasoning array as `*.json.bak`, keeps the notes body of `project_config.md`, keeps CRLF files CRLF, and is idempotent. Run the dry run again to confirm: exit `0`, or exit `1` with only report-only items left.

---

## Step 4 — Report-only findings

The script edits only the project's own memory, git files and instruction block. It reports — never edits — neuroflow blocks in:

- `~/.claude/CLAUDE.md` — written there by older versions; it pushes one project's phase into every session on the machine
- `.github/copilot-instructions.md` and `AGENTS.md` — mirrors neuroflow no longer writes (it is a Claude Code plugin)

For each one, show the exact block (the script prints it) and ask with `AskUserQuestion` (**Remove the block** / **Keep it**). On yes, delete only that block — from `## neuroflow` to the next level-1 or level-2 heading, or the end of the file — and nothing else. Delete a mirror file only if the block was its only content and the person agrees.

---

## Step 5 — Your flowie and the team hive

The same plan-then-apply flow for the folders outside the project: your flowie (`~/.neuroflow/flowie/`) and each cached hive (`~/.neuroflow/hives/{org-repo}/`). Skip a folder that does not exist and say so in one line; skip the step when neither exists. A cached hive without a `.git/` folder is the read-only cache of copied files that `/hive --init` replaces with a clone (`neuroflow:phase-hive` → **Local hive cache**): skip it as well, and say so in one line that names `/hive --init` — the script reports such a folder the same way and never writes to it.

1. **Pull each level first**, so the plan is made against the current state. Only a level whose pull succeeded is in this run. A pull with rebase refuses to start while tracked files hold uncommitted changes, so before pulling a level that is a git repository, list what is not committed there:
   ```bash
   git -C ~/.neuroflow/flowie -c core.quotepath=off status --porcelain --untracked-files=all
   ```
   (the same with `~/.neuroflow/hives/{org-repo}` for a hive). Each line is a two-letter state and a path (a rename: `old -> new`, two paths). `core.quotepath=off` shows a name with accents or other non-ASCII letters as it is; a path with a space comes inside double quotes, which are not part of its name. When it lists anything, add `--autostash` to that level's pull below (`git -C ~/.neuroflow/flowie pull --rebase --autostash`): git sets the uncommitted changes aside for the pull and puts them back after it. Before that pull:
   - flowie — the person's own private repository: show the list and ask with `AskUserQuestion` (nothing to ask when `integrations.json` is all it lists — it is never committed):
     <!-- nf-rule: GIT-NO-SECRETS -->
     - **Sync these first** (recommended): commit exactly those paths, by path, as `/flowie --sync` does (`/flowie` → **Git operations pattern**): `git -C ~/.neuroflow/flowie add -- "{path}" …`, then `git -C ~/.neuroflow/flowie commit -m "sync: before migrate" -- "{path}" …` — never `git add -A`, never `integrations.json`. Push the commit (`git -C ~/.neuroflow/flowie push`) once the pull below went through.
     - **Leave them**: they stay uncommitted and out of the migration commit (5.3 asks first when a planned change would take one along).
   - hive — the team's shared repository, and the changes may be someone's unfinished work: never commit them unasked. Show them, leave them as they are, and say so.
   - flowie: `git -C ~/.neuroflow/flowie pull --rebase`. If it stops on a conflict, run `git -C ~/.neuroflow/flowie rebase --abort`, tell the person, point at `/flowie --sync`, and leave the flowie out of this run.
   - each hive clone: `git -C ~/.neuroflow/hives/{org-repo} pull --rebase`; on a conflict, `git -C ~/.neuroflow/hives/{org-repo} rebase --abort`, tell the person, and leave that hive out (`neuroflow:phase-hive` → **`--sync`**).
   - With `--autostash`, the `rebase --abort` of a conflict puts the set-aside changes back too. If instead git says that applying the autostash resulted in conflicts, the pull went through but could not put them back: the files `git status` marks `UU` now hold conflict markers, and the stash keeps the person's uncommitted version (`git stash list` shows `autostash`). Show those files, leave that level out, and resolve them with the person before anything else is written there.
   - A pull that fails for another reason (no network, no access): say so once and leave that level out too.
   - For every level left out, tell the person to run `/neuroflow:migrate` again once its pull works: once the project is up to date, the version notice no longer reminds them.
2. **Dry run** — name each level that pulled cleanly, and only those:
   ```bash
   python <neuroflow-core base dir>/scripts/migrate.py --flowie --hive {org-repo}
   ```
   `--flowie` only when the flowie pulled cleanly, and one `--hive {org-repo}` per hive that did; skip the dry run when no level is left. Never `--hives` here: it checks every cached hive, also one whose pull failed. The script plans task files written in a legacy form — flat in `tasks/`, or with `id` / `assignee` / `responsible` / `level` keys — into `tasks/{column}/{slug}.md` with the keys `/tasks` defines (**Task file format**, **Legacy files**): a slug `/tasks` accepts stays as it is, and when a name has to change, the `blocked_by` entries that name the task follow it. It adds `integrations.json` (flowie) or `sync.json` (hive) to that folder's `.gitignore`, and only reports such a file when git already tracks it. It also only reports a task file that is not UTF-8, one that names more than one person as its owner, and a `blocked_by` entry that could now mean two tasks. In a git repository it lists the files with uncommitted changes (`uncommitted` in `--json`) and marks each planned change to one of them (`local_changes`); unresolved conflicts block that level (`blocking`). Exit codes here: `0` — these levels are current: say so in one line and go to **At end**; `1` — findings: a level with planned changes goes on with 5.3, a level with only report-only items goes straight to 5.7, and a blocked level is left out like a failed pull, with its message shown; `2` — an unknown `--hive` folder or a failure: show the message and skip the rest of this step.
3. **Show the plan** per level in short form, one line per moved or rewritten file. A `blocked_by` entry the plan reports as possibly meaning two tasks is settled now, while the old name is still known: ask which task it means and keep the answer, writing nothing yet (when it means the task that keeps its name, the entry stays as it is). Files with uncommitted changes stay out of the migration commit, which takes only the paths it names (5.5). A planned change marked `local_changes` touches such a file, though: applying it carries those uncommitted changes into the migration commit — for a hive, to the whole team — and so does a `blocked_by` answer (5.4) or a fix (5.7) written into one. Name each such file in the plan and ask before including it, in the level's question below, whose options then read **Apply, local changes included** (for a hive, **Apply and push to the hive, local changes included**) / **Cancel**. Then ask per level with `AskUserQuestion`:
   - flowie: **Apply these changes** / **Cancel**.
   <!-- nf-rule: EGRESS-CONFIRM -->
   - hive: the change rewrites the team's shared board and goes to the shared hive repository, so applying it and pushing it are one decision, asked before anything is written. Show the plan, everything already waiting in that clone (`git -C ~/.neuroflow/hives/{org-repo} log --stat @{u}..HEAD` — it would leave with the same push), and tell the person that teammates on an older neuroflow should update the plugin before they use the migrated board. Ask: **Apply and push to the hive** / **Cancel**. On Cancel nothing is written to that hive.
4. **Apply:** the same command for the levels the person agreed to, with `--apply --json`. In a git repository the script moves tracked task files with `git mv`, so their history follows them, stages every path it changed and lists those paths per level in `commit_paths`. It never commits or pushes. Take the paths from that JSON, never from the human output: a path may contain spaces. Then write each `blocked_by` answer from 5.3 (the task's new slug) into its entry and stage that file too (`git -C {level folder} add -- "{path}"`): it joins the level's commit paths, since the script stages only what it changed itself.
5. **Commit by path** — exactly the `commit_paths` of each level plus the files staged in 5.4, each one quoted, never `git add -A`, so the uncommitted changes left in 5.1 stay as they are; skip a level whose list is empty (a commit without paths would take whatever else is staged there):
   ```bash
   git -C ~/.neuroflow/flowie commit -m "migrate: current task format" -- "{path}" "{path}" …
   ```
   For a hive, the same inside `~/.neuroflow/hives/{org-repo}`.
6. **Push:**
   - flowie — the person's own private repository, a sync target they set up (`neuroflow:neuroflow-core` → **Sharing tiers**): `git -C ~/.neuroflow/flowie pull --rebase && git -C ~/.neuroflow/flowie push`, with `--autostash` added to the pull when uncommitted changes were left there in 5.1. If the pull stops on a conflict, abort the rebase and leave the push for `/flowie --sync`.
   - hive — push what the person agreed to in 5.3, in the same turn, pulling with rebase first (`neuroflow:phase-hive` → **Pushing to the hive**, which also covers a protected branch), with `--autostash` added when the clone still holds uncommitted changes (5.1). If the pull stops on a conflict (abort the rebase) or the push fails, the commit is still in the clone and would leave with the next hive push: say so, and offer to undo it (`git -C ~/.neuroflow/hives/{org-repo} reset --keep HEAD~1`) so nothing waits there unasked.
7. **Report-only findings:** show the script's message for each. A tracked `integrations.json` stays the person's call: `git rm --cached` stops tracking it, older commits keep their copies. A tracked `sync.json` in a hive is the team's call. A file that is not UTF-8: offer to convert it (ask which encoding it was written in when that is unclear). A task that names several people: ask who owns it — the others can go into its notes — and never drop one unasked. Whatever is edited here is a change like the others — for a hive, edit nothing before the person's yes to apply and push it. Then run the dry run and `--apply --json` again, commit that level's `commit_paths` plus every file you edited yourself, by path, and push as in 5.6.

---

## At end

- When something was written, append `## HH:MM — [migrate] {what changed, per level}` to `.neuroflow/sessions/YYYY-MM-DD.md` if `.neuroflow/` exists — e.g. `## 10:12 — [migrate] project to nf_schema 1 and neuroflow 0.2.22; flowie: 3 task files in the current format`.
- Add a line to `reasoning/general.jsonl` for each decision the person made in Step 2 (for example the phase chosen for a legacy value).
- Suggest committing the project's migration on its own (`/neuroflow:git`), so collaborators see one clean change. Collaborators on an older neuroflow should update the plugin before they write to `.neuroflow/` again.
- Close with `Next: /neuroflow:phase`.
