---
title: Installation
---

# Installation

neuroflow is a plugin for [Claude Code](https://claude.ai/code), and only for Claude Code. Its commands, skills, agents and its optional mod layer all run inside Claude Code.

---

## From the marketplace

In Claude Code v2.1.275 or later, one command adds the marketplace and installs the plugin:

```
/plugin install neuroflow --marketplace stanislavjiricek/neuroflow
```

Or in two steps, from a terminal:

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

or inside Claude Code:

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```

After a new version arrives, run `/neuroflow:migrate` once in each project — see [Upgrading](upgrading.md).

---

## Local development

Clone the repo and point Claude Code at it:

```bash
git clone https://github.com/stanislavjiricek/neuroflow
claude --plugin-dir ./neuroflow
```

This is the recommended way to contribute or test changes before they are released. The repo's `CLAUDE.md` describes its structure and conventions.

---

## Verify installation

Open any project folder in Claude Code and run:

```
/neuroflow:neuroflow
```

You should see neuroflow scan your project and offer to set up `.neuroflow/` project memory.

---

## MCP server requirements

neuroflow uses three MCP (Model Context Protocol) servers that are launched automatically via `npx`. No manual installation is needed — they are pulled from npm on first use.

| Server | npm package | Purpose |
|---|---|---|
| PubMed / bioRxiv | `paper-search-mcp-nodejs` | Literature and preprint search |
| Context7 | `@upstash/context7-mcp` | Library documentation lookup |
| Sequential thinking | `@modelcontextprotocol/server-sequential-thinking` | Structured multi-step reasoning |

None needs credentials. Miro and Zotero are optional servers you add yourself — see [Integrations](integrations.md).

---

## System requirements

| Requirement | Notes |
|---|---|
| Claude Code | v2.1.271 or later — older versions cannot load the plugin, because its settings offer fixed choices (`userConfig` options). The one-step `/plugin install … --marketplace` needs v2.1.275 or later. The optional mod is tested from v2.1.292; `/neuroflow:doctor` warns on older versions |
| Node.js | Required for the MCP servers via `npx` |
| Python 3.10+ | Recommended. `/neuroflow` and `/migrate` run small standard-library scripts; without Python, Claude does the same steps by hand. Also needed for analysis scripts you run |

---

## Uninstall

```bash
claude plugin uninstall neuroflow
```

---

## Upgrading from an older version

Older neuroflow versions also wrote a neuroflow block into `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md` and `AGENTS.md`. Current versions keep a single static block in each project's `.claude/CLAUDE.md`. Run `/neuroflow:migrate` in a project to bring its memory up to the current format; it also points out the old blocks and offers to remove them.
