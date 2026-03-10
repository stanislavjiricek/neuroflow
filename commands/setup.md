---
name: setup
description: Interactive credential wizard for neuroflow MCP integrations. Checks PubMed and Miro credentials, prompts for missing values, and saves them to .neuroflow/integrations.json.
phase: utility
reads:
  - .neuroflow/integrations.json
writes:
  - .neuroflow/integrations.json
---

# /setup

Guide the user through connecting the neuroflow MCP integrations. This command can be run at any time — on first run, after skipping during `/start`, or to update existing credentials.

---

## Step 1 — Read current state

Check whether `.neuroflow/integrations.json` exists. If it does, read it. Note which credentials are already set.

Also check whether the environment variables `PUBMED_EMAIL` and `MIRO_ACCESS_TOKEN` are set in the current shell (you can tell by whether the MCP servers are responding). If they are already set via env vars, note that for the user.

Display a status table:

```
Integration   Status
───────────   ──────
PubMed        ✅ configured  (or ❌ not configured)
bioRxiv       ✅ no credentials needed
Miro          ✅ configured  (or ❌ not configured)
Context7      ✅ no credentials needed
```

---

## Step 2 — PubMed setup

**If PubMed is already configured:** ask "PubMed email is already set to `<email>`. Update it? (y/N)". If no, skip to Step 3.

**If PubMed is not configured:**

Tell the user:
> **PubMed** requires an email address so NCBI can contact you if there are issues with automated queries. Any valid email works — it does not need to match an NCBI account.

Ask: "Enter your email for PubMed (or press Enter to skip):"

- If the user enters a value:
  - Validate: must contain `@`. If invalid, say so and ask again (up to 3 attempts).
  - On valid input, store it.
- If the user presses Enter / types "skip" / types "s": skip PubMed and note it was skipped.

---

## Step 3 — Miro setup

**If Miro is already configured:** ask "Miro token is already set. Update it? (y/N)". If no, skip to Step 4.

**If Miro is not configured:**

Tell the user:
> **Miro** requires a personal access token. To get one:
> 1. Go to https://miro.com/app/settings/user-profile/apps
> 2. Click **Create new app** (or use an existing one)
> 3. Under **Token**, click **Create token** — copy the token shown
>
> The token starts with `eyJ…` and is long. Miro does not support OAuth from the terminal — you must paste a token you create in the browser.

Ask: "Paste your Miro access token (or press Enter to skip):"

- If the user enters a value:
  - Validate: must be non-empty and at least 20 characters. If the token starts with `eyJ`, treat that as a good sign (JWT format); otherwise accept any non-empty value of sufficient length.
  - On valid input, store it.
- If the user presses Enter / types "skip" / types "s": skip Miro and note it was skipped.

---

## Step 4 — Save and confirm

**If any credentials were entered:**

1. Create `.neuroflow/` if it does not exist.
2. Write `.neuroflow/integrations.json` with this structure (include only keys that were set):

```json
{
  "pubmed": {
    "PUBMED_EMAIL": "user@example.com"
  },
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJ..."
  }
}
```

3. If the file already existed, merge — only overwrite keys the user just set; leave others unchanged.

4. Tell the user:

> ✅ Credentials saved to `.neuroflow/integrations.json`.
>
> **Important:** This file is excluded from git (`.gitignore`) so your credentials are not committed. It is local to this machine.
>
> **To activate the MCP servers**, export the env vars in your shell before starting Claude Code:
> ```bash
> export PUBMED_EMAIL="user@example.com"
> export MIRO_ACCESS_TOKEN="eyJ..."
> ```
> Or add them to your shell profile (`~/.zshrc`, `~/.bashrc`) so they load automatically.

**If nothing was configured (all skipped):**

Tell the user: "No credentials saved. You can run `/neuroflow:setup` at any time to configure integrations."

---

## Step 5 — Suggest next step

- If the user came from `/start`, tell them to continue with the suggested phase command.
- Otherwise, suggest: "Run `/neuroflow:ideation` to start exploring literature, or any other command to continue your project."
