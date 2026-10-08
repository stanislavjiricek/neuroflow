---
title: /dashboard
---

# `/neuroflow:dashboard`

**The project at a glance: phase map, upcoming deadlines, integrity state, task board and the running autoresearch
loop.**

---

## With the neuroflow mod

The dashboard opens as a pane drawn by code — no model turn, no tokens — docked beside the conversation in a wide
terminal, or inline above the prompt otherwise. It stays current as files change.

| Key | Tab |
|---|---|
| `p` | **Phase** — the phase map (`●` current, `✔` visited, `○` recommended) and the next step; `s` opens the phase picker |
| `d` | **Deadlines** — dated rows of `.neuroflow/timeline.md` and the ethics expiry, with days left |
| `i` | **Integrity** — ethics approval, frozen preregistration, read-only raw-data folders, config problems; `f` freezes the preregistration after you confirm, `v` re-checks its hashes, `u` unfreezes it with a reason |
| `t` | **Tasks** — task files per board column |
| `l` | **Loop** — the running autoresearch loop: iteration, best snapshot, a quality sparkline and its open questions; `r` refreshes |

`/neuroflow:dashboard loop` opens it on a tab. The one-line band above the prompt opens it with `d`. When the project is on an
older neuroflow than the one installed, an `Update` line sits under the title and `m` runs [`/neuroflow:migrate`](migrate.md).

Every symbol comes with a word, so the dashboard reads correctly without colour and with a screen reader.

## Without the mod

The same overview is printed once as a compact text block, read from the same files. Nothing is written. When the
project is on an older neuroflow version than the one installed, an `Update` line names [`/neuroflow:migrate`](migrate.md);
with the mod, the band above the prompt and the dashboard pane say the same.

---

## Files read

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/timeline.md`, `.neuroflow/ethics/status.md`, `.neuroflow/preregistration/status.md`, `.neuroflow/tasks/`, `.neuroflow/{phase}/autoresearch-loops.md` and the loops' `results.md` / `report.md` |
| Writes | nothing, unless you freeze or unfreeze the preregistration from the integrity tab: then `freeze.py` writes `.neuroflow/preregistration/status.md`, the banners and `deviations.md`, and the mod adds a session line and a reasoning entry |

## Related

- [`/phase`](phase.md) — the phase map and phase switching (a picker with the mod)
- [`/tasks`](tasks.md) — work the task board
- [The neuroflow mod](../concepts/mods.md) — what the mod adds and how to turn it on or off
