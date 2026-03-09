# decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-03-09 | Project memory lives in `.neuroflow/` in the user's repo, not in the plugin | Config must be per-project; plugin is stateless |
| 2026-03-09 | Every subfolder has a `flow.md` index | Context window efficiency — agents read index first, load files only when needed |
| 2026-03-09 | Command frontmatter includes `phase`, `reads`, `writes` | Makes dependencies explicit; sentinel-dev can validate consistency |
| 2026-03-09 | `sessions/` goes to `.gitignore`; `decisions.md` is git-tracked | Sessions are local continuity; decisions are team-shared history |
| 2026-03-09 | `/literature` is not a standalone command — literature lives under `/ideation` via scholar agent | Avoids redundant entry points; scholar agent is reusable across commands |
| 2026-03-09 | Renamed `/new-project` → `/start`, `/research-question` → `/ideation`, `/write-paper` → `/paper-write`, `/review-paper` → `/paper-review` | Consistent naming: verb or noun, no hyphens in verb phrases |
