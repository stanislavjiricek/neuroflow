---
title: /autoresearch
---

# `/neuroflow:autoresearch`

**Infinite improvement loop — point it at any file(s) and it runs a worker-evaluator cycle indefinitely, keeping or reverting each change based on whether it improved the artifact.**

Inspired by Andrej Karpathy's autoresearch. Runs until you interrupt it.

---

## When to use it

- You want to improve a hypothesis, paper section, grant aim, or analysis plan overnight
- You want to leave something running and come back to a better version
- You want a live dashboard showing quality trends across iterations
- You want to explore what "continuous improvement" looks like for a research artifact

---

## How it works

### First run — initialization

1. Claude determines the active phase from `project_config.md`
2. You name the files to improve (or use `--target path/to/file.md`)
3. Criteria are built in three layers:
   - **Phase defaults** (e.g. paper: language, claim support, statistics, reproducibility, novelty)
   - **Context-inferred** (e.g. adds "aligns with preregistered hypotheses" if `preregistration/` exists)
   - **Your additions** (you can add any criteria before the loop starts)
4. A baseline snapshot is saved to `history/v000/`
5. A local dashboard server (`server.py`) is generated

```
Dashboard: python .neuroflow/{phase}/autoresearch/server.py → http://localhost:8765
```

### The loop — never stops until you interrupt

Each iteration:
1. **Worker** — makes one focused change to the tracked files (targets the weakest criterion)
2. **Evaluator** — compares the new version to the previous best and returns `BETTER / WORSE / NO CHANGE`
3. **Keep or revert** — if BETTER, the new version is archived to `history/vNNN/`; if WORSE, the previous best is restored
4. **Log** — result logged to `results.md` with verdict, delta, and next focus

---

## Invocation forms

| Form | Behaviour |
|---|---|
| `/autoresearch` | Uses active phase from `project_config.md` |
| `/autoresearch paper` | Targets the paper phase explicitly |
| `/paper autoresearch` | Any phase command + `autoresearch` keyword triggers this |
| `/paper autoresearch --target manuscript/intro.md` | Pre-fills the tracked file |

---

## Dashboard

```bash
python .neuroflow/{phase}/autoresearch/server.py
# → http://localhost:8765
# → http://localhost:8765?watch=1   (auto-refresh every 30s)
```

The dashboard shows:
- **Quality curve** — running delta over iterations (staircase: rises on KEPT, flat on REVERTED)
- **Numeric metric charts** — power, R², rejection rate, etc. when applicable
- **Last recommendation** — what the evaluator says to target next
- **Plateau warning** — triggered after 5 consecutive reversions

---

## Files created

```
.neuroflow/{phase}/autoresearch/
├── flow.md
├── program.md         # task + criteria (edit this to guide the loop)
├── __thetask__.md     # pointer to tracked files
├── results.md         # iteration log
├── server.py          # dashboard server
└── history/
    ├── v000/          # baseline
    ├── v001/          # first KEPT improvement
    └── ...
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, tracked external files, `program.md`, `results.md`, `history/` snapshots |
| Writes | `.neuroflow/{phase}/autoresearch/`, tracked external files (on KEPT), `history/vNNN/` snapshots |

---

## Related

- [`neuroflow:autoresearch` skill](../skills/autoresearch/SKILL/) — full protocol, criteria, and dashboard template
- [`/paper`](paper.md) — uses the worker-critic loop (bounded, 3 iterations) for section drafting
- [`/pipeline`](pipeline.md) — multi-step orchestration across phases
