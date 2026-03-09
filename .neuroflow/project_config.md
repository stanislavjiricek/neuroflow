# neuroflow — project config

**Project:** neuroflow Claude Code plugin
**Plugin version:** 0.1.1
**Phase:** active development
**Repo:** https://github.com/stanislavjiricek/neuroflow

## Description

End-to-end agentic research workflow plugin for neuroscience teams. Covers the full pipeline from hypothesis formulation to manuscript submission.

## Structure

- **skills/** — agent-invoked skills (SKILL.md per folder)
- **commands/** — slash commands (one .md per command)
- **agents/** — autonomous agent definitions
- **hooks/** — event hooks (hooks.json)
- **.claude-plugin/** — plugin manifest (plugin.json, marketplace.json)

## Tools & tech

- Claude Code plugin system
- MCP: bioRxiv, PubMed, Miro, Context7
- Hooks: PostToolUse (ruff formatter, session logger)

## Key decisions

See `decisions.md`.
