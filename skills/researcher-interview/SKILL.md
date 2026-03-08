---
name: researcher-interview
description: Use when a technical team needs to interview researchers or PI to scope a neuroscience study, gather requirements, understand the scientific goal, determine recording parameters, or plan a collaboration. Triggers on "interview the researcher", "talk to the PI", "gather requirements for the study", "what should we ask the researcher", "project scoping interview", or "understand what they want to measure".
version: 1.0.0
---

# Researcher Interview Guide

## Purpose

Help technical team members (engineers, programmers, data scientists) conduct structured interviews with neuroscience researchers or PIs to extract all information needed to plan, implement, and analyze a study.

## When This Skill Applies

- Technical team onboarding to a new neuroscience project
- Scoping a collaboration between engineers and researchers
- Clarifying ambiguous requirements before paradigm development
- Defining data recording parameters and storage structure

## Interview Structure

### Phase 1: Scientific Goal (10 min)

1. "What is the main research question?"
2. "What is your primary hypothesis? What direction of effect do you expect?"
3. "Why this modality — what does it give you that others don't?"
4. "Is there a clinical application or translation goal?"
5. "What prior studies does this build on?"

### Phase 2: Participants & Ethics (5 min)

1. "How many participants? What population (age, sex, clinical status)?"
2. "Do you have ethics approval? What number/reference?"
3. "Are there exclusion criteria we need to screen for?"
4. "Will participants be compensated? Any data retention constraints (GDPR)?"

### Phase 3: Experimental Design (15 min)

1. "Describe the paradigm — what does the participant see / do / hear?"
2. "How many conditions, blocks, trials? Inter-trial interval?"
3. "What are the critical events we need to mark in the signal?"
4. "Is there a response (button press, eye movement, verbal)?"
5. "What software are you expecting to use (PsychoPy, Presentation, E-Prime)?"
6. "Should the paradigm be adaptive / closed-loop in any way?"

### Phase 4: Recording Setup (10 min)

1. "Which recording system? (BrainProducts, g.tec, Biosemi, Neuralynx…)"
2. "Sampling rate? Number of channels? Reference electrode?"
3. "Any additional physio signals? (ECG, EMG, eye tracker, respiration)"
4. "How are markers/triggers sent? (parallel port, LSL, serial, audio)"
5. "Online monitoring needed? Any real-time feedback?"
6. "Storage format expected? (EDF, BDF, XDF, BIDS?)"

### Phase 5: Analysis & Output (10 min)

1. "What analysis pipeline do you envision? (MNE, EEGLAB, SPM, custom)"
2. "Is there a specific feature you want extracted? (ERP, power, connectivity)"
3. "What statistical test do you expect? (t-test, ANOVA, permutation)"
4. "Are there existing scripts from prior studies we should be compatible with?"
5. "What is the expected output — figures, stats table, paper?"
6. "Which journal / conference is the target?"

### Phase 6: Logistics (5 min)

1. "What is the timeline — when is data collection planned?"
2. "Who is responsible for each component (recording, paradigm, analysis)?"
3. "How should we communicate and hand off files?"
4. "Are there dependencies on equipment availability?"

## Output

After the interview, produce a structured **Project Brief** containing:

```markdown
## Project Brief: [Study Name]

**PI / Contact**: ...
**Date**: ...

### Scientific Goal
...

### Participants
- N: ...
- Population: ...
- Ethics: ...

### Paradigm
- Conditions: ...
- Trials: ...
- Duration: ...

### Recording
- System: ...
- Channels: ...
- Sampling rate: ...
- Markers: ...
- Additional signals: ...

### Analysis Plan
- Pipeline: ...
- Target features: ...
- Statistics: ...

### Output
- Target journal: ...
- Timeline: ...
- Team roles: ...
```

## Tips

- Avoid jargon when speaking with non-technical researchers; explain LSL, BIDS, etc. briefly
- Always clarify trigger/marker logic explicitly — this is the most common source of errors
- Ask about "edge cases": what happens if the participant makes an error? falls asleep? needs a break?
