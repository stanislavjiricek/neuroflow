# e-INFRA CZ LLM — Claude Code Integration

> **Country-specific:** This guide is for **Czech academic researchers only**. Access requires Metacentrum / e-INFRA CZ membership. See https://metavo.metacentrum.cz for eligibility.

---

## What is e-INFRA CZ

e-INFRA CZ is the Czech national research e-infrastructure providing free LLM API access to the academic community. The LLM service at `https://llm.ai.e-infra.cz` exposes an **OpenAI-compatible API**, which means Claude Code can use it via a proxy that translates between Anthropic and OpenAI formats.

---

## Available models

| Model | Category | Best for |
|---|---|---|
| `kimi-k2.5` | Agentic / tool use | **Recommended for Claude Code** — tool calling, MCP, agentic workflows |
| `qwen3.5-122b` | General / best overall | Long reasoning, general tasks |
| `deepseek-v3.2` | Coding + reasoning | Good all-rounder |
| `deepseek-v3.2-thinking` | Reasoning / thinking | Complex multi-step reasoning |
| `qwen3-coder-next` | Coding | Latest coding model |
| `qwen3-coder-30b` | Fast / coding | Lighter coding model |
| `mistral-small-4` | Fast / small | Quick tasks |

**For Claude Code agentic use (tool calling, MCP tools, neuroflow), use `kimi-k2.5`.**

---

## Mode A — Direct connection (simplest, no model selection)

Set two environment variables and launch Claude Code:

```bash
ANTHROPIC_BASE_URL=https://llm.ai.e-infra.cz/v1 \
ANTHROPIC_API_KEY=<YOUR_API_KEY> \
claude
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:ANTHROPIC_AUTH_TOKEN = "<YOUR_API_KEY>"
claude
```

⚠️ **Limitations:** Cannot select a specific model. The e-INFRA API may return a non-Claude `model` field causing Claude Code to error with *"unexpected model"*. Use Mode B for serious agentic workflows.

---

## Mode B — Custom Python proxy (recommended)

The custom FastAPI proxy (`proxy.py`) performs the full Anthropic↔OpenAI translation including streaming, multi-turn tool use, and thinking block passthrough. It is the most reliable option for Claude Code with e-INFRA — specifically tested and fixed for the edge cases that third-party proxies (LiteLLM) fail on with these models.

The proxy is available in `skills/setup/scripts/einfra/proxy.py`.

### Check available models first

The model list at e-INFRA changes frequently. Before picking a model, fetch the current list:

```bash
curl -s -H "Authorization: Bearer <YOUR_API_KEY>" https://llm.ai.e-infra.cz/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"
```

Or just ask Claude Code to do it — paste your API key and run:
```
fetch the model list from https://llm.ai.e-infra.cz/v1/models with my key <YOUR_API_KEY>
```

The table above reflects models available as of April 2026 — verify if more than a few weeks have passed.

### Step-by-step workflow

**Terminal 1 — start the proxy:**

```bash
# Unix
OPENAI_API_KEY=<YOUR_API_KEY> \
OPENAI_BASE_URL=https://llm.ai.e-infra.cz/v1 \
BIG_MODEL=kimi-k2.5 \
SMALL_MODEL=kimi-k2.5 \
uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 0.0.0.0 --port 4001
```

```powershell
# Windows PowerShell
$env:OPENAI_API_KEY = "<YOUR_API_KEY>"
$env:OPENAI_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:BIG_MODEL = "kimi-k2.5"
$env:SMALL_MODEL = "kimi-k2.5"
uv run --python 3.12 --with fastapi --with httpx --with uvicorn uvicorn proxy:app --host 0.0.0.0 --port 4001
```

**Terminal 2 — connect Claude Code:**

```bash
# Unix
ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude
```

```powershell
# Windows PowerShell
$env:ANTHROPIC_BASE_URL = "http://localhost:4001"
$env:ANTHROPIC_AUTH_TOKEN = "dummy"
claude
```

Note: use `ANTHROPIC_AUTH_TOKEN` on Windows — more reliably picked up by Claude Code CLI than `ANTHROPIC_API_KEY`.

### Switch model

Change `BIG_MODEL` and `SMALL_MODEL` to any model from the table above:

```powershell
$env:BIG_MODEL = "deepseek-v3.2"
$env:SMALL_MODEL = "deepseek-v3.2"
```

### What the proxy does

- Maps all `claude-*` model names to the configured `BIG_MODEL` / `SMALL_MODEL`
- Translates Anthropic message format → OpenAI format (including tool_use, tool_result, multi-turn)
- Translates OpenAI streaming SSE → Anthropic streaming SSE with correct block indices
- Restores the original `claude-*` model name in all responses so Claude Code doesn't reject them
- Injects behavioral directives into the system prompt for better agentic performance
- Passes through `reasoning_content` as thinking blocks

---

## Why not LiteLLM?

LiteLLM was tested with e-INFRA models and produced two blocking errors:

1. **`API Error: Content block is not a text block`** — `kimi-k2.5` returns thinking/reasoning blocks that LiteLLM passes through incorrectly, causing Claude Code to find a thinking block where it expects text.

2. **`No tool calls but found tool output`** — `deepseek-v3.2` rejects multi-turn conversations where LiteLLM's tool result→tool message translation loses the pairing with the preceding tool call.

The custom `proxy.py` handles both cases correctly. LiteLLM may work in a future version — but as of April 2026, use `proxy.py` for e-INFRA.

---

## Port conflict resolution (Windows)

A common Windows issue: port already in use (`[WinError 10048]`).

**Check what's using the port:**
```powershell
netstat -ano | findstr :4001
```

**Kill the process (must use cmd.exe — `taskkill` breaks in Git Bash on Windows):**
```powershell
cmd.exe /c "taskkill /F /PID <PID>"
```

**If the process doesn't appear in tasklist** but netstat still shows it — ghost socket in TIME_WAIT. Switch to a different port rather than waiting:
```powershell
# change --port 4001 to --port 4002
```

**Use port 4001 or higher** — port 4000 is commonly grabbed by other services on Windows.

---

## Known issues and fixes

### `API Error: Content block not found`

**What it means:** Claude Code's streaming parser received a `content_block_delta` or `content_block_stop` referencing an index never opened with `content_block_start`.

**Root cause in proxy.py (fixed):** `tool_block_started` was a `set` tracking which tool indices had started, but not which Anthropic block index they were assigned. The final cleanup recalculated `next_idx + idx` which was stale.

**Fix:** `tool_block_started` is now a `dict` mapping `openai_tool_idx → assigned_block_index`. Block indices are assigned once at creation time and stored — never recalculated.

### `API Error: Content block is not a text block`

LiteLLM + kimi-k2.5 issue — kimi returns thinking/reasoning blocks that LiteLLM passes through as Anthropic thinking blocks. Claude Code finds a thinking block where it expects text. Use `proxy.py` instead.

### `No tool calls but found tool output`

LiteLLM + deepseek-v3.2 issue — message history translation loses the pairing between tool calls and tool results in multi-turn conversations. Use `proxy.py` instead.

### `semantic search failed: sema*...sts`

The Semantic Scholar MCP tool's API key is expired or rate-limited — unrelated to the proxy. Get a free key at `https://www.semanticscholar.org/product/api`. Workaround: use `search_pubmed` or `search_biorxiv` (no API key required).

### Claude Code freezes or hangs with many concurrent tool calls

e-INFRA models can time out under high concurrency. neuroflow's `scholar` agent runs searches sequentially for this reason. For other workflows: prefer sequential tool use patterns.

### `[WinError 10048]` immediately after killing a process

Windows TIME_WAIT state — port locked for up to 60 seconds after process death. Switch port instead of waiting.

---

## Saving to neuroflow integrations.json

The `/neuroflow:setup` Step 5 saves the following to `.neuroflow/integrations.json`:

```json
"custom_llm": {
  "provider": "einfra",
  "base_url": "https://llm.ai.e-infra.cz/v1",
  "api_key": "<YOUR_API_KEY>",
  "model": "kimi-k2.5",
  "proxy_mode": "custom",
  "proxy_port": 4001
}
```

- `api_key` is stored locally and gitignored — never synced anywhere.
- Non-secret fields can optionally be synced to your flowie private GitHub repo for cross-machine portability.

---

## Quick reference

| Goal | Command |
|---|---|
| Start proxy (Unix) | `BIG_MODEL=kimi-k2.5 OPENAI_API_KEY=<key> uv run ... uvicorn proxy:app --port 4001` |
| Start proxy (Windows) | `.\start_proxy.ps1` |
| Connect Claude Code (Unix) | `ANTHROPIC_BASE_URL=http://localhost:4001 ANTHROPIC_AUTH_TOKEN=dummy claude` |
| Connect Claude Code (Windows) | `$env:ANTHROPIC_BASE_URL="http://localhost:4001"; $env:ANTHROPIC_AUTH_TOKEN="dummy"; claude` |
| Check port in use (Windows) | `netstat -ano \| findstr :4001` |
| Kill port owner (Windows) | `cmd.exe /c "taskkill /F /PID <PID>"` |
| Switch model | Set `BIG_MODEL=<model>` env var before starting |
| Best model for tool use | `kimi-k2.5` |
| Best model for reasoning | `deepseek-v3.2-thinking` |
