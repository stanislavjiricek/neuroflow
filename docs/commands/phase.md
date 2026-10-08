---
title: /phase
---

# `/neuroflow:phase`

**Show the current project phase and optionally switch to a different one.**

`/phase` gives you a quick status overview — what phase you're in, what phases have been worked on, and when the last session was. It also lets you switch phase from a menu if you want to jump to a different part of the pipeline.

---

## When to use it

- You want to quickly check where you are in the project
- You want to switch from one phase to another
- You're orienting yourself at the start of a session (though `/neuroflow` does this too)

---

## What it does

1. Reads `project_config.md` to get the current active phase and the phases recommended at setup
2. Checks which phase subfolders exist in `.neuroflow/` and when the last session was
3. Prints the phase map — `◉` current, `●` visited, `→` recommended, `○` not started — followed by upcoming deadlines from `timeline.md`, a one-line living-paper status (only with `/paper --auto` on), any long runs not yet reviewed, and your personality mode
4. For the current phase, lists its expected inputs and outputs (`[x]` present, `[ ]` missing — information only, never a gate) and the commands that usually come next
5. Asks whether to switch, as a **menu**: move with the arrow keys and press Enter, or click an option. "Stay in the current phase" comes first, then the next recommended phases; **Other** lets you type any phase.
6. If you pick a different phase, it changes `active_phase` in `project_config.md` — that one value — logs the switch, and suggests the new phase's command.

With the neuroflow mod active, the mod answers `/neuroflow:phase` itself: the same map with a picker (arrow keys and Enter, or a click), and the switch is written by code. Without the mod, Claude asks the same question with Claude Code's question menu.

The switch never edits `.claude/CLAUDE.md`: its neuroflow block is static and points at `project_config.md`, so nothing goes stale.

---

## Example session

```
/neuroflow:phase
```

```
Phase map — Last session: 2026-03-08

  ● ideation
  ● experiment
  ● data
  ◉ data-preprocess     ← current
  → data-analyze        ← recommended
  → paper               ← recommended
  ○ preregistration
  ...

Personality mode: 🔍 Critic (critic, team default)
Next: /neuroflow:data-analyze

Switch phase?
  ▸ Stay in data-preprocess
    data-analyze
    paper
    Other…

You: (arrow down, Enter) data-analyze

Claude: ✅ Active phase updated to: data-analyze

        Run /neuroflow:data-analyze to continue.
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sessions/`, `.neuroflow/timeline.md`, `.neuroflow/paper/` (only with `/paper --auto` on), `.neuroflow/*/runs.md`, `~/.neuroflow/user.yaml`, `~/.neuroflow/local-projects.json` (flowie sync) |
| Writes | only when you switch: `active_phase` in `project_config.md`, a session line, a `reasoning/general.jsonl` entry, and your flowie project registry (if linked) |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — full project status + session start
- [`/sentinel`](sentinel.md) — audit project for consistency issues
