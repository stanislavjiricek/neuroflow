---
title: Mod live check
---

# Live check of the mod's keyboard

`claude plugin test .` exercises the mod's hooks and the trees they draw — never focus, key dispatch or paint. Who
holds the keys after which open, where ^X Tab lands, whether a hotkey moves the highlight, whether a rule lines up
under its tab: that shows only in a real terminal. Run this check before a release that changes the views
(`hooks/mod/features/views.tsx`, `user.tsx`, `hooks/mod/lib/keys.ts`, `layout.ts`, `complete.ts`), on the Claude Code
version the mod is tested from and on the newest one, and write the outcome into the pull request.

## 1. A fixture project outside the plugin repository

The mod stays off in the plugin's own repository ([charter](../concepts/mods.md#the-charter) rule 23), so the check runs
in a throwaway project somewhere else. This script writes one with something on every row of the dashboard — a deadline
tomorrow, a meeting in 45 minutes, one left open with action items, wiki cards, a running autoresearch loop, six cards in
one column, an X-ray, a living paper, and a project on an older neuroflow, so the version notice shows. The band shows
only its most urgent item and that item's keys, so with `--band` the script writes one band state at a time instead: only
what puts that item first, the project on the checkout's version unless the state is the notice. Save it outside the
plugin repository and run it with the folder to create:

```python
"""Writes a neuroflow fixture project for the mod's live check.

python make_fixture.py <folder>                                    rows for every tab, the boards and the panes
python make_fixture.py <folder> --band <state> --plugin <checkout>  one band state, written over the last one
"""
import argparse
import datetime as dt
import json
import pathlib
import shutil

parser = argparse.ArgumentParser(description="Write a neuroflow fixture project for the mod's live check.")
parser.add_argument("folder")
parser.add_argument("--band", choices=["deadline", "meeting", "open-meeting", "notice", "wiki"],
                    help="write only what puts this item first on the band")
parser.add_argument("--plugin", help="your neuroflow checkout: the project goes on its version, so no version notice shows")
args = parser.parse_args()
root = pathlib.Path(args.folder).expanduser()
config = root / ".neuroflow" / "project_config.md"
if config.exists() and "project_name: Live check" not in config.read_text(encoding="utf-8"):
    raise SystemExit(f"{root} holds another neuroflow project: name a new folder")
version = "0.0.1"  # older than any release: the version notice shows
if args.band not in (None, "notice"):
    if not args.plugin:
        raise SystemExit("--band needs --plugin <your neuroflow checkout>, so the project is on its version")
    manifest = pathlib.Path(args.plugin).expanduser() / ".claude-plugin" / "plugin.json"
    version = json.loads(manifest.read_text(encoding="utf-8"))["version"]
now = dt.datetime.now()


def wants(*states: str) -> bool:
    """True when the fixture writes what these band states need: all of it without --band."""
    return args.band is None or args.band in states


def day(days: int) -> str:
    return (now + dt.timedelta(days=days)).strftime("%Y-%m-%d")


def at(minutes: int) -> str:
    return (now + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M")


def put(rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# The band's own files go first, so a state written over the last one leaves nothing of it behind.
for rel in (".neuroflow/timeline.md", ".neuroflow/meetings", ".neuroflow/wiki/.pending"):
    if (root / rel).is_dir():
        shutil.rmtree(root / rel)
    elif (root / rel).exists():
        (root / rel).unlink()
put(".neuroflow/project_config.md", "---\nnf_schema: 1\nproject_name: Live check\nactive_phase: data-analyze\n"
    f"plugin_version: {version}\npaper_auto: on\nrecommended_phases: [ideation, preregistration, data, data-analyze, paper]\n---\n")
put(".neuroflow/flow.md", "# Live check\n")
if wants("deadline"):
    ethics = f"| {day(12)} | Ethics approval expires | data |\n" if args.band is None else ""
    put(".neuroflow/timeline.md", f"| Date | What | Gates |\n|---|---|---|\n| {day(1)} | Abstract deadline | paper |\n{ethics}")
if wants("meeting"):
    put(f".neuroflow/meetings/lab-{day(0)}.md", f"---\ntitle: Lab meeting\ndate: {at(45)}\n---\n")
if wants("meeting", "open-meeting"):
    put(f".neuroflow/meetings/pi-{day(-1)}.md", f"---\ntitle: PI check-in\ndate: {at(-24 * 60)}\n---\n"
        "## Actions\n- [ ] send the data\n- [ ] book the room\n")
if wants("wiki"):
    for n in (1, 2):
        put(f".neuroflow/wiki/.pending/{day(0)}-card-{n}.md", f"---\ntitle: Card {n}\ntype: decision\n"
            "evidence: reasoning/data-analyze.jsonl\nstatus: pending\nby: mod\n---\nA card to review.\n")
for column, slugs in {"inbox": ["fix-markers"], "active": [f"step-{n}" for n in range(1, 7)], "review": ["qc-report"]}.items():
    for slug in slugs:
        put(f".neuroflow/tasks/{column}/{slug}.md", f"---\ntitle: {slug.replace('-', ' ').capitalize()}\n"
            f"status: {column}\ncreated: {day(-3)}\n---\n")
for phase in ("ideation", "preregistration", "data"):
    put(f".neuroflow/{phase}/flow.md", f"# {phase}\n")
put(".neuroflow/preregistration/prereg-osf.md", "# Preregistration\n")
loop = "analysis/loops/connectivity"
put(".neuroflow/data-analyze/autoresearch-loops.md", "| Name | Location | Iterations | Best | Status |\n"
    f"|---|---|---|---|---|\n| connectivity | {loop}/ | 6 | v005 | running |\n")
put(f"{loop}/results.md", "| # | Verdict | Running |\n|---|---|---|\n" + "".join(f"| {n:03d} | KEPT | {n} |\n" for n in range(6)))
put(f"{loop}/report.md", "# Report\n\n## Open questions\n- **Q1** — keep the third control analysis?\n")
findings = [
    {"id": f"S1.{n}-1", "scope": "sentence", "sentence": f"S1.{n}", "line": 10 + n, "severity": "red" if n % 4 == 0 else "orange",
     "area": 4, "basis": "model", "finding": f"finding {n}", "fix": "a fix", "status": "open"}
    for n in range(1, 13)
]
put(f".neuroflow/paper/xray-results-{day(0)}.jsonl", "".join(json.dumps(item) + "\n" for item in findings))
put(".neuroflow/paper/paper-ledger.md", "| Key | Value | Source | Date | Status |\n|---|---|---|---|---|\n")
put(".neuroflow/paper/skeleton.md", f"<!-- generated by /paper --auto sync {day(-2)} from paper-ledger.md: edit the sources, "
    "not this file -->\n## Results\n- **H1** no final result yet\n")
put(".neuroflow/paper/gaps.md", "| Gap | Checklist item | Fill with |\n|---|---|---|\n| reference electrode | COBIDAS-MEEG 3.2 | /data-preprocess |\n")
print(f"fixture written to {root}" + (f", band state {args.band}" if args.band else ""))
```

```bash
python make_fixture.py ~/nf-live-check/oddball
cd ~/nf-live-check/oddball && git init -q
```

The fixture's dates are relative to when it was written: write it again on the day of the check. Each band state of the
checklist names the `--band` it needs; write it over the fixture in the same folder, then let the mod read the files
again (`/neuroflow:dashboard`, `r`, `q`). The band states that need a live session — a drafted decision, a driven loop,
a note capture, a wellbeing check-in, a flowie sync that waits — are listed in the checklist with how to reach them.

## 2. The dev copy, with the installed copy off

Never load a `--plugin-dir` copy and an installed copy together: every skill, command, agent and MCP server would load
twice ([neuroflow-develop](../skills/neuroflow-develop/SKILL.md) → Local development).

```bash
claude plugin disable neuroflow@neuroflow          # the installed copy, for the check only
cd ~/nf-live-check/oddball
claude --plugin-dir <path to your neuroflow checkout>
```

In the session, `/neuroflow:doctor` must say the mod is live and name the Claude Code version. Set the copy's options in
`/config` (a `--plugin-dir` copy is keyed `neuroflow` or `neuroflow@inline`, not `neuroflow@neuroflow`): `runtime` on, for
the decision drafter and the loop driver. Leave `band` quiet, the default, except where a line says normal: a normal band
also shows the wiki cards and the other information items, and a second item only from 110 columns. When the check is
done: `claude plugin enable neuroflow@neuroflow`.

## 3. The terminals

- **80 × 24 over SSH, inside tmux, mouse off.** `ssh` to a host with Claude Code, `tmux new -s nf` with
  `set -g mouse off` and `set -sg escape-time 10` in `~/.tmux.conf`; size the window until `stty size` prints `24 80`.
  Once with `TERM=xterm-16color`, and once with a light Claude Code theme (`/theme`).
- **120 × 40, the fullscreen layout**, where panes dock beside the conversation from 110 columns; and once **inline at
  120 columns** (Claude Code's main screen, as inside tmux), where a pane has the terminal's width.
- Once in **GNU screen**, for its Ctrl+A prefix.
- Once on the desktop app, if you have it: the same views by mouse, with no chord to teach.

## 4. The checklist

Tick each line in each terminal; where a line says *note*, write down what happened — those are the engine's behaviours
the code assumes but cannot test.

### Getting in and out

- [ ] `/neuroflow:dashboard` Enter: the pane opens on now and holds the keys — `2` shows the phase tab at once.
- [ ] `/neuroflow:dashboard` Enter, then `2` straight away: that first `2` does nothing; one half a second later works.
- [ ] Esc gives the keys back to the prompt and the pane stays; typing goes into the prompt. `q` closes it.
- [ ] `/neuroflow:dashboard` again, with the pane open: it holds the keys again.
- [ ] *Note* what ^X Tab focuses while the band shows keys and the dashboard is open, and how you get from the band to
  the pane and back.
- [ ] `d` on the band (after ^X Tab): the dashboard opens on now. *Note* whether it holds the keys; if not, its foot reads
  `/neuroflow:dashboard gives it the keys · ^X Tab reaches it after the band`.
- [ ] `5`, then `b`: the dashboard closes and the boards open holding the keys. Open the dashboard again
  (`/neuroflow:dashboard`), then `2` and `g`: the phase picker opens holding the keys.
- [ ] Esc in the picker closes it; `q` there does nothing.
- [ ] At 24 rows the dashboard takes about 10 rows and the conversation keeps room; at 40 rows about 18.
- [ ] *Note* whether `/neuroflow:dashboard` typed while a turn runs opens at 80 columns or waits until the turn ends.

### The band, at 80 and at 120 columns

Each state on one row, the most urgent item first and cut at its end with `…`. Until ^X Tab has given the band the keys
three times, `^X Tab: keys` ends the row wherever the item keeps its room beside it; the keys take their short words
(`x: hide`, `+1`) to make that room. Write each fixture state over the last one, then `/neuroflow:dashboard`, `r`, `q`:

```bash
python make_fixture.py ~/nf-live-check/oddball --band <state> --plugin <path to your neuroflow checkout>
```


- [ ] `--band deadline`: `⚠ Abstract deadline — tomorrow  d: dashboard  x: hide today  ^X Tab: keys`, at 80 columns too;
- [ ] `--band meeting`: the meeting in 45 minutes with `p: prepare  o: notes  d: dashboard` — at 80 columns `x: hide`
  and `+1`, so the meeting keeps its room, and no hint; at 120 `+1 more`, `x: hide today` and `^X Tab: keys`;
- [ ] `--band open-meeting`: the one left open, with `c: close meeting`; the hint at 120 columns only;
- [ ] `--band notice`: the version notice, cut at its end, with `m: migrate` — at 80 columns `x: hide` and
  `^X Tab: keys`, at 120 `x: hide today`; the dashboard shows the sentence whole under its title;
- [ ] `--band wiki`, `band` normal: `w: review`; at 120 columns the running loop beside the cards as the second item;
- [ ] a flowie sync that waits — `idea: live check` saves an idea to your own flowie and syncs it, so try it offline:
  `s: sync`;
- [ ] a drafted decision — run a full command such as `/neuroflow:data-analyze` and let its answer settle a choice
  without logging it: `y: keep  n: drop  d: dashboard`, with the highlight starting on `d`, never on keep;
- [ ] a driven loop — `/neuroflow:autoresearch drive connectivity` (it needs a real loop folder: `program.md` and
  `ar.py begin`; stop at once): `x: stop  d: dashboard`;
- [ ] a note capture — `/neuroflow:notes` in live mode: `x: stop`, which ends it as `done` does;
- [ ] the wellbeing check-in — your flowie's `wellbeing/config.json` with `"collect": true` and no entry today, on a band
  whose first item is no alert (`--band notice`, say): ^X Tab lands in the field; `x: not today` hides it.

And on every state:

- [ ] `^X Tab: keys` shows, where the row has room for it, until ^X Tab has given the band the keys three times, then not
  again, in later sessions too.
- [ ] Every letter acts once the band holds the keys; no digit does anything there.
- [ ] *Note* the colour the key letters are drawn in (`k: label`), in a dark and a light theme.

### The dashboard

- [ ] `1`–`6` pick the tabs; the shown tab reads as text, the others as keys; `h` and `l` step and wrap.
- [ ] Now lists every band item with its actions. From no highlight, `j` and `k` go to the tab's own name (`1: now`),
  then between the actions (*note* whether a hotkey moves it, or only Tab does); `m`, `y`, `p` and `s` do nothing there.
- [ ] Enter on an action asks first in Claude Code's question dialog, *Not now* (or *Keep it waiting*) on top: Enter
  there runs and writes nothing; the yes runs it. *Note* whether a digit typed into the dialog picks an option.
- [ ] Words typed for the prompt: open the dashboard, wait a second, type `ok` and Enter — nothing is kept, migrated or
  run, and no question appears. Type `k`, wait a second and press Enter: the tab is read again, nothing else.
- [ ] *Note* what Up and Down do in the pane: scroll, or nothing.
- [ ] *Note* what a letter with no key does while the pane holds the keys: dropped, or typed into the prompt.
- [ ] Integrity: `f` and `u` do nothing; Tab to *freeze prereg…* and Enter asks before it freezes, *unfreeze…* asks for a
  reason; `v` re-checks the hashes.
- [ ] `r` reads the files again.

### The task boards

- [ ] The digits pick the level; the shown level reads as text.
- [ ] The highlight starts on the first card; `h` and `l` move between columns, `j` and `k` within one; Tab works too.
- [ ] Enter on a card marks it `▸` and moves the highlight to the next column's target; `h`, `l`, `j` and `k` move
  between the targets; Enter there at project level asks first, *Not now* on top — Enter in the question leaves the card
  picked, the yes runs the move (it shows in the conversation); `x` cancels a pick.
- [ ] An Enter pressed at once after `h`, `j`, `k` or `l` does nothing; one a moment later acts.
- [ ] At a hive's level, Enter on a target only puts the command in the prompt; Esc and then Enter would send it — do not
  send it during the check.
- [ ] Another repository's board, read-only, has no card to pick.
- [ ] The six cards in active: five show, then `+1 more`; `j` on the fifth shows the sixth and `6–6 of 6`, `k` goes
  back to the first five; `h` or `l` from the sixth lands on the neighbour's first row.
- [ ] Narrow the dock (or the terminal) until a column would get under 18 cells: the columns stand one under the
  other, each with its name and count.

### The picker and the review panes

- [ ] Picker (`/neuroflow:phase`): each option names the phase first, then its mark and state — `◉ current` on
  data-analyze, `● visited · next` on paper (the fixture gives it a folder), `● visited` or `○ not started` on the rest.
  Down or Enter opens the list, a letter jumps to the phase that starts with it, Enter asks and a yes switches, Esc
  closes. *Note* whether the list takes letters for itself.
- [ ] Wiki cards (`/neuroflow:wiki --review`): `y` and `n` do nothing; Tab to *accept* and Enter asks first, and the yes
  runs `/neuroflow:wiki --add`; *skip* asks before it skips the card for good; `j` and `k`, `q`.
- [ ] X-ray (`/neuroflow:paper --xray view`): `y` and `n` do nothing; Tab to *accept* and Enter asks first; *reject…*
  asks for a reason, *Keep it open* on top; `j` past the eighth finding turns the page; `q`.
- [ ] Living paper (`/neuroflow:paper --auto status`): `s` does nothing — type `so which gaps…` into it; Tab to
  *sync now* and Enter asks first, and the yes runs the sync; `r`, `q`.
- [ ] Each review pane without the keys (Esc) reads `{its command} gives it the keys · ^X Tab reaches it after the band`
  at its foot.

### The look

Each view is drawn with characters: *note* every line below that does not hold.

- [ ] Each view starts with `◌` and its name (`◌ neuroflow`, `◌ tasks`, `◌ switch phase`, `◌ wiki cards`, `◌ X-ray`,
  `◌ living paper`); *note* whether your font draws `◌` (a dotted ring) or a box.
- [ ] The dashboard's tab rule: the heavy segment sits exactly under the shown tab, for each of the six; the closing
  rule fills the pane's width without wrapping to a second line.
- [ ] Rows with `⚠` or `✔` (the band, now, deadlines, integrity, a board card) keep the pane's right edge straight,
  and a board column's right border stays in line on a row with `⚠`; *note* any row where a glyph takes two cells.
- [ ] The phase tab: `◉` on the current phase, the line heavy (`━`) up to it and light after; where a phase would get
  under nine cells (under 45 columns for the fixture's five phases), the word list instead.
- [ ] The deadlines tab: the ruler's ticks fall every seven cells, tomorrow's `⚠` under day 1 and the ethics expiry's
  `▸` under day 12.
- [ ] The board's columns have round corners and dim borders; a long card ends in `…` inside its column.
- [ ] At 80 × 24 the dashboard is compact: the title on the mark's line, no blank rows, no summary under now, no
  closing rule. Inline at 120 columns the now tab stands as NEEDS ATTENTION beside AT A GLANCE (side by side needs a
  pane of 90 cells).
- [ ] Fullscreen at 120 columns: *note* how wide the docked dashboard (asks 64 columns) and boards (84) open. In a dock
  at its own width the now tab is stacked; widened until the pane has 90 cells (a dock of about 94 columns), it stands
  side by side.
- [ ] Light theme and 16 colours: the dim text, the warnings and the errors stay readable; nothing is drawn on a
  background colour except the engine's own focus highlight.

### Typeahead

- [ ] Type `/neuroflow:phase da`: under Claude Code's own rows, `data`, `data-analyze` and `data-preprocess` with
  their marks and states; taking one writes it over `da`.
- [ ] `/neuroflow:dashboard d` offers `deadlines`; `/neuroflow:tasks --level h` offers `hive`.
- [ ] After the boards, or the dashboard on its now or tasks tab, have been open once: `/neuroflow:tasks --move s`
  offers the `step-…` cards, then `/neuroflow:tasks --move step-1 r` offers `ready` and `review`.

### One chord per view

- [ ] With the recipe from [Keyboard and SSH](../concepts/mods.md#one-chord-per-view) in `~/.claude/keybindings.json`,
  Ctrl+X D, T and P open the dashboard, the boards and the picker holding the keys.
- [ ] *Note* what they do while a pane holds the keys, and while a turn runs.

### tmux and screen

- [ ] Inside tmux with `escape-time 10`, Esc gives the keys back at once.
- [ ] Inside screen, Ctrl+X, then Ctrl+A and `a`, collapses the band; ^X Tab works as it is.

## 5. The record

Write the Claude Code version, the terminals and every *note* into the pull request description. A key that does not do
what [the key tables](../concepts/mods.md#the-keys) say is a bug: open an issue with the terminal, the view and the key.
