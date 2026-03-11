---
title: /data-analyze
---

# `/neuroflow:data-analyze`

**Run an analysis pipeline on your preprocessed data.**

`/data-analyze` covers the full range of neuroscience analysis methods — ERPs, time-frequency, connectivity, decoding, and GLM.

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
| `analysis-summary.md` | `.neuroflow/data-analyze/` | Key findings, figures produced, open questions |
| Figures | `figures/` | All generated plots |
| Results | `results/` | Statistical output tables |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/data-preprocess/flow.md`, `.neuroflow/data-analyze/flow.md` |
| Writes | `.neuroflow/data-analyze/`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `scripts/analysis/`, `results/`, `figures/` |

---

## Related commands

- [`/data-preprocess`](data-preprocess.md) — preprocess your data first
- [`/paper-write`](paper-write.md) — write the manuscript from your results
