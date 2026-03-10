---
title: Installation
---

# Installation

neuroflow is a [Claude Code](https://claude.ai/code) plugin. You need Claude Code installed before proceeding.

---

## From the marketplace

The easiest way to install neuroflow:

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

Or from within Claude Code:

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```

---

## Local development

Clone the repo and point Claude Code at it:

```bash
git clone https://github.com/stanislavjiricek/neuroflow
claude --plugin-dir ./neuroflow
```

This is the recommended way to contribute or test changes before they are released.

---

## Verify installation

Once installed, open any project folder and run:

```
/neuroflow:start
```

You should see neuroflow scan your project and offer to set up `.neuroflow/` project memory.

---

## MCP server requirements

neuroflow uses four MCP (Model Context Protocol) servers that Claude Code launches automatically via `npx`. No manual installation is needed — they are pulled from npm on first use.

| Server | npm package | Purpose |
|---|---|---|
| PubMed | `pubmed-mcp-server` | Literature search on NCBI PubMed |
| bioRxiv | `paper-search-mcp-nodejs` | Preprint search on bioRxiv |
| Miro | `@k-jarzyna/mcp-miro` | Visual collaboration boards |
| Context7 | `@upstash/context7-mcp` | Library documentation lookup |

Two of these require credentials — see the [Integrations](integrations.md) page for how to configure them.

---

## System requirements

| Requirement | Notes |
|---|---|
| Claude Code | Any recent version |
| Node.js | Required for MCP servers via `npx` |
| Python | Optional — only needed if you run preprocessing / analysis scripts Claude generates |

---

## Uninstall

```bash
claude plugin uninstall neuroflow
```
