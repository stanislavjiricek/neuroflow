---
title: The neuroflow mod
---

# The neuroflow mod

neuroflow is a Claude Code plugin. Besides its commands, skills and agents it ships an optional **mod**: a hooks module
(`hooks/mod/neuroflow.ts`) that runs inside Claude Code itself. The mod shows project state without spending tokens,
answers a few commands instantly, fills bookkeeping gaps, and enforces a small set of rules the skills already state.

The mod is a layer, not the product. Every command works without it — slower, and with the model doing the
bookkeeping — because the prose in `skills/` and `commands/` stays the source of truth.

!!! warning "Early access"
    Claude Code function hooks are an early-access API that changes between releases. The mod is tested against a
    minimum Claude Code version and a weekly canary on the latest release; when it cannot load, neuroflow keeps
    working as a plain plugin.

---

## Settings

Set them in Claude Code's plugin configuration (`/plugin` → neuroflow → configure) or in settings under
`pluginConfigs`. Values are per user; per-project facts stay in `.neuroflow/`.

| Setting | Values | Default | What it does |
|---|---|---|---|
| `runtime` | `off` · `observe` · `on` | `observe` | `off`: the mod does nothing. `observe`: views, status and warnings only — it never writes into project memory and never blocks. `on`: it also fills bookkeeping gaps and may enforce guards. |
| `guards` | `warn` · `enforce` | `warn` | `enforce` lets guards deny a tool call (only with `runtime: on`). `warn` says what a guard would have blocked. |
| `band` | `off` · `quiet` · `normal` | `quiet` | The one-line band above the prompt. `quiet` shows only what needs attention. |
| `citations` | on · off | off | Check that DOIs in manuscripts resolve after writes. |

## When the mod is not running

The module does not load when the rollout of plugin hooks modules has not reached your account, when hooks are
disabled by settings or policy, in safe mode, or on a Claude Code version older than the floor. Nothing breaks:
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
    pressed the button or confirmed in the turn (`set_by: person`); the model's edits to those markers are denied.
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

## Doors the guards cannot close

Guards see tool calls Claude Code routes through hooks. They cannot see or stop:

- what a Python, R or MATLAB script writes once it runs, or what a shell command does inside its own process;
- other shells and tools (PowerShell, Monitor), other plugins, and MCP servers acting on their own;
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
- `$` never crosses a file: the validator follows it only into functions declared in the same file, so helpers take an
  `NfIo` of closures (`ioOf($)` in each feature file). State references (`atom(...)`) are declared in the file that
  uses them. `$.env.get` takes literal names only.
- Every gating hook has a `.catch`: guards deny when they fail; observers pass the call through.
- Check with `claude plugin validate .` and `claude plugin test .` from the repo root; CI runs both and diffs the
  validator's inventory against `policy.json`.
