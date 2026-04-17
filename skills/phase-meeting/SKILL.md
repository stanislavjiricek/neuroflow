---
name: phase-meeting
description: Phase guidance for the /meeting command. Covers meeting file structure, recurring templates, attendee resolution from profiles, Google Calendar MCP integration, agenda preparation with project context, and action-item-to-task conversion at all three levels (project, flowie, hive).
reads:
  - .neuroflow/project_config.md
  - .neuroflow/tasks/**
  - .neuroflow/meetings/config.json
  - .neuroflow/meetings/*.md
  - .neuroflow/hive/hive.md
  - .neuroflow/flowie/profile.md
  - .neuroflow/flowie/meetings/config.json
writes:
  - .neuroflow/meetings/
  - .neuroflow/flowie/meetings/
  - .neuroflow/tasks/**
---

# phase-meeting

The `/meeting` command manages structured meetings — distinct from `/notes` which captures unstructured live input. Meetings have schema (attendees, agenda, decisions, action items), optional calendar integration, and task creation from action items.

---

## Meeting levels

| Level | Storage | Git-tracked in | Who sees it |
|-------|---------|----------------|-------------|
| `project` (default) | `.neuroflow/meetings/YYYY-MM-DD-{slug}.md` | Project repo | All collaborators |
| `flowie` | `.neuroflow/flowie/meetings/YYYY-MM-DD-{slug}.md` | Flowie repo | Owner only |
| `hive` | `{hive-repo}/meetings/YYYY-MM-DD-{slug}.md` | Hive org repo | Whole team |

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
    email: {email}
level: {project|flowie|hive}
tags: [{tag1}, {tag2}]
linked_tasks: []
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
- `.neuroflow/flowie/meetings/config.json` — personal (flowie level)
- `{hive-repo}/meetings/config.json` — team-level (hive, synced with `--sync`)

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

4. **Resolve attendees:**
   - For `default_attendees: ["all-hive-members"]` → read `hive.md` members table → extract name + email for each row
   - For `default_attendees: ["all-project-collaborators"]` → read `collaborators:` from `project_config.md`
   - For explicit email strings → use as-is
   - For custom meeting: ask *"Who should attend? (names or emails, comma-separated)"* — look up emails from hive members and collaborators by name if given

5. **Write meeting file** to the appropriate storage location (see levels table above). Filename: `YYYY-MM-DD-{slug}.md` where slug is derived from the title.

6. **Calendar invite (optional):** ask *"Create Google Calendar event and send invites? [Y/n]"*

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
2. Read `.neuroflow/project_config.md` for current phase
3. Read `.neuroflow/tasks/active/` and `.neuroflow/tasks/review/` — list active and under-review tasks
4. If hive is connected: read `hive.md` directions for relevant team context
5. If any tasks are tagged with the meeting slug, include them under a dedicated heading

Compose an agenda draft:
```markdown
## Agenda

### Project status
- Phase: {current phase}
- Active tasks: {list slugs with titles}
- In review: {list slugs with titles}

### Team context
{relevant hive directions if any}

### Items
{blank or template sections}
```

Show the draft and ask *"Does this look right? Edit inline or confirm."*

Write the updated `## Agenda` section back to the meeting file (preserve other sections).

---

## Mode: --view \<slug\>

1. Find meeting file by slug
2. Read all `linked_tasks` from frontmatter → for each, check current column in `.neuroflow/tasks/` (or hive tasks)
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

Show all meetings at the active level, sorted by date (newest first):

```
[project]  2026-04-20  Weekly Lab Meeting         weekly-lab-2026-04-20
[project]  2026-04-13  Weekly Lab Meeting         weekly-lab-2026-04-13
[flowie]   2026-04-17  Supervisor 1:1             supervisor-1on1-2026-04-17
```

If `--level` not given: show project and flowie levels together.

---

## Mode: --invite \<slug\>

Re-send or send calendar invites for a meeting that doesn't have a `calendar_event_id` yet.

1. Read meeting file
2. If `calendar_event_id` is already set: ask *"Invites were already sent (event ID: {id}). Re-send? [y/N]"*
3. Call `mcp__claude_ai_Google_Calendar__create_event` (or `update_event` if re-sending) with attendees from the meeting file
4. Update `calendar_event_id` in frontmatter

---

## Mode: --close \<slug\>

Finalize the meeting and convert action items to tasks.

1. Read meeting file
2. Parse `## Action Items` section — find all checkboxes:
   ```
   - [ ] Description → @person [level/column]
   ```
   - `→ @person` is optional — used to assign the task's `project` tag
   - `[level/column]` is optional — defaults to `[project/inbox]`
   - Unformatted items default to `[project/inbox]`

3. For each unchecked item: create a task file at the specified level and column. Task frontmatter:
   ```yaml
   ---
   title: {item description}
   level: {project|flowie|hive}
   project: {project from config, or from @person annotation}
   created: {today}
   tags: [meeting:{meeting-slug}]
   ---
   ```

4. Update `linked_tasks` in the meeting frontmatter with the new task slugs.

5. Report:
   ```
   Meeting closed: {title}
   Tasks created: {N}
     [project/inbox]  fix-rt-pipeline
     [project/inbox]  update-ethics-form
     [flowie/inbox]   review-grant-draft
   ```

6. Push all changes (meeting file + task files).

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

1. `"all-hive-members"` → read `.neuroflow/hive/hive.md` `## Members` table → return all rows as `{name, email}`
2. `"all-project-collaborators"` → read `.neuroflow/project_config.md` `collaborators:` list → return all entries
3. Plain email string → use as-is, name = email prefix
4. Name string (no `@`) → search hive members and collaborators by name → use matched email; if ambiguous, ask

If Google Calendar MCP is not authenticated: skip the calendar step and note *"Google Calendar not configured — run `/setup` to connect."*
