---
name: notes
description: Lightweight live note-taking — capture notes during a meeting, talk, or session, then reformat them into a clean structured document.
phase: notes
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/notes/flow.md
  - skills/phase-notes/SKILL.md
writes:
  - .neuroflow/notes/
  - .neuroflow/notes/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /notes

Read the `neuroflow:phase-notes` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Captures live notes during a meeting, talk, lab session, or supervisory meeting, then reformats them into a clean structured document.

---

## Steps

### 1 — Setup

Ask a few quick questions before starting:
- What is the context? (meeting, conference talk, lab session, supervisory meeting, other)
- Who is involved? (speakers, attendees — optional)
- Location or event name? (optional)

### 2 — Live capture

Tell the user: "Ready. Type your notes — as rough as you like. Send them in any order, one chunk at a time. When you're done, say 'done'."

Accept freeform input prompts until the user says "done" or "finish". Do not restructure anything yet — just acknowledge each input and wait for the next.

**Auto-save:** After every 3 prompts received, write all captured notes so far to `.neuroflow/notes/notes-[context]-[date]-draft.md` (overwriting any previous draft). Notify the user with a brief inline message: `💾 Auto-saved draft — [N] entries captured so far.` (where N is the total number of entries captured in this session). Continue capturing without interruption.

### 3 — Reformat

Once done, reformat everything into a clean structured document:
- Header: context, date, participants
- Body: organised by topic or chronology, cleaned up but faithful to the content
- Action items section (if any were mentioned)

### 4 — Save

Save as `notes-[context]-[date].md` in `.neuroflow/notes/`. Delete the draft file `notes-[context]-[date]-draft.md` if it exists, since the final formatted file supersedes it.

---

## At end

- Update `.neuroflow/notes/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
