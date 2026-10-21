---
title: The neuroflow mod
---

# The neuroflow mod

neuroflow is a Claude Code plugin. Besides its commands, skills and agents it ships an optional **mod**: a hooks module
(`hooks/mod/neuroflow.ts`) that runs inside Claude Code itself. The mod shows project state without spending tokens,
answers a few commands instantly, fills bookkeeping gaps, and enforces a small set of rules the skills already state.

The mod is a layer, not the product. Every command works without it — slower, and with the model doing the
bookkeeping — because the prose in `skills/` and `commands/` stays the source of truth.

What became of each idea in the review behind the mod is in the [design record](design-record.md).

!!! warning "Early access"
    Claude Code function hooks are an early-access API that changes between releases. The mod is tested against a
    minimum Claude Code version and a weekly canary on the latest release; when it cannot load, neuroflow keeps
    working as a plain plugin.

---

## What it looks like

<figure class="nf-shot">
<div class="nf-term"><span class="dim">&gt;</span> /neuroflow:dashboard phase
<div class="nf-pane"><span class="nf-pane__title">neuroflow</span><span class="b">Oddball EEG study · data-analyze · critic</span>
<span class="nf-key"><i>1:</i> now</span><span class="nf-key on">2: phase</span><span class="nf-key"><i>3:</i> deadlines</span><span class="nf-key"><i>4:</i> integrity</span><span class="nf-key"><i>5:</i> tasks</span><span class="nf-key"><i>6:</i> loop</span>

<span class="ok">✔</span> ideation  <span class="ok">✔</span> preregistration  <span class="ok">✔</span> data  <span class="ok">✔</span> data-preprocess  <span class="b">● data-analyze</span>  <span class="dim">○ paper</span>
Current: data-analyze — analysis
<span class="dim">Next: /neuroflow:paper — manuscript</span>
<span class="dim">● current  ✔ visited  ○ recommended</span>

<span class="nf-key"><i>g:</i> go to phase…</span>
<span class="nf-key"><i>h:</i> ‹ tab</span><span class="nf-key"><i>l:</i> tab ›</span><span class="nf-key"><i>r:</i> reread</span><span class="nf-key"><i>q:</i> close</span><span class="dim">esc: prompt</span></div></div>
<figcaption>The dashboard opens as a pane drawn in code, holding the keyboard — no model turn, no tokens. The digits pick the tabs: now, phase, deadlines, integrity, tasks and the autoresearch loop; <code>h</code> and <code>l</code> step between them.</figcaption>
</figure>

<figure class="nf-shot">
<div class="nf-term"><div class="nf-pane"><span class="nf-pane__title">integrity</span><span class="ok">✔</span> ethics approved · expires 2027-06-30
<span class="dim">  participant data the model may read: pseudonymised</span>
<span class="ok">■</span> preregistration frozen 2026-10-01 · 2 file(s)
<span class="dim">  planned N: 24</span>
<span class="ok">■</span> <span class="dim">read-only raw data: sourcedata/</span>

<span class="nf-key"><i>v:</i> verify</span><span class="nf-key"><i>u:</i> unfreeze…</span><span class="nf-key"><i>q:</i> close</span></div></div>
<figcaption>The integrity tab (<code>4</code>). A person freezes the preregistration here (<code>f</code>, after an explicit yes), re-checks its hashes (<code>v</code>) or unfreezes it with a reason (<code>u</code>).</figcaption>
</figure>

<figure class="nf-shot">
<div class="nf-term"><span class="warn">⚠ Abstract deadline — tomorrow</span>  <span class="dim">+1 more</span>  <span class="nf-key"><i>d:</i> dashboard</span><span class="nf-key"><i>x:</i> hide today</span><span class="dim">^X Tab: keys</span>
<span class="nf-rule"></span><span class="b">&gt;</span> <span class="nf-caret"></span>
<span class="nf-rule"></span><span class="dim">neuroflow: ⚠ Abstract deadline tomorrow</span><span class="nf-right dim">neuroflow · data-analyze · critic</span></div>
<figcaption>The band above the prompt names the most urgent item on one row — with the default <code>band: quiet</code> one item and <code>+N more</code> for the rest (<code>normal</code> shows two where they fit) — then <code>d: dashboard</code> and <code>x: hide today</code>. Its keys work once ^X Tab has given it the keyboard, and it says so until you have done that three times. An item's own keys, such as a meeting's <code>p: prepare</code> and <code>o: notes</code>, appear when it is first; the version notice's <code>m: migrate</code> appears whenever the notice is shown. While a check-in still waits to sync to your flowie, a key puts its command in the prompt instead: press Esc and then Enter, and the sync runs first. The status line speaks only about exceptions; the footer names the phase and the mode.</figcaption>
</figure>

<figure class="nf-shot">
<div class="nf-term"><span class="b">●</span> Edit(.neuroflow/preregistration/analysis-plan.md)
<span class="dim">  ⎿</span>  <span class="warn">neuroflow: .neuroflow/preregistration/analysis-plan.md belongs to the frozen preregistration — record the change in .neuroflow/preregistration/deviations.md instead (/neuroflow:preregistration → Deviation log) [nf-rule: PREREG-FROZEN]</span></div>
<figcaption>A guard. With <code>guards: enforce</code> the edit is refused with the rule and the way forward; with <code>warn</code> the same sentence is a warning.</figcaption>
</figure>

<figure class="nf-shot">
<div class="nf-term"><span class="dim">&gt;</span> /neuroflow:tasks
<div class="nf-pane"><span class="nf-pane__title">tasks</span><span class="nf-key on">1: project 3</span><span class="nf-key"><i>2:</i> flowie 12</span><span class="nf-key"><i>3:</i> example-lab-hive 4</span>
┌─ inbox ──────────┬─ active ─────────┬─ review ────────┐
│ fix-marker       │ <span class="warn">▸ ⚠ rerun-ica @li</span>│ qc-report       │
│                  │   due 08-20      │                 │
│                  │ spin-tests       │                 │
└──────────────────┴──────────────────┴─────────────────┘
move "Rerun ICA" to  inbox  ready  <span class="b">review</span>  meeting  done  <span class="nf-key"><i>x:</i> cancel</span>
<span class="dim">done: 3 · archived: 0 · level: project</span>
<span class="nf-key"><i>h:</i> ◂</span><span class="nf-key"><i>l:</i> ▸</span><span class="nf-key"><i>j:</i> ▾</span><span class="nf-key"><i>k:</i> ▴</span><span class="nf-key"><i>r:</i> reread</span><span class="nf-key"><i>q:</i> close</span><span class="dim">enter: pick · esc: prompt</span></div></div>
<figcaption>The task boards: the project's, your flowie's and each hive's, read from the local copies. The digits pick the level; on flowie and hive boards this project's tasks come first, marked ◆. Tab or <code>h</code> <code>j</code> <code>k</code> <code>l</code> reach a card, Enter picks it (▸) and Enter on a column moves it — at once at project and flowie level, as one command in the prompt for you to send at a hive's.</figcaption>
</figure>

---

## What it does

| Feature | What you see | Needs |
|---|---|---|
| Views | `/neuroflow:dashboard` opens a pane (now — every band item with its action —, phase map, deadlines, integrity, open tasks at every level, the autoresearch loop); `/neuroflow:phase` opens a picker (arrows and Enter, or a click); `/neuroflow:tasks` the task boards of the project, your flowie and each hive, the digits picking the level; `/neuroflow:paper --auto status`, `/neuroflow:paper --xray view` and `/neuroflow:wiki --review` open panes for the living paper, the paper X-ray and the wiki review queue. Each opens holding the keyboard ([Keyboard and SSH](#keyboard-and-ssh)) | — |
| Band, status line, footer | One line above the prompt when something needs attention (a deadline, a meeting, a drafted decision, a loop being driven, a plugin update the project has not been [migrated](../upgrading.md) to, a flowie sync of the mod's that is pending or did not go through); a status line that speaks only about exceptions; `neuroflow · phase · mode` in the footer | `band` |
| Instant answers | `/neuroflow:doctor`, `/neuroflow:phase <name>`, `idea: …` and live note capture answered in code, with no model turn | — |
| Bookkeeping | Missing session lines and `flow.md` rows filled after a command's turn and marked `(auto)`; a decision drafted when a command logged none, kept only on your key press | `runtime: on` |
| Integrity | The guards below; freezing, verifying and unfreezing the preregistration from the dashboard; frozen files re-hashed at start | `guards: enforce` to deny |
| Checks | Text hidden from human readers in documents from outside, reported after the model reads them; DOIs checked after manuscript writes and weekly for notices | `citations` and `runtime: on` for DOIs |
| Context | A digest of the project's integrity facts as a neuroflow command starts; wiki pages a prompt names; a capped digest of a linked flowie profile (no identity or wellbeing); the current and next phase marked in the slash menu | — |
| Quiet | A `quiet` command such as `/idk` silences the band, status line and footer label until the next neuroflow command | — |
| Autoresearch driver | `/neuroflow:autoresearch drive <name>`: one iteration per turn, caps checked between turns, a stop key | `runtime: on` |

When changes you made on your claude.ai [workbench](workbench.md) wait for Claude Code (as `~/.neuroflow/workbench/pending.json`
last recorded them), the band says how many and `a` puts `/neuroflow:tasks --apply-web` in the prompt for you to send;
the boards mark those cards `↻`. The mod reads that file only — it never calls the workbench or uploads anything, and
`/neuroflow:dashboard --web` always runs the full command.

When you open the boards (`/neuroflow:tasks`, the dashboard's tasks tab) or press `r` there, the mod refreshes the cache of the project's other repositories' boards in `~/.neuroflow/boards/` in the background — a shallow, sparse fetch of their `.neuroflow/tasks/` only, with git hooks off and no password prompt; nothing leaves — at most once a minute, and ten minutes after a fetch that failed. Those boards are read-only in the pane.

The band asks for the wellbeing check-in only once it knows today's entry is not already on your flowie's remote — made on another machine: as a session starts in a neuroflow project the mod fetches your flowie in the background (it reads the remote's refs: nothing leaves, your files are not touched, the first prompt never waits), and when the entry is there it does not ask — the next pull brings it down; offline, or with git hooks or LFS in your flowie, it asks as before. The wellbeing check-in on the band and `idea: …` write into your private [flowie](flowie.md). The mod commits those
files by path, pulls and pushes them — for an idea right away, for the check-in before your next neuroflow command
(which pulls your flowie first) or when the next turn ends, never from the band's own field and never while a session
starts — and writes each attempt and its outcome as a line of `~/.neuroflow/flowie-sync.log`. A sync that does not go
through stays on the band, pointing at `/neuroflow:flowie --sync`; it is tried again when something new is saved or in
the next session, never in a loop.

---

## Keyboard and SSH

Everything the mod draws works from the keyboard, without a mouse and without leaving the prompt — in a local terminal,
over SSH, inside tmux or screen.

### Getting in

| You want | From the prompt | Then |
|---|---|---|
| The dashboard | `/neuroflow:dashboard`, or `/neuroflow:dashboard <tab>` (`now`, `phase`, `deadlines`, `integrity`, `tasks`, `loop`) | It opens holding the keys; the same command again gives an open dashboard the keys again |
| The task boards | `/neuroflow:tasks` | They open holding the keys, on the level `/tasks` names |
| A phase switch | `/neuroflow:phase` for the picker, or `/neuroflow:phase <name>` at once | The picker opens holding the keys |
| The wiki cards, an X-ray, the living paper | `/neuroflow:wiki --review`, `/neuroflow:paper --xray view`, `/neuroflow:paper --auto status` | Each opens holding the keys |
| The band's keys | ^X Tab (Ctrl+X, then Tab) | Esc gives the keys back to the prompt |

Keys you type in the first 400 ms after a view opened holding the keys do nothing: a quick Enter or the start of your
next sentence never acts in a pane you did not mean to type into. Esc always gives the keys back to the prompt and leaves
the pane open; `q` closes it. A pane that does not hold the keys says so at its foot: `^X Tab: use the keys here ·
/neuroflow:dashboard focuses it`. While the band shows keys of its own, ^X Tab can land on the band before a pane, so
running the pane's command again is the sure way back into it.

### The keys

One key means one thing everywhere. Letters work on the band only after ^X Tab; digits work only in a pane that holds
the keys, so a number you type into the prompt ("2026", "128 channels") never presses anything.

| In every pane | |
|---|---|
| `h` `l` | previous, next — tab, column or move target |
| `j` `k` | down, up — row, card, finding or wiki card |
| `y` | yes: keep, accept |
| `n` | no: drop, skip, reject |
| `x` | cancel, stop |
| `r` | read the files again |
| `q` | close |
| Tab, Enter, Esc | Claude Code's own: Tab moves the highlight, Enter acts on what it is on, Esc goes back to the prompt |

| View | Its keys |
|---|---|
| Band | `d` dashboard (opens on now) · `x` hide today, not today, stop a driven loop or a note capture · `p` prepare and `o` notes for a meeting soon · `c` close a meeting left open · `m` migrate · `w` review wiki cards · `s` sync the flowie · `a` apply your workbench changes (puts the command in the prompt for you to send) · `y` keep and `n` drop a drafted decision · the wellbeing check-in is a field: ^X Tab lands in it |
| Dashboard | `1` now · `2` phase · `3` deadlines · `4` integrity · `5` tasks · `6` loop; on phase `g` go to a phase; on integrity `f` freeze (asks first), `v` verify, `u` unfreeze (asks first); on tasks `b` the boards. On now, every action runs with Enter on its row, never on a letter |
| Task boards | `1`–`9` level · `h` `j` `k` `l` or Tab to a card · Enter picks it (▸), Enter on a column moves it · `x` cancel · a hive's move goes into the prompt for you to send |
| Phase picker | Down or Enter opens the list · the arrows move · a letter jumps to the phases that start with it · Enter switches · Esc closes |
| Wiki cards | `y` accept (runs `/neuroflow:wiki --add`) · `n` skip · `j` `k` next, previous |
| X-ray | `y` accept · `n` reject, with a reason · `j` `k` next, previous finding, red first, eight to a page |
| Living paper | `s` sync now · `r` read again |

### One chord per view

Claude Code runs a slash command from a key binding of yours. To open the dashboard, the boards or the picker with one
chord, add this to `~/.claude/keybindings.json` (merge it into what is there; neuroflow never writes that file):

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/en/keybindings",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+x d": "command:neuroflow:dashboard",
        "ctrl+x t": "command:neuroflow:tasks",
        "ctrl+x p": "command:neuroflow:phase"
      }
    }
  ]
}
```

The chords are free in Claude Code's defaults. A `command:` binding runs the command as if you typed it, so the view
opens holding the keys; it works while the prompt has them (Esc first when a pane does).

### Over SSH, in tmux and in screen

- **No mouse needed.** Every view above opens and works from the keys alone.
- **Inline, not docked.** On Claude Code's main screen — the default inside tmux — panes sit above the prompt. Each view
  asks for its rows; on a terminal under 30 rows (24 over SSH) it asks for fewer, so the conversation keeps room.
- **tmux** waits after Esc to see whether a key sequence follows; with `set -sg escape-time 10` in `~/.tmux.conf` Esc
  gives the keys back at once. Its prefix (Ctrl+B) does not meet the chords above.
- **GNU screen** takes Ctrl+A as its prefix: the band's collapse chord, Ctrl+X Ctrl+A, becomes Ctrl+X, then Ctrl+A
  and `a` there (screen's way to send a Ctrl+A through). ^X Tab works as it is.
- **Colours and glyphs.** The views use your theme's colours, never fixed ones, and pair each with a glyph and a word,
  so 8- and 16-colour terminals and light themes read the same. Claude Code itself needs a UTF-8 terminal; the views'
  glyphs (▸ ◆ ⚠ ✔ ↻) need nothing more.

---

## Settings

Set them in Claude Code itself: `/plugin` → **Installed** → neuroflow → **Configure options**, or the neuroflow rows
in `/config`. Claude Code saves them in your user settings (`~/.claude/settings.json`). To write them by hand, put
them there under the plugin's marketplace key:

```json
{
  "pluginConfigs": {
    "neuroflow@neuroflow": {
      "options": { "runtime": "on", "guards": "enforce", "band": "quiet", "citations": true }
    }
  }
}
```

A copy loaded with `--plugin-dir` (local development) is keyed `neuroflow` (or `neuroflow@inline`) instead. Claude
Code reads plugin options only from your user settings, a file passed with `--settings` and managed settings — never
from a project's `.claude/settings.json` or `.claude/settings.local.json`, so a repository you clone cannot change
them. Values are per user; per-project facts stay in `.neuroflow/`.

| Setting | Values | Default | What it does |
|---|---|---|---|
| `runtime` | `off` · `observe` · `on` | `observe` | `off`: the mod does nothing. `observe`: views, status and warnings — it never writes into project memory on its own (only when you press a key or type a command that asks it to) and never blocks. `on`: it also fills bookkeeping gaps and may enforce guards. |
| `guards` | `warn` · `enforce` | `warn` | `enforce` lets guards deny a tool call (only with `runtime: on`). `warn` says what a guard would have blocked. |
| `band` | `off` · `quiet` · `normal` | `quiet` | The one-line band above the prompt. `quiet` shows only what needs attention. |
| `citations` | `true` · `false` | `false` | After a turn that wrote a manuscript, grant, poster or report citing DOIs, look up the new DOIs with `cite_check.py`; once a week, re-check the manuscript's DOIs for retraction and correction notices. Needs `runtime: on` (it keeps a DOI cache in `.neuroflow/paper/`). |

## When the mod is not running

The module does not load when the rollout of plugin hooks modules has not reached your account, when hooks are
disabled by settings or policy, or in safe mode. It is tested from Claude Code 2.1.292; on an older build it may not
load or may misbehave, and `/neuroflow:doctor` warns about the version. Nothing breaks:
commands run their prose, and `/sentinel` (via `nf_check.py`) covers the checks the guards would have made. The
missing footer label is the visible sign; the doctor says "module not live".

The mod also stays off where it should not act: outside a neuroflow project, in your home folder, and in the plugin's
own repository. In headless runs (`claude -p`, the SDK, CI) it draws nothing and asks nothing; guards still deny with a
reason.

---

## The charter

These rules bind every feature of the mod. They come from a skeptical review of what a hooks module can and cannot
promise in a research setting.

### The prose is the source of truth

1. **Skills stay normative.** The mod never carries a duty the prose does not also state; it observes, shows, fills
   gaps and denies. Every rule a guard enforces is stated in a skill or command next to an `<!-- nf-rule: ID -->`
   marker, and CI fails when a guard has no marker.
2. **No runtime rewriting of skill text.** The mod may add a delimited preamble to a skill's prompt (a digest, a
   reminder); it never patches or removes the skill's own words.
3. **Truth lives in `.neuroflow/` files.** `$.state` only mirrors them for drawing; `$.store` holds preferences and
   caches, never research state. Secrets belong in sensitive settings fields, never in the store or in chat.
4. **One executable home per check.** A check is a Python script under `skills/<skill>/scripts/`, run by the prose and
   by the mod alike — never a second implementation in TypeScript.
5. **Mod writes are marked and idempotent.** Lines the mod adds to project memory end with `(auto)`; it appends, never
   rewrites what a person or the model wrote, and recovers on the next start instead of flushing at session end.

### Quiet by default

6. **No UI the person did not ask for.** Panes open on request; the band is a single slot shown by priority; toasts
   only for actionable changes; nothing appears during `lifecycle: quiet` commands such as `/idk`.
7. **Letter hotkeys only in the band.** Digits typed into the prompt ("2026", "128 channels") must never become
   button presses; digits are allowed only in focused panes. The band yields while a survey is showing.
8. **Every visual has a text form.** Status uses a glyph, a word and a colour together; heat maps have a keyboard-reachable
   text summary; palettes are colour-vision safe. Surfaces differ (images draw only in some terminals, the mobile app has
   no inputs), so every view has a plain-text path.

### Honest guards

9. **Hard rules deny before the call, and fail closed.** A guard judges before `next`, and its `.catch` denies when the
   guard itself fails. A deny after the call undoes nothing.
10. **A ladder, not a wall.** Observe, warn, ask, and only then deny — reserved for irreversible breaks: frozen
    preregistrations, raw data, secrets, consent. Model judgement never decides enforcement.
11. **Integrity markers are set by a person.** "Preregistration frozen" or "ethics approved" counts only when a person
    pressed the button or confirmed in the turn (`set_by: person`). The model writes `set_by: person` only after the
    person's explicit confirmation in that turn. With `runtime: on` and `guards: enforce` the mod also asks before such a
    write and lets it through only on "Allow — I confirm this myself" (in a headless run, where nobody can answer, it
    denies); otherwise it warns.
12. **Badges name the test.** "DOI resolves", not "citation verified"; "hash matches", not "no drift".
13. **Records state their blind spots.** The mod sees only Claude Code sessions in which it loaded. Generated records say
    what window they observed and what they cannot see (work done in other tools or by hand).

### The record

14. **Annotate, never rewrite.** The mod never hides or edits what a person said or what the model wrote in the record;
    plugin text is always labelled as such; consent is only ever the label of a real press.
15. **AI use is disclosed, never evaded.** The humanizer is a style editor run on request; disclosure statements are
    generated from provenance.

### Privacy and data movement

16. **No automatic outbound data.** Every upload, push or export needs a preview and a person's confirmation in that
    turn; nothing leaves from a timer.
17. **Other people's text never becomes instructions.** Wiki pages, collaborators' notes, manuscripts and web content
    may be shown to the model as data — never injected as system-prompt policy.
18. **Participant data follows the ethics record.** Whether the model may read participant data is decided by
    `ai_processing` in `.neuroflow/ethics/status.md`, not by convenience.
19. **No surveillance.** No inferred mood, no presence broadcasting; wellbeing features are explicit, self-reported and
    switchable per person.

### Budget and loops

20. **No hidden judgement, no uncapped spend.** Code does bookkeeping, scheduling and explicit rules; scientific calls
    stay with the model and the person. No model calls in hot paths (prompt edits, drawing).
21. **Every loop can be stopped.** Long-running loops have caps on iterations, wall-clock time and cost, stop on an
    abort or repeated errors, and show a stop control.
22. **Context injection is small and stable.** One short, stable session section; volatile state goes to the screen,
    not the system prompt; command digests are budgeted.

### Scope and the engine

23. **Project-only activation, observe by default.** Never in the home folder or the plugin repository; a tested
    version floor; `observe` until a person chooses `on`.
24. **Headless means no UI and no questions.** A person is present when a surface draws; otherwise the mod asks nothing
    and draws nothing, while guards still deny with a reason.
25. **Stay additive.** No replacing the engine's messages, models or other plugins' behaviour; mod-run git only in the
    mod's own caches; no blanket permission auto-approval.
26. **Durable writes never wait for session end, timers or child processes.** Write when the fact happens; recover on
    the next start.

### Lab safety

27. **Never in the acquisition path.** The mod may observe a recording; it never carries samples, triggers or timing.
28. **Participants only ever see validated software.** No stimuli, questionnaires or consent forms run inside Claude
    Code, and no software check is ever presented as a stimulation-safety interlock.
29. **No AI costs booked into grant expenses** by code.

### Feature budget

30. **A fixed allowlist and a kill rule.** The events, `$` calls and environment variables the mod may use are listed in
    `hooks/mod/policy.json`; CI fails on anything new until it is reviewed. A feature that is not used, or whose guard
    produces more false positives than catches, is removed at the next review.

---

## The guards

Each guard enforces a rule a skill or command already states next to its `<!-- nf-rule: ID -->` marker. The last
column is what happens with `runtime: on` and `guards: enforce`; otherwise every guard only says what it would have
done. A guard that would ask denies instead in a headless run, where nobody is there to confirm.

| Rule | What the guard checks | With `enforce` |
|---|---|---|
| `PREREG-FROZEN` | Writes to the files of a preregistration a person froze; changes to earlier entries of `deviations.md` while it is frozen (new entries are appended) | deny |
| `RAW-READONLY` | Changing, moving or deleting an existing file under `raw_roots` (`sourcedata/` while unset); new recordings may be added | deny |
| `PARTICIPANT-ROUTE` | The model reading participant data (recordings, `participants.tsv` rows) when `ai_processing` is `none`, missing, or not set by a person; sidecar JSON and a table's header row are fine. Off when `project_config.md` says `ethics: not-applicable` (a project with no participant data to protect) | deny — a warning when the project has no ethics record yet |
| `GIT-NO-SECRETS` | `git clean -x`, staging local-only files (a project's, and any `integrations.json`; your flowie's other files are synced, so staging them by path is fine), `git add .` / `-A` / `-u` in your flowie or while `.gitignore` lacks the local-only lines; commands that throw work away (`reset --hard`, force push) | deny — ask for a broad `git add` and for discards |
| `GIT-ALIAS-SCOPE` | A git verb beyond the endpoint of the running `/git` alias | deny |
| `INTEGRITY-MARKER` | The model writing `set_by: person` into an ethics or preregistration status file | ask |
| `EGRESS-CONFIRM` | Uploads to outside services (NotebookLM sources); `ArtifactData` writes to anything but your recorded [workbench](workbench.md) under `data/users/me` (or your resolved id there) for a level you mirror from this machine — as `workbench.py levels` decides it, from your consent and the team's opt-in; Claude creating or rewriting a workbench request, which only the page does | ask — deny for a workbench request |
| `LOGIN-NODE` | Heavy compute on an HPC login node (a scheduler on `PATH`, no job around the session) | ask |
| `MEMORY-PURITY` | Files outside the documented `.neuroflow/` structure (read from `nf_check.py --structure`), deliverables inside it | warn |

At session start the mod also re-hashes a frozen preregistration (`freeze.py verify`) and puts a changed file on the
status line, and the footer says `login node` on a cluster login node.

## Doors the guards cannot close

Guards see tool calls Claude Code routes through hooks, and they read shell commands by pattern only. They cannot see
or stop:

- what a Python, R or MATLAB script writes once it runs, or what a shell command does inside its own process;
- commands started in other ways (Monitor, a terminal of your own), other plugins, and MCP servers acting on their own;
- `@`-mentions, pasted text and dragged files, which reach the model without a tool call;
- network shares and synced folders where file identity is unreliable;
- work done outside Claude Code, or in a session where the module did not load.

That is why guards are paired with detection: hashes checked at session start and by `/sentinel`, plain-text banners on
frozen files for collaborators without the mod, and records that state what they could not observe.

---

## For contributors

- Layout: `hooks/mod/neuroflow.ts` (entry, feature order), `hooks/mod/features/*` (one file per feature),
  `hooks/mod/lib/*` (pure helpers), `hooks/mod/tests/*.test.ts`, `types/index.d.ts` (the `$.state` contract),
  `hooks/mod/policy.json` (allowlist).
- Keys: every hotkey comes from `hooks/mod/lib/keys.ts`, the one key map (by view, each key with its meaning). The
  map is frozen: a change to how a view looks never moves a letter. `hooks/mod/tests/keys.test.ts` fails on a digit
  in the band, a key with two meanings, a key drawn twice in one view, or one the map does not list. A Button with a
  hotkey is `plain`, so the key shows.
- The test kit exercises hooks and trees, never focus, key dispatch or paint: before a release that changes the views,
  run the [live check](../maintenance/mod-live-check.md) in a real terminal.
- `$` never crosses a file: the validator follows it only into functions declared in the same file, so helpers take an
  `NfIo` of closures (`ioOf($)` in each feature file). State references (`atom(...)`) are declared in the file that
  uses them. `$.env.get` takes literal names only.
- Every gating hook has a `.catch`: guards deny when they fail; observers pass the call through.
- Check with `claude plugin validate .` and `claude plugin test .` from the repo root. CI runs both on the Claude Code
  version the mod is tested from, then `python scripts/automation/mod_policy.py`, which compares the events the module
  hooks and the calls, environment variables and state the validator reports with `hooks/mod/policy.json`: anything
  new fails until a reviewer adds it (`--write` regenerates the file; commit it with the change it allows).
- A weekly canary (`.github/workflows/mod-canary.yml`) runs the same checks on the newest Claude Code release and
  opens an issue when the mod breaks there.
