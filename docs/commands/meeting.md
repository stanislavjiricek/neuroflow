# /meeting

First-class meeting management for neuroflow — schedule, prepare, invite, and close meetings at project, personal (flowie), or team (hive) level.

Distinct from [`/notes`](notes.md), which captures unstructured live input. `/meeting` is for planned meetings with agenda, attendees, calendar integration, and action-item-to-task conversion.

---

## Modes

| Flag | What it does |
|------|-------------|
| `--new` | Schedule a new meeting (from template or custom) |
| `--prepare <slug>` | Populate agenda with active tasks and project context |
| `--view <slug>` | Display meeting file with linked task statuses inline |
| `--list` | List all meetings at the current level |
| `--invite <slug>` | Send or re-send Google Calendar invites |
| `--close <slug>` | Finalize meeting and auto-create tasks from action items |
| `--init` | Create recurring meeting templates |

---

## Meeting levels

Use `--level` to specify where the meeting lives:

| Level | Storage | Who sees it |
|-------|---------|-------------|
| `project` (default) | `.neuroflow/meetings/` | All project collaborators |
| `flowie` | `.neuroflow/flowie/meetings/` | You only |
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

`--new` optionally calls the Google Calendar MCP to create an event with all attendees, returning an event link stored in the meeting file's frontmatter.

---

## Action items → tasks

`--close` parses the `## Action Items` section and creates tasks:

```markdown
- [ ] Fix RT pipeline → @stanislav [project/active]
- [ ] Update ethics form [project/inbox]
```

Each item becomes a task file at the specified level and column, tagged with `meeting:{slug}`.

---

## Related

- [`neuroflow:phase-meeting`](../skills/phase-meeting/SKILL.md) — full skill with mode-by-mode implementation
- [`/hive`](hive.md) — team Hive for shared directions and hive-level meetings
- [`/notes`](notes.md) — unstructured live note capture (use this for talks, seminars)
- [`/flowie --tasks`](flowie.md) — 3-tier Kanban task board
