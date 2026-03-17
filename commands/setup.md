---
name: setup
description: Interactive credential wizard for neuroflow MCP integrations. Checks PubMed, Miro, and Google Workspace CLI credentials, prompts for missing values, and saves them to .neuroflow/integrations.json.
phase: utility
reads:
  - .neuroflow/integrations.json
writes:
  - .neuroflow/integrations.json
---

# /setup

Guide the user through connecting the neuroflow MCP integrations. This command can be run at any time — on first run, after skipping during `/neuroflow`, or to update existing credentials.

---

## Step 1 — Read current state

Check whether `.neuroflow/integrations.json` exists. If it does, read it. Note which credentials are already set.

Also check whether the environment variables `PUBMED_EMAIL`, `MIRO_ACCESS_TOKEN`, and `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` are set in the current shell. If they are already set via env vars, note that for the user.

Run `gws --version 2>/dev/null` (or `which gws`) to detect whether the Google Workspace CLI is installed.

Display a status table:

```
Integration              Status
──────────────────────   ──────
PubMed                   ✅ configured  (or ❌ not configured)
bioRxiv                  ✅ no credentials needed
Miro                     ✅ configured  (or ❌ not configured)
Context7                 ✅ no credentials needed
Google Workspace CLI     ✅ installed  (or ❌ not installed)
  └─ OAuth credentials   ✅ configured  (or ❌ not configured)
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

## Step 4 — Google Workspace CLI setup

This step covers the `gws` CLI — a single tool for Drive, Gmail, Calendar, Sheets, Docs, and more. It is optional but enables the Google Calendar and Gmail MCP integrations in neuroflow.

### 4a — Check if gws is installed

Run `gws --version 2>/dev/null` or `which gws`. If the command is found, skip to Step 4b.

**If not installed:**

Tell the user:
> **Google Workspace CLI (`gws`)** is not installed.
>
> **Prerequisites:** Node.js 18+ required. Run `node --version` to check — if missing, install from https://nodejs.org
>
> Install with:
> ```bash
> npm install -g @googleworkspace/cli
> ```
> Then run `/neuroflow:setup` again to configure credentials.

Ask: "Install `gws` now? (y/N)"
- If yes: run `npm install -g @googleworkspace/cli` and confirm success, then continue to 4b.
- If no: note it was skipped, move to Step 5.

### 4b — Check OAuth credentials

Run `which gcloud 2>/dev/null` to check if the `gcloud` CLI is present.

**If `gcloud` IS installed:** fully automated. Run:
```bash
gws auth setup --login
```
This creates the GCP project, enables APIs, creates an OAuth app, and opens the browser for login in one command. Skip the rest of this step.

**If `gcloud` is NOT installed** (the common case): `gws auth setup` exits with `"gcloud CLI not found"`. The workaround is a one-time manual step in the browser — after that, `gws auth login` opens the browser automatically on every re-auth.

Tell the user:
> **One-time setup required in Google Cloud Console.** `gws auth setup` needs `gcloud` (not installed). Do this once:
>
> **Part A — Create OAuth credentials:**
> 1. Opening https://console.cloud.google.com/apis/credentials in your browser now.
> 2. Create a project (or select an existing one)
> 3. Click **+ Create Credentials → OAuth client ID**
> 4. Application type: **Desktop app** → name it anything → **Create**
> 5. Click **Download JSON** → save the file to:
>    - **Windows:** `C:\Users\<your-name>\.config\gws\client_secret.json`
>    - **macOS/Linux:** `~/.config/gws/client_secret.json`
> 6. Come back here and press Enter — `gws auth login` will open your browser to complete sign-in (Google may show an "unverified app" warning — click Advanced → Continue).
>
> **Part B — Enable the APIs** (required — `gws auth setup` would have done this automatically):
> For each API you want to use, open its library URL and click **Enable**:
> - Calendar: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
> - Gmail: https://console.cloud.google.com/apis/library/gmail.googleapis.com
> - Drive: https://console.cloud.google.com/apis/library/drive.googleapis.com
> - Sheets: https://console.cloud.google.com/apis/library/sheets.googleapis.com
> - Docs: https://console.cloud.google.com/apis/library/docs.googleapis.com
> - Slides: https://console.cloud.google.com/apis/library/slides.googleapis.com
> - Tasks: https://console.cloud.google.com/apis/library/tasks.googleapis.com
>
> Append `?project=<your-project-id>` to each URL to go directly to the right project.
>
> **Tip:** Install `gcloud` to skip all of this in future projects: https://cloud.google.com/sdk/docs/install

Open the URL now: run `start https://console.cloud.google.com/apis/credentials` (Windows) or `open https://console.cloud.google.com/apis/credentials` (macOS/Linux).

Wait for the user to confirm they have downloaded `client_secret.json`, then run:
```bash
gws auth login
```
This opens the browser for OAuth consent automatically. On success, `gws auth status` should show the authenticated account.

**Alternative — env vars (no file download needed):** the user can paste the Client ID and Client Secret directly from the GCP Console instead of downloading the file:
> From the GCP Console OAuth credential page, copy the **Client ID** and **Client Secret** values and set:
> ```bash
> export GOOGLE_WORKSPACE_CLI_CLIENT_ID="<client-id>"
> export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="<client-secret>"
> ```
> Then run `gws auth login`.

**If credentials are already configured** (client_secret.json exists at the platform path, or `GOOGLE_WORKSPACE_CLI_CLIENT_ID` env var is set):
- Run `gws auth status 2>&1` to check. If authenticated, ask "Google Workspace is already authenticated. Re-authenticate? (y/N)". If no, skip to Step 5.

**If credentials are not configured:**
- Ask: "Which auth method? (1) I'll save client_secret.json  (2) Paste Client ID + Secret  (3) Skip"
- **Option 1:** open GCP Console URL, wait for confirmation, run `gws auth login` (opens browser).
- **Option 2:** ask for Client ID and Client Secret; store both; run `gws auth login` (opens browser).
- **Option 3:** note it was skipped.

---

## Step 5 — Save and confirm

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
  },
  "google_workspace": {
    "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE": "/home/user/.config/gws/client_secret.json",
    "GOOGLE_WORKSPACE_CLI_CLIENT_ID": "<optional — alternative to file>",
    "GOOGLE_WORKSPACE_CLI_CLIENT_SECRET": "<optional — alternative to file>"
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
> export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="$HOME/.config/gws/client_secret.json"
# or, if using env vars instead of file:
export GOOGLE_WORKSPACE_CLI_CLIENT_ID="<client-id>"
export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="<client-secret>"
> ```
> Or add them to your shell profile (`~/.zshrc`, `~/.bashrc`) so they load automatically.

**If nothing was configured (all skipped):**

Tell the user: "No credentials saved. You can run `/neuroflow:setup` at any time to configure integrations."

---

## Step 6 — Suggest next step

- If the user came from `/neuroflow`, tell them to continue with the suggested phase command.
- Otherwise, suggest: "Run `/neuroflow:ideation` to start exploring literature, or any other command to continue your project."
