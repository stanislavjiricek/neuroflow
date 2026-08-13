# e-INFRA CZ LLM — Claude Code Integration

> **Country-specific:** This guide is for **Czech academic researchers only**. Access requires Metacentrum / e-INFRA CZ membership. See https://metavo.metacentrum.cz for eligibility.

---

## What is e-INFRA CZ

e-INFRA CZ is the Czech national research e-infrastructure providing free LLM API access to the academic community. The LLM gateway at `https://llm.ai.e-infra.cz` speaks the **Anthropic protocol natively** (it also exposes an OpenAI-compatible API at `/v1`).

**This changes everything about the setup:** Claude Code connects directly — **no proxy, no translation layer**. The old Python proxy workflow is kept below as a legacy appendix only.

Get an API key at https://chat.ai.e-infra.cz → Settings → Account → API keys.

---

## Recommended approach — native direct connection

Launch Claude Code with per-process environment variables. Nothing global changes, and your normal Anthropic-subscription `claude` keeps working in other terminals.

**Unix:**
```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-meta" \
ANTHROPIC_BASE_URL="https://llm.ai.e-infra.cz/v1" \
ANTHROPIC_AUTH_TOKEN="<YOUR_API_KEY>" \
ANTHROPIC_MODEL="agentic" \
ANTHROPIC_SMALL_FAST_MODEL="mini" \
ANTHROPIC_DEFAULT_HAIKU_MODEL="mini" \
ANTHROPIC_DEFAULT_SONNET_MODEL="agentic" \
ANTHROPIC_DEFAULT_OPUS_MODEL="agentic" \
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1 \
claude
```

**Windows PowerShell:**
```powershell
$env:CLAUDE_CONFIG_DIR = "$env:USERPROFILE\.claude-meta"
$env:ANTHROPIC_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:ANTHROPIC_AUTH_TOKEN = "<YOUR_API_KEY>"
$env:ANTHROPIC_MODEL = "agentic"
$env:ANTHROPIC_SMALL_FAST_MODEL = "mini"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "mini"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "agentic"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "agentic"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
claude
```

### What each variable does

| Variable | Why |
|---|---|
| `ANTHROPIC_BASE_URL` | The gateway API endpoint: `https://llm.ai.e-infra.cz/v1` |
| `ANTHROPIC_AUTH_TOKEN` | Your e-INFRA key. Takes precedence over subscription OAuth — this process can only talk to the gateway |
| `ANTHROPIC_MODEL` | The gateway model to use (see live list below) |
| `ANTHROPIC_SMALL_FAST_MODEL` + `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Route Claude Code's background/light tasks to the gateway's small `mini` model |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` + `ANTHROPIC_DEFAULT_OPUS_MODEL` | Map the Anthropic-named picker slots to your gateway model, so no request ever goes out with a `claude-*` id the gateway doesn't know |
| `CLAUDE_CONFIG_DIR` | Isolated config/credentials/history — lets subscription `claude` and gateway Claude Code run **concurrently with zero shared state** |
| `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` | Gateway models appear in the `/model` picker inside the session |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Set only when the model's real context window is **below** Claude Code's 200k assumption (e.g. to ~75% of the real window) so auto-compaction triggers in time |

Inside the session, `/model <id>` switches to any gateway model.

A small launcher script that wraps this — fetches the live model list, shows a picker, sets the env block, and `exec`s `claude` — is the comfortable long-term setup. Store the API key in a file under the isolated config dir with `chmod 600`, never in a repo.

### Models

The gateway's model list **changes over time — always fetch it live** rather than trusting any static table:

```bash
curl -s -H "Authorization: Bearer <YOUR_API_KEY>" https://llm.ai.e-infra.cz/v1/models
```

As of August 2026 the list includes `agentic`, `coder`, `thinker`, `mini`, `kimi-k3`, `qwen3.5-122b`, `glm-5`, `deepseek`, `mistral-medium-3.5`, `gemma4`. Guidance:

- **Agentic/tool use (Claude Code, neuroflow):** `agentic` is the purpose-built alias; `coder` for coding-heavy sessions.
- **Vision-capable:** `agentic`, `coder`, `qwen3.5-122b`, `mistral-medium-3.5`, `gemma4`. Text-only: `glm-5`, `deepseek`, `thinker`.
- **Background tasks:** `mini`.
- Filter out non-chat entries (`embed*`, `rerank*`, `whisper*`, …) when listing.

Real context window per model is available at `/v1/model/info` (`model_info.max_input_tokens`) — use it to set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` for models under 200k.

### Rate limit — the one real constraint

The gateway currently allows **4 parallel requests per key**. Normal interactive use fits (main model + background `mini` ≈ 2–3 concurrent). **Launching many parallel subagents will hit 429s** — Claude Code retries automatically, but expect slowdowns. Prefer sequential patterns; this is why neuroflow's `scholar` agent searches sequentially.

---

## Saving to neuroflow integrations.json

The `/neuroflow:setup` custom-LLM step saves the following to the chosen scope's `integrations.json` (global `~/.neuroflow/integrations.json` or per-project `.neuroflow/integrations.json`):

```json
"custom_llm": {
  "provider": "einfra",
  "base_url": "https://llm.ai.e-infra.cz/v1",
  "api_key": "<YOUR_API_KEY>",
  "model": "agentic"
}
```

- `api_key` is stored locally and gitignored — never synced anywhere.
- Non-secret fields can optionally be synced to your flowie private GitHub repo for cross-machine portability.
- The legacy `proxy_mode` / `proxy_port` fields are only relevant to the legacy proxy appendix below.

---

## Unrelated known issues

### `semantic search failed: sema*...sts`

The Semantic Scholar MCP tool's API key is expired or rate-limited — unrelated to the gateway. Get a free key at `https://www.semanticscholar.org/product/api`. Workaround: use `search_pubmed` or `search_biorxiv` (no API key required).

---

## Legacy appendix — OpenAI-compat proxy (pre-native-gateway)

> **Only needed if the native Anthropic endpoint is unavailable to you** (or for other providers that are OpenAI-compatible only). For e-INFRA today, use the native approach above.

The custom FastAPI proxy (`skills/setup/scripts/einfra/proxy.py`) translates Anthropic↔OpenAI formats including streaming, multi-turn tool use, and thinking block passthrough. It was built because LiteLLM failed on two blocking cases with these models (`Content block is not a text block` with kimi thinking blocks; `No tool calls but found tool output` with deepseek multi-turn tool pairing).

**Terminal 1 — start the proxy:**
```bash
OPENAI_API_KEY=<YOUR_API_KEY> \
OPENAI_BASE_URL=https://llm.ai.e-infra.cz/v1 \
BIG_MODEL=<model> SMALL_MODEL=<model> \
uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 0.0.0.0 --port 4001
```

**Terminal 2 — connect Claude Code:**
```bash
ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude
```

Proxy-specific troubleshooting (Windows): port in use → `netstat -ano | findstr :4001`, kill via `cmd.exe /c "taskkill /F /PID <PID>"`; `[WinError 10048]` right after a kill is a TIME_WAIT ghost — switch ports instead of waiting; use port 4001+ (4000 is commonly taken). `API Error: Content block not found` was a proxy bug, fixed by assigning tool block indices once at creation (`tool_block_started` as dict, not set).

---

## Quick reference

| Goal | How |
|---|---|
| Connect Claude Code (native) | Set the env block above, run `claude` |
| Run alongside subscription Claude | `CLAUDE_CONFIG_DIR=~/.claude-meta` (isolated) — both work concurrently |
| List live models | `curl -s -H "Authorization: Bearer <key>" https://llm.ai.e-infra.cz/v1/models` |
| Switch model mid-session | `/model <id>` |
| Best model for tool use | `agentic` |
| Background/light tasks | `mini` |
| Context window info | `/v1/model/info` → `model_info.max_input_tokens` |
| Parallel request limit | 4 per key — avoid heavy parallel subagent fan-out |
