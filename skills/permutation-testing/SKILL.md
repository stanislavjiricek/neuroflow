---
name: permutation-testing
description: Use when performing permutation tests, cluster-based permutation tests, non-parametric statistics for EEG/neural data, correcting for multiple comparisons in time-frequency or sensor space, or when parametric assumptions are violated. Triggers on "permutation test", "cluster-based permutation", "non-parametric statistics", "multiple comparison correction EEG", "FDR correction", "TFCE", "MNE statistics", "permutation t-test", "chance level significance".
version: 1.0.0
---

# Permutation Testing for Neural Data

## Purpose

Permutation tests are the gold standard for neuroscience statistics — they make no distributional assumptions, directly control multiple comparisons in sensor×time space, and are robust for small samples.

## Why Permutation Tests?

- **No normality assumption** needed (EEG data is rarely Gaussian)
- **Controls Type I error** at sensor×time×frequency level without data-driven threshold
- **Cluster correction** accounts for spatial/temporal smoothness of neural signals
- Recommended by MNE, FieldTrip, and most neuroscience journals

---

## 1. Basic Permutation T-Test (Single Measure)

```python
import numpy as np
from scipy import stats

def permutation_ttest(group_a, group_b, n_permutations=10000, seed=42):
    """
    Non-parametric permutation test for independent samples.
    Returns: observed t-stat, p-value
    """
    rng = np.random.default_rng(seed)
    observed_t, _ = stats.ttest_ind(group_a, group_b)

    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)

    perm_t = np.zeros(n_permutations)
    for i in range(n_permutations):
        perm = rng.permutation(combined)
        perm_t[i], _ = stats.ttest_ind(perm[:n_a], perm[n_a:])

    p_value = np.mean(np.abs(perm_t) >= np.abs(observed_t))
    return observed_t, p_value

# Usage
t_stat, p_val = permutation_ttest(p300_amplitudes_group_a, p300_amplitudes_group_b)
```

---

## 2. Cluster-Based Permutation Test (MNE) – ERP / Time-Frequency

The cluster approach corrects for the entire time×sensor space simultaneously.

```python
import mne
import numpy as np
from mne.stats import permutation_cluster_test, permutation_cluster_1samp_test

# --- Two-sample: compare two conditions or groups ---
# X_cond_a, X_cond_b: shape (n_subjects, n_channels, n_times) or (n_subjects, n_times)

X_a = epochs_a.get_data(picks='Pz').mean(axis=1)  # (n_subj, n_times)
X_b = epochs_b.get_data(picks='Pz').mean(axis=1)

T_obs, clusters, cluster_p, H0 = permutation_cluster_test(
    [X_a, X_b],
    n_permutations=1000,
    threshold=None,        # None = TFCE (threshold-free)
    tail=0,               # 0=two-tailed, 1=one-tailed positive, -1=negative
    n_jobs=-1,
    seed=42,
    out_type='mask'
)

# Report significant clusters
for i, (cluster, p) in enumerate(zip(clusters, cluster_p)):
    if p < 0.05:
        t_start = epochs.times[cluster[0].start]
        t_end = epochs.times[cluster[0].stop]
        print(f"Cluster {i}: p={p:.4f}, t=[{t_start*1000:.0f}, {t_end*1000:.0f}] ms")
```

```python
# --- One-sample: test against zero (e.g., decoding above chance) ---
X_scores = all_scores - 0.5   # center at chance

T_obs_1s, clusters_1s, p_vals_1s, H0_1s = permutation_cluster_1samp_test(
    X_scores,
    n_permutations=1000,
    threshold=None,
    tail=1,   # one-tailed: above chance
    seed=42
)
```

---

## 3. Permutation Test for Classifier (Chance Level)

```python
from sklearn.model_selection import StratifiedKFold, permutation_test_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

clf = Pipeline([('sc', StandardScaler()), ('lda', LinearDiscriminantAnalysis())])
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

score, perm_scores, pvalue = permutation_test_score(
    clf, X_2d, y,
    cv=cv,
    n_permutations=1000,
    scoring='roc_auc',
    n_jobs=-1,
    random_state=42
)

print(f"True AUC: {score:.3f}, p={pvalue:.4f}")
```

---

## 4. FDR / FWE Correction (Alternative for Mass Univariate)

```python
from mne.stats import fdr_correction, bonferroni_correction

# Run t-test at every time point × channel
from scipy.stats import ttest_rel
t_obs = np.zeros((n_channels, n_times))
p_obs = np.zeros((n_channels, n_times))

for ch in range(n_channels):
    for t in range(n_times):
        t_obs[ch, t], p_obs[ch, t] = ttest_rel(X_a[:, ch, t], X_b[:, ch, t])

# FDR correction
reject_fdr, p_fdr = fdr_correction(p_obs, alpha=0.05, method='indep')

# Bonferroni
reject_bon, p_bon = bonferroni_correction(p_obs, alpha=0.05)
```

---

## 5. Threshold-Free Cluster Enhancement (TFCE)

TFCE is recommended when you don't want to set an arbitrary cluster-forming threshold.

```python
# Use threshold=None in MNE functions (TFCE is default when threshold=None)
T_obs, clusters, p_values, H0 = permutation_cluster_test(
    [X_a, X_b],
    threshold=None,       # TFCE
    n_permutations=5000,
    seed=42,
)
```

---

## Reporting Template

> "We used cluster-based permutation tests (10,000 permutations, two-tailed, p < .05) to identify significant differences between conditions in the [time-frequency / sensor-time] space. This non-parametric approach controlled the family-wise error rate without assuming data normality. Significant clusters are reported with their onset, offset, and cluster-level p-value."

## Checklist

- [ ] n_permutations ≥ 1000 (5000 recommended for publications)
- [ ] Seed set for reproducibility (report seed in Methods)
- [ ] Tail (one/two) justified a priori
- [ ] Threshold choice explained (TFCE vs. fixed threshold)
- [ ] Cluster mass vs. cluster sum reported
- [ ] Effect size reported alongside p-value (Cohen's d, η², AUC)
