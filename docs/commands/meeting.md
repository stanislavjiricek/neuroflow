# /meeting

First-class meeting management for neuroflow — schedule, prepare, invite, and close meetings at project, personal (flowie), or team (hive) level.

Distinct from [`/notes`](notes.md), which captures unstructured live input. `/meeting` is for planned meetings with agenda, attendees, calendar integration, and action-item-to-task conversion.

---

## Modes

| Flag | What it does |
|------|-------------|
| `--new` | Schedule a new meeting (from template or custom) |
| `--prepare <slug>` | Populate agenda with active tasks, follow-ups from earlier meetings of the same series, and project context |
| `--notes <slug>` | Take live notes straight into the meeting file (`a:` action items, `d:` decisions) |
| `--view <slug>` | Display meeting file with linked task statuses inline |
| `--list` | List meetings at the current level — next upcoming and not-yet-closed first |
| `--invite <slug>` | Send or re-send Google Calendar invites, after you confirm the recipient list |
| `--close <slug>` | Finalize meeting and create tasks from action items (dry run first) |
| `--init` | Create recurring meeting templates |

---

## Meeting levels

Use `--level` to specify where the meeting lives:

| Level | Storage | Who sees it |
|-------|---------|-------------|
| `project` (default) | `.neuroflow/meetings/` | All project collaborators |
| `flowie` | `~/.neuroflow/flowie/meetings/` | You only |
| `hive` | `{hive-repo}/meetings/` | Whole team |

---

## Recurring templates

Define templates once in `config.json` — reuse on every `/meeting --new`:

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
      "agenda_template": "## Updates\n\n## Papers\n\n## Action Items"
    }
  ]
}
```

`default_attendees` can be:
- An explicit email string
- `"all-hive-members"` — resolved from `hive.md` members table
- `"all-project-collaborators"` — resolved from `project_config.md`

---

## Calendar integration

`--new` optionally calls the Google Calendar MCP to create an event with all attendees, returning an event link stored in the meeting file's frontmatter. Invites email real people, so Claude lists every recipient address and sends only after you say yes.

Email addresses come only from the roster (the hive's `members.md`, `collaborators:` in `project_config.md`, your flowie profile) or from you — Claude never guesses or constructs one. Attendees without an address are left out of invites.

---

## Action items → tasks

`--close` turns the open checkboxes in `## Action Items` into task files in the [`/tasks`](tasks.md) format:

```markdown
- [ ] Fix RT pipeline → @alex [project/active]
- [ ] Review grant draft -> @sam due:2026-10-20 [flowie]
- [ ] Update ethics form
```

Owner (`→ @handle`), `due:` and `[level/column]` are optional; the default is `[project/inbox]`. The conversion is done by a small script (`meeting_close.py`) so it is the same every time: it first shows a dry-run plan, writes only after you confirm, records the new tasks in the meeting's `linked_tasks`, stamps `closed:`, and never creates a task twice. It never sends invites or emails and never pushes.

---

## Related

- [`neuroflow:phase-meeting`](../skills/phase-meeting/SKILL.md) — full skill with mode-by-mode implementation
- [`/hive`](hive.md) — team Hive for shared directions and hive-level meetings
- [`/notes`](notes.md) — unstructured live note capture (use this for talks, seminars)
- [`/tasks`](tasks.md) — the 3-tier Kanban task board (task file format)
