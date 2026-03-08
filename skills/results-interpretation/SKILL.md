---
name: results-interpretation
description: Use when interpreting neuroscience results — comparing findings to hypotheses, discussing effect sizes, contextualizing against prior literature, interpreting ERP components or fMRI clusters, explaining unexpected findings, or writing the Results and Discussion sections. Triggers on "interpret results", "what does this mean", "discuss findings", "compare to hypothesis", "unexpected result explanation", "effect size interpretation", "discussion section", "clinical relevance", "theoretical implications".
version: 1.0.0
---

# Results Interpretation in Neuroscience

## Purpose

Guide the structured interpretation of neuroscience results — mapping findings back to hypotheses, contextualizing with literature, quantifying effect sizes, and producing publication-ready Discussion text.

## Step 1: Map Results to Hypotheses

For each result, check against the pre-registered or stated hypothesis:

| Hypothesis | Prediction | Observed | Verdict |
|---|---|---|---|
| H1: N200 larger for deviant | Deviant > Standard at Fz, 150–250 ms | Deviant > Standard, p=.012, d=0.82 | ✅ Supported |
| H2: RT shorter for standard | Standard RT < Deviant RT | No significant difference | ❌ Not supported |
| H3: Alpha suppression during deviant | Alpha decrease 200–400 ms | Trend only, p=.09 | ⚠️ Partial |

## Step 2: Quantify and Report Effect Sizes

Always pair statistical significance with effect size:

| Measure | Small | Medium | Large |
|---|---|---|---|
| Cohen's d | 0.2 | 0.5 | 0.8 |
| Cohen's f² | 0.02 | 0.15 | 0.35 |
| η²p (partial eta squared) | 0.01 | 0.06 | 0.14 |
| r (correlation) | 0.1 | 0.3 | 0.5 |
| AUC (classification) | 0.6 | 0.7 | 0.8+ |

```latex
% Reporting template
We observed a significantly larger N200 amplitude for deviant compared
to standard stimuli at Fz [$t(19) = 3.84$, $p = .001$, $d = 0.86$],
consistent with our primary hypothesis (H1).
```

## Step 3: Contextualize with Literature

For each significant finding:

1. **Confirm**: Does this replicate prior work? Cite 2–3 key references.
2. **Extend**: Does this extend prior work (new population, modality, condition)?
3. **Contradict**: If surprising, consider alternative explanations:
   - Methodological differences (filtering, reference, epoch window)
   - Population differences (age, expertise, clinical status)
   - Paradigm differences (ISI, stimulus complexity, response demand)

## Step 4: Interpret Component-Specific Findings

### ERP Components

| Component | Interpretation template |
|---|---|
| **N200 ↑** | Increased conflict monitoring / response inhibition demand |
| **P300 ↑** | Greater attentional resource allocation / WM update |
| **P300 latency ↑** | Slower stimulus evaluation / categorization speed |
| **N400 ↑** | Greater semantic mismatch / prediction error |
| **ERN ↑** | Heightened error monitoring / performance monitoring |
| **Alpha ↓** | Cortical activation / inhibition release in visual cortex |
| **Beta ↓ then ↑** | Motor preparation (ERD) followed by post-movement beta rebound |
| **Gamma ↑** | Local processing / feature binding / neural firing proxy (iEEG) |

### fMRI BOLD

| Finding | Interpretation |
|---|---|
| PFC activation | Executive control, top-down regulation |
| ACC activation | Conflict monitoring, error detection |
| Hippocampus | Memory encoding / retrieval |
| Amygdala | Emotional processing, threat detection |
| BOLD suppression | Neural inhibition, default mode deactivation |

### HRV

| Metric | Interpretation |
|---|---|
| RMSSD ↑ | Greater parasympathetic tone / reduced stress |
| LF/HF ratio ↑ | Sympathetic dominance |
| SD1 ↑ | Beat-to-beat variability ↑ |

---

## Step 5: Address Null / Unexpected Results

**Never ignore null results.** In Discussion, explain:

1. **Insufficient power?** — compare observed d to minimum detectable d given N
2. **Wrong time window / electrode?** — specify post-hoc justification clearly
3. **Floor/ceiling effect?** — behavioral performance distribution
4. **Paradigm confound?** — ISI, ITI, cognitive load, habituation
5. **Individual differences masked the group effect?** — consider correlation analyses

Template:
> "Contrary to our prediction (H2), we did not observe a significant
> reduction in reaction time for standard stimuli. This null result
> may reflect [insufficient statistical power / ceiling effects in RT
> / confound X]. Future studies should address this by [solution]."

---

## Step 6: Theoretical Implications

Structure the theoretical discussion as:
1. **What does the finding mean for the theoretical model?**
   - Confirm, extend, or challenge existing framework (name it explicitly)
2. **Mechanistic interpretation** — what neural process does this reflect?
3. **Clinical relevance** (if applicable) — what does this mean for diagnosis/intervention?

---

## Step 7: Limitations

Standard limitations to address in every neuroscience paper:

- Sample size and statistical power
- Population generalizability (healthy adults → clinical groups)
- Ecological validity (lab task vs. real-world)
- Reverse inference in fMRI (activation ≠ exclusive cognitive function)
- Volume conduction in EEG (limits spatial interpretation)
- Correlational design (no causal claims without stimulation/lesion data)
