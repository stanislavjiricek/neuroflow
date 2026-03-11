---
title: /idk
---

# `/neuroflow:idk`

**Personal support companion — decompress, talk things through, or just take a break.**

`/idk` is a quiet moment in the research workflow. Not a to-do list. Not a project audit. Just a space to say *I don't know* and have someone listen.

---

## When to use it

- You're burned out or overwhelmed by deadlines
- You have too many things in your head and don't know where to start
- You want to break down an impossibly long task list
- You just want to chat — no research agenda

---

## What it does

Claude reads `project_config.md` and `flow.md` for context, then opens with a simple, warm check-in. No structure, no bullet points — just conversation.

Claude listens first, validates before suggesting anything, and only helps you untangle things **if you want that**. It won't push you back toward work.

| Signal | How Claude responds |
|---|---|
| "I have so much to do" | Helps you breathe, then optionally breaks it down |
| "I don't know where to start" | Gently surfaces the one next thing |
| "I'm so tired" | Validates — asks what kind of tired, doesn't try to fix |
| "Nothing is working" | Listens fully before offering any frame |
| "I just needed to say that" | Stays present — doesn't offer solutions |
| "Can you help me figure this out?" | Moves to untangling mode |

If you want to untangle things, Claude asks what feels heaviest, what actually has to happen today, and helps you find just the one next step — not the whole plan.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md` (if they exist) |
| Writes | `.neuroflow/sessions/YYYY-MM-DD.md` — a one-line timestamp only; no details logged |

---

## Related commands

- [`/quiz`](quiz.md) — a lighter break with neuroscience trivia
