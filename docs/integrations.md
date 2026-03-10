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

## Credential storage

When you run `/neuroflow:setup`, credentials are saved to `.neuroflow/integrations.json`:

```json
{
  "pubmed": {
    "PUBMED_EMAIL": "you@example.com"
  },
  "miro": {
    "MIRO_ACCESS_TOKEN": "eyJ..."
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

You can always re-run `/neuroflow:setup` to add or update credentials at any time.
