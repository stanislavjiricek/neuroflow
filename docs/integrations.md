---
title: Integrations
---

# Integrations

neuroflow connects to four MCP (Model Context Protocol) servers that Claude Code launches automatically via `npx`. Two require credentials; two work out of the box.

---

## MCP servers

| Server | npm package | Requires credentials |
|---|---|---|
| **PubMed** | `pubmed-mcp-server` | ✅ `PUBMED_EMAIL` |
| **bioRxiv** | `paper-search-mcp-nodejs` | ❌ None |
| **Miro** | `@k-jarzyna/mcp-miro` | ✅ `MIRO_ACCESS_TOKEN` |
| **Context7** | `@upstash/context7-mcp` | ❌ None |

All four are started automatically by Claude Code — you do not need to run them manually.

---

## PubMed

The PubMed integration enables the [scholar agent](concepts/agents.md) to search NCBI PubMed for peer-reviewed literature.

### Why an email is required

NCBI requires an email address for automated API access so they can contact you if your queries cause problems. **Any valid email works** — it does not need to be registered with NCBI.

### Setup

Run the wizard:
```
/neuroflow:setup
```

Or set the environment variable directly:
```bash
export PUBMED_EMAIL="you@example.com"
```

Add to your shell profile for persistence:
```bash
echo 'export PUBMED_EMAIL="you@example.com"' >> ~/.zshrc
```

### What happens without it

If `PUBMED_EMAIL` is not configured and you try to search literature, the plugin detects this and offers to run `/setup` before searching. You can also proceed with bioRxiv only (no email required).

---

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

The e-INFRA CZ platform provides free access to large open-source models via an OpenAI-compatible API at `https://llm.ai.e-infra.cz`.

**Available models:**

| Model | Category | Notes |
|---|---|---|
| `qwen3.5-122b` | General / best overall | Default recommended |
| `qwen3-coder-next` | Coding | Latest coding model |
| `deepseek-v3.2` | Coding + reasoning | Good all-rounder |
| `deepseek-v3.2-thinking` | Reasoning / thinking | For complex reasoning |
| `kimi-k2.5` | Agentic / tool use | Best for tool-calling workflows |
| `mistral-small-4` | Fast / small | Quick tasks |
| `qwen3-coder-30b` | Fast / coding | Lighter coding model |

**Direct connection:**

```bash
ANTHROPIC_BASE_URL=https://llm.ai.e-infra.cz/v1 \
ANTHROPIC_API_KEY=<YOUR_API_KEY> \
claude
```

**Proxy mode (for model selection):**

Copy `skills/setup/scripts/proxy.mjs` from the neuroflow plugin, edit in your API key, then:

```bash
node proxy.mjs kimi-k2.5   # Terminal 1 — start the proxy
# Close Claude Code, then reopen in Terminal 2:
ANTHROPIC_BASE_URL=http://localhost:3456 ANTHROPIC_API_KEY=any claude
```

For full documentation — including all available models, direct mode limitations, and the complete terminal workflow — see the `neuroflow:setup` skill → [`references/einfra-cc.md`](../skills/setup/references/einfra-cc.md).

### Other providers

Any OpenAI-compatible endpoint works: set `base_url` and `api_key` during `/setup` Step 5. The custom LLM settings are saved to `.neuroflow/integrations.json` under the `custom_llm` key.

---

## Credential storage

When you run `/neuroflow:setup`, credentials are saved to `.neuroflow/integrations.json`:

```json
{
  "pubmed": {
    "PUBMED_EMAIL": "you@example.com"
  },
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
    `.neuroflow/integrations.json` is automatically added to `.gitignore` by neuroflow. Your credentials are stored locally only and never committed to your repository.

---

## Reminder behavior

neuroflow checks credentials at the point of use, not upfront:

| Trigger | Reminder |
|---|---|
| `/ideation` → Explore literature | If `PUBMED_EMAIL` missing → offer to run `/setup` or use bioRxiv only |
| Mention Miro in any command | If `MIRO_ACCESS_TOKEN` missing → offer to run `/setup` or skip |
| Mention custom LLM / e-INFRA | If `custom_llm` missing → offer to run `/setup` Step 5 |

You can always re-run `/neuroflow:setup` to add or update credentials at any time.
