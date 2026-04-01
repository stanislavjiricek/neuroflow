# e-INFRA CZ LLM — Claude Code Integration

> **Country-specific:** This guide is for **Czech academic researchers only**. Access requires Metacentrum / e-INFRA CZ membership. See https://metavo.metacentrum.cz for eligibility. This is not available for general international use.

---

## What is e-INFRA CZ

e-INFRA CZ is the Czech national research e-infrastructure, providing computing, data storage, and — relevant here — **free LLM API access** to the Czech academic community. The LLM service is hosted at `https://llm.ai.e-infra.cz` and exposes an OpenAI-compatible API, which means Claude Code can use it as a drop-in replacement for Anthropic's API.

---

## Who can access

Czech academic researchers with an active **Metacentrum / e-INFRA CZ membership**. Membership is free for researchers affiliated with Czech universities and research institutions. Register or check your status at https://metavo.metacentrum.cz.

---

## Available models

| Model | Category | Notes |
|---|---|---|
| `qwen3.5-122b` | General / best overall | Default recommended |
| `qwen3-coder-next` | Coding | Latest coding model |
| `deepseek-v3.2` | Coding + reasoning | Good all-rounder |
| `deepseek-v3.2-thinking` | Reasoning / thinking | For complex reasoning |
| `kimi-k2.5` | Agentic / tool use | Best for tool-calling workflows |
| `mistral-small-4` | Fast / small | Quick tasks |
| `qwen3-coder-30b` | Fast / coding | Lighter coding model |

---

## Mode A — Direct connection (simplest)

Set two environment variables and launch Claude Code:

```bash
ANTHROPIC_BASE_URL=https://llm.ai.e-infra.cz/v1 \
ANTHROPIC_API_KEY=<YOUR_API_KEY> \
claude
```

⚠️ **Limitation:** Claude Code sends `claude-*` model names in all requests. The e-INFRA API accepts these in direct mode, but you cannot select a specific e-INFRA model — the API uses its default routing. If you need a specific model (e.g. `kimi-k2.5` for agentic workflows), use Mode B.

> **Note on model name in responses:** In direct mode the e-INFRA API may return a response with a non-Claude `model` field (e.g. `"model": "qwen3.5-122b"`). Claude Code validates this field and may error with *"unexpected model"*. If this happens, switch to Mode B (proxy) — the proxy automatically restores the original `claude-*` model name in every response so Claude Code is satisfied.

---

## Mode B — Proxy (model selection)

The proxy script intercepts requests from Claude Code, replaces the model name with your chosen e-INFRA model, and forwards the request to the e-INFRA API. This lets you select any model from the table above.

### Step-by-step terminal workflow

**Step 1 — Copy the proxy script**

Copy `skills/setup/scripts/proxy.mjs` from the neuroflow plugin to a convenient local folder (e.g. `~/tools/einfra/`).

**Step 2 — Add your API key**

Open the copied `proxy.mjs` and replace `<YOUR_API_KEY>` with your actual e-INFRA API key.

**Step 3 — Terminal 1: start the proxy**

```bash
node proxy.mjs                     # default: qwen3.5-122b, port 3456
node proxy.mjs kimi-k2.5           # use kimi-k2.5
node proxy.mjs deepseek-v3.2 8080  # custom model + port
```

The proxy prints a confirmation:
```
e-INFRA proxy running on http://localhost:3456
Routing all requests → qwen3.5-122b
```

**Step 4 — Close Claude Code**

If Claude Code is currently running, close it completely before proceeding. Environment variables are read at startup — Claude Code will not pick them up if it is already open.

**Step 5 — Terminal 2: start Claude Code pointing at the proxy**

```bash
ANTHROPIC_BASE_URL=http://localhost:3456 ANTHROPIC_API_KEY=any claude
```

Note: `ANTHROPIC_API_KEY=any` is a placeholder — Claude Code requires a non-empty value, but the proxy handles the real API key. The value itself does not matter.

**Step 6 — Verify**

Claude Code is now routing all requests through the proxy → e-INFRA. The proxy terminal will print each request as it arrives.

---

## For persistence (shell profile)

**Direct mode** — add to `~/.zshrc` or `~/.bashrc` (macOS / Linux):

```bash
export ANTHROPIC_BASE_URL=https://llm.ai.e-infra.cz/v1
export ANTHROPIC_API_KEY=<YOUR_API_KEY>
```

Then restart your terminal and reopen Claude Code — no proxy needed.

**Proxy mode** — start the proxy in a background terminal each session, or add it to a launch script. The `ANTHROPIC_BASE_URL=http://localhost:3456` pointing to the proxy must be set in the shell where you open Claude Code.

---

## Windows users

Node.js runs `proxy.mjs` on Windows without changes. The only difference is how you set environment variables.

**PowerShell (recommended):**

```powershell
# Direct mode — set for this terminal session, then launch Claude Code
$env:ANTHROPIC_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:ANTHROPIC_API_KEY  = "<YOUR_API_KEY>"
claude

# Proxy mode — open two PowerShell windows
# Window 1: start the proxy
node proxy.mjs kimi-k2.5

# Window 2: launch Claude Code
$env:ANTHROPIC_BASE_URL = "http://localhost:3456"
$env:ANTHROPIC_API_KEY  = "any"
claude
```

**For persistence on Windows:** add to your PowerShell profile (`notepad $PROFILE`):
```powershell
$env:ANTHROPIC_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:ANTHROPIC_API_KEY  = "<YOUR_API_KEY>"
```
Or set them permanently via Settings → System → About → Advanced system settings → Environment Variables.

**cmd.exe (legacy):**
```cmd
set ANTHROPIC_BASE_URL=https://llm.ai.e-infra.cz/v1
set ANTHROPIC_API_KEY=<YOUR_API_KEY>
claude
```

---

## ⚠️ Parallelization note

Custom API providers — including e-INFRA — can freeze or time out when Claude Code fires many concurrent tool calls. neuroflow's `scholar` agent was specifically updated to run searches **sequentially** (PubMed → bioRxiv → fallbacks, one at a time) and download papers in **batches of 2** for this reason.

If you experience freezing or silent hangs with other neuroflow workflows while using e-INFRA, reduce concurrency manually: avoid commands that trigger many simultaneous file reads or API calls, and prefer sequential workflows over parallel ones.

---

## Saving to neuroflow setup

The `/neuroflow:setup` Step 5 saves the following to `.neuroflow/integrations.json` under the `custom_llm` key:

```json
"custom_llm": {
  "provider": "einfra",
  "base_url": "https://llm.ai.e-infra.cz/v1",
  "api_key": "<YOUR_API_KEY>",
  "model": "qwen3.5-122b",
  "proxy_port": 3456
}
```

- `api_key` is stored locally and gitignored — it is never synced anywhere.
- Non-secret fields (`provider`, `base_url`, `model`, `proxy_port`) can optionally be written to your linked flowie private GitHub repo for cross-machine sync. Run `/neuroflow:setup` Step 5 to configure this.
