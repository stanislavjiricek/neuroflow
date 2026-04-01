---
title: /setup
---

# `/neuroflow:setup`

**Interactive credential wizard for MCP integrations.**

`/setup` guides you through connecting the neuroflow MCP integrations — Miro for visual collaboration, Google Workspace, and optional custom LLM providers. It stores credentials securely in `.neuroflow/integrations.json`, which is git-ignored by default.

---

## When to use it

- First time setting up credentials (or if you skipped it during `/neuroflow`)
- Updating an existing credential
- Checking which integrations are currently configured

---

## What it does

### Step 1 — Show current status

Displays a status table so you know what's already configured:

```
Integration      Status
─────────────    ──────
PubMed/bioRxiv   ✅ no credentials needed
Miro             ❌ not configured
Context7         ✅ no credentials needed
Custom LLM       ❌ not configured
```

### Step 2 — Miro setup

Miro requires a personal access token. The wizard tells you exactly how to get one:

1. Go to [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
2. Click **Create new app** (or use an existing one)
3. Under **Token**, click **Create token** — copy the token shown

```
Paste your Miro access token (or press Enter to skip):
> eyJhbGciOiJSUzI1NiJ9...
```

### Step 3 — Google Workspace CLI setup

See the [Integrations guide](../integrations.md) for full details on getting OAuth credentials.

### Step 4 — Custom LLM provider (optional)

Optionally configure an alternative LLM API endpoint for Claude Code. Skip this step if you use Anthropic directly.

If configuring:
- Enter provider name, base URL, API key, preferred model, and proxy port
- Credentials are saved to `.neuroflow/integrations.json` under `custom_llm`
- Non-secret settings (provider, URL, model) can also be synced to your flowie profile for cross-machine use

!!! note "e-INFRA CZ"
    Czech academic researchers can use the e-INFRA CZ free LLM API (`https://llm.ai.e-infra.cz`) via Metacentrum/e-INFRA CZ membership. See the [integrations guide](../integrations.md#e-infra-cz-czech-academic-researchers-only) for details.

### Step 5 — Save credentials

Credentials are saved to `.neuroflow/integrations.json`:

```json
{
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJhbGciOiJSUzI1NiJ9..."
  },
  "custom_llm": {
    "provider": "einfra",
    "base_url": "https://llm.ai.e-infra.cz/v1",
    "api_key": "<stored locally, gitignored>",
    "model": "qwen3.5-122b"
  }
}
```

!!! warning "This file is local only"
    `.neuroflow/integrations.json` is excluded from git (added to `.gitignore` by neuroflow). Your credentials are never committed to your repository.

---

## Activating credentials

After running `/setup`, export the env vars in your shell before starting Claude Code:

```bash
export MIRO_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiJ9..."
```

Add to your shell profile (`~/.zshrc` or `~/.bashrc`) so it loads automatically:

```bash
echo 'export MIRO_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiJ9..."' >> ~/.zshrc
```

---

## What is automatic vs manual

| Step | Automatic | Manual |
|---|---|---|
| MCP server processes started | ✅ Claude Code launches them via `npx` | — |
| Miro token entry | ✅ Prompted by `/setup` | ⚠️ You must create the token in Miro first |
| Miro OAuth browser login | ❌ Not implemented | Use a personal access token instead |
| Env var export | ❌ Not automatic | Run `export …` or add to shell profile |

---

## Reminder behavior

- If you mention Miro and `MIRO_ACCESS_TOKEN` is missing, Claude offers to run `/setup`.
- You can always re-run `/setup` to add or update credentials.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/integrations.json` |
| Writes | `.neuroflow/integrations.json` |

---

## Related

- [Integrations guide →](../integrations.md)
- [`/neuroflow`](neuroflow.md) — also offers to run setup on first use
