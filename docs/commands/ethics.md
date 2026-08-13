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
| *(none)* / `--status` | Approval dashboard — status, dates, consent version, amendments |
| `--protocol` | Draft or update the ethics protocol; log amendments (append-only) |
| `--consent` | Create or revise a consent form — always as a new version, never edited in place |
| `--approved` | Record an approval: committee, reference, approval date, expiry date |

---

## Why it matters

- **Consent forms are versioned** because participants signed a specific version — it must stay retrievable exactly as signed.
- **Expiry dates go to `timeline.md`**, so [`/phase`](phase.md) shows an approaching expiry without you running `/ethics`.
- **The gate is checked**: if data exists but no approval is recorded (or data predates it), `/ethics --status` and the [sentinel](sentinel.md) audit both warn.
- [`/output --archive`](output.md) reads the consent version in force before letting a dataset go public.

Everything lives in `.neuroflow/ethics/` with `status.md` as the single source of truth.

---

## Related

- [`/preregistration`](preregistration.md) — study design registration (scientific commitment; ethics is the legal/administrative one)
- [`/data`](data.md) — data intake happens only behind this gate
