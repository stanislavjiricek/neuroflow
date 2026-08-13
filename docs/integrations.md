---
title: Integrations
---

# Integrations

neuroflow connects to four MCP (Model Context Protocol) servers that Claude Code launches automatically via `npx`. One requires credentials; three work out of the box.

---

## MCP servers

| Server | npm package | Requires credentials |
|---|---|---|
| **PubMed / bioRxiv** | `paper-search-mcp-nodejs` | ❌ None |
| **Miro** | `@k-jarzyna/mcp-miro` | ✅ `MIRO_ACCESS_TOKEN` |
| **Context7** | `@upstash/context7-mcp` | ❌ None |

All are started automatically by Claude Code — you do not need to run them manually.

**Optional — Zotero:** neuroflow does not bundle a Zotero server, but if you add a community one (e.g. `zotero-mcp` — `claude mcp add zotero -- uvx zotero-mcp`, with the Zotero desktop app running or a `ZOTERO_API_KEY`), `/ideation` automatically switches to library-first literature search: your existing papers are recognized and skipped, and new findings can be saved into a project collection. See `/setup` for guidance.

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
    The bioRxiv MCP server uses a date-range API that does not support keyword filtering. When a keyword search returns zero results, the scholar agent will warn you and automatically fall back to **CrossRef** and **Semantic Scholar** — both free public APIs that support full keyword search across preprints and peer-reviewed literature. No additional setup is required for the fallback.

---

## Miro

The Miro integration enables Claude to create and edit Miro boards — useful for mind maps, experiment diagrams, and visual collaboration during ideation.

### Getting a personal access token

1. Go to [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
2. Click **Create new app** (or select an existing one)
3. Under **Token**, click **Create token**
4. Copy the token — it starts with `eyJ…`

!!! note "No OAuth support"
    Miro OAuth browser login is not supported from a terminal subprocess. Use a personal access token instead.

### Setup

Run the wizard:
```
/neuroflow:setup
```

Or set the environment variable directly:
```bash
export MIRO_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiJ9..."
```

---

## Context7

The Context7 integration provides Claude with up-to-date documentation for libraries like MNE, nilearn, scikit-learn, and PsychoPy — directly in context.

**No credentials needed.** Works automatically after installation.

This means when Claude writes an MNE preprocessing script, it can look up the current API instead of relying on training data that may be outdated.

---

## Custom LLM providers

neuroflow's `/setup` command (Step 5) lets you configure an alternative LLM API endpoint for Claude Code — replacing Anthropic's API with any OpenAI-compatible endpoint.

### e-INFRA CZ (Czech academic researchers only)

> **Access requirement:** e-INFRA CZ LLM API is available to Czech academic researchers with Metacentrum/e-INFRA CZ membership. See https://metavo.metacentrum.cz for eligibility. This service is not available for general international use.

The e-INFRA CZ gateway at `https://llm.ai.e-infra.cz` provides free access to large open-source models — and it speaks the **Anthropic protocol natively**, so Claude Code connects directly. **No proxy needed.**

**Native connection (recommended):**

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

The isolated `CLAUDE_CONFIG_DIR` lets this run **alongside** your normal subscription `claude` in another terminal — zero shared state. Get an API key at [chat.ai.e-infra.cz](https://chat.ai.e-infra.cz) → Settings → Account → API keys.

**Models:** the gateway list changes over time — fetch it live from `https://llm.ai.e-infra.cz/v1/models`. As of August 2026 it includes `agentic` (recommended for Claude Code tool use), `coder`, `thinker`, `mini` (background tasks), `kimi-k3`, `qwen3.5-122b`, `glm-5`, `deepseek`, and more. Switch mid-session with `/model <id>`.

**Rate limit:** 4 parallel requests per key — normal interactive use fits; heavy parallel subagent fan-out will hit 429s.

For full documentation — env var reference, context-window handling, and the legacy proxy appendix — see the `neuroflow:setup` skill → [`references/einfra-cc.md`](skills/setup/references/einfra-cc.md).

### Other providers

Any OpenAI-compatible endpoint works: set `base_url` and `api_key` during `/setup` Step 5. The custom LLM settings are saved to your chosen scope's `integrations.json` under the `custom_llm` key.

---

## Credential storage

When you run `/neuroflow:setup`, credentials are saved to `~/.neuroflow/integrations.json` (global, all projects on this machine) or `.neuroflow/integrations.json` (per-project override — takes precedence). The wizard asks which scope to use:

```json
{
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJ..."
  },
  "custom_llm": {
    "provider": "einfra",
    "base_url": "https://llm.ai.e-infra.cz/v1",
    "api_key": "<stored locally, gitignored>",
    "model": "qwen3.5-122b"
  }
}
```

!!! warning "Never committed"
    The per-project `.neuroflow/integrations.json` is automatically added to `.gitignore` by neuroflow, and the global `~/.neuroflow/integrations.json` lives outside any repository. Your credentials are stored locally only and never committed. Only non-secret settings (never `api_key`) are ever synced via `~/.neuroflow/flowie/integrations.json`.

---

## Reminder behavior

neuroflow checks credentials at the point of use, not upfront:

| Trigger | Reminder |
|---|---|
| Mention Miro in any command | If `MIRO_ACCESS_TOKEN` missing → offer to run `/setup` or skip |
| Mention custom LLM / e-INFRA | If `custom_llm` missing → offer to run `/setup` Step 5 |

You can always re-run `/neuroflow:setup` to add or update credentials at any time.
