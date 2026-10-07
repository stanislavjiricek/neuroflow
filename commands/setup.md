---
name: setup
description: Interactive setup wizard for neuroflow integrations. Checks Miro, Google Workspace CLI and custom LLM gateway settings, guides the missing ones without ever asking for a secret in chat, and saves non-secret settings to .neuroflow/integrations.json (per-project) or ~/.neuroflow/integrations.json (global, device-wide).
phase: utility
reads:
  - ~/.neuroflow/integrations.json
  - ~/.neuroflow/user.yaml
  - .neuroflow/integrations.json
  - ~/.neuroflow/flowie/sync.json
writes:
  - ~/.neuroflow/integrations.json
  - ~/.neuroflow/user.yaml
  - .neuroflow/integrations.json
  - ~/.neuroflow/flowie/integrations.json
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: light
---

# /setup

Guide the user through connecting the neuroflow integrations. This command can be run at any time — on first run, after skipping during `/neuroflow`, or to update existing settings.

**Never ask for a secret in chat.** Tokens, API keys and client secrets never pass through the conversation: the person puts them where they belong in their own terminal — Miro's token into Claude Code's MCP configuration, a gateway key into their launch setup, Google OAuth into `gws`. Never read a secret back or print one; `integrations.json` holds non-secret settings only.

---

## Step 0 — Detect platform and credential scope

### Platform detection

Detect the operating system at the start of the wizard. This affects paths and env var syntax shown to the user throughout all steps.

- **Unix (macOS / Linux):** home dir = `~`, shell profile = `~/.zshrc` or `~/.bashrc`, use `export VAR=value`
- **Windows:** home dir = `%USERPROFILE%` (e.g. `C:\Users\YourName`), use PowerShell `$env:VAR = "value"` or persistent via System settings

Global config path:
- Unix: `~/.neuroflow/integrations.json`
- Windows: `%USERPROFILE%\.neuroflow\integrations.json`

### Credential scope

Ask once at the start:
> "Save settings for **this project only** (`.neuroflow/integrations.json`) or **globally on this machine** (`~/.neuroflow/integrations.json`, shared by all projects)?"
>
> **Recommended: global** — so you don't repeat setup on every new project.

- Choices: **(1) Global (recommended)**  **(2) This project only**

Store the choice as `save_global` (boolean) — use it in Step 5 when writing settings.

If either file already exists, read both and merge (per-project overrides global).

---

## Step 1 — Read current state

Check whether `~/.neuroflow/integrations.json` (global) and `.neuroflow/integrations.json` (per-project) exist. Read **key names only** — never print values into the conversation — e.g. `python -c "import json,sys; d=json.load(open(sys.argv[1])); print({k: sorted(v) if isinstance(v, dict) else '-' for k, v in d.items()})" <file>`. Per-project keys override global. Note which settings are already present. If an older file still holds a secret (`miro.MIRO_ACCESS_TOKEN`, `custom_llm.api_key`, `google_workspace.GOOGLE_WORKSPACE_CLI_CLIENT_SECRET`), tell the user and offer to delete that key — secrets no longer live there.

Miro is connected when any tool whose name contains `miro` is available in this session (`claude mcp list` also shows server names and status). Never run `claude mcp get miro`: it prints the token.

Check whether `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` is set in the current shell, and run `gws --version 2>/dev/null` (Unix) or `where gws 2>nul` (Windows) to detect whether the Google Workspace CLI is installed.

Display a status table:

```
Integration              Status
──────────────────────   ──────
PubMed / bioRxiv         ✅ no credentials needed
Context7                 ✅ no credentials needed
Miro (optional)          ✅ connected  (or — not added)
Google Workspace CLI     ✅ installed  (or ❌ not installed)
  └─ OAuth credentials   ✅ configured  (or ❌ not configured)
Custom LLM gateway       ✅ configured (provider: my-gateway)  (or — not configured)
Zotero MCP (optional)    ✅ connected  (or — not set up)
```

**Zotero (optional):** if the user asks about Zotero (or `/ideation` sent them here), guide them to add a community Zotero MCP server — e.g. `zotero-mcp`: install per its README (typically `claude mcp add zotero -- uvx zotero-mcp` with the Zotero desktop app running for the local API; for the web API the server needs a `ZOTERO_API_KEY` and library ID, which the user adds with `-e` in their own terminal — never in this chat). Once the server's tools are visible, `/ideation` automatically offers library-first search and saving results into Zotero collections. No credentials are stored in `integrations.json` for this — the MCP server holds its own config.

---

## Step 2 — Miro (optional)

neuroflow does not start a Miro server itself: Miro's many tools take context in every session, and its token belongs to the user. The user adds Miro once, at user scope (all their projects).

**If Miro is already connected:** say so and skip to Step 3.

**Otherwise** ask whether they want Miro at all (mind maps, experiment diagrams, visual collaboration). If not, skip to Step 3.

If yes, tell the user:
> 1. Create a personal access token at https://miro.com/app/settings/user-profile/apps → **Create new app** (or open an existing one) → **Token** → **Create token**, and copy it.
> 2. In a **separate terminal** — not in this chat — run:
>    ```bash
>    claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<your-token> -- npx -y @k-jarzyna/mcp-miro
>    ```
>    On native Windows, if the server later fails to connect, use `-- cmd /c npx -y @k-jarzyna/mcp-miro` as the command part.
> 3. Restart Claude Code (or check `/mcp`); the Miro tools then appear in every project.
>
> Please don't paste the token here, and don't run the command with `!` inside Claude Code: `!` commands and their output are recorded in the conversation, so the token would enter it.

Never ask for the token, never read it back, and never store it in `integrations.json`. If the user pastes it anyway, do not repeat or store it; suggest revoking it in Miro and creating a new one.

---

## Step 3 — Google Workspace CLI setup

This step covers the `gws` CLI — a single tool for Drive, Gmail, Calendar, Sheets, Docs, and more. It is optional but enables the Google Calendar and Gmail MCP integrations in neuroflow.

### 3a — Check if gws is installed

Run `gws --version 2>/dev/null` or `which gws` (Unix) / `where gws 2>nul` (Windows). If the command is found, skip to Step 3b.

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
- If yes: run `npm install -g @googleworkspace/cli` and confirm success, then continue to 3b.
- If no: note it was skipped, move to Step 4.

### 3b — Check OAuth credentials

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

**Alternative — env vars (no file download needed):** the user sets the Client ID and Client Secret from the GCP Console as environment variables themselves — in their shell profile, not in this chat:
> From the GCP Console OAuth credential page, copy the **Client ID** and **Client Secret** values into your shell profile:
> ```bash
> export GOOGLE_WORKSPACE_CLI_CLIENT_ID="<client-id>"
> export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="<client-secret>"
> ```
> Open a new terminal, then run `gws auth login`.

**If credentials are already configured** (client_secret.json exists at the platform path, or `GOOGLE_WORKSPACE_CLI_CLIENT_ID` env var is set):
- Run `gws auth status 2>&1` to check. If authenticated, ask "Google Workspace is already authenticated. Re-authenticate? (y/N)". If no, skip to Step 4.

**If credentials are not configured:**
- Ask: "Which auth method? (1) I'll save client_secret.json  (2) I'll set Client ID + Secret as environment variables myself  (3) Skip"
- **Option 1:** open GCP Console URL, wait for confirmation, run `gws auth login` (opens browser).
- **Option 2:** show the two `export` lines with placeholders (PowerShell: `$env:…` or the User environment variables dialog); the user sets them outside the conversation; then run `gws auth login` (opens browser). Never ask for the values.
- **Option 3:** note it was skipped.

---

## Step 4 — Custom LLM gateway (optional)

This step is **optional**. If the user presses Enter or types "skip" / "s", skip to Step 5.

**Check existing configuration:**
If `custom_llm` already exists in `integrations.json`, ask:
> "A custom LLM gateway is already configured (provider: {provider}, model: {model}). Update it? (y/N)"
If no, skip to Step 5.

**If not configured (or user wants to update), ask:**
> "Do you want to run Claude Code through a custom LLM gateway — an Anthropic-compatible endpoint from your institution or another provider — instead of Anthropic's API? (y/N)"

If no / Enter, skip to Step 5.

Say once before collecting anything: with a gateway, every prompt, file the model reads and tool result goes to the gateway operator — the project's ethics approval and data agreements must allow that route.

**If yes, collect the following (no secrets):**

1. "A short name for the provider (e.g. my-gateway):"
2. "The base URL your provider documents for Anthropic-compatible clients (e.g. https://llm.example.org):"
3. "Preferred model name (or press Enter to choose later):" — help choose with the model-selection steps in the `neuroflow:setup` skill
4. "Legacy proxy only (providers with an OpenAI-compatible API and no Anthropic endpoint): proxy port, or Enter to skip:"

**Never ask for the API key.** Tell the user where it goes instead: a file only they can read inside the gateway's isolated config folder (e.g. `~/.claude-gateway/gateway-key`), or the OS credential store, read by the launch command — outside this conversation. For the launch command, model aliases, context window, rate limits and the legacy proxy, surface the `neuroflow:setup` skill and its guide `skills/setup/references/custom-gateway.md`.

**Save** the non-secret fields to the `integrations.json` of the scope chosen in Step 0 (global `~/.neuroflow/integrations.json` or per-project `.neuroflow/integrations.json`) under `custom_llm`:

```json
"custom_llm": {
  "provider": "my-gateway",
  "base_url": "https://llm.example.org",
  "model": "<model-id>"
}
```

(`proxy_port` is only included when the legacy proxy mode is used.)

- If flowie is linked (check `~/.neuroflow/flowie/sync.json` exists), offer to sync these non-secret settings to the flowie profile.
  <!-- nf-rule: EGRESS-CONFIRM -->
  A push to the flowie repository is outbound: ask *"Sync the gateway settings (no key) to your flowie profile on GitHub? (y/N)"* and act only on yes. Write `provider`, `base_url`, `model` and `proxy_port` to `~/.neuroflow/flowie/integrations.json`:

  ```json
  {
    "custom_llm": {
      "provider": "my-gateway",
      "base_url": "https://llm.example.org",
      "model": "<model-id>"
    }
  }
  ```

  Then commit and push:

  ```bash
  git -C ~/.neuroflow/flowie add integrations.json && git -C ~/.neuroflow/flowie commit -m "sync: custom_llm settings" -- integrations.json && git -C ~/.neuroflow/flowie push
  ```

  Report a failure instead of hiding it. On success tell the user: "Synced the gateway settings (no key) to your flowie profile."

---

## Step 5 — Save and confirm

**If any settings were entered:**

1. **Determine save location** based on `save_global` from Step 0:
   - **Global:** `~/.neuroflow/integrations.json` (Unix) or `%USERPROFILE%\.neuroflow\integrations.json` (Windows). Create `~/.neuroflow/` if it does not exist.
   - **Per-project:** `.neuroflow/integrations.json` — only when `.neuroflow/` exists; never create it from here.

2. Write the integrations file with this structure (include only keys that were set — non-secret settings only):

```json
{
  "google_workspace": {
    "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE": "/home/user/.config/gws/client_secret.json"
  },
  "custom_llm": {
    "provider": "my-gateway",
    "base_url": "https://llm.example.org",
    "model": "<model-id>",
    "proxy_port": 4001
  }
}
```

3. If the file already existed, merge — only overwrite keys the user just set; leave others unchanged.

4. Tell the user the save location and how to activate. Use the correct syntax for the detected platform:

**Unix (macOS / Linux):**

> ✅ Settings saved to `~/.neuroflow/integrations.json` (global) _or_ `.neuroflow/integrations.json` (per-project). The file holds no secrets and is never committed.
>
> - **Miro** (if you added it in Step 2) is active after you restart Claude Code.
> - **Google Workspace CLI:** if your `client_secret.json` is not at the default path, add its location to your shell profile (`~/.zshrc`, `~/.bashrc`):
>   ```bash
>   export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="$HOME/.config/gws/client_secret.json"
>   ```
> - **Custom LLM gateway:** start Claude Code with the launch command from the gateway guide (the key is read from your key file at launch).

**Windows (PowerShell):**

> ✅ Settings saved to `%USERPROFILE%\.neuroflow\integrations.json` (global) _or_ `.neuroflow\integrations.json` (per-project). The file holds no secrets and is never committed.
>
> - **Miro** (if you added it in Step 2) is active after you restart Claude Code.
> - **Google Workspace CLI:** if your `client_secret.json` is not at the default path, set its location:
>   ```powershell
>   $env:GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE = "$env:USERPROFILE\.config\gws\client_secret.json"
>   ```
>   For persistence, add it to your PowerShell profile (`notepad $PROFILE`) or set it as a User environment variable via Settings → System → Environment Variables.
> - **Custom LLM gateway:** start Claude Code with the PowerShell launch block from the gateway guide.

**If nothing was configured (all skipped):**

Tell the user: "No settings saved. You can run `/neuroflow:setup` at any time to configure integrations."

---

## Step 6 — Save user identity to global config

Ask: *"Would you like to save your GitHub username to your global neuroflow config so future projects can pre-fill it automatically? (Y/n)"*

If yes (or Enter), ask: *"What is your GitHub username?"* — then write or update `~/.neuroflow/user.yaml` (Unix) / `%USERPROFILE%\.neuroflow\user.yaml` (Windows):

```yaml
flowie_handle: {username}
flowie_repo: {username}/flowie
hives: []
```

If the file already exists, merge: only overwrite `flowie_handle` and `flowie_repo`; leave `hives` unchanged. Confirm: *"Saved `{username}` to your global neuroflow user config."*

If the user says no, skip silently.

---

## Step 7 — Session log and next step

**If `.neuroflow/` exists** (per the neuroflow-core lifecycle — never create it from here): append one milestone to `.neuroflow/sessions/YYYY-MM-DD.md`, e.g. `## HH:MM — [setup] Integrations updated: Miro added by user, gws skipped, custom LLM gateway (my-gateway) saved to global scope.` Never write credential values into the session log — names and statuses only.

Then suggest the next step:
- If the user came from `/neuroflow`, tell them to continue with the suggested phase command.
- Otherwise, suggest: "Run `/neuroflow:ideation` to start exploring literature, or any other command to continue your project."
