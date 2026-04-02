---
name: phase-notes
description: Phase guidance for the neuroflow /notes command. Loaded automatically when /notes is invoked to orient agent behavior, relevant skills, and workflow hints for the notes phase.
---

# phase-notes

The notes phase captures live notes during a meeting, talk, or session, then reformats them into a clean structured document.

## Approach

- Accept freeform input without correcting or restructuring until the user signals they are done
- Do not prompt for formatting, completeness, or clarification during capture — just record
- Only reformat when explicitly asked, or when the user signals the session is over
- Auto-save the raw capture to a draft file every 3 prompts to prevent data loss in long sessions

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- Auto-save raw notes to `.neuroflow/notes/notes-[date]-draft.md` after every 3 prompts; notify the user briefly each time
- Save the final formatted notes to `.neuroflow/notes/notes-[date].md`
- Delete the draft file once the final formatted file has been written
- Keep the raw capture separate from the reformatted version if both are useful
- After saving, check `.neuroflow/notes/config.json` for `sync_to_flowie`; if `true` (default), offer to copy the note to `.neuroflow/flowie/notes/` for GitHub sync
- `.neuroflow/notes/config.json` stores per-project defaults: `default_type`, `default_speaker`, `default_project`, and `sync_to_flowie`; create it with standard defaults on first run if absent

## Slash command

`/neuroflow:notes` — runs this workflow as a slash command.
