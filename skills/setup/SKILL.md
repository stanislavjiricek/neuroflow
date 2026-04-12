---
name: setup
description: Configure neuroflow integrations — Miro, Google Workspace, and custom LLM providers. Use when setting up credentials, checking integration status, or guiding a user through connecting external services. Also covers e-INFRA CZ connection for Czech academic researchers.
reads:
  - ~/.neuroflow/integrations.json
  - .neuroflow/integrations.json
  - skills/setup/references/einfra-cc.md
  - skills/setup/scripts/einfra/
writes:
  - ~/.neuroflow/integrations.json
  - .neuroflow/integrations.json
---

# neuroflow:setup

Agent-facing knowledge for all neuroflow integrations. Use this skill when a user asks about credentials, integration status, or setting up an external service — without necessarily running the full `/setup` wizard.

---

## Integrations overview

| Integration | Credential required | Key |
|---|---|---|
| PubMed / bioRxiv | ❌ No | — (handled by biorxiv MCP server) |
| Miro | ✅ Yes | `MIRO_ACCESS_TOKEN` |
| Context7 | ❌ No | — |
| Google Workspace CLI (`gws`) | ✅ Yes | OAuth via `gws auth login` |
| Custom LLM provider | ✅ Yes (API key) | `custom_llm.api_key` in integrations.json |

---

## Global vs project-level credentials

neuroflow supports two credential scopes:

| Scope | Location | When to use |
|---|---|---|
| **Global (device-wide)** | `~/.neuroflow/integrations.json` | Set once — applies to all projects on this machine |
| **Per-project** | `.neuroflow/integrations.json` | Overrides global for this project only |

**Resolution order:** per-project credentials take precedence over global. If a key is not found per-project, fall back to global.

**Platform paths for global config:**
- **macOS / Linux:** `~/.neuroflow/integrations.json`
- **Windows:** `%USERPROFILE%\.neuroflow\integrations.json` (e.g. `C:\Users\YourName\.neuroflow\integrations.json`)

When guiding a user, ask:
> "Save credentials for this project only, or globally on this machine (all projects)?"

Default recommendation: **global**, so they don't repeat setup on every new project.

---

## How to check integration status

1. Detect platform (`os.platform()` or check `$OSTYPE` / `$env:OS`).
2. Read global config at `~/.neuroflow/integrations.json` (or `%USERPROFILE%\.neuroflow\integrations.json` on Windows) if it exists.
3. Read per-project `.neuroflow/integrations.json` if it exists. Per-project keys override global keys.
4. Check whether the corresponding environment variables are set in the current shell (`MIRO_ACCESS_TOKEN`, etc.).
5. For `gws`: run `gws --version 2>/dev/null` or `which gws` (Unix) / `where gws` (Windows) to detect installation; run `gws auth status` to check OAuth.
6. For custom LLM: check `integrations.json` for a `custom_llm` key; if present, show `provider` and `base_url`.

Display a status table:

```
Integration              Status
──────────────────────   ──────
PubMed / bioRxiv         ✅ no credentials needed
Miro                     ✅ configured  (or ❌ not configured)
Context7                 ✅ no credentials needed
Google Workspace CLI     ✅ installed  (or ❌ not installed)
  └─ OAuth credentials   ✅ configured  (or ❌ not configured)
Custom LLM               ✅ configured (provider: einfra)  (or ❌ not configured)
```

---

## integrations.json schema

Full schema including all integrations:

```json
{
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJ..."
  },
  "google_workspace": {
    "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE": "/home/user/.config/gws/client_secret.json",
    "GOOGLE_WORKSPACE_CLI_CLIENT_ID": "<optional>",
    "GOOGLE_WORKSPACE_CLI_CLIENT_SECRET": "<optional>"
  },
  "custom_llm": {
    "provider": "einfra",
    "base_url": "https://llm.ai.e-infra.cz/v1",
    "api_key": "<YOUR_API_KEY>",
    "model": "kimi-k2.5",
    "proxy_mode": "custom",
    "proxy_port": 4001
  }
}
```

- `.neuroflow/integrations.json` is gitignored — credentials never leave the local machine.
- When merging: only overwrite keys the user just set; leave others unchanged.
- `api_key` fields are always local-only, even if other non-secret fields are synced to a flowie profile.

---

## Credential validation rules

| Integration | Validation |
|---|---|
| Miro | Non-empty, at least 20 characters; `eyJ` prefix is a good sign (JWT) |
| Google Workspace | File must exist at platform path, or env vars must be set |
| Custom LLM | API key: non-empty; base URL: must start with `http`; model: optional |

---

## Custom LLM provider support

The `/setup` Step 5 allows configuring any OpenAI-compatible API endpoint as a replacement for Anthropic's API in Claude Code.

### Model selection during setup

When setting up a custom LLM provider, always ask the user which model to use. Do not assume a default silently.

**Step 1 — try to fetch available models from the API:**

```bash
curl -s -H "Authorization: Bearer <API_KEY>" <BASE_URL>/models | jq '.[].id' 2>/dev/null
```

Or via Python:
```python
import httpx
r = httpx.get("<BASE_URL>/models", headers={"Authorization": "Bearer <API_KEY>"})
print([m["id"] for m in r.json().get("data", [])])
```

If this succeeds, present the model list to the user. If it fails (auth error, endpoint not supported), skip to Step 2.

**Step 2 — ask the user to pick:**

> I couldn't fetch the model list automatically. Please check the provider's documentation or dashboard for available model names, then tell me which one to use.
>
> For e-INFRA CZ, the current models are listed in `skills/setup/references/einfra-cc.md` — but the list changes, so verify at https://llm.ai.e-infra.cz if unsure.

**Step 3 — recommend based on use case:**

Once you have the model list (fetched or provided by user), recommend based on their project type:

| Use case | Recommend |
|---|---|
| Claude Code agentic workflows, MCP tools, neuroflow | Model with best tool-calling support (e.g. `kimi-k2.5` on e-INFRA) |
| General research, writing, analysis | Largest general-purpose model available |
| Reasoning / complex multi-step tasks | Thinking/reasoning model if available |
| Fast iteration, simple tasks | Smallest/fastest model |

Always state your recommendation and why, then confirm:
> I recommend `kimi-k2.5` for your setup — it has the best tool-calling performance on e-INFRA, which matters for Claude Code's agentic workflows. Use this? (Y / type a different model name)

Save the confirmed model as `BIG_MODEL` in the start script and as `model` in `integrations.json`.

---

**Recommended approach: custom Python proxy (`proxy.py`)**

The custom FastAPI proxy in `skills/setup/scripts/einfra/proxy.py` is the most reliable way to connect Claude Code to e-INFRA. It performs the full Anthropic↔OpenAI translation — streaming, multi-turn tool use, model name mapping — and has been specifically tested and fixed for the edge cases that arise with e-INFRA models.

```bash
# Terminal 1 — start proxy (Unix)
OPENAI_API_KEY=<key> OPENAI_BASE_URL=https://llm.ai.e-infra.cz/v1 \
BIG_MODEL=kimi-k2.5 SMALL_MODEL=kimi-k2.5 \
uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 0.0.0.0 --port 4001

# Terminal 2 — connect Claude Code
ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude
```

**Windows PowerShell:**
```powershell
# Terminal 1 — use the provided start_proxy.ps1
.\start_proxy.ps1

# Terminal 2
$env:ANTHROPIC_BASE_URL = "http://localhost:4001"
$env:ANTHROPIC_AUTH_TOKEN = "dummy"
claude
```

Note: on Windows, use `ANTHROPIC_AUTH_TOKEN` — more reliably picked up by Claude Code CLI than `ANTHROPIC_API_KEY`.

**⚠️ Why not LiteLLM?** LiteLLM was tested with e-INFRA and produced two blocking errors: (1) `Content block is not a text block` with kimi-k2.5 (thinking blocks passed through incorrectly), and (2) `No tool calls but found tool output` with deepseek-v3.2 (tool result pairing lost in multi-turn translation). Use `proxy.py` instead.

**⚠️ Known proxy.py fix — `Content block not found`:** `tool_block_started` must be a `dict` mapping `openai_tool_idx → assigned_block_index`, not a `set`. Block indices assigned once at creation, never recalculated. See `skills/setup/references/einfra-cc.md` for details.

**⚠️ Port conflicts on Windows (`[WinError 10048]`):** Use `netstat -ano | findstr :<port>` to find what holds the port. Kill with `cmd.exe /c "taskkill /F /PID <PID>"` (must use cmd.exe, not Git Bash). Use port 4001+, avoid 4000.

For full setup, available models, Windows workflows, and troubleshooting — read `skills/setup/references/einfra-cc.md`.

---

## Security note

- **Secrets stay local.** API keys and OAuth tokens are stored only in `integrations.json` (global or per-project), which is gitignored. Never write credentials to any other file.
- **Global config** (`~/.neuroflow/integrations.json`) is in the home directory — not inside any repo — so it can never be accidentally committed.
- **Per-project config** (`.neuroflow/integrations.json`) is gitignored via the project's `.gitignore`. Double-check this is in place before any `git push`.
- **Non-secret settings** (provider name, base URL, preferred model, proxy port) are safe to sync. If the user has a flowie profile linked (check `.neuroflow/flowie/sync.json`), non-secret `custom_llm` settings can be written to `.neuroflow/flowie/integrations.json` and pushed to the user's private GitHub repo for cross-machine sync. The `api_key` field is always excluded from this sync.

---

## Running the setup wizard

The full interactive wizard is `/neuroflow:setup`. It covers all integrations step by step. This skill provides agent-level knowledge so Claude can guide credential setup without running the wizard — for example, answering "how do I configure Miro?" or surfacing the right reference when a user mentions e-INFRA.
