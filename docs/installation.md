---
title: Installation
---

# Installation

neuroflow is a plugin for [Claude Code](https://claude.ai/code) and [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-finding-installing). Install it with whichever AI assistant you use.

---

## Claude Code

### From the marketplace

The easiest way to install neuroflow in Claude Code:

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

Or from within an interactive Claude Code session:

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```

### Local development (Claude Code)

Clone the repo and point Claude Code at it:

```bash
git clone https://github.com/stanislavjiricek/neuroflow
claude --plugin-dir ./neuroflow
```

This is the recommended way to contribute or test changes before they are released.

---

## GitHub Copilot CLI

neuroflow installs natively into the GitHub Copilot CLI — no workarounds needed.

### Install directly from GitHub

```bash
copilot plugin install stanislavjiricek/neuroflow
```

Or from within an interactive Copilot session:

```
/plugin install stanislavjiricek/neuroflow
```

### Install from a registered marketplace

If `stanislavjiricek/neuroflow` is available in a registered marketplace (e.g. `awesome-copilot`):

```bash
copilot plugin install neuroflow@awesome-copilot
```

### Uninstall (Copilot)

```bash
copilot plugin uninstall neuroflow
```

---

## Verify installation

Once installed (in either tool), open any project folder and run:

```
/neuroflow:neuroflow
```

You should see neuroflow scan your project and offer to set up `.neuroflow/` project memory.

---

## MCP server requirements

neuroflow uses four MCP (Model Context Protocol) servers that are launched automatically via `npx`. No manual installation is needed — they are pulled from npm on first use.

| Server | npm package | Purpose |
|---|---|---|
| PubMed / bioRxiv | `paper-search-mcp-nodejs` | Literature and preprint search |
| Miro | `@k-jarzyna/mcp-miro` | Visual collaboration boards |
| Context7 | `@upstash/context7-mcp` | Library documentation lookup |

One of these requires credentials — see the [Integrations](integrations.md) page for how to configure them.

---

## System requirements

| Requirement | Notes |
|---|---|
| Claude Code **or** GitHub Copilot CLI | Any recent version |
| Node.js | Required for MCP servers via `npx` |
| Python | Optional — only needed if you run preprocessing / analysis scripts the AI generates |

---

## Uninstall (Claude Code)

```bash
claude plugin uninstall neuroflow
```

---

## Using on other platforms

neuroflow's skills and commands can also be adapted for other AI coding assistants.

### GitHub Copilot (VS Code extension)

The VS Code Copilot extension does not share the same plugin system as the Copilot CLI, but you can make neuroflow's instructions available to Copilot agent mode via instruction files.

**Option 1 — Project-level instructions (recommended):**

Create a `.github/copilot-instructions.md` file in your project root and paste the contents of your relevant neuroflow skill files into it. Copilot agent mode reads this file automatically when working in the project.

```markdown
<!-- .github/copilot-instructions.md -->
<!-- Paste relevant neuroflow skill content here -->
```

**Option 2 — VS Code user instructions:**

Open VS Code Settings → search for `github.copilot.chat.codeGeneration.instructions` → add a new instruction entry pointing to any neuroflow SKILL.md file (absolute path).

**Option 3 — `.instructions.md` files in `.github/instructions/`:**

VS Code Copilot also reads `*.instructions.md` files from `.github/instructions/`. Copy individual skill files there and rename them with the `.instructions.md` extension.

**Limitations on VS Code Copilot extension:**
- No native slash command routing — commands must be triggered by natural language
- No automatic `.neuroflow/` project memory creation — do this manually or prompt Copilot Agent to create it
- MCP server connections work the same way (configured in VS Code MCP settings)

---

### Cursor

Cursor supports custom AI rules via the `.cursor/rules/` directory (formerly `.cursorrules`). You can expose neuroflow skills to Cursor's AI assistant.

**Setup:**

1. Create a `.cursor/rules/` directory in your project root
2. Copy the neuroflow skill files you want Cursor to follow into `.cursor/rules/`, renaming each to `*.mdc`:

```bash
# Example: add the neuroflow-core and review-neuro skills
cp path/to/neuroflow/skills/neuroflow-core/SKILL.md .cursor/rules/neuroflow-core.mdc
cp path/to/neuroflow/skills/review-neuro/SKILL.md .cursor/rules/review-neuro.mdc
```

3. Cursor will include these rules when the AI generates responses in agent mode.

**Triggering commands in Cursor:**

Cursor does not have a `/command` routing system. Instead, refer to commands by natural language:
- "Follow the neuroflow flowie skill and set up a flowie for this project"
- "Use the review-neuro skill to review this manuscript"

**Project memory in Cursor:**

Ask Cursor's agent to run the neuroflow interview manually:
- "Read the neuroflow-core skill rules and set up `.neuroflow/` project memory for this project"

**Limitations on Cursor:**
- No automatic plugin installation — copy skill files manually
- No marketplace integration
- Command routing relies entirely on natural language + rules files
