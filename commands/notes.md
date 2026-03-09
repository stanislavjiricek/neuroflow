---
name: notes
description: Lightweight live note-taking — capture notes during a meeting, talk, or session, then reformat them into a clean structured document.
phase: notes
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/notes/flow.md
writes:
  - .neuroflow/notes/
  - .neuroflow/notes/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /notes

Follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

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

### 3 — Reformat

Once done, reformat everything into a clean structured document:
- Header: context, date, participants
- Body: organised by topic or chronology, cleaned up but faithful to the content
- Action items section (if any were mentioned)

### 4 — Save

Save as `notes-[context]-[date].md` in `.neuroflow/notes/`.

---

## At end

- Update `.neuroflow/notes/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
