---
title: /ethics
---

# `/neuroflow:ethics`

**Ethics and IRB workflow — the hard gate before human data collection.**

Tracks protocol submissions and amendments, versions consent forms, and keeps the approval status — including the expiry date — visible across the whole project.

---

## Modes

| Mode | What it does |
|---|---|
| *(none)* / `--status` | Approval dashboard — status, dates, consent version, amendments, AI processing |
| `--protocol` | Draft or update the ethics protocol; log amendments (append-only) |
| `--consent` | Create or revise a consent form — always as a new version, never edited in place |
| `--approved` | Record an approval: committee, reference, approval date, expiry date, and whether participant data may be read by the AI model |
| `--erase` | A participant asked for erasure: record it, run the sweep, work through the checklist |

---

## Why it matters

- **Consent forms are versioned** because participants signed a specific version — it must stay retrievable exactly as signed.
- **Expiry dates go to `timeline.md`**, so [`/phase`](phase.md) shows an approaching expiry without you running `/ethics`.
- **The gate is enforced in the workflow.** `status.md` starts with a small machine-readable block (`status`, `approval_id`, `expires`, `ai_processing`, `set_by`, `set_at`). [`/data`](data.md) and [`/experiment`](experiment.md) read it and stop every step that involves participants while the approval is missing, expired, or recorded without your confirmation (`set_by: model`). Projects without participants note `ethics: not-applicable`.
- **The gate is checked**: if data exists but no approval is recorded (or data predates it), `/ethics --status` and the [sentinel](sentinel.md) audit both warn.
- **Reading participant data with an AI model is a data transfer.** Everything the model reads goes to the model provider and into Claude Code's local transcripts. `ai_processing` (`none`, `pseudonymised`, `identifiable`) records what your approval, consent form and data-protection officer allow under applicable law (e.g. GDPR or HIPAA); with `none`, Claude writes the scripts, you run them, and Claude works from the aggregate output.
- **Erasure requests are a checklist, not a single delete.** `--erase` lists every place a participant's data can hide — derivatives, project memory, git history, Claude Code's own transcripts and caches, personal and team caches, external services — and `erasure_sweep.py` finds every file that mentions the ID. It reports paths and counts only and never deletes; you run it in your own terminal and decide.
- **Participants only ever see validated software** — stimuli, questionnaires and consent never run inside Claude Code.
- [`/output --archive`](output.md) reads the consent version in force before letting a dataset go public.

Everything lives in `.neuroflow/ethics/` with `status.md` as the single source of truth.

---

## Related

- [`/preregistration`](preregistration.md) — study design registration (scientific commitment; ethics is the legal/administrative one)
- [`/experiment`](experiment.md) — participant sessions, pilots and allocation happen only behind this gate
- [`/data`](data.md) — data intake happens only behind this gate
