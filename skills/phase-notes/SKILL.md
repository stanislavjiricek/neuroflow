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

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- Save the final formatted notes to `.neuroflow/notes/notes-[date].md`
- Keep the raw capture separate from the reformatted version if both are useful
