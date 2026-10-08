---
name: doctor
description: Health check of the setup around a neuroflow project — Python, git, Claude Code version, whether the neuroflow mod is live, backups (unpushed commits, last commit, remote, and your flowie's sync state), network or cloud-synced locations, and whether the config and git files follow the current contracts.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .gitignore
  - .gitattributes
  - ~/.neuroflow/flowie/           # git state only: commits not pushed, uncommitted paths
  - ~/.neuroflow/flowie-sync.log
  - skills/neuroflow-core/scripts/doctor.py
writes: []
lifecycle: light
next:
  - migrate
  - sentinel
---

# /doctor

Checks the environment around the project, not the project memory itself (that is `/sentinel`). It changes nothing.

**With the neuroflow mod active**, the mod answers this command in code: its first lines say the mod is live, its
settings, the Claude Code version against the version the mod was tested on, and any mod feature that could not run.
If you see the prose answer below instead, **the mod is not live** in this session — say so in the report, and point
to the reasons in `docs/concepts/mods.md` → "When the mod is not running".

## Steps

1. Run the portable checks from the `neuroflow:neuroflow-core` skill's scripts folder:

   ```bash
   python <neuroflow-core skill base dir>/scripts/doctor.py --project <project root> --json
   ```

   Exit 0 = all good, 1 = warnings found, 2 = the script could not run (say why — usually no Python 3.10+).
2. Print one line per check, glyph first (`✔` ok, `·` info, `⚠` warning, `✖` failure), then the mod line:
   "⚠ neuroflow mod not live in this session" (this prose only runs when the mod did not answer).
3. For each warning, name the fix in one line: `/neuroflow:migrate` for config and git-file contracts and for a project
   on an older neuroflow version, `git push` or adding a remote for backups, `/neuroflow:flowie --sync` for unpushed or
   uncommitted flowie changes or logged flowie sync failures, moving the project to a local disk for network or synced
   folders, updating Claude Code for an old version.

The checks it runs:

| Check | Why it matters |
|---|---|
| Python 3.10+, git, Claude Code version | neuroflow's scripts and the mod need them |
| git repository, remote, unpushed commits, last commit age | project memory that exists on one disk only is one disk failure from lost |
| uncommitted changes under `.neuroflow/` | the same, for today's work |
| network share or cloud-synced folder | sync and shares corrupt or duplicate files written mid-sync |
| `project_config.md` frontmatter and `nf_schema` | the mod and the scripts read the current contract |
| the neuroflow version the project is on (`plugin_version`) against the installed one | after a plugin update the memory may still be in an older format; the warning is the version notice every command opens with (`neuroflow:neuroflow-core` → **Command lifecycle**, step 3) — `/neuroflow:migrate` |
| `.gitignore` local-only paths, `.gitattributes` union merge | keeps private files out of git and makes append-only logs merge cleanly |
| your flowie, if set up: commits in `~/.neuroflow/flowie` not pushed to its upstream, failures in `~/.neuroflow/flowie-sync.log` (count and first timestamp) | profile, task and wiki changes that never reached your private repo exist on this machine only — `/neuroflow:flowie --sync`; nothing is reported when flowie is not set up |
| your flowie, if set up: uncommitted changes in `~/.neuroflow/flowie` (a count and up to three paths, never file contents; `integrations.json` aside) | they exist on this machine only, and changes to tracked files stop every pull with rebase, so your flowie stops updating — `/neuroflow:flowie --sync` commits and pushes them |

This command writes nothing, so it adds no session line.
