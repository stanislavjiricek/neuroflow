---
name: hypothesis-generation
description: Use when formulating neuroscience research hypotheses, defining research questions, applying PICO framework, operationalizing variables, or designing experimental logic. Triggers when users ask to "generate hypotheses", "define research question", "what should we study", "operationalize variables", "create a study design", or discuss scientific rationale for a neuroscience study.
version: 1.0.0
---

# Hypothesis Generation for Neuroscience Research

## Purpose

Guide researchers from a raw research idea to a set of testable, operationalized hypotheses grounded in the neuroscience literature.

## When This Skill Applies

- Formulating primary and secondary research hypotheses
- Applying the PICO (Population, Intervention, Comparison, Outcome) framework
- Operationalizing abstract concepts into measurable neural/physiological variables
- Designing the logical flow from RQ → hypothesis → expected results
- Aligning hypotheses with suitable modalities and analysis methods

## Core Framework

### 1. Research Question (RQ) Clarification

Define the RQ precisely:
- **Domain**: Which cognitive/neural domain? (attention, memory, motor, emotion…)
- **Population**: Healthy adults? Clinical group? Age range? N?
- **Context**: Rest, task, stimulation, pharmacological?
- **Level of analysis**: Single unit, ERP, oscillatory, connectivity, BOLD?

### 2. PICO Application in Neuroscience

| Element | Neuroscience Adaptation |
|---|---|
| **Population** | Participant group (healthy, clinical, age-stratified) |
| **Intervention/Condition** | Experimental manipulation or condition |
| **Comparison** | Control condition, baseline, or alternative group |
| **Outcome** | Neural measure (amplitude, latency, power, BOLD, connectivity) |

### 3. Hypothesis Structure

Each hypothesis should specify:
- **Direction**: Increase / decrease / difference / correlation
- **Neural measure**: Specific DV (e.g., N200 amplitude at Fz, alpha power 8–12 Hz at Pz)
- **Condition**: Under what experimental conditions
- **Theoretical grounding**: Which framework/prior findings support this

**Template:**
> *We hypothesize that [population] will show [increase/decrease] in [neural measure] at [electrode/ROI] during [condition] compared to [control condition], consistent with [theoretical framework/prior finding].*

### 4. Operationalization Checklist

For each hypothesis, define:
- [ ] Independent variable (IV): manipulation type, levels
- [ ] Dependent variable (DV): exact neural measure, time window, frequency band, ROI
- [ ] Covariates: age, sex, IQ, medication, session
- [ ] Exclusion criteria: artifact threshold, behavioral performance cutoff
- [ ] Expected effect size (Cohen's d / η²) based on literature

### 5. Alignment with Modality

| Hypothesis type | Recommended modality |
|---|---|
| Temporal dynamics (<10 ms resolution) | EEG / iEEG |
| Spatial localization (mm resolution) | fMRI |
| Arousal / autonomic | ECG, EDA |
| Gaze-linked cognitive load | Eye tracking |
| High-freq oscillations, single unit proxy | iEEG |

### 6. Output Format

Produce:
1. **Primary hypothesis** (H1): Main expected effect
2. **Secondary hypotheses** (H2–Hn): Exploratory or auxiliary predictions
3. **Null hypothesis** (H0): What absence of effect would mean
4. **Alternative explanations**: What else could produce the observed pattern

## Common Pitfalls

- Circular hypotheses that merely restate the design
- Failure to specify exact time windows / frequency bands a priori
- Ignoring individual differences that could mask effects
- Hypothesizing without referencing effect sizes (underpowered designs)
