---
title: /data-analyze
---

# `/neuroflow:data-analyze`

**Run an analysis pipeline on your preprocessed data.**

`/data-analyze` covers the full range of neuroscience analysis methods — ERPs, time-frequency, connectivity, decoding, and GLM — with built-in statistical auditing to ensure your results are rigorous.

---

## When to use it

- After `/data-preprocess` — you have cleaned, epoched data
- You want to compute ERPs, time-frequency representations, or connectivity
- You need to run statistical comparisons or multivariate decoding
- You want an analysis plan before running anything (pre-registration support)

---

## What it does

Claude asks:

1. **Analysis goal?** (ERP, time-frequency, connectivity, decoding, GLM, other)
2. **Where is the preprocessed data?**
3. **Is there a pre-registered analysis plan to follow?**

---

## Analysis approaches

Claude selects the appropriate tooling based on your goal:

=== "ERP"

    Event-related potential analysis using MNE-Python.

    ```python
    # Example: P300 ERP comparison
    evoked_standard = epochs['standard'].average()
    evoked_target = epochs['target'].average()

    # Grand average across subjects
    grand_avg = mne.grand_average([evoked_target, ...])

    # Statistical test: cluster permutation
    T_obs, clusters, p_values, _ = mne.stats.permutation_cluster_1samp_test(
        X, n_permutations=1000
    )
    ```

=== "Time-Frequency"

    Time-frequency analysis using Morlet wavelets or multitaper.

    ```python
    # Morlet wavelet TFR
    freqs = np.arange(4, 40, 1)
    n_cycles = freqs / 2.0

    power = mne.time_frequency.tfr_morlet(
        epochs, freqs=freqs, n_cycles=n_cycles,
        return_itc=True
    )
    ```

=== "Connectivity"

    Functional connectivity using MNE spectral connectivity tools.

    ```python
    from mne_connectivity import spectral_connectivity_epochs

    con = spectral_connectivity_epochs(
        epochs, method='coh',
        fmin=8, fmax=12,  # alpha band
        faverage=True
    )
    ```

=== "Decoding"

    Multivariate pattern analysis (MVPA) using scikit-learn.

    ```python
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import cross_val_score

    clf = LinearDiscriminantAnalysis()
    scores = cross_val_score(clf, X, y, cv=5, scoring='roc_auc')
    ```

=== "fMRI GLM"

    First- and second-level GLM using nilearn.

    ```python
    from nilearn.glm.first_level import FirstLevelModel

    fmri_glm = FirstLevelModel(t_r=2.0, hrf_model='spm')
    fmri_glm.fit(fmri_imgs, events_df)
    z_map = fmri_glm.compute_contrast('target - standard')
    ```

---

## Figure check

After collecting results, Claude looks at the final figures — the ones listed in `analysis-summary.md`, never per-subject dumps, at most 8 at a time (it asks before more). It reads each PNG or PDF page and checks it against the figure checklist of the review-neuro skill: colour map, font size at print size, axis labels and units, error bars, statistical annotations, caption completeness.

Every finding becomes a row in `.neuroflow/data-analyze/figure-notes.md`, anchored in the data rather than in pixels:

| Figure | Panel | Element | Data anchor | Class | Note | Author | Status |
|---|---|---|---|---|---|---|---|
| `figures/erp_pz.png` | B | y-axis label | Pz, 300–600 ms, target vs standard | cosmetic | Unit missing (µV) | model | claimed-fixed |

- **Cosmetic** findings (labels, units, fonts, overlap, colour map choice, layout) are fixed in the plotting code and the figure is regenerated. Claude re-reads it, tells you what visibly changed and marks the row `claimed-fixed`; only you mark it `verified` (or `wontfix`).
- **Analytic** findings (time or frequency windows, thresholds, baselines, cluster parameters, exclusions, colour limits, smoothing) are never fixed automatically. Claude asks; a change you approve goes through `analysis-plan.md`, the preregistration deviations log when the preregistration is frozen, and the decision log.
- Figures are never edited as images: every change is made in the plotting code and the figure regenerated. Compared conditions share colour limits and axes, and the caption states colour limits, thresholds and masks.

**Pointing at a spot yourself:** take a screenshot, circle the region with your screenshot tool's markup and paste it into the conversation — or name the panel and the data coordinates ("panel B, around 350 ms at Pz"). Claude records it as a row, like its own findings.

---

## Statistical auditing

After running analysis, Claude audits the statistical approach:

- **Test assumptions** — normality, sphericity, independence
- **Multiple comparison correction** — cluster permutation, FDR, Bonferroni
- **Effect size reporting** — Cohen's d, partial η², AUC
- **Pre-registration compliance** — if a plan exists, flags any deviations
- **Peeking check** — before a confirmatory test on fewer participants than the preregistered `planned_n`, Claude stops and asks; an interim look you approve is logged in `deviations.md`

---

## Reproducibility and robustness

| What | How |
|---|---|
| **Provenance** | Each analysis script calls `nf_provenance`, which writes `environment.md` (Python, package versions, declared seeds, git commit and dirty flag) and one run record per run with input and output hashes — on your laptop or in an HPC job. |
| **Notebooks** | Outputs are stripped before committing (`nbstripout`); a number from a notebook counts only after a clean headless rerun, or when a script writes it to `results/`. |
| **Multiverse** (exploratory) | `multiverse.py` runs a declared grid of analysis choices and logs every specification, with its result, to `multiverse.md`. You report the whole curve, labelled exploratory. |
| **Clean-room reproduction** | `cleanroom.py` clones the project at the recorded commit, builds a fresh environment, reruns the pipeline and compares the outputs — before submission or archiving. |
| **Long runs** | Analyses over ~10 minutes run in the background or detached and are tracked in `.neuroflow/data-analyze/runs.md`. |

---

## Example session

```
/neuroflow:data-analyze
```

```
Claude: Research question: "Does noise background reduce P300 amplitude?"

        Analysis goal?

You: P300 ERP comparison between noise and silent conditions, 
     then cluster permutation test.

Claude: Analysis plan:
        1. Average epochs by condition (noise, silent) per subject
        2. Compute difference wave: noise - silent
        3. Cluster permutation test across 300-600ms window, Pz

        Writing analysis-plan.md...
        Writing scripts/analysis/erp_analysis.py...

        [runs analysis, generates figures/erp_comparison.png]

        Results: Significant cluster at 350-520ms over central-parietal 
        electrodes (p = 0.012). P300 amplitude reduced by 2.3 µV in noise 
        condition (Cohen's d = 0.71).
```

---

## Output

| File | Where | What it contains |
|---|---|---|
| `analysis-plan.md` | `.neuroflow/data-analyze/` | What will be computed, comparisons, statistical tests, expected output |
| `analysis.py` | `scripts/analysis/` | Analysis code |
| `environment.md`, `provenance/*.json` | `scripts/analysis/` | Versions, seeds and git commit; one run record per run (written by `nf_provenance`) |
| `analysis-summary.md` | `.neuroflow/data-analyze/` | Key findings, figures produced, open questions |
| `figure-notes.md` | `.neuroflow/data-analyze/` | Figure check findings: one row per finding, with its data anchor, class and status |
| `multiverse.md` | `.neuroflow/data-analyze/` | Append-only ledger of every exploratory specification and its result |
| `cleanroom-YYYY-MM-DD.md` | `.neuroflow/data-analyze/` | Clean-room reproduction report (when run) |
| `runs.md` | `.neuroflow/data-analyze/` | Registry of long or detached runs |
| Figures | `figures/` | All generated plots |
| Results | `results/` | Statistical output tables |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/data-preprocess/flow.md`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/preregistration/flow.md`, `.neuroflow/preregistration/status.md` |
| Writes | `.neuroflow/data-analyze/`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/reasoning/data-analyze.jsonl`, `.neuroflow/preregistration/deviations.md` (deviations only), `.neuroflow/sessions/YYYY-MM-DD.md`, `scripts/analysis/`, `results/`, `figures/` |

---

## Related commands

- [`/data-preprocess`](data-preprocess.md) — preprocess your data first
- [`/paper`](paper.md) — write the manuscript from your results
