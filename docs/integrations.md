---
title: Integrations
---

# Integrations

neuroflow bundles three MCP (Model Context Protocol) servers that Claude Code launches automatically via `npx`, each pinned to a tested version; none needs credentials. Miro and Zotero are optional servers you add yourself, and the [Google Workspace CLI](#google-workspace-cli) and a [custom LLM gateway](#custom-llm-gateways) are optional tools you set up in your own terminal.

---

## MCP servers

| Server | npm package | Requires credentials |
|---|---|---|
| **PubMed / bioRxiv** | `paper-search-mcp-nodejs` | ❌ None |
| **Context7** | `@upstash/context7-mcp` | ❌ None |
| **Sequential thinking** | `@modelcontextprotocol/server-sequential-thinking` | ❌ None |

All are started automatically by Claude Code — you do not need to run them manually.

**Optional — Miro:** added by you, at user scope — see [Miro](#miro) below.

**Optional — Zotero:** neuroflow does not bundle a Zotero server, but if you add a community one (e.g. `zotero-mcp` — `claude mcp add zotero -- uvx zotero-mcp`, with the Zotero desktop app running or a `ZOTERO_API_KEY` passed with `-e` in your own terminal), `/ideation` automatically switches to library-first literature search: your existing papers are recognized and skipped, and new findings go into a project collection only after you confirm that write. See `/setup` for guidance.

---

## PubMed / bioRxiv

The `paper-search-mcp-nodejs` server handles both PubMed and bioRxiv searches — no credentials required.

The [scholar agent](concepts/agents.md) uses it to search NCBI PubMed for peer-reviewed literature and bioRxiv for preprints.

## bioRxiv

The bioRxiv integration enables the [scholar agent](concepts/agents.md) to search preprints.

**No credentials needed.** Works automatically after installation.

!!! warning "Preprints are not peer-reviewed"
    The scholar agent marks all bioRxiv results with ⚠️ PREPRINT. Preprints have not been peer-reviewed and should be treated with appropriate caution.

!!! warning "bioRxiv API keyword-search limitation"
    The bioRxiv / medRxiv search tools only scan one page of recent preprints (default: the last 30 days) for the exact query phrase, so keyword searches find little there; the search protocol then falls back to CrossRef, Semantic Scholar and arXiv through the same server, with no setup needed. Downloads use open-access routes only; the server Sci-Hub tools are never used (and are blocked by the plugin PreToolUse hook).

---

## Miro

The Miro integration enables Claude to create and edit Miro boards — useful for mind maps, experiment diagrams, and visual collaboration during ideation. It is optional and not bundled: its many tools would take context in every session, and its token is yours, so you add it yourself, once, for all your projects.

### Getting a personal access token

1. Go to [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
2. Click **Create new app** (or select an existing one)
3. Under **Token**, click **Create token**
4. Copy the token

!!! note "No OAuth support"
    Miro OAuth browser login is not supported from a terminal subprocess. Use a personal access token instead.

### Setup

In a **separate terminal** — not in the Claude Code chat — run:
```bash
claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<your-token> -- npx -y @k-jarzyna/mcp-miro
```
On native Windows, if the server later fails to connect, use `-- cmd /c npx -y @k-jarzyna/mcp-miro` as the command part. Restart Claude Code (or check `/mcp`); the Miro tools then appear in every project. Claude Code keeps the token in its own user configuration on this machine.

!!! warning "Keep the token out of the chat"
    Never paste the token into a conversation, and don't run the command with the `!` prefix inside Claude Code — `!` commands and their output are recorded in the conversation. `/neuroflow:setup` walks you through the same steps.

---

## Context7

The Context7 integration provides Claude with up-to-date documentation for libraries like MNE, nilearn, scikit-learn, and PsychoPy — directly in context.

**No credentials needed.** Works automatically after installation.

This means when Claude writes an MNE preprocessing script, it can look up the current API instead of relying on training data that may be outdated.

---

## Google Workspace CLI

The Google Workspace CLI (`gws`) is one command-line tool for Drive, Gmail, Calendar, Sheets, Docs and more. It is optional: with it, Claude can reach your Google Workspace from the terminal. `/neuroflow:setup` (Step 3) checks whether it is installed and signed in and walks you through the steps below.

### Install

It needs Node.js 18 or later (`node --version`):

```bash
npm install -g @googleworkspace/cli
```

### Sign in

With the Google Cloud CLI (`gcloud`) installed, one command creates the Cloud project, enables the APIs, creates the OAuth client and opens the browser to sign in:

```bash
gws auth setup --login
```

Without `gcloud`, do this once in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Create a project (or pick one), then **Create Credentials → OAuth client ID**, application type **Desktop app**.
2. **Download JSON** and save the file as `~/.config/gws/client_secret.json` (on Windows `%USERPROFILE%\.config\gws\client_secret.json`). If you keep it elsewhere, set `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` to its path in your shell profile.
3. Enable the APIs you want to use in the project's API library: Calendar, Gmail, Drive, Sheets, Docs, Slides, Tasks.
4. Run `gws auth login`. It opens the browser for your consent; Google may warn that the app is unverified, which is expected for your own OAuth client (**Advanced → Continue**). `gws auth status` then shows the signed-in account.

Instead of the file, you can set `GOOGLE_WORKSPACE_CLI_CLIENT_ID` and `GOOGLE_WORKSPACE_CLI_CLIENT_SECRET` in your shell profile and run `gws auth login`. Either way the OAuth secret stays with `gws`: neuroflow never asks for it in the chat and never stores it.

---

## Custom LLM gateways

Claude Code can run against an **Anthropic-compatible gateway** instead of Anthropic's API — for example a gateway your institution or another provider runs for open models. Such a gateway speaks the Anthropic protocol, so Claude Code connects directly. **No proxy needed.** neuroflow's `/setup` (Step 4) records the non-secret settings; the launch itself happens in your terminal.

**Native connection (recommended)** — the values are placeholders; take yours from the provider:

```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-gateway" \
ANTHROPIC_BASE_URL="https://llm.example.org" \
ANTHROPIC_AUTH_TOKEN="$(cat "$HOME/.claude-gateway/gateway-key")" \
ANTHROPIC_MODEL="<main-model>" \
ANTHROPIC_DEFAULT_SONNET_MODEL="<main-model>" \
ANTHROPIC_DEFAULT_OPUS_MODEL="<main-model>" \
ANTHROPIC_DEFAULT_HAIKU_MODEL="<small-model>" \
ANTHROPIC_SMALL_FAST_MODEL="<small-model>" \
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1 \
claude
```

- The isolated `CLAUDE_CONFIG_DIR` lets this run **alongside** your normal subscription `claude` in another terminal — zero shared state.
- The API key stays in a file only you can read (or your OS credential store) and is read at launch — never pasted into a chat or saved by neuroflow.
- **Models:** gateway model lists change — list them live (`<base URL>/v1/models`); switch mid-session with `/model <id>`. Map the Sonnet/Opus slots to your main model and the Haiku slot to a small one.
- **Rate limits:** gateways often cap parallel requests per key — heavy parallel subagent fan-out can hit 429s.
- **Your data:** every prompt and file the model reads goes to the gateway operator; check that your ethics approval and data agreements allow that route.

For the full guide — Windows PowerShell launch, variable reference, context-window handling, and the legacy proxy for OpenAI-compatible-only providers — see the `neuroflow:setup-guide` skill → [`references/custom-gateway.md`](skills/setup-guide/references/custom-gateway.md).

---

## Settings storage

When you run `/neuroflow:setup`, non-secret settings are saved to `~/.neuroflow/integrations.json` (global, all projects on this machine) or `.neuroflow/integrations.json` (per-project override — takes precedence). The wizard asks which scope to use:

```json
{
  "custom_llm": {
    "provider": "my-gateway",
    "base_url": "https://llm.example.org",
    "model": "<model-id>"
  }
}
```

!!! warning "No secrets, never committed"
    neuroflow never asks for a token or key in the chat and stores none in `integrations.json`: Miro's token lives in Claude Code's own MCP configuration, a gateway key in your key file, Google OAuth in `gws`. The per-project `.neuroflow/integrations.json` is automatically added to `.gitignore` by neuroflow, and the global `~/.neuroflow/integrations.json` lives outside any repository. A copy in `~/.neuroflow/flowie/integrations.json` stays on this machine too: it is gitignored in your flowie repo and never committed, so on another machine you enter the settings again (or copy the file).

---

## Reminder behavior

neuroflow checks integrations at the point of use, not upfront:

| Trigger | Reminder |
|---|---|
| Mention Miro in any command | If no Miro tools are available → show how to add Miro (`/setup` Step 2) or skip |
| Mention a custom LLM gateway | If `custom_llm` missing → offer to run `/setup` Step 4 |

You can always re-run `/neuroflow:setup` to add or update credentials at any time.
