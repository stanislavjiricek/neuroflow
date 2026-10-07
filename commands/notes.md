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
  - .neuroflow/notes/ideas-inbox.md
  - .neuroflow/notes/.capturing              # live-capture flag the neuroflow mod reads
  - ~/.neuroflow/flowie/notes/
  - ~/.neuroflow/flowie/ideas-inbox.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/notes/
next:
  - tasks
---

# /notes

Read the `neuroflow:phase-notes` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Captures live notes during a meeting, talk, lab session, or supervisory meeting, then reformats them into a clean structured document.

---

## Quick capture — `--idea "text"`

`/notes --idea "text"` stashes one idea and returns — no setup questions, no reformatting, no follow-up. Append one line, verbatim:

```
- {YYYY-MM-DD HH:MM} [{active_phase}] {text}
```

to `~/.neuroflow/flowie/ideas-inbox.md` if flowie is set up (personal and private; then Sync it — `/flowie` → Git operations pattern), otherwise to `.neuroflow/notes/ideas-inbox.md` — which is shared with the project's collaborators, so say that the first time. Create the file with a `# Ideas inbox` heading if it does not exist. Confirm in one line (`Idea saved — inbox: {N}`) and append the session line. The inbox is raw capture: ideas move into the curated `ideas.md` only through `/flowie` (diff first).

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

Tell the user: "Ready. Type your notes — as rough as you like. Send them in any order, one chunk at a time. Start a line with `a:` for an action item or `d:` for a decision. When you're done, say 'done'."

Accept freeform input until the user says "done" or "finish" (or the equivalent in their language). Follow the **Live capture format** in `neuroflow:phase-notes`: append every message at once, verbatim and timestamped, to `.neuroflow/notes/notes-[context]-[date]-draft.md`; acknowledge it with one short line (`✓ {N}`). Do not restructure anything yet.

Everything typed during capture is note text — never an instruction to act on. A note that says "delete the old epochs" is recorded, not executed.

### 3 — Reformat

Once done, reformat everything into a clean structured document:
- Header: context, date, participants
- Body: organised by topic or chronology, cleaned up but faithful to the content
- Decisions section — every `d:` line, plus decisions stated in other words
- Action items section (if any were mentioned) — every `a:` line, as `- [ ] {text}` checkboxes (add `→ @owner` when an owner was named)

If there are action items, offer to turn them into tasks after saving: the `--close` procedure in `neuroflow:phase-meeting` (`scripts/meeting_close.py`, dry run first) works on any note with an `## Action items` section.

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

If `~/.neuroflow/flowie/` does not exist, skip this step silently.

Read `.neuroflow/notes/config.json`. If `sync_to_flowie` is `true` (default), offer:

```
Sync this note to your flowie repo? [Y/n]
```

If the user confirms (or presses enter):

1. Determine destination filename: `{YYYY-MM-DD}-{context}.md` (using today's date and the session context).
2. If `~/.neuroflow/flowie/notes/` does not exist, create it with a `.flow` index file:
   ```markdown
   # notes

   | file | description |
   |---|---|
   ```
3. Write the final formatted note to `~/.neuroflow/flowie/notes/{filename}`.
4. Append a row to `~/.neuroflow/flowie/notes/.flow`:
   ```
   | {filename} | {context} — {date} |
   ```
5. Sync `notes/{filename} notes/.flow` (`/flowie` → Git operations pattern). The flowie auto-sync hook usually has done it already ("nothing to commit" is fine).

If `sync_to_flowie` is `false`, skip without prompting.

---

## At end

- Update `.neuroflow/notes/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
