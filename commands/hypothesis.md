---
description: Guide a neuroscience researcher through formulating, operationalizing, and documenting testable research hypotheses using the PICO framework. Produces a hypothesis document ready for pre-registration.
argument-hint: [research-area]
allowed-tools: [Read, Write]
---

# /hypothesis — Hypothesis Formulation

You are guiding a neuroscience researcher through the process of formulating and operationalizing their research hypotheses.

**Research area**: $ARGUMENTS

## Your Task

Lead an interactive, structured dialogue to produce a complete hypothesis document. Ask one group of questions at a time.

## Dialogue Flow

### Step 1: Research Question
Ask:
- "What phenomenon are you trying to understand or measure?"
- "What population are you studying?"
- "What experimental manipulation or contrast are you making?"
- "What neural/behavioral outcome do you expect to differ?"

### Step 2: PICO Framework
Apply PICO to their answer:
- **Population**: Who are the participants?
- **Intervention/Condition**: What is the experimental manipulation?
- **Comparison**: What is the control condition or group?
- **Outcome**: What neural or behavioral measure is the DV?

Show your PICO formulation and ask if it captures their intent.

### Step 3: Hypothesis Specification
For each hypothesis, elicit:
1. **Direction**: Will the DV increase, decrease, or differ?
2. **Neural measure specifics**: Exact component (N200 at Fz?), time window, frequency band, ROI
3. **Statistical threshold**: p < .05? Bayesian? What correction?
4. **Expected effect size**: Based on prior studies (ask if they know of any)

### Step 4: Modality Alignment
Check: Does the hypothesis require a resolution the chosen modality can provide?

### Step 5: Generate Hypothesis Document

Produce a `hypotheses.md` file:

```markdown
# Research Hypotheses: {study name}
Date: {today}

## Research Question
{one sentence}

## PICO
- Population: ...
- Intervention: ...
- Comparison: ...
- Outcome: ...

## Primary Hypothesis (H1)
{specific, directional, operationalized statement}
Expected measure: {e.g., N200 amplitude at Fz, 150–250 ms}
Expected direction: {increase/decrease}
Expected effect size: {Cohen's d = X, based on ...}
Statistical criterion: {p < .05, cluster-corrected}

## Secondary Hypotheses
### H2: ...
### H3: ...

## Null Hypothesis (H0)
{what absence of effect would mean}

## Alternative Explanations
- {What else could produce the observed pattern?}

## Open Questions
- {What needs to be decided before analysis?}
```

Save the file and confirm. Suggest running `/paradigm` next.
