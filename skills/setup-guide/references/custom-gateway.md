# Custom LLM gateway — Claude Code on an Anthropic-compatible endpoint

Some institutions and providers run an LLM gateway that speaks the Anthropic Messages API — for example a research-network or on-premise service that hosts open models. Claude Code can use such a gateway directly: point it at the gateway with environment variables at launch. No proxy, no translation layer.

This guide is provider-neutral. `my-gateway`, `https://llm.example.org`, `<main-model>` and `<small-model>` are placeholders — take the real values from your provider's documentation.

---

## Before you start

- **Base URL** — the gateway's root URL for Anthropic-compatible clients. Claude Code appends the API paths itself (`/v1/messages`, and `/v1/models` for model discovery), so the base URL usually has no `/v1` suffix; follow your provider's documentation if it says otherwise.
- **API key** — from your provider's account page. It is a credential: keep it out of chats, repositories and shared files (see **Storing the key**).
- **Model names** — the gateway's own model IDs. They change over time; list them live (see **Models**).
- **Your data** — with a gateway, every prompt, every file the model reads and every tool result goes to the gateway operator instead of Anthropic. Check that your ethics approval and data agreements allow that route for the data the project touches.

---

## Native connection (recommended)

Launch Claude Code with per-process environment variables. Nothing global changes, and your normal `claude` keeps working in other terminals.

**macOS / Linux:**
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

**Windows PowerShell** (the settings last for this window only — open a new window for your normal `claude`):
```powershell
$env:CLAUDE_CONFIG_DIR = "$env:USERPROFILE\.claude-gateway"
$env:ANTHROPIC_BASE_URL = "https://llm.example.org"
$env:ANTHROPIC_AUTH_TOKEN = (Get-Content "$env:USERPROFILE\.claude-gateway\gateway-key" -Raw).Trim()
$env:ANTHROPIC_MODEL = "<main-model>"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "<main-model>"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "<main-model>"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "<small-model>"
$env:ANTHROPIC_SMALL_FAST_MODEL = "<small-model>"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
claude
```

### What each variable does

| Variable | Why |
|---|---|
| `ANTHROPIC_BASE_URL` | The gateway endpoint |
| `ANTHROPIC_AUTH_TOKEN` | Your gateway key, sent as a bearer token. It takes precedence over a subscription login, so this process talks only to the gateway. On Windows it is picked up more reliably than `ANTHROPIC_API_KEY` |
| `ANTHROPIC_MODEL` | The gateway model for the main conversation |
| `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL` | Map Claude Code's model slots to a gateway model, so no request goes out with a `claude-*` ID the gateway does not know |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` (older builds: `ANTHROPIC_SMALL_FAST_MODEL`) | Route background and light tasks to a small, fast gateway model |
| `CLAUDE_CONFIG_DIR` | An isolated config, credential and history folder: the gateway session and a normal subscription `claude` run side by side with no shared state |
| `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` | Gateway models appear in the `/model` picker inside the session |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Set it only when the model's real context window is smaller than Claude Code assumes — about 75% of the real window — so auto-compaction starts in time |

Inside the session, `/model <id>` switches to any gateway model.

### Storing the key

Never paste the key into a Claude Code conversation, and never put it in a repository, `integrations.json` or a flowie profile. Keep it in a file only you can read inside the isolated config folder — for example `~/.claude-gateway/gateway-key` (`chmod 600` on macOS/Linux) — or in your operating system's credential store, and let the launch command read it, as above. A small launcher script that lists the models, offers a picker, sets the variables and starts `claude` is the comfortable long-term setup.

---

## Models

Gateway model lists change — fetch them live instead of trusting a static table:

```bash
curl -s -H "Authorization: Bearer $(cat "$HOME/.claude-gateway/gateway-key")" https://llm.example.org/v1/models
```

Inside a session that already runs through the gateway, the shell has the variables, so the key never needs to be typed: `curl -s -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" "$ANTHROPIC_BASE_URL/v1/models"`.

| Use case | Choose |
|---|---|
| Claude Code agentic work, MCP tools, neuroflow | The model with the best tool-calling support — many gateways offer a dedicated alias for agentic or coding workloads |
| General research, writing, analysis | The largest general-purpose model |
| Reasoning, complex multi-step tasks | A thinking/reasoning model, if offered |
| Background and light tasks (`ANTHROPIC_DEFAULT_HAIKU_MODEL`) | The smallest, fastest model |

Leave out non-chat entries (embedding, reranking, speech models) when listing, and check whether a model accepts images if you work with figures.

### Context window

Claude Code assumes a large context window. If your gateway reports a model's real limit (some expose it through a model-info endpoint) and it is smaller, set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` to about 75% of it.

### Rate limits

Gateways often cap parallel requests per key. Interactive use — the main model plus background tasks — needs two or three at a time; many parallel subagents can exceed a cap and get `429` responses. Claude Code retries automatically, but expect slowdowns and prefer sequential work (neuroflow's `scholar` agent searches sequentially for this reason).

---

## What neuroflow stores

`/neuroflow:setup` records only non-secret settings, in the chosen scope's `integrations.json` (global `~/.neuroflow/integrations.json` or per-project `.neuroflow/integrations.json`, both local-only):

```json
"custom_llm": {
  "provider": "my-gateway",
  "base_url": "https://llm.example.org",
  "model": "<main-model>"
}
```

- There is no `api_key` field: the key lives only where your launch command reads it. An older file that still has one — remove that key.
- With flowie linked, the non-secret settings can also be copied to `~/.neuroflow/flowie/integrations.json` (for `/flowie --credentials`). That file is gitignored in the flowie repo and never committed: the settings stay on this machine.
- `proxy_port` appears only with the legacy proxy below.

---

## Legacy appendix — proxy for OpenAI-compatible-only providers

Only needed when your provider exposes an OpenAI-compatible API (`/v1/chat/completions`) and **no** Anthropic-compatible endpoint. The FastAPI proxy `skills/setup-guide/scripts/gateway/proxy.py` translates Anthropic ↔ OpenAI formats, including streaming, multi-turn tool use and thinking blocks. It exists because generic translation layers failed on two cases with some models: thinking blocks (`Content block is not a text block`) and multi-turn tool pairing (`No tool calls but found tool output`).

**Terminal 1 — start the proxy** (it listens on this computer only):
```bash
OPENAI_API_KEY="$(cat "$HOME/.claude-gateway/gateway-key")" \
OPENAI_BASE_URL=https://llm.example.org/v1 \
BIG_MODEL=<main-model> SMALL_MODEL=<small-model> \
uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 127.0.0.1 --port 4001
```
or run `start_proxy.sh` / `start_proxy.ps1` from the same folder; both read the key and settings from environment variables.

**Terminal 2 — connect Claude Code:**
```bash
ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude
```

`proxy.mjs` (Node, no dependencies) is the smaller alternative for a gateway that speaks the Anthropic protocol but rejects Claude Code's `claude-*` model names when the `ANTHROPIC_DEFAULT_*_MODEL` mapping is not enough: it rewrites the model name in each request and restores it in the response.

Proxy troubleshooting on Windows: a port in use → `netstat -ano | findstr :4001`, stop the process with `taskkill /F /PID <PID>`; `[WinError 10048]` right after a stop is a TIME_WAIT leftover — pick another port instead of waiting; ports from 4001 up are usually free. `API Error: Content block not found` was a proxy bug, fixed by assigning tool block indices once, when each block starts.

---

## Quick reference

| Goal | How |
|---|---|
| Connect Claude Code (native) | Set the variables above, run `claude` |
| Run alongside subscription Claude | Isolated `CLAUDE_CONFIG_DIR` — both work at the same time |
| List live models | `GET <base URL>/v1/models` with the key as bearer token |
| Switch model mid-session | `/model <id>` |
| Background/light tasks | A small model via `ANTHROPIC_DEFAULT_HAIKU_MODEL` |
| Smaller context window | `CLAUDE_CODE_AUTO_COMPACT_WINDOW` ≈ 75% of the real window |
| Parallel request cap | Avoid heavy parallel subagent fan-out |
