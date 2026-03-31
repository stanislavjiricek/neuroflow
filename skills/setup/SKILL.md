---
name: setup
description: Configure neuroflow integrations — PubMed, Miro, Google Workspace, and custom LLM providers. Use when setting up credentials, checking integration status, or guiding a user through connecting external services. Also covers e-INFRA CZ connection for Czech academic researchers.
reads:
  - .neuroflow/integrations.json
  - skills/setup/references/einfra-cc.md
writes:
  - .neuroflow/integrations.json
---

# neuroflow:setup

Agent-facing knowledge for all neuroflow integrations. Use this skill when a user asks about credentials, integration status, or setting up an external service — without necessarily running the full `/setup` wizard.

---

## Integrations overview

| Integration | Credential required | Key |
|---|---|---|
| PubMed | ✅ Yes | `PUBMED_EMAIL` |
| bioRxiv | ❌ No | — |
| Miro | ✅ Yes | `MIRO_ACCESS_TOKEN` |
| Context7 | ❌ No | — |
| Google Workspace CLI (`gws`) | ✅ Yes | OAuth via `gws auth login` |
| Custom LLM provider | ✅ Yes (API key) | `custom_llm.api_key` in integrations.json |

---

## How to check integration status

1. Read `.neuroflow/integrations.json` if it exists — note which keys are present.
2. Check whether the corresponding environment variables are set in the current shell (`PUBMED_EMAIL`, `MIRO_ACCESS_TOKEN`, etc.).
3. For `gws`: run `gws --version 2>/dev/null` or `which gws` to detect installation; run `gws auth status` to check OAuth.
4. For custom LLM: check `integrations.json` for a `custom_llm` key; if present, show `provider` and `base_url`.

Display a status table:

```
Integration              Status
──────────────────────   ──────
PubMed                   ✅ configured  (or ❌ not configured)
bioRxiv                  ✅ no credentials needed
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
  "pubmed": {
    "PUBMED_EMAIL": "you@example.com"
  },
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
    "model": "qwen3.5-122b",
    "proxy_port": 3456
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
| PubMed | Must contain `@`; up to 3 attempts |
| Miro | Non-empty, at least 20 characters; `eyJ` prefix is a good sign (JWT) |
| Google Workspace | File must exist at platform path, or env vars must be set |
| Custom LLM | API key: non-empty; base URL: must start with `http`; model: optional |

---

## Custom LLM provider support

The `/setup` Step 5 allows configuring any OpenAI-compatible API endpoint as a replacement for Anthropic's API in Claude Code. This is how it works:

1. Set `ANTHROPIC_BASE_URL` to the custom endpoint (e.g. `https://llm.ai.e-infra.cz/v1`).
2. Set `ANTHROPIC_API_KEY` to the custom provider's API key.
3. Launch Claude Code — it will use the custom endpoint for all requests.

**Model selection limitation:** Claude Code always sends `claude-*` model names in requests. In direct mode, the custom API must accept these names (some do, routing to a default model). To select a specific model, use the proxy script (`skills/setup/scripts/proxy.mjs`), which intercepts requests and replaces the model name before forwarding.

For the Czech-specific e-INFRA CZ example — including available models, direct mode, proxy mode, and full terminal workflow — read `skills/setup/references/einfra-cc.md`.

---

## Security note

- **Secrets stay local.** API keys and OAuth tokens are stored only in `.neuroflow/integrations.json`, which is gitignored. Never write credentials to any other file.
- **Non-secret settings** (provider name, base URL, preferred model, proxy port) are safe to sync. If the user has a flowie profile linked (check `.neuroflow/flowie/sync.json`), non-secret `custom_llm` settings can be written to `.neuroflow/flowie/integrations.json` and pushed to the user's private GitHub repo for cross-machine sync. The `api_key` field is always excluded from this sync.

---

## Running the setup wizard

The full interactive wizard is `/neuroflow:setup`. It covers all integrations step by step. This skill provides agent-level knowledge so Claude can guide credential setup without running the wizard — for example, answering "how do I configure Miro?" or surfacing the right reference when a user mentions e-INFRA.
