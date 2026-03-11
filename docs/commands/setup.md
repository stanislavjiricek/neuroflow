---
title: /setup
---

# `/neuroflow:setup`

**Interactive credential wizard for MCP integrations.**

`/setup` guides you through connecting the neuroflow MCP integrations — PubMed for literature search and Miro for visual collaboration. It stores credentials securely in `.neuroflow/integrations.json`, which is git-ignored by default.

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
Integration   Status
───────────   ──────
PubMed        ❌ not configured
bioRxiv       ✅ no credentials needed
Miro          ❌ not configured
Context7      ✅ no credentials needed
```

### Step 2 — PubMed setup

PubMed requires an email address so NCBI can contact you if there are issues with automated queries. **Any valid email works** — it does not need to match an NCBI account.

```
Enter your email for PubMed (or press Enter to skip):
> you@example.com
```

The email is validated for `@` format. Up to 3 attempts before skipping.

### Step 3 — Miro setup

Miro requires a personal access token. The wizard tells you exactly how to get one:

1. Go to [https://miro.com/app/settings/user-profile/apps](https://miro.com/app/settings/user-profile/apps)
2. Click **Create new app** (or use an existing one)
3. Under **Token**, click **Create token** — copy the token shown

```
Paste your Miro access token (or press Enter to skip):
> eyJhbGciOiJSUzI1NiJ9...
```

### Step 4 — Save credentials

Credentials are saved to `.neuroflow/integrations.json`:

```json
{
  "pubmed": {
    "PUBMED_EMAIL": "you@example.com"
  },
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJhbGciOiJSUzI1NiJ9..."
  }
}
```

!!! warning "This file is local only"
    `.neuroflow/integrations.json` is excluded from git (added to `.gitignore` by neuroflow). Your credentials are never committed to your repository.

---

## Activating credentials

After running `/setup`, export the env vars in your shell before starting Claude Code:

```bash
export PUBMED_EMAIL="you@example.com"
export MIRO_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiJ9..."
```

Add these to your shell profile (`~/.zshrc` or `~/.bashrc`) so they load automatically:

```bash
echo 'export PUBMED_EMAIL="you@example.com"' >> ~/.zshrc
echo 'export MIRO_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiJ9..."' >> ~/.zshrc
```

---

## What is automatic vs manual

| Step | Automatic | Manual |
|---|---|---|
| MCP server processes started | ✅ Claude Code launches them via `npx` | — |
| PubMed email entry | ✅ Prompted by `/setup` | — |
| Miro token entry | ✅ Prompted by `/setup` | ⚠️ You must create the token in Miro first |
| Miro OAuth browser login | ❌ Not implemented | Use a personal access token instead |
| Env var export | ❌ Not automatic | Run `export …` or add to shell profile |

---

## Reminder behavior

- If you skip setup and later run `/neuroflow:ideation` → **Explore literature**, the plugin detects that `PUBMED_EMAIL` is missing and offers to run `/setup` before searching.
- If you mention Miro and `MIRO_ACCESS_TOKEN` is missing, the same reminder appears.
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
