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

### PubMed search fails

**Cause:** `PUBMED_EMAIL` is not configured.

**Fix:**

```
/neuroflow:setup
```

Or manually:

```bash
export PUBMED_EMAIL="you@example.com"
```

Then restart Claude Code.

### Search returns no results

**Cause:** Query too specific, or NCBI rate limiting.

**Fix:**

- Try a broader or different query term
- Wait a few minutes if you've been searching repeatedly
- The scholar agent will automatically try synonyms — let it run

---

## Project memory issues

### `.neuroflow/` was not created

**Cause:** `/neuroflow` was interrupted, or you declined to create it.

**Fix:** Run `/neuroflow:neuroflow` again and complete the setup interview.

### Project context is wrong or stale

**Cause:** `project_config.md` is out of date, or Claude is not reading it.

**Fix:**

1. Run `/neuroflow:sentinel` to detect and fix inconsistencies
2. Check that `.claude/CLAUDE.md` contains the neuroflow block
3. Run `/neuroflow:neuroflow` to refresh the status

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

Then select the correct phase.

### A command wrote to the wrong folder

**Cause:** Output paths in `project_config.md` are incorrect or missing.

**Fix:** Run `/neuroflow:sentinel` to audit `flow.md` files, then manually update the `## Output paths` table in `project_config.md` if needed.

---

## Miro issues

### Miro commands don't work

**Cause:** `MIRO_ACCESS_TOKEN` is not configured, or the token has expired.

**Fix:**

1. Run `/neuroflow:setup` and enter a fresh token
2. Create a new token at [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
3. Export the token: `export MIRO_ACCESS_TOKEN="eyJ..."`

---

## Sentinel issues

### Sentinel reports `plugin_version` mismatch

This is normal after a plugin update. Sentinel will auto-fix this by updating `plugin_version` in `project_config.md`.

### Sentinel finds skill-named subfolders in `.neuroflow/`

**Cause:** A skill incorrectly created its own subfolder instead of writing to the phase subfolder.

**Fix:** Sentinel will offer to move any `.md` files to the correct phase subfolder and delete the skill-named folder. Accept the auto-fix.

---

## Getting help

- [Open an issue](https://github.com/stanislavjiricek/neuroflow/issues) on GitHub
- Check the [README](https://github.com/stanislavjiricek/neuroflow) for the latest information
