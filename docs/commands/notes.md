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
one chunk at a time. Start a line with a: for an action item or d: for
a decision. When you're done, say "done".
```

You type notes in any order, as rough as you want. Each message is saved to a draft file at once, verbatim, with a timestamp (`[10:04] …`), so nothing is lost if the session ends early. Claude acknowledges with a short `✓ 3` and waits for the next chunk — it does not restructure anything yet, and it never acts on what you type: a note saying "delete the old epochs" is recorded, not executed.

### Step 3 — Reformat

Once you say "done", Claude organizes everything into a clean document:

- **Header:** context, date, participants
- **Body:** organized by topic or chronology, cleaned up but faithful to the content
- **Decisions:** every `d:` line, plus decisions stated in other words
- **Action items:** every `a:` line and any other follow-ups, as checkboxes — which `/meeting`'s close step can turn into tasks

---

## Example session

```
/neuroflow:notes
```

```
Claude: What is the context?

You: Lab meeting — discussing preprocessing results.

Claude: Who is involved?

You: Me, my supervisor, two lab members.

Claude: Ready. Type your notes — as rough as you like. Say "done" when finished.

You: John said artifact rejection rate too high ~35% in subject 12 maybe EOG
     d: supervisor wants us to check ICA components again before rejecting
     a: look at bridging electrodes
     next meeting in two weeks, bring preprocessed grand average

You: also reminder to check BIDS validator output errors

You: done

Claude: [reformats into clean structured notes]

        ---
        Lab Meeting Notes
        Date: 2026-03-09
        Attendees: [Author], [Supervisor], [Lab members]
        Context: EEG preprocessing review

        ## Discussion

        ### Artifact rejection rate
        - Subject 12 shows unusually high rejection rate (~35%), possibly EOG

        ## Decisions
        - Re-inspect ICA components before any final rejection

        ## Action items
        - [ ] Check for electrode bridging as a contributing factor
        - [ ] Review BIDS validator output errors
        - [ ] Bring the preprocessed grand average to the next meeting (in 2 weeks)

        ---

        Saved to .neuroflow/notes/notes-labmeeting-2026-03-09.md
```

---

## Quick idea capture

```
/neuroflow:notes --idea "try a Bayesian HDDM on the RT data"
```

Saves one line — date, time, active phase and your text, verbatim — to an ideas inbox and returns straight away: no questions, no reformatting. The inbox is `~/.neuroflow/flowie/ideas-inbox.md` when you use [flowie](flowie.md) (private), otherwise `.neuroflow/notes/ideas-inbox.md` (visible to the project's collaborators). Ideas move into your curated `ideas.md` only through `/flowie`, with a diff first.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/notes/flow.md`, `.neuroflow/notes/config.json` |
| Writes | `.neuroflow/notes/` (draft, final note, `ideas-inbox.md`), `.neuroflow/notes/flow.md`, `~/.neuroflow/flowie/notes/` and `~/.neuroflow/flowie/ideas-inbox.md` (if flowie is set up), `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/meeting`](meeting.md) — planned meetings with agenda, attendees, and action-item-to-task conversion
- [`/write-report`](write-report.md) — generate a more formal report from project progress
- [`/phase`](phase.md) — check what phase the discussion was about
