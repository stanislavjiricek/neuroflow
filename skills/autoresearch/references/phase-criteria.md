# Per-phase default criteria (Layer 1)

Read during INIT. Copy the active phase's criteria into `program.md` under `## Default criteria`. These are the baseline against which the evaluator judges BETTER / WORSE / NO CHANGE each iteration.

**Outcome-blind rule (`data-analyze`, `data-preprocess`).** A criterion may require that a result is *reported*; it never rewards the *size or significance* of a result on the study data. Test: would the value change if the condition, group, or outcome labels were shuffled? If yes, it is not a default criterion. An exploratory loop may add such a metric as a user criterion — every value it produces then goes into the multiverse ledger (`references/integrity.md`).

---

## paper
Drawn from `agents/paper-critic.md` — six evaluation areas:
1. **Language, style, terminology** — spelling, grammar, undefined abbreviations, causality language errors (e.g. "X activates Y" from correlational data)
2. **Internal consistency** — all figures referenced exist and are numbered correctly; numerical values match across sections; subject counts consistent
3. **Claim support** — every claim has evidence; no causality creep; no functional-connectivity overclaims; no over-generalization beyond the sample
4. **Statistics** — power justification, correct test choice, effect sizes reported, multiple-comparison correction stated and justified
5. **Methods reproducibility** — COBIDAS compliance for fMRI; ARRIVE 2.0 for animals; electrode montage and reference stated for EEG; data and code availability statement
6. **Contribution and novelty** — novelty grounded relative to specific prior papers; alternative interpretations addressed; journal fit justified

## grant-proposal
Drawn from `skills/phase-grant-proposal/SKILL.md`:
1. **Scope** — all aims achievable within the stated timeline; no aim requires success of another unless stated
2. **Power analysis** — formal power analysis per aim with effect size cited from published literature
3. **Hypothesis in Approach** — every aim has a testable prediction, not just a description of methods
4. **Funder alignment** — Significance framed for the funder's stated priority (e.g. disease burden and mechanism for a health-research agency; frontier science for a basic-research council; scientific opportunity for a charitable foundation)
5. **Preliminary data** — at least one result figure per aim with statistics visible
6. **Budget justification** — every budget line has a rationale; FTE fractions stated; equipment identified by model

## ideation
1. **Novelty** — question not already answered in the cited literature; state the closest prior paper
2. **Testability** — can be empirically tested with standard neuroscience methods in a reasonable timeframe
3. **Specificity** — stated as one sentence with named independent variable, dependent variable, and population
4. **Feasibility** — achievable by a neuroscience lab given realistic equipment, sample, and timeline constraints
5. **Mechanistic grounding** — proposes a biological or computational mechanism, not just a correlational observation

## data-analyze
1. **Plan precedes code** — analysis-plan.md written and accepted before any analysis script
2. **Assumption audit** — normality, sphericity, and independence checked explicitly before test selection
3. **Multiple comparison correction** — method named (FWE, FDR, Bonferroni) and justified for the design
4. **Reproducibility** — script is self-contained and re-runnable from raw inputs alone
5. **Coverage** — all hypotheses listed in project_config.md are addressed
6. **Reporting completeness** — effect sizes (Cohen's d or η²) with confidence intervals, N per condition, and the a-priori power analysis (target ≥ 0.8) from the plan are reported. Scored on whether they are reported, never on their values — a larger effect or a smaller p-value is never BETTER

## experiment
1. **Ecological validity** — experimental conditions reflect the real-world scenario being studied
2. **Control conditions** — every independent variable has a matched control condition
3. **Counterbalancing** — order effects addressed; counterbalancing scheme stated
4. **Confound identification** — known confounds listed; design choices explain how each is controlled
5. **Numeric** — formal power analysis with target power ≥ 0.8; trial count per condition stated

## preregistration
1. **Specificity** — hypothesis statement has no wiggle room; can be unambiguously confirmed or disconfirmed
2. **Prior grounding** — at least one prior result cited per directional prediction
3. **Falsifiability** — defined rejection criterion (threshold, direction) for each hypothesis
4. **Analysis plan completeness** — exact statistical tests, thresholds, exclusion rules, and dependent variable operationalization stated
5. **Deviation protocol** — explicitly states what will be done if a planned analysis cannot run as specified

## brain-build
1. **Biological plausibility** — all parameters fall within physiologically reported ranges (cite sources)
2. **Formal completeness** — every equation and free parameter defined; no undefined symbols
3. **Testability** — model makes at least two specific, falsifiable empirical predictions
4. **Parameter justifiability** — each free parameter sourced from data, prior fit, or justified literature estimate
5. **Data relationship** — relationship between model output and empirical recordings explicitly stated

## brain-optimize
1. **Convergence evidence** — optimization converged (loss curve shown or stability criterion met)
2. **Objective alignment** — cost function reflects the scientific question being asked
3. **Sensitivity justification** — parameters the optimizer was most sensitive to are identified and discussed
4. **Generalisability** — fit not only to training data; held-out or cross-validated performance reported
5. **Numeric** — final loss / R² / correlation with empirical data reported per iteration

## brain-run
1. **Output clarity** — outputs are labelled, units stated, axes named
2. **Parameter documentation** — full parameter set used for the run is saved alongside outputs
3. **Reproducibility** — run is reproducible from the saved parameter set alone
4. **Interpretation soundness** — results interpreted within the bounds of model assumptions
5. **Limitation acknowledgment** — at least one key model limitation noted in context of the outputs

## data-preprocess
1. **Pipeline completeness** — all steps from raw to analysis-ready documented in order
2. **Artifact handling** — ocular, muscle, and line-noise artifacts addressed; strategy stated
3. **BIDS compliance** — output folder structure matches BIDS specification (see `neuroflow:bids`)
4. **Reproducibility** — pipeline re-runnable from the script alone with no manual steps
5. **Numeric** — channel rejection rate (flag if > 20%), epoch rejection rate, and SNR estimate reported, all computed pooled across conditions — never tune preprocessing on a condition contrast or on downstream effects

## poster / slideshow / write-report
1. **Visual / structural hierarchy** — most important claim is the most prominent element
2. **Core claim clarity** — the main message is readable or identifiable within 5 seconds
3. **Evidence density** — every claim has at least one supporting data point or citation visible
4. **Audience targeting** — vocabulary and technical depth match the stated audience
5. **Narrative flow** — logical order; each panel or section leads naturally to the next

## all other phases
Clarity, Completeness, Scientific rigour, Feasibility, Audience alignment
