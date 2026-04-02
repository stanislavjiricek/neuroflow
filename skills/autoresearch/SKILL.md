---
name: autoresearch
description: Infinite improvement loop for any research artifact in any phase — worker makes one focused change per iteration, evaluator compares to previous best, keeps or reverts. Loop never stops until the human interrupts it. Inspired by Andrej Karpathy's autoresearch (MIT).
---

<!-- Inspired by Andrej Karpathy's autoresearch (MIT) — https://github.com/karpathy/autoresearch -->

# autoresearch

An infinite, multi-session improvement loop for any research artifact. A worker agent makes one focused change per iteration; an evaluator compares the result to the previous best and returns BETTER / WORSE / NO CHANGE. The best version is kept; worse versions are reverted. The loop never stops on its own.

---

## Core rule — NEVER STOP

**The loop runs until the human interrupts it. Period.**

- Never decide the artifact is "good enough" and exit
- Never stop because the score plateaued
- Never stop because iterations look repetitive
- Plateau detection is a notification, not a termination condition
- The only valid exit is the user pressing Ctrl-C or typing a stop command

---

## File structure (created in user's project)

```
.neuroflow/{phase}/autoresearch/
├── flow.md
├── program.md         # task + criteria (phase defaults + context-inferred + user-added)
├── __thetask__.md     # pointer manifest — lists which external files are tracked
├── results.md         # iteration log (verdict, delta, running, decision, next focus)
├── server.py          # local dashboard — serves http://localhost:8765
└── history/
    ├── v000/          # baseline snapshot of tracked files
    ├── v001/          # snapshot saved on each KEPT iteration
    └── ...
```

**`__thetask__.md` is a pointer, not the artifact itself.** It lists paths to the external files being improved (e.g. `manuscript/introduction.md`, `.neuroflow/ideation/hypothesis.md`, `scripts/analysis/pipeline.py`). Workers modify those files directly. The evaluator compares current file state to the last `history/vBEST/` snapshot.

---

## `__thetask__.md` format

```markdown
# Task Manifest

## Tracked files
- `../../../manuscript/introduction.md`
- `../../../manuscript/methods.md`

## Task description
Continuously improve the introduction and methods until they pass peer review.

## Current best snapshot
history/v004/

## Iterations run
12 (last: YYYY-MM-DD)
```

---

## `program.md` template

```markdown
# Autoresearch Program — {phase}
Started: YYYY-MM-DD

## Task
{one sentence: what is being improved and why}

## Tracked files
{listed from __thetask__.md for reference}

## Default criteria (phase: {phase})
{phase-specific criteria — see per-phase table below}

## User criteria
<!-- Add your own criteria here, e.g.:
     - Must cite at least 3 papers from 2022–2025
     - Keep under 500 words
     - Target: Nature Neuroscience  -->

## Improvement direction
{what "better" looks like — guiding instruction for the worker each iteration}

## Out of scope
{what must NOT change between iterations}
```

---

## Criteria initialization — three layers

On first run, build `program.md` criteria in three layers:

**Layer 1 — Phase defaults** (always included; see per-phase table in this skill)

**Layer 2 — Context-inferred** (read existing `.neuroflow/` files and infer relevant additions):

| If this exists | Add criterion |
|---|---|
| `.neuroflow/ideation/research-question.md` | "Alignment with stated research question" |
| `.neuroflow/preregistration/` | "Adherence to preregistered hypotheses / analysis plan" |
| `project_config.md` has `target_journal:` | "Meets [journal] editorial standards" |
| `.neuroflow/grant-proposal/` has a named funder | "Meets [funder] reviewer criteria (Significance / Innovation / Approach)" |
| `.neuroflow/data-analyze/analysis-plan.md` | "Covers all hypotheses from the analysis plan" |
| `.neuroflow/objectives.md` | "Addresses all project objectives" |

**Layer 3 — User input**

After printing layers 1+2, ask:
```
These criteria will guide autoresearch. Add your own? (press Enter to skip)
```
Append any user additions to `program.md` under `## User criteria`.

---

## Per-phase default criteria (Layer 1)

### paper
Drawn from `agents/paper-critic.md` — six evaluation areas:
1. **Language, style, terminology** — spelling, grammar, undefined abbreviations, causality language errors (e.g. "X activates Y" from correlational data)
2. **Internal consistency** — all figures referenced exist and are numbered correctly; numerical values match across sections; subject counts consistent
3. **Claim support** — every claim has evidence; no causality creep; no functional-connectivity overclaims; no over-generalization beyond the sample
4. **Statistics** — power justification, correct test choice, effect sizes reported, multiple-comparison correction stated and justified
5. **Methods reproducibility** — COBIDAS compliance for fMRI; ARRIVE 2.0 for animals; electrode montage and reference stated for EEG; data and code availability statement
6. **Contribution and novelty** — novelty grounded relative to specific prior papers; alternative interpretations addressed; journal fit justified

### grant-proposal
Drawn from `skills/phase-grant-proposal/SKILL.md`:
1. **Scope** — all aims achievable within the stated timeline; no aim requires success of another unless stated
2. **Power analysis** — formal power analysis per aim with effect size cited from published literature
3. **Hypothesis in Approach** — every aim has a testable prediction, not just a description of methods
4. **Funder alignment** — Significance framed for funder priority (NIH: disease burden / mechanism; ERC: frontier science; Wellcome: scientific opportunity)
5. **Preliminary data** — at least one result figure per aim with statistics visible
6. **Budget justification** — every budget line has a rationale; FTE fractions stated; equipment identified by model

### ideation
1. **Novelty** — question not already answered in the cited literature; state the closest prior paper
2. **Testability** — can be empirically tested with standard neuroscience methods in a reasonable timeframe
3. **Specificity** — stated as one sentence with named independent variable, dependent variable, and population
4. **Feasibility** — achievable by a neuroscience lab given realistic equipment, sample, and timeline constraints
5. **Mechanistic grounding** — proposes a biological or computational mechanism, not just a correlational observation

### data-analyze
1. **Plan precedes code** — analysis-plan.md written and accepted before any analysis script
2. **Assumption audit** — normality, sphericity, and independence checked explicitly before test selection
3. **Multiple comparison correction** — method named (FWE, FDR, Bonferroni) and justified for the design
4. **Reproducibility** — script is self-contained and re-runnable from raw inputs alone
5. **Coverage** — all hypotheses listed in project_config.md are addressed
6. **Numeric** — statistical power (target ≥ 0.8), effect size (Cohen's d or η²), N per condition reported

### experiment
1. **Ecological validity** — experimental conditions reflect the real-world scenario being studied
2. **Control conditions** — every independent variable has a matched control condition
3. **Counterbalancing** — order effects addressed; counterbalancing scheme stated
4. **Confound identification** — known confounds listed; design choices explain how each is controlled
5. **Numeric** — formal power analysis with target power ≥ 0.8; trial count per condition stated

### preregistration
1. **Specificity** — hypothesis statement has no wiggle room; can be unambiguously confirmed or disconfirmed
2. **Prior grounding** — at least one prior result cited per directional prediction
3. **Falsifiability** — defined rejection criterion (threshold, direction) for each hypothesis
4. **Analysis plan completeness** — exact statistical tests, thresholds, exclusion rules, and dependent variable operationalization stated
5. **Deviation protocol** — explicitly states what will be done if a planned analysis cannot run as specified

### brain-build
1. **Biological plausibility** — all parameters fall within physiologically reported ranges (cite sources)
2. **Formal completeness** — every equation and free parameter defined; no undefined symbols
3. **Testability** — model makes at least two specific, falsifiable empirical predictions
4. **Parameter justifiability** — each free parameter sourced from data, prior fit, or justified literature estimate
5. **Data relationship** — relationship between model output and empirical recordings explicitly stated

### brain-optimize
1. **Convergence evidence** — optimization converged (loss curve shown or stability criterion met)
2. **Objective alignment** — cost function reflects the scientific question being asked
3. **Sensitivity justification** — parameters the optimizer was most sensitive to are identified and discussed
4. **Generalisability** — fit not only to training data; held-out or cross-validated performance reported
5. **Numeric** — final loss / R² / correlation with empirical data reported per iteration

### brain-run
1. **Output clarity** — outputs are labelled, units stated, axes named
2. **Parameter documentation** — full parameter set used for the run is saved alongside outputs
3. **Reproducibility** — run is reproducible from the saved parameter set alone
4. **Interpretation soundness** — results interpreted within the bounds of model assumptions
5. **Limitation acknowledgment** — at least one key model limitation noted in context of the outputs

### data-preprocess
1. **Pipeline completeness** — all steps from raw to analysis-ready documented in order
2. **Artifact handling** — ocular, muscle, and line-noise artifacts addressed; strategy stated
3. **BIDS compliance** — output folder structure matches BIDS specification
4. **Reproducibility** — pipeline re-runnable from the script alone with no manual steps
5. **Numeric** — channel rejection rate (flag if > 20%), epoch rejection rate, and SNR estimate reported

### poster / slideshow / write-report
1. **Visual / structural hierarchy** — most important claim is the most prominent element
2. **Core claim clarity** — the main message is readable or identifiable within 5 seconds
3. **Evidence density** — every claim has at least one supporting data point or citation visible
4. **Audience targeting** — vocabulary and technical depth match the stated audience
5. **Narrative flow** — logical order; each panel or section leads naturally to the next

### all other phases
Clarity, Completeness, Scientific rigour, Feasibility, Audience alignment

---

## Loop protocol

### INIT (first run only)

1. Read `project_config.md` → determine active phase
2. Create `.neuroflow/{phase}/autoresearch/`
3. Ask: *"Which files should autoresearch improve?"* (or infer from `--target` flag in the invocation)
4. Build criteria: Layer 1 + Layer 2 (from context) + Layer 3 (user input) → write to `program.md`
5. Copy current state of tracked files into `history/v000/` (baseline snapshot)
6. Write baseline row to `results.md`
7. Write `server.py` into `.neuroflow/{phase}/autoresearch/server.py` using the template in the **Dashboard server template** section of this skill
8. Tell the user: *"Dashboard: run `python .neuroflow/{phase}/autoresearch/server.py` → http://localhost:8765"*
9. Write `flow.md` for the autoresearch folder
10. Start loop

### LOOP — NEVER STOP

```
REPEAT FOREVER until the human interrupts:

  a. Read program.md + __thetask__.md → resolve tracked file paths
  b. Read tracked files (current state)
  c. Read results.md tail (last 5 rows) — what was tried recently
  d. Read history/vBEST/ snapshot (the current best version)

  e. WORKER — spawn general-purpose agent:
       Prompt contains:
         - Phase skill content (neuroflow:phase-{phase})
         - program.md (task, criteria, improvement direction, out of scope)
         - Current content of tracked files
         - results.md tail for context
         - Instruction: "Make ONE focused improvement targeting the weakest criterion.
                         Do NOT rewrite everything. Make one surgical change.
                         Return only the modified file(s) with the change applied."

  f. EVALUATOR — spawn general-purpose agent:
       Prompt contains:
         - Criteria from program.md
         - Current tracked files (post-worker)
         - history/vBEST/ snapshot (previous best)
         - Instruction: "Compare these two versions of the tracked files.
                         Is the new version BETTER, WORSE, or NO CHANGE relative to the previous best?
                         Return exactly:
                           VERDICT: BETTER | WORSE | NO CHANGE
                           Delta: integer −5 (much worse) to +5 (much better)
                           Criteria notes: per-criterion one-line assessment
                           Numeric values: extract any numeric criteria values if applicable
                             (power, R², rejection rate, loss, word count, citation count, etc.)
                           Next focus: one sentence — the single weakest area to target next"

  g. If BETTER:
       - Save current state of tracked files → history/vNNN/ (N = zero-padded iteration number)
       - Update __thetask__.md: increment "Iterations run", update "Current best snapshot"
       - Append KEPT row to results.md
       - Update flow.md

  h. If WORSE or NO CHANGE:
       - Restore tracked files from history/vBEST/ (overwrite tracked files with snapshot content)
       - Append REVERTED row to results.md

  i. Plateau detection — if 5 consecutive REVERTs:
       - Append "--- PLATEAU DETECTED (5 consecutive REVERTs) ---" to results.md
       - Print: "5 consecutive reversions with no improvement.
                 Consider adding new directions to program.md under '## User criteria'
                 or '## Improvement direction'. Continuing loop."
       - DO NOT STOP — continue the loop

  j. Go to step a. NEVER stop on your own.
```

---

## Evaluator output format

```
VERDICT: BETTER

Delta: +3

Criteria notes:
- Language/style: no change — prose quality unchanged
- Claim support: improved — mechanism sentence added, previously missing
- Statistics: improved — power value now cited (0.74)
- Methods reproducibility: no change
- Contribution/novelty: no change

Numeric values:
- power: 0.74
- word_count: 487

Next focus: The intro-to-methods transition is abrupt — add a single bridging sentence.
```

---

## `results.md` format

```markdown
# Autoresearch Results — {phase}
Started: YYYY-MM-DD HH:MM

| # | Verdict | Δ | Running | Decision | Next focus |
|---|---------|---|---------|----------|------------|
| 000 | — | 0 | 0 | KEPT (baseline) | — |
| 001 | BETTER | +3 | 3 | KEPT | Intro–methods transition |
| 002 | WORSE | -1 | 3 | REVERTED | Overcomplicated methods |
| 003 | BETTER | +2 | 5 | KEPT | Citation density in Discussion |
```

For phases with numeric criteria, append columns after `Next focus` (e.g. `power`, `R2`, `word_count`).

**Running column rules:**
- KEPT: running = previous running + delta
- REVERTED: running = unchanged (file was restored; quality is the same as before)

---

## Session logging

Append to `.neuroflow/sessions/YYYY-MM-DD.md` at:
- Loop start: `## HH:MM — [autoresearch/{phase}] loop started — tracking {N} file(s)`
- Every 10 iterations: `## HH:MM — [autoresearch/{phase}] iteration {N} — running quality: {R} — best: {snapshot}`
- Plateau detection: `## HH:MM — [autoresearch/{phase}] PLATEAU — 5 consecutive REVERTs`
- Loop interrupted: `## HH:MM — [autoresearch/{phase}] loop interrupted at iteration {N} — best: history/{snapshot}/`

---

## Slash command

`/autoresearch` or any phase command invoked with the keyword `autoresearch` in the prompt.

---

## Dashboard server template

Write the following Python script verbatim to `.neuroflow/{phase}/autoresearch/server.py` during INIT. It uses Python stdlib only plus Chart.js from CDN — no pip installs required.

```python
#!/usr/bin/env python3
"""
Autoresearch dashboard — serves http://localhost:8765
Reads results.md on every request; auto-refreshes with ?watch=1
Usage: python server.py [--port 8765]
"""
import argparse
import csv
import io
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.md")
THETASK_FILE = os.path.join(os.path.dirname(__file__), "__thetask__.md")


def parse_results():
    """Parse results.md table into list of dicts."""
    rows = []
    if not os.path.exists(RESULTS_FILE):
        return rows
    with open(RESULTS_FILE, encoding="utf-8") as f:
        content = f.read()
    in_table = False
    headers = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("| #") or line.startswith("|#"):
            headers = [h.strip() for h in line.strip("|").split("|")]
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= len(headers):
                rows.append(dict(zip(headers, cells)))
        elif in_table and not line.startswith("|"):
            if line.startswith("---"):
                continue  # section divider in results
    return rows


def parse_thetask():
    """Return task description and tracked files from __thetask__.md."""
    if not os.path.exists(THETASK_FILE):
        return "", [], "history/v000", 0
    with open(THETASK_FILE, encoding="utf-8") as f:
        content = f.read()
    desc = re.search(r"## Task description\n(.+?)(?:\n##|\Z)", content, re.S)
    desc = desc.group(1).strip() if desc else ""
    files_section = re.search(r"## Tracked files\n(.+?)(?:\n##|\Z)", content, re.S)
    files = []
    if files_section:
        for line in files_section.group(1).splitlines():
            line = line.strip().strip("-").strip().strip("`")
            if line:
                files.append(line)
    best = re.search(r"## Current best snapshot\n(.+)", content)
    best = best.group(1).strip() if best else "history/v000"
    iters = re.search(r"## Iterations run\n(\d+)", content)
    iters = int(iters.group(1)) if iters else 0
    return desc, files, best, iters


def build_html(rows, desc, files, best, iters, watch):
    labels = [r.get("#", "") for r in rows]
    running = []
    for r in rows:
        try:
            running.append(float(r.get("Running", 0)))
        except ValueError:
            running.append(0)

    # collect numeric columns (anything after "Next focus")
    all_keys = []
    if rows:
        all_keys = list(rows[0].keys())
    std_keys = {"#", "Verdict", "Δ", "Running", "Decision", "Next focus"}
    num_keys = [k for k in all_keys if k not in std_keys and k]

    num_datasets = []
    for key in num_keys:
        vals = []
        for r in rows:
            try:
                vals.append(float(r.get(key, "").replace("—", "").replace("nan", "") or "nan"))
            except ValueError:
                vals.append(None)
        num_datasets.append({"label": key, "data": vals})

    kept_points = [
        {"x": r.get("#", ""), "y": float(r.get("Running", 0))}
        for r in rows if "KEPT" in r.get("Decision", "")
        if r.get("#") and r.get("Running")
    ]
    reverted_points = [
        {"x": r.get("#", ""), "y": float(r.get("Running", 0))}
        for r in rows if "REVERTED" in r.get("Decision", "")
        if r.get("#") and r.get("Running")
    ]

    last_focus = rows[-1].get("Next focus", "—") if rows else "—"
    plateau = any("PLATEAU" in r.get("Decision", "") for r in rows)

    refresh = '<meta http-equiv="refresh" content="30">' if watch else ""

    num_charts_html = ""
    for ds in num_datasets:
        clean_vals = [v if v is not None else "null" for v in ds["data"]]
        num_charts_html += f"""
        <div class="chart-wrap">
          <canvas id="chart_{ds['label']}"></canvas>
        </div>
        <script>
        new Chart(document.getElementById('chart_{ds["label"]}'), {{
          type: 'line',
          data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
              label: '{ds["label"]}',
              data: {json.dumps(clean_vals)},
              borderColor: '#a78bfa',
              backgroundColor: 'rgba(167,139,250,0.15)',
              tension: 0.3,
              spanGaps: true,
            }}]
          }},
          options: {{ responsive: true, plugins: {{ legend: {{ display: true }} }} }}
        }});
        </script>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{refresh}
<title>Autoresearch Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f0f13; color: #e2e8f0; margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; color: #c4b5fd; }}
  .meta {{ font-size: 0.82rem; color: #94a3b8; margin-bottom: 20px; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .card {{ background: #1e1e2e; border-radius: 10px; padding: 16px 20px; min-width: 160px; }}
  .card-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }}
  .card-value {{ font-size: 1.6rem; font-weight: 700; color: #c4b5fd; }}
  .plateau {{ color: #f59e0b; font-weight: bold; }}
  .chart-wrap {{ background: #1e1e2e; border-radius: 10px; padding: 16px; margin-bottom: 20px; }}
  .focus-box {{ background: #1e1e2e; border-left: 3px solid #c4b5fd; padding: 12px 16px;
                border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 0.9rem; }}
  .files {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
</style>
</head>
<body>
<h1>Autoresearch Dashboard</h1>
<div class="meta">{desc}</div>
<div class="files">Tracked: {" &nbsp;·&nbsp; ".join(files)}</div>
<div class="meta">Best snapshot: {best} &nbsp;·&nbsp; Iterations: {iters}</div>

<div class="cards">
  <div class="card"><div class="card-label">Iterations</div><div class="card-value">{iters}</div></div>
  <div class="card"><div class="card-label">Running quality</div>
    <div class="card-value">{running[-1] if running else 0:+.0f}</div></div>
  <div class="card"><div class="card-label">Last verdict</div>
    <div class="card-value" style="font-size:1.1rem">{rows[-1].get("Verdict","—") if rows else "—"}</div></div>
  {"<div class='card'><div class='card-label plateau'>⚠ Plateau</div><div class='card-value plateau'>5 REVERTs</div></div>" if plateau else ""}
</div>

<div class="focus-box"><strong>Next focus:</strong> {last_focus}</div>

<div class="chart-wrap">
  <canvas id="qualityChart"></canvas>
</div>
<script>
new Chart(document.getElementById('qualityChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [
      {{
        label: 'Running quality',
        data: {json.dumps(running)},
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129,140,248,0.1)',
        tension: 0.2,
        fill: true,
      }},
      {{
        label: 'KEPT',
        data: {json.dumps([r.get("Running") if "KEPT" in r.get("Decision","") else None for r in rows])},
        borderColor: 'rgba(0,0,0,0)',
        backgroundColor: '#34d399',
        pointRadius: 7,
        pointHoverRadius: 9,
        showLine: false,
        spanGaps: false,
      }},
      {{
        label: 'REVERTED',
        data: {json.dumps([r.get("Running") if "REVERTED" in r.get("Decision","") else None for r in rows])},
        borderColor: 'rgba(0,0,0,0)',
        backgroundColor: '#f87171',
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: false,
        spanGaps: false,
      }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: true }} }},
    scales: {{ y: {{ grid: {{ color: '#2d2d3d' }}, ticks: {{ color: '#94a3b8' }} }},
               x: {{ grid: {{ color: '#2d2d3d' }}, ticks: {{ color: '#94a3b8' }} }} }}
  }}
}});
</script>

{num_charts_html}

</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs

    def do_GET(self):
        watch = "watch=1" in self.path
        rows = parse_results()
        desc, files, best, iters = parse_thetask()
        html = build_html(rows, desc, files, best, iters, watch)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Autoresearch dashboard → http://localhost:{args.port}")
    print(f"Auto-refresh: http://localhost:{args.port}?watch=1")
    print("Ctrl-C to stop")
    HTTPServer(("", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
```
