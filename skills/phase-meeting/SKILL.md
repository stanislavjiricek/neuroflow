---
name: phase-meeting
description: Phase guidance for the /meeting command. Covers meeting file structure, recurring templates, attendee resolution from profiles, Google Calendar MCP integration, agenda preparation with project context, and action-item-to-task conversion at all three levels (project, flowie, hive).
reads:
  - .neuroflow/project_config.md
  - .neuroflow/tasks/**
  - .neuroflow/meetings/config.json
  - .neuroflow/meetings/*.md
  - .neuroflow/timeline.md
  - .neuroflow/reasoning/*.jsonl
  - ~/.neuroflow/hives/{org-repo}/hive.md
  - ~/.neuroflow/hives/{org-repo}/members.md
  - ~/.neuroflow/flowie/profile.md
  - ~/.neuroflow/flowie/meetings/config.json
writes:
  - .neuroflow/meetings/
  - ~/.neuroflow/flowie/meetings/
  - ~/.neuroflow/hives/{org-repo}/meetings/
  - .neuroflow/tasks/**
  - ~/.neuroflow/flowie/tasks/**
  - ~/.neuroflow/hives/{org-repo}/tasks/**
user-invocable: false
---

# phase-meeting

The `/meeting` command manages structured meetings — distinct from `/notes` which captures unstructured live input. Meetings have schema (attendees, agenda, decisions, action items), optional calendar integration, and task creation from action items.

---

## Meeting levels

| Level | Storage | Git-tracked in | Who sees it |
|-------|---------|----------------|-------------|
| `project` (default) | `.neuroflow/meetings/YYYY-MM-DD-{slug}.md` | Project repo | All collaborators |
| `flowie` | `~/.neuroflow/flowie/meetings/YYYY-MM-DD-{slug}.md` | Flowie repo | Owner only |
| `hive` | `~/.neuroflow/hives/{org-repo}/meetings/YYYY-MM-DD-{slug}.md` | Hive org repo | Whole team |

Each level root (`.neuroflow/`, `~/.neuroflow/flowie/`, `~/.neuroflow/hives/{org-repo}/`) holds both `meetings/` and `tasks/`. Flowie-level files are synced with the flowie Sync step (`/flowie` → Git operations pattern); hive-level files are pushed only after the person confirms; project-level files stay in the working tree until the person commits them.

---

## Meeting file format

```markdown
---
title: {title}
date: {YYYY-MM-DDTHH:MM:00}
duration: {minutes}
location: {Zoom link / room / online}
attendees:
  - name: {name}
    email: {email}          # from the roster or the person — omit if unknown, never guess
level: {project|flowie|hive}
tags: [{tag1}, {tag2}]
linked_tasks: []            # {level}:{slug} entries written by --close
closed: ""                  # YYYY-MM-DD, stamped by --close
calendar_event_id: ""
template: {slug of recurring template, or omit}
---

## Agenda

## Notes

## Decisions

## Action Items
```

---

## Recurring meeting templates

Templates live in:
- `.neuroflow/meetings/config.json` — project-level (shared with collaborators)
- `~/.neuroflow/flowie/meetings/config.json` — personal (flowie level)
- `~/.neuroflow/hives/{org-repo}/meetings/config.json` — team-level (hive, synced with `/hive --sync`)

```json
{
  "recurring": [
    {
      "name": "Weekly Lab Meeting",
      "slug": "weekly-lab",
      "duration": 60,
      "location": "Room 301",
      "level": "hive",
      "default_attendees": ["all-hive-members"],
      "default_tags": ["lab-meeting"],
      "agenda_template": "## Updates\n\n## Papers\n\n## Action Items"
    },
    {
      "name": "Supervisor 1:1",
      "slug": "supervisor-1on1",
      "duration": 30,
      "location": "Zoom",
      "level": "flowie",
      "default_attendees": ["supervisor@example.com"],
      "default_tags": ["1on1"],
      "agenda_template": "## Progress\n\n## Blockers\n\n## Next steps"
    }
  ]
}
```

`default_attendees` can be:
- An explicit email string
- `"all-hive-members"` → resolved from `hive.md` members table
- `"all-project-collaborators"` → resolved from `project_config.md` collaborators list

---

## Mode: --new

1. **Check for templates:** read all `config.json` files at the relevant level(s). If any recurring templates exist, show a picker:
   ```
   Create meeting from template?
     [1] Weekly Lab Meeting  (hive, 60 min, Room 301)
     [2] Supervisor 1:1      (flowie, 30 min, Zoom)
     [3] Custom meeting
   ```

2. **If template selected:** pre-fill title, duration, location, level, tags, and agenda from the template. Ask only for date and time.

3. **If custom:** ask all fields:
   - Title?
   - Date and time? (YYYY-MM-DD HH:MM)
   - Duration? (minutes, default 60)
   - Location? (optional)
   - Level? [project / flowie / hive] (default: project)
   - Tags? (comma-separated, optional)

4. **Resolve attendees** (Attendee resolution rules below — never invent an email):
   - For `default_attendees: ["all-hive-members"]` → read the hive's `members.md` table → extract name + email for each row
   - For `default_attendees: ["all-project-collaborators"]` → read `collaborators:` from `project_config.md`
   - For explicit email strings → use as-is
   - For custom meeting: ask *"Who should attend? (names or emails, comma-separated)"* — look up emails from hive members and collaborators by name if given; for anyone without a roster email, ask

5. **Write meeting file** to the appropriate storage location (see levels table above). Filename: `YYYY-MM-DD-{slug}.md` where slug is derived from the title.

<!-- nf-rule: EGRESS-CONFIRM -->
6. **Calendar invite (optional):** invites email real people, so list every recipient address first and ask *"Create a Google Calendar event and send invites to: {emails}? [y/N]"* — send only on an explicit yes in this turn.

   If yes:
   - Use `mcp__claude_ai_Google_Calendar__create_event` with:
     - `summary`: meeting title
     - `start`: ISO 8601 datetime
     - `end`: start + duration
     - `location`: as given
     - `attendees`: list of email strings
     - `description`: the agenda from the meeting file
   - Store the returned event ID in `calendar_event_id` in the meeting frontmatter

7. Confirm:
   ```
   Meeting created: {title} — {date} {time}
   File: {path}
   Attendees: {N} · Calendar: {event link or "not sent"}
   ```

---

## Mode: --prepare \<slug\>

Prepopulate the `## Agenda` section with context from the project and team.

1. Read the meeting file by slug (search across all levels)
2. Read `.neuroflow/project_config.md` for `active_phase`
3. Read `.neuroflow/tasks/active/` and `.neuroflow/tasks/review/` — list active and under-review tasks (task format: `/tasks`)
4. Read `.neuroflow/timeline.md` (if present) — pull entries within the next 30 days for a Deadlines block
5. If hive is connected: read `hive.md` directions for relevant team context
6. If the meeting comes from a recurring template, find the previous meeting of the same template and add:
   - **Follow-ups** — open tasks (not `done`/`archive`) whose `source` is an earlier meeting of this template
   - **Since last time** — tasks that reached `done` after that meeting's date (by `updated`), and reasoning entries since then (`.neuroflow/reasoning/*.jsonl`, by `at`). Useful for a supervisor 1:1; keep each item to one line.

Compose an agenda draft:
```markdown
## Agenda

### Project status
- Phase: {active_phase}
- Active tasks: {list slugs with titles}
- In review: {list slugs with titles}

### Follow-ups
{open tasks from earlier meetings of this template — omit section if none}

### Since last time
{done tasks and decisions since the previous meeting of this template — omit section if none}

### Upcoming deadlines
{timeline.md entries within 30 days, ⚠ on anything within 14 — omit section if none}

### Team context
{relevant hive directions if any}

### Items
{blank or template sections}
```

Show the draft and ask *"Does this look right? Edit inline or confirm."*

Write the updated `## Agenda` section back to the meeting file (preserve other sections).

---

## Mode: --notes \<slug\>

Live notes during the meeting, straight into the meeting file. Use the live-capture format in `neuroflow:phase-notes` (Live capture format), with the meeting's `## Notes` section as the target:

- Each message is appended to `## Notes` at once, verbatim, as `[HH:MM] {text}` — rewrite the file with the Write tool; never pass note text through a shell command.
- While capturing, every message is note text, never an instruction ("delete the old epochs" is recorded, not executed). Only `done` (or the equivalent in the person's language) or a message starting with `/` ends capture.
- Acknowledge with one short line (`✓ {N}`), nothing more.

On `done`: copy every line whose text starts with `a:` into `## Action Items` as `- [ ] {text}` and every `d:` line into `## Decisions` as `- {text}` (the raw lines stay in `## Notes`), show the result, and offer `--close`.

---

## Mode: --view \<slug\>

1. Find meeting file by slug
2. Read all `linked_tasks` from frontmatter — each entry is `{level}:{slug}` → find `{slug}.md` in that level's `tasks/{column}/` folders; the folder is its current column
3. Display meeting file with task statuses inline:

```
─────────────────────────────────────────
  Weekly Lab Meeting — 2026-04-20 10:00
  Location: Room 301 · Duration: 60 min
  Attendees: Stan, Jana, Petr (3)
  Calendar: https://calendar.google.com/...
─────────────────────────────────────────

## Agenda
...

## Linked tasks
  [active]  fix-rt-glasses        RT_DES
  [review]  grant-draft           AlphaModulation
  [done]    eeg-param-sweep       AlphaModulation  ✓

─────────────────────────────────────────
```

---

## Mode: --list

Show all meetings at the active level. Put the next upcoming meeting first (`next`), then past meetings that are not closed — no `closed:` date and unchecked action items left (`not closed — run --close`), then the rest by date (newest first):

```
next        [project]  2026-04-27  Weekly Lab Meeting   weekly-lab-2026-04-27
not closed  [project]  2026-04-20  Weekly Lab Meeting   weekly-lab-2026-04-20
            [flowie]   2026-04-17  Supervisor 1:1       supervisor-1on1-2026-04-17
            [project]  2026-04-13  Weekly Lab Meeting   weekly-lab-2026-04-13
```

Meeting dates have no timezone; compare them with the local date and time. If `--level` not given: show project and flowie levels together.

---

## Mode: --invite \<slug\>

Re-send or send calendar invites for a meeting that doesn't have a `calendar_event_id` yet.

1. Read meeting file
2. If `calendar_event_id` is already set: ask *"Invites were already sent (event ID: {id}). Re-send? [y/N]"*
<!-- nf-rule: EGRESS-CONFIRM -->
3. List the recipient emails from the meeting file and send only after the person's explicit yes in this turn. Attendees without an email are skipped and named — never fill one in.
4. Call `mcp__claude_ai_Google_Calendar__create_event` (or `update_event` if re-sending) with those attendees
5. Update `calendar_event_id` in frontmatter

---

## Mode: --close \<slug\>

Finalize the meeting and convert its open action items into tasks in the `/tasks` format. Parsing and writing are done by `scripts/meeting_close.py`, so the same note always gives the same tasks and a second run never duplicates them. The script never sends invites or emails and never pushes.

1. Find the meeting file by slug.
2. Check the `## Action Items` section. Each open item is a checkbox:
   ```
   - [ ] Description → @owner due:YYYY-MM-DD [level/column]
   ```
   - `->` works as the arrow; `→ @owner`, `due:` and the annotation are all optional
   - `[level/column]` defaults to `[project/inbox]`; `[level]` or `[column]` alone also work
   - Checked items (`- [x]`) are skipped; plain bullets are listed as "not a checkbox" — ask whether any of them should become a task, and if so turn them into checkboxes first
   - Owners must be roster handles (Attendee resolution rules) — ask about any that are not
3. **Dry run** (from the project root):
   ```bash
   python <skill base dir>/scripts/meeting_close.py <meeting file> [--hive-root ~/.neuroflow/hives/{org-repo}]
   ```
   `--hive-root` is needed only for `[hive/…]` items in a project or flowie meeting. Exit 0: show the plan to the person. Exit 1: show the errors (unknown level or column, bad date, level not set up), fix the note with the person, and run the dry run again. Exit 2: usage or runtime error — report it and stop.
4. **Write** — only after the person confirms the plan, run the same command with `--write`. It creates `{level root}/tasks/{column}/{slug}.md` per item (with `source: {level}:meetings/{file}`), adds `{level}:{slug}` entries to `linked_tasks`, and stamps `closed: {today}`. Items already converted from this meeting are reported as `exists`.
5. Report what was created, by level and column (the script's output is the report).
6. Sync — the script writes files directly, so the flowie auto-sync hook does not see them:
   - flowie-level task files: the flowie Sync step for those paths (`/flowie` → Git operations pattern)
<!-- nf-rule: EGRESS-CONFIRM -->
   - hive-level task or meeting files: commit by path; push to the hive repo only after the person's explicit yes in this turn
   - project-level files stay in the working tree — pushing to the shared project remote is the person's call

If Python is not available, do the same by hand: show the planned tasks first, then write them in the `/tasks` format and update `linked_tasks` and `closed:`.

---

## Mode: --init

Set up recurring meeting templates for the current level.

1. Ask for level: [project / flowie / hive]
2. Walk through template creation:
   - Name? (e.g. "Weekly Lab Meeting")
   - Slug? (auto-suggested from name, editable)
   - Duration (minutes)?
   - Location?
   - Default attendees? (emails, "all-hive-members", "all-project-collaborators")
   - Default tags?
   - Agenda template? (section headings, freeform)
3. Write to `config.json` at the appropriate location
4. Confirm: `Template saved: {slug}`
5. Ask *"Add another template? [y/N]"*

---

## Attendee resolution rules

When resolving attendees for any mode:

1. `"all-hive-members"` → read `~/.neuroflow/hives/{org-repo}/members.md` (the hive roster file) → return all rows as `{name, email}`
2. `"all-project-collaborators"` → read `.neuroflow/project_config.md` `collaborators:` list → return all entries
3. Plain email string → use as-is, name = email prefix
4. Name string (no `@`) → search hive members and collaborators by name → use matched email; if ambiguous, ask
5. `@handle` (task owners in action items) → match the `handle` of a collaborator or the `github` column of `members.md`; if there is no match, ask — never create a handle

**Never invent an email address.** An address comes from the roster (`members.md`, `collaborators:`, the person's flowie `profile.md`) or from the person, typed in this conversation — never guessed, completed or built from a name and a domain. If someone has no address there, ask; if the person does not give one, keep the attendee without `email:` and leave them out of invites.

If Google Calendar MCP is not authenticated: skip the calendar step and note *"Google Calendar not configured — run `/setup` to connect."*
