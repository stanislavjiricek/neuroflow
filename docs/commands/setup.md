---
title: /setup
---

# `/neuroflow:setup`

**Interactive setup wizard for neuroflow integrations.**

`/setup` guides you through connecting the neuroflow integrations — Miro for visual collaboration, Google Workspace, and an optional custom LLM gateway. It never asks you to paste a token, key or secret into the chat: you put each secret where it belongs yourself, in your own terminal. Non-secret settings are saved to `~/.neuroflow/integrations.json` (global, all projects on this machine) or `.neuroflow/integrations.json` (per-project override, git-ignored) — the wizard asks which scope you want first.

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
Integration          Status
─────────────        ──────
PubMed/bioRxiv       ✅ no credentials needed
Context7             ✅ no credentials needed
Miro (optional)      — not added
Custom LLM gateway   — not configured
```

### Step 2 — Miro (optional)

Miro is not bundled with neuroflow — you add it yourself, once, for all your projects. The wizard tells you how:

1. Create a personal access token at [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps) (**Create new app** → **Token** → **Create token**).
2. In a **separate terminal** — not in the Claude Code chat — run:
   ```bash
   claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<your-token> -- npx -y @k-jarzyna/mcp-miro
   ```
3. Restart Claude Code (or check `/mcp`).

!!! warning "Keep the token out of the chat"
    Never paste the token into the conversation, and don't run the command with the `!` prefix inside Claude Code — `!` commands and their output are recorded in the conversation.

### Step 3 — Google Workspace CLI setup

See the [Integrations guide](../integrations.md) for full details on getting OAuth credentials. If you use a client ID and secret instead of a `client_secret.json` file, you set them as environment variables yourself — the wizard never asks for them.

### Step 4 — Custom LLM gateway (optional)

Optionally run Claude Code through an Anthropic-compatible gateway — for example one your institution provides — instead of Anthropic's API. Skip this step if you use Anthropic directly.

If configuring:
- Enter a provider name, the base URL, a preferred model, and (legacy proxy only) a proxy port — never the API key
- Keep the API key in a file only you can read (or your OS credential store); the launch command reads it
- The settings are saved to your chosen scope's `integrations.json` under `custom_llm`, and can be synced to your flowie profile after you confirm

See the [integrations guide](../integrations.md#custom-llm-gateways) for the launch command and caveats.

### Step 5 — Save settings

Non-secret settings are saved to `~/.neuroflow/integrations.json` (global) or `.neuroflow/integrations.json` (per-project override):

```json
{
  "custom_llm": {
    "provider": "my-gateway",
    "base_url": "https://llm.example.org",
    "model": "<model-id>"
  }
}
```

!!! warning "This file is local only"
    The per-project `.neuroflow/integrations.json` is excluded from git (added to `.gitignore` by neuroflow) and the global file lives outside any repository. It holds no secrets. Only non-secret settings are synced via `~/.neuroflow/flowie/integrations.json`, and only after you confirm.

---

## Activating

- **Miro:** restart Claude Code after `claude mcp add`; the tools appear in every project.
- **Google Workspace CLI:** if `client_secret.json` is not at the default path, set `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` in your shell profile.
- **Custom LLM gateway:** start Claude Code with the launch command from the integrations guide.

---

## What is automatic vs manual

| Step | Automatic | Manual |
|---|---|---|
| Bundled MCP servers started | ✅ Claude Code launches them via `npx` | — |
| Miro | ❌ Not bundled | You create a token and run `claude mcp add` in your own terminal |
| Miro OAuth browser login | ❌ Not implemented | Use a personal access token instead |
| Gateway API key | ❌ Never handled by neuroflow | Keep it in a key file read by your launch command |

---

## Reminder behavior

- If you mention Miro and no Miro tools are available, Claude shows the Step 2 instructions.
- You can always re-run `/setup` to add or update settings.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `~/.neuroflow/integrations.json`, `.neuroflow/integrations.json` (key names only), `~/.neuroflow/user.yaml` |
| Writes | `~/.neuroflow/integrations.json` or `.neuroflow/integrations.json`, `~/.neuroflow/user.yaml`, `~/.neuroflow/flowie/integrations.json` (after you confirm a sync) |

---

## Related

- [Integrations guide →](../integrations.md)
- [`/neuroflow`](neuroflow.md) — also offers to run setup on first use
