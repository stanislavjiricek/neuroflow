---
title: /notes
---

# `/neuroflow:notes`

**Live note-taking — capture rough input and reformat it into a clean structured document.**

`/notes` is designed for real-time use during meetings, conference talks, lab sessions, or supervisory meetings. You type notes as rough as you like, then Claude reformats everything into a clean, structured document.

---

## When to use it

- During a lab meeting or supervisory session
- At a conference talk
- During a data collection session (to capture observations)
- Any time you want to capture freeform thoughts and turn them into clean notes

---

## How it works

### Step 1 — Quick setup

Claude asks three short questions:

- **Context?** (meeting, conference talk, lab session, supervisory meeting, other)
- **Who is involved?** (speakers, attendees — optional)
- **Location or event name?** (optional)

### Step 2 — Live capture

Claude switches to capture mode:

```
Ready. Type your notes — as rough as you like. Send them in any order,
one chunk at a time. When you're done, say "done".
```

You type notes in any order, as rough as you want. Claude just acknowledges and waits for the next chunk — it does not restructure anything yet.

### Step 3 — Reformat

Once you say "done", Claude organizes everything into a clean document:

- **Header:** context, date, participants
- **Body:** organized by topic or chronology, cleaned up but faithful to the content
- **Action items:** any tasks or follow-ups mentioned

---

## Example session

```
/neuroflow:notes
```

```
Claude: What is the context?

You: Lab meeting — discussing preprocessing results.

Claude: Who is involved?

You: Me, supervisor (Dr. Novak), two lab members.

Claude: Ready. Type your notes — as rough as you like. Say "done" when finished.

You: John said artifact rejection rate too high ~35% in subject 12 maybe EOG
     dr novak wants us to check ICA components again before rejecting
     someone mentioned we should look at bridging electrodes
     next meeting in two weeks, bring preprocessed grand average

You: also reminder to check BIDS validator output errors

You: done

Claude: [reformats into clean structured notes]

        ---
        Lab Meeting Notes
        Date: 2026-03-09
        Attendees: [Author], Dr. Novak, [Lab members]
        Context: EEG preprocessing review

        ## Discussion

        ### Artifact rejection rate
        - Subject 12 shows unusually high rejection rate (~35%)
        - Action: Re-inspect ICA components for sub-12 before final rejection
        - Action: Check for electrode bridging as a contributing factor

        ### BIDS validation
        - Action: Review BIDS validator output errors

        ## Next steps
        - Next meeting in 2 weeks
        - Bring preprocessed grand average for review

        ---

        Saved to .neuroflow/notes/notes-labmeeting-2026-03-09.md
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/notes/flow.md` |
| Writes | `.neuroflow/notes/`, `.neuroflow/notes/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/write-report`](write-report.md) — generate a more formal report from project progress
- [`/phase`](phase.md) — check what phase the discussion was about
