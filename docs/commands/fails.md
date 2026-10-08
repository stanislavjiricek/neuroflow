---
title: /fails
---

# `/neuroflow:fails`

**Log dissatisfaction — record what went wrong in plugin behavior, science quality, or interaction experience.**

`/fails` captures things that didn't work as expected and optionally opens a GitHub issue for the neuroflow team.

---

## When to use it

- A phase acted unexpectedly or produced wrong outputs
- An analysis ran on the wrong data or used a wrong method
- The interaction was confusing, circular, or produced unhelpful prompts
- You want to report a bug to the neuroflow team directly from the session

---

## Three categories

| Category | What belongs here |
|---|---|
| **Core** | Plugin behavior problems — unexpected phase actions, files written to wrong locations, loops without progress, ignored instructions, corrupted project state |
| **Science** | Scientific quality problems — wrong paper retrieved, analysis on wrong data, incorrect axes, violated statistical assumptions, misapplied method |
| **UX** | Interaction quality problems — confusing prompts, output too verbose or sparse, wrong suggested next steps, circular conversation, too many questions |

If the complaint spans categories, Claude asks which is primary — or splits it across files if both aspects are equally important.

---

## What it does

1. **Read existing fails** — reads `.neuroflow/fails/core.md`, `science.md`, `ux.md` if they exist; creates the folder and files if they don't
2. **Listen** — asks what went wrong; listens in full before categorising
3. **Write the entry** — appends to the appropriate file with date, context, description, and expected behaviour
4. **Offer to report** — asks if you want a GitHub issue; if yes, drafts it, shows it to you, and opens the pre-filled issue page in your browser only after you say so (or just prints the link)

Besides `/fails`, neuroflow notices frustration or problem signals in any message, in any language, and adds a short paraphrased line to `fails/`. If you opted in to issue drafts during `/neuroflow` (stored in your own `~/.neuroflow/user.yaml`), it also offers a draft — nothing is opened without your yes, and nothing is recorded during `/idk`.

---

## GitHub issue format

Issues are drafted for `https://github.com/stanislavjiricek/neuroflow/issues/new` with a pre-filled title and body — you review and submit them yourself:

```
## What went wrong
<description>

## Expected behaviour
<expected>

## Context
Phase: <phase>
Date: <date>
Plugin version: <version>
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/fails/` |
| Writes | `.neuroflow/fails/core.md`, `.neuroflow/fails/science.md`, `.neuroflow/fails/ux.md`, `.neuroflow/fails/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

!!! note
    `/fails` requires `.neuroflow/` to exist. Run `/neuroflow:neuroflow` first if you haven't set it up.

---

## Related commands

- [`/sentinel`](sentinel.md) — audits `.neuroflow/` for structural issues
- [`/neuroflow`](neuroflow.md) — full project status and session start
