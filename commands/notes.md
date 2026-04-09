---
name: notes
description: Lightweight live note-taking — capture notes during a meeting, talk, or session, then reformat them into a clean structured document.
phase: notes
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/notes/flow.md
  - .neuroflow/notes/config.json
  - skills/phase-notes/SKILL.md
writes:
  - .neuroflow/notes/
  - .neuroflow/notes/flow.md
  - .neuroflow/notes/config.json
  - .neuroflow/flowie/notes/
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /notes

Read the `neuroflow:phase-notes` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Captures live notes during a meeting, talk, lab session, or supervisory meeting, then reformats them into a clean structured document.

---

## Steps

### 0 — Load config

Before asking the context question, read `.neuroflow/notes/config.json` if it exists. Use `default_type` as the pre-filled suggestion for context, and `default_speaker` as the optional pre-fill for speaker. If the file does not exist, proceed with no defaults — it will be created at Step 4.

### 1 — Setup

Ask a few quick questions before starting:
- What is the context? (meeting, conference talk, lab session, supervisory meeting, other) — suggest `default_type` from config if set
- Who is involved? (speakers, attendees — optional) — suggest `default_speaker` from config if set
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

If `.neuroflow/notes/config.json` does not exist, create it now with standard defaults, using the current session's context as `default_type`:

```json
{
  "sync_to_flowie": true,
  "name_format": "{type}-{date}",
  "default_type": "{context}",
  "default_project": null,
  "default_speaker": null,
  "types": ["meeting", "conference-talk", "lab-session", "supervisory", "freeform"]
}
```

### 5 — Flowie sync

If `.neuroflow/flowie/` does not exist, skip this step silently.

Read `.neuroflow/notes/config.json`. If `sync_to_flowie` is `true` (default), offer:

```
Sync this note to your flowie repo? [Y/n]
```

If the user confirms (or presses enter):

1. Determine destination filename: `{YYYY-MM-DD}-{context}.md` (using today's date and the session context).
2. If `.neuroflow/flowie/notes/` does not exist, create it with a `.flow` index file:
   ```markdown
   # notes

   | file | description |
   |---|---|
   ```
3. Write the final formatted note to `.neuroflow/flowie/notes/{filename}`.
4. Append a row to `.neuroflow/flowie/notes/.flow`:
   ```
   | {filename} | {context} — {date} |
   ```

The existing auto-sync hook will push the note to GitHub automatically.

If `sync_to_flowie` is `false`, skip without prompting.

---

### 6 — Wiki ingest offer

If `.neuroflow/flowie/wiki/` exists (the user has a personal wiki set up), offer after the flowie sync step:

```
Extract key insights into your personal wiki? Run:
  /flowie --wiki-ingest .neuroflow/notes/{filename}
```

This is a nudge only — do not run the ingest automatically. The user chooses when to do it.

---

## At end

- Update `.neuroflow/notes/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
