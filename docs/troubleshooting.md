---
title: Troubleshooting
---

# Troubleshooting

Common issues and how to resolve them.

---

## Installation issues

### `/neuroflow:neuroflow` is not recognized

**Cause:** neuroflow is not installed, or the installation did not complete.

**Fix:**

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

Restart Claude Code after installing.

---

### MCP servers fail to start

**Symptoms:** Literature search fails, Miro commands don't work, or you see MCP-related errors.

**Cause:** Node.js is not installed, or `npx` is not on your PATH.

**Fix:**

```bash
# Check if Node.js is installed
node --version

# Check if npx is available
npx --version
```

If not installed, install Node.js from [nodejs.org](https://nodejs.org).

---

## Literature search issues

### Search returns no results

**Cause:** Query too specific, or NCBI rate limiting.

**Fix:**

- Try a broader or different query term
- Wait a few minutes if you've been searching repeatedly
- The scholar agent will automatically try synonyms — let it run

---

## Project memory issues

### `.neuroflow/` was not created

**Cause:** `/neuroflow` was interrupted, or the scaffold refused — it never creates project memory in your home directory or inside another project.

**Fix:** Run `/neuroflow:neuroflow` again from the project folder and complete the setup interview. It resumes a half-finished setup and never overwrites files that already exist.

### Project context is wrong or stale

**Cause:** `project_config.md` is out of date, or Claude is not reading it.

**Fix:**

1. Run `/neuroflow:sentinel` to detect and fix inconsistencies
2. Check that `.claude/CLAUDE.md` contains the neuroflow block
3. Check your global `~/.claude/CLAUDE.md`: older neuroflow versions wrote a neuroflow block naming an active phase there, which injects that phase into every Claude Code session on your machine. Run `/neuroflow:neuroflow` — it shows the block and offers to remove it
4. Run `/neuroflow:neuroflow` to refresh the status

### neuroflow says the project uses an older format

**Cause:** `project_config.md` was written by an older neuroflow version (no `nf_schema` frontmatter), or decision logs are still `reasoning/*.json` arrays.

**Fix:** Run `/neuroflow:migrate`. It shows the full plan first and writes only after you agree.

### `/migrate` refuses: "nf_schema newer than this script knows"

**Cause:** A collaborator with a newer neuroflow version already converted the project.

**Fix:** Update the plugin (`claude plugin update neuroflow@neuroflow`, or `/plugin` in a session). Do not edit the file by hand to get past the check.

### I started Claude in a subfolder

Commands walk up from the working directory to the first folder with `.neuroflow/project_config.md`, stopping at the repository root. `/neuroflow` never creates a second `.neuroflow/` inside an existing project.

### Claude does not remember the project

**Cause:** `.claude/CLAUDE.md` is missing or does not reference `project_config.md`.

**Fix:** Run `/neuroflow:sentinel` — it will check for this and auto-fix by appending the neuroflow block.

---

## Phase and command issues

### The wrong phase is active

**Fix:**

```
/neuroflow:phase
```

Then pick the correct phase from the menu (arrow keys and Enter, or a click).

### The personality mode changed when I did not ask for it

Only an explicit prefix switches modes: `mode: critic` or `--mode critic` at the start of a message. Words in ordinary text — "critical period", "be careful with ICA" — never do. Your standing default lives in `~/.neuroflow/user.yaml` (`default_mode`); a team default can sit in `project_config.md`.

### Too many permission prompts for neuroflow's own logs

`/neuroflow` offers, once during setup, to allow its bookkeeping writes — session logs, decision logs and `flow.md` indexes — with three narrow rules in `.claude/settings.json`:

```json
"Edit(.neuroflow/sessions/**)", "Edit(.neuroflow/reasoning/**)", "Edit(.neuroflow/**/flow.md)"
```

Add them to `permissions.allow` yourself if you skipped the offer. Avoid a blanket `.neuroflow/**` rule — it would also cover credentials and confidential reviews.

### A command wrote to the wrong folder

**Cause:** Output paths in `project_config.md` are incorrect or missing.

**Fix:** Run `/neuroflow:sentinel` to audit `flow.md` files, then manually update the `## Output paths` table in `project_config.md` if needed.

---

## Miro issues

### Miro commands don't work

**Cause:** Miro has not been added to Claude Code (neuroflow does not bundle it), or its token has expired.

**Fix:**

1. Create a new token at [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
2. In a separate terminal — not in the Claude Code chat — add the server (to replace an expired token, first run `claude mcp remove --scope user miro`):
   ```bash
   claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<your-token> -- npx -y @k-jarzyna/mcp-miro
   ```
3. Restart Claude Code (or check `/mcp`). `/neuroflow:setup` shows the same steps; it never asks for the token.

---

## Sentinel issues

### Sentinel reports `plugin_version` mismatch

This is normal after a plugin update. `plugin_version` in `project_config.md` records the neuroflow version the project was last brought up to date to, so it stays behind until you migrate. Run `/neuroflow:migrate` after every update: it records the new version when it brings the project, your flowie and the team hive to the current format ([Upgrading](upgrading.md)). Never set the version by hand, and Sentinel does not change it either: that would silence the update notice while the formats stay old. A `plugin_version` newer than your plugin means a teammate on a newer neuroflow migrated the project: update your plugin. To see what changed between versions, read the [changelog](changelog.md).

### Sentinel finds skill-named subfolders in `.neuroflow/`

**Cause:** A skill incorrectly created its own subfolder instead of writing to the phase subfolder.

**Fix:** Sentinel will offer to move any `.md` files to the correct phase subfolder and delete the skill-named folder. Accept the auto-fix.

---

## Getting help

- [Open an issue](https://github.com/stanislavjiricek/neuroflow/issues) on GitHub
- Check the [README](https://github.com/stanislavjiricek/neuroflow) for the latest information
