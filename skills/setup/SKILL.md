---
name: setup
description: Configure neuroflow integrations — Miro, Google Workspace, and custom LLM gateways. Use when setting up credentials, checking integration status, or guiding a user through connecting external services, including running Claude Code against an Anthropic-compatible gateway.
reads:
  - ~/.neuroflow/integrations.json
  - .neuroflow/integrations.json
  - skills/setup/references/custom-gateway.md
  - skills/setup/scripts/gateway/
writes:
  - ~/.neuroflow/integrations.json
  - .neuroflow/integrations.json
---

# neuroflow:setup

Agent-facing knowledge for all neuroflow integrations. Use this skill when a user asks about credentials, integration status, or setting up an external service — without necessarily running the full `/setup` wizard.

**Secrets never pass through the conversation.** Never ask for a token, API key or client secret in chat, never read one back, never print one. Tokens go where the person puts them, outside the conversation: Miro's into Claude Code's own MCP configuration (added by the person in a separate terminal), a gateway key into the person's launch setup, Google OAuth into `gws`.

---

## Integrations overview

| Integration | Credential | Where it lives |
|---|---|---|
| PubMed / bioRxiv | ❌ None | — (bundled biorxiv MCP server) |
| Context7 | ❌ None | — (bundled) |
| Miro (optional) | ✅ Personal access token | Claude Code's user-scope MCP config — the person runs `claude mcp add` in their own terminal |
| Google Workspace CLI (`gws`) | ✅ OAuth | `gws auth login` |
| Custom LLM gateway (optional) | ✅ API key | The person's launch setup (key file or OS credential store) — never `integrations.json` |

---

## Global vs project-level settings

neuroflow supports two scopes for its (non-secret) integration settings:

| Scope | Location | When to use |
|---|---|---|
| **Global (device-wide)** | `~/.neuroflow/integrations.json` | Set once, applies to all projects on this machine |
| **Global user identity** | `~/.neuroflow/user.yaml` | GitHub username + known hives — pre-fills `/neuroflow` setup across projects |
| **Per-project** | `.neuroflow/integrations.json` | Overrides global settings for this project only |

**Resolution order:** per-project settings take precedence over global. If a key is not found per-project, fall back to global.

**Platform paths for global config:**
- **macOS / Linux:** `~/.neuroflow/integrations.json` and `~/.neuroflow/user.yaml`
- **Windows:** `%USERPROFILE%\.neuroflow\integrations.json` and `%USERPROFILE%\.neuroflow\user.yaml`

**`user.yaml` schema:**
```yaml
flowie_handle: {github-username}
flowie_repo: {github-username}/flowie
hives:
  - org/repo   # one entry per team hive the user is a member of
```
Written by `/setup` Step 6. Read by `/neuroflow` Step 1b to pre-fill the GitHub username without asking again.

When guiding a user, ask:
> "Save these settings for this project only, or globally on this machine (all projects)?"

Default recommendation: **global**, so they don't repeat setup on every new project.

---

## How to check integration status

1. Detect platform (`os.platform()` or check `$OSTYPE` / `$env:OS`).
2. Read global `~/.neuroflow/integrations.json` (or `%USERPROFILE%\.neuroflow\integrations.json` on Windows) and per-project `.neuroflow/integrations.json` if present — **key names only**, never values, e.g. `python -c "import json,sys; d=json.load(open(sys.argv[1])); print({k: sorted(v) if isinstance(v, dict) else '-' for k, v in d.items()})" <file>`. Per-project keys override global keys. An older file may still hold a secret (`miro.MIRO_ACCESS_TOKEN`, `custom_llm.api_key`, `google_workspace.GOOGLE_WORKSPACE_CLI_CLIENT_SECRET`): tell the person and offer to remove that key.
3. **Miro:** connected if any tool whose name contains `miro` is available in this session. `claude mcp list` also shows server names and status. Never run `claude mcp get miro` — it prints the token.
4. **gws:** run `gws --version 2>/dev/null` or `which gws` (Unix) / `where gws` (Windows) to detect installation; run `gws auth status` to check OAuth.
5. **Custom LLM gateway:** a `custom_llm` key in `integrations.json` — show `provider` and `base_url`. The session itself runs through a gateway when `ANTHROPIC_BASE_URL` is set (check with `[ -n "$ANTHROPIC_BASE_URL" ] && echo gateway`).

Display a status table:

```
Integration              Status
──────────────────────   ──────
PubMed / bioRxiv         ✅ no credentials needed
Context7                 ✅ no credentials needed
Miro                     ✅ connected  (or — not added)
Google Workspace CLI     ✅ installed  (or ❌ not installed)
  └─ OAuth credentials   ✅ configured  (or ❌ not configured)
Custom LLM gateway       ✅ configured (provider: my-gateway)  (or — not configured)
```

---

## integrations.json schema

`/setup` writes only non-secret settings:

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

- `proxy_port` appears only with the legacy proxy.
- Both files stay local: the global one lives outside any repository, the per-project one is gitignored (neuroflow-core → Sharing tiers, local tier).
- When merging: only overwrite keys the user just set; leave others unchanged.

---

## Validation rules

| Integration | Validation |
|---|---|
| Miro | Done by Claude Code when the server connects — neuroflow never sees the token |
| Google Workspace | `client_secret.json` exists at the platform path, or the person set the client ID/secret variables in their own shell |
| Custom LLM gateway | Base URL starts with `https://` (`http://localhost` only for a local proxy); model optional |

---

## Miro (optional, added by the person)

neuroflow does not start a Miro server itself — its many tools take context in every session, and the token belongs to the person. To add Miro once for all projects, the person creates a personal access token (https://miro.com/app/settings/user-profile/apps → **Create new app** → **Token** → **Create token**) and runs, **in a separate terminal — not in the chat**:

```bash
claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<token> -- npx -y @k-jarzyna/mcp-miro
```

On native Windows, if the server later fails to connect, use `-- cmd /c npx -y @k-jarzyna/mcp-miro` as the command part. After a restart of Claude Code (or a check in `/mcp`) the Miro tools are available everywhere. Do not suggest the `!` prefix for this command: bash-mode commands and their output are recorded in the conversation, so the token would enter it.

---

## Custom LLM gateway support

`/setup` Step 4 records an Anthropic-compatible gateway — an endpoint, typically from an institution or another provider, that Claude Code talks to instead of Anthropic's API. Full guide: `skills/setup/references/custom-gateway.md` (native connection, isolated config folder, model aliases, context window, rate limits, key storage, legacy proxy).

Say once, before configuring: with a gateway, every prompt, file the model reads and tool result goes to the gateway operator — the project's ethics approval and data agreements must allow that route.

### Model selection during setup

Always ask which model to use. Do not assume a default silently.

**Step 1 — list the models without handling the key.** If this session already runs through the gateway, the shell has the variables: `curl -s -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" "$ANTHROPIC_BASE_URL/v1/models"` (use `$ANTHROPIC_BASE_URL/models` when the base URL already ends in `/v1`). The key never appears in the conversation. Otherwise ask the person to list the models in their own terminal (the command is in the guide) or to check the provider's documentation, and tell you the names.

**Step 2 — recommend by use case:**

| Use case | Recommend |
|---|---|
| Claude Code agentic workflows, MCP tools, neuroflow | The model with the best tool-calling support (many gateways offer an alias for agentic or coding work) |
| General research, writing, analysis | Largest general-purpose model available |
| Reasoning / complex multi-step tasks | Thinking/reasoning model if available |
| Fast iteration, simple tasks | Smallest/fastest model |

Always state your recommendation and why, then confirm:
> I recommend `<model-id>` — it is the gateway's model for tool-calling workloads, which matters for Claude Code's agentic workflows. Use this? (Y / type a different model name)

Save the confirmed model as `model` in `integrations.json`.

### Native connection (no proxy)

Claude Code connects directly with per-process environment variables. An isolated `CLAUDE_CONFIG_DIR` lets the gateway session and a normal subscription `claude` run at the same time with no shared state:

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

Key points (details and the PowerShell version in the guide):
- Map the Sonnet/Opus slots to the chosen gateway model so no request goes out with a `claude-*` ID; route background tasks to a small model.
- Model lists change — list them live; `/model <id>` switches mid-session.
- Gateways often cap parallel requests per key — avoid heavy parallel subagent fan-out.
- For a context window smaller than Claude Code assumes, set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (~75% of the real window).
- On Windows, `ANTHROPIC_AUTH_TOKEN` is picked up more reliably than `ANTHROPIC_API_KEY`.
- The key stays in a file only the person can read (or the OS credential store), read at launch.

**Legacy proxy (`scripts/gateway/`):** only for providers with an OpenAI-compatible API and no Anthropic endpoint (`proxy.py`, `start_proxy.sh`, `start_proxy.ps1`), or for a gateway that rejects `claude-*` model names (`proxy.mjs`). Setup and Windows port troubleshooting are in the guide's legacy appendix.

---

## Security note

- **No secrets in chat or in neuroflow files.** `/setup` never asks for a token, key or client secret. `integrations.json` (global or per-project) holds non-secret settings only and stays local (gitignored).
- **Global config** (`~/.neuroflow/integrations.json`) is in the home directory — not inside any repository.
- **Per-project config** (`.neuroflow/integrations.json`) is gitignored through the project's `.gitignore` (the scaffold adds it). Double-check this is in place before any `git push`.
- **Non-secret settings** (provider name, base URL, preferred model, proxy port) may be synced to the user's flowie profile (`~/.neuroflow/flowie/integrations.json`, private GitHub repo) for cross-machine use — a push, so only after the person confirms.

---

## Running the setup wizard

The full interactive wizard is `/neuroflow:setup`. It covers all integrations step by step. This skill provides agent-level knowledge so Claude can guide setup without running the wizard — for example, answering "how do I connect Miro?" or surfacing the gateway guide when a user asks to run Claude Code through an institutional or other LLM gateway.
