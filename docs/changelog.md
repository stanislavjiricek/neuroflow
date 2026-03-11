---
title: Changelog
---

# Changelog

---

## 0.1.2

- **12 phase skills** — `neuroflow:phase-ideation` through `neuroflow:phase-write-report`, each loaded automatically by its corresponding command to orient agent approach, relevant skills, and workflow hints

---

## 0.1.1

- **Full research pipeline** — 15 commands from `/start` through `/paper-review`, each writing to `.neuroflow/` project memory
- **`neuroflow:neuroflow-core`** — shared lifecycle and `.neuroflow/` folder spec that every command and agent follows; commands now automatically append significant decisions to `.neuroflow/reasoning/{phase}.json`
- **`scholar`**, **`sentinel`**, **`sentinel-dev`** agents
- `sentinel` checks plugin version against `project_config.md` and flags when the plugin has been updated; both sentinels clear their report to "All clear" after fixing issues
- `project_config.md` now tracks `plugin_version` — kept in sync with `plugin.json` by `/start` and `/sentinel`
- MCP servers declared in `plugin.json`: PubMed, bioRxiv, Miro, Context7

---

## 0.1.0

- Initial release
