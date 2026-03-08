<div align="center">
  <img src="logo.png" alt="neuroflow" width="180" />
  <h1>neuroflow</h1>
  <p><strong>A Claude plugin for end-to-end neuroscientific research.</strong></p>
  <p>
    <a href="#installation">Install</a> ·
    <a href="#how-it-works">How it works</a> ·
    <a href="#modalities">Modalities</a> ·
    <a href="#workflow">Workflow</a> ·
    <a href="#commands--agents">Commands & Agents</a>
  </p>
</div>

---

neuroflow is not a classical analysis toolbox. It is an **agent-driven framework** that brings Claude into every stage of a neuroscientific study — from the first research question through experimental design, data collection, statistical analysis, and final manuscript preparation.

You describe your research problem. neuroflow orchestrates the right agents, skills, and domain knowledge to move the work forward.

---

## How it works

Most neuroscience software handles one phase: a preprocessing library, a stats package, a reference manager. Researchers are left to manually stitch these phases together, translate between tools, and re-explain context at every step.

neuroflow treats the **entire research cycle as a single, stateful workflow**. Context built during hypothesis formulation carries into paradigm design. Paradigm decisions inform preprocessing choices. Analysis results feed directly into the manuscript. Agents collaborate across phases rather than operating in isolation.

```
Hypothesis → Paradigm → Recording → Analysis → Publication
     ↑______________________________________________|
                  (iterative feedback)
```

---

## Modalities

| Modality | Coverage |
|---|---|
| **EEG** | Scalp EEG, high-density arrays, resting state, ERP, time-frequency |
| **iEEG** | Cortical EEG, SEEG, ECoG, high-gamma |
| **fMRI** | Block design, event-related, resting state, GLM, ROI |
| **Eye tracking** | Fixations, saccades, pupillometry, gaze contingency |
| **ECG / Physio** | Heart rate, HRV, skin conductance, respiration |
| **Multimodal** | Synchronized EEG+fMRI, EEG+Eye, EEG+ECG, any combination |

---

## Workflow

### 1. Hypothesis & Planning

The framework opens with a structured **researcher interview** that captures the scientific question, population, and constraints. From there, agents assist with:

- Hypothesis formulation using the PICO framework
- Systematic literature search across PubMed and bioRxiv, with gap analysis
- Modality selection — recommending the right signal given the question and lab resources
- Recording setup and hardware configuration guidance
- BIDS-compliant project scaffolding

### 2. Paradigm Design

neuroflow generates complete, runnable experimental paradigms — not pseudocode or templates to fill in. It covers:

- Standard designs: oddball, N-back, checkerboard, resting state, go/no-go, cueing
- PsychoPy scripts with proper timing, counterbalancing, and randomization
- Lab Streaming Layer (LSL) integration for real-time marker streaming
- Trigger/marker writing synchronized to EEG, fMRI, and physiological recordings
- Paradigm audit agent that verifies timing accuracy and edge-case handling

### 3. Data Analysis

The analysis phase adapts to the study modality and design. Agents handle:

- **EEG**: filtering, re-referencing, ICA artifact removal, epoch rejection, ERP, time-frequency analysis, connectivity
- **fMRI**: GLM construction, contrast definition, ROI extraction, whole-brain maps
- **iEEG**: high-gamma broadband power, single-trial analysis, spatial localization
- **Eye tracking**: fixation detection, saccade metrics, gaze-contingent epoch extraction
- **Physio**: HRV features, SCR detection, cardioballistic artifact removal in EEG
- **Multimodal**: cross-modal synchrony, feature fusion, joint modeling
- **Statistics**: permutation testing, cluster correction, Bayesian inference, effect sizes

### 4. Manuscript Preparation

Results flow directly into a structured publication pipeline:

- LaTeX paper generation with figures, tables, and statistical reporting formatted to journal standards
- Target journals: NeuroImage, Journal of Neuroscience, Brain, Cerebral Cortex, eLife, and others
- APA/Vancouver/Chicago citation formatting
- Paper review agent for logic, methodology, and style consistency

---

## Commands & Agents

### Slash Commands

| Command | What it does |
|---|---|
| `/new-project` | Scaffold a new BIDS project with team config |
| `/interview` | Structured researcher interview to define the study |
| `/hypothesis` | Formulate and operationalize a research hypothesis |
| `/paradigm` | Generate a complete paradigm (PsychoPy + LSL + markers) |
| `/analyze` | Launch an analysis pipeline for a dataset |
| `/write-paper` | Draft a scientific manuscript in LaTeX |
| `/review-paper` | Quality review of a paper draft |
| `/check-bids` | Validate BIDS directory structure |

### Agents

| Agent | Role |
|---|---|
| `literature-reviewer` | Autonomous literature search, synthesis, and gap identification |
| `paradigm-auditor` | Verify paradigm code — timing precision, markers, edge cases |
| `stats-auditor` | Audit statistical analysis — assumptions, corrections, reporting |
| `paper-editor` | Review and improve manuscript — logic, style, consistency |
| `data-quality-checker` | Assess recording quality — artifacts, impedance, missing trials |

---

## Installation

```bash
# Via Claude Code plugin system
claude plugin install neuroflow

# Or clone and link locally
git clone https://github.com/jiric/neuroflow
claude plugin link ./neuroflow
```

Configure your lab profile in `config/team.json`:

```json
{
  "team_name": "Your Lab",
  "modalities": ["EEG", "eye-tracking"],
  "programming_language": "python",
  "analysis_tools": ["MNE-Python", "pandas", "scipy"],
  "journal_target": "NeuroImage",
  "citation_style": "APA"
}
```

---

## License

MIT © jiric
