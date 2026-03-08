---
name: classification-clustering
description: Use when classifying EEG/neural data with machine learning, decoding brain states, cross-validation for BCI, or unsupervised clustering of neural patterns. Triggers on "classify EEG", "decode brain states", "LDA classifier", "SVM EEG", "cross-validation neural data", "MVPA", "multivariate pattern analysis", "cluster EEG epochs", "k-means EEG", "BCI classification", "temporal generalization".
version: 1.0.0
---

# Classification & Clustering for Neural Data

## Purpose

Apply supervised and unsupervised machine learning to neural signals for brain state decoding, BCI applications, and pattern discovery.

## 1. Supervised Classification (Decoding)

### Basic Pipeline

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_score
import mne

# Load epochs
epochs = mne.read_epochs('sub-01_epo.fif')
X = epochs.get_data()            # (n_epochs, n_channels, n_times)
y = epochs.events[:, 2]          # labels

# Flatten spatial+temporal features
n_epochs, n_ch, n_times = X.shape
X_2d = X.reshape(n_epochs, n_ch * n_times)

# Pipeline: standardize → LDA
clf = Pipeline([
    ('scaler', StandardScaler()),
    ('lda', LinearDiscriminantAnalysis()),
])

# Cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X_2d, y, cv=cv, scoring='roc_auc')
print(f"AUC: {scores.mean():.3f} ± {scores.std():.3f}")
```

### Recommended Classifiers for EEG

| Classifier | When to use |
|---|---|
| **LDA** | Small N, high-dimensional, BCI baseline |
| **SVM (RBF kernel)** | Nonlinear boundary, moderate N |
| **CSP + LDA** | Motor imagery, oscillatory features |
| **Riemannian (MDM)** | Covariance matrix features, robust to noise |
| **Random Forest** | Feature importance needed, interpretable |
| **Deep learning (EEGNet)** | Large N (>500 trials), raw data |

### Common Spatial Pattern (CSP) for Motor Imagery

```python
from mne.decoding import CSP

csp = CSP(n_components=4, log=True)
X_csp = csp.fit_transform(X, y)  # X: (n_epochs, n_channels, n_times)

clf_csp = Pipeline([
    ('csp', CSP(n_components=4, log=True)),
    ('lda', LinearDiscriminantAnalysis()),
])
scores_csp = cross_val_score(clf_csp, X, y, cv=cv, scoring='roc_auc')
```

---

## 2. Temporal Generalization (Time × Time Decoding)

```python
from mne.decoding import SlidingEstimator, GeneralizingEstimator, cross_val_multiscore
from sklearn.svm import SVC

base_clf = Pipeline([
    ('scaler', StandardScaler()),
    ('svc', SVC(kernel='linear', C=1.0)),
])

# Sliding: classify at each time point
sliding = SlidingEstimator(base_clf, n_jobs=-1, scoring='roc_auc')
scores_time = cross_val_multiscore(sliding, X, y, cv=cv)
# scores_time: (n_folds, n_times)

# Generalizing: train at each time, test at all times
gen = GeneralizingEstimator(base_clf, n_jobs=-1, scoring='roc_auc')
scores_gen = cross_val_multiscore(gen, X, y, cv=cv)
# scores_gen: (n_folds, n_train_times, n_test_times)

# Plot
import matplotlib.pyplot as plt
plt.plot(epochs.times, scores_time.mean(axis=0))
plt.axhline(0.5, ls='--', color='gray')
plt.xlabel('Time (s)'); plt.ylabel('AUC')
```

---

## 3. Riemannian Geometry Approach

```python
from pyriemann.estimation import Covariances
from pyriemann.classification import MDM  # Minimum Distance to Mean

# Compute covariance matrices
cov = Covariances(estimator='oas').fit_transform(X)  # (n_epochs, n_ch, n_ch)

# Classify on Riemannian manifold
clf_riem = MDM(metric='riemann')
scores_riem = cross_val_score(clf_riem, cov, y, cv=cv, scoring='roc_auc')
```

---

## 4. Unsupervised Clustering

```python
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Reduce dimensionality first
pca = PCA(n_components=20)
X_pca = pca.fit_transform(X_2d)

# K-Means
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_pca)

# Determine optimal k (elbow + silhouette)
from sklearn.metrics import silhouette_score
sil_scores = []
for k in range(2, 10):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    sil_scores.append(silhouette_score(X_pca, km.fit_predict(X_pca)))

# Hierarchical clustering
hc = AgglomerativeClustering(n_clusters=3, linkage='ward')
hc_labels = hc.fit_predict(X_pca)
```

---

## 5. Evaluation Metrics

| Metric | Use when |
|---|---|
| **AUC-ROC** | Binary, imbalanced classes |
| **Accuracy** | Balanced classes only |
| **F1 / balanced accuracy** | Multi-class, imbalanced |
| **Silhouette score** | Clustering quality |
| **Confusion matrix** | Per-class performance |

## Critical: Avoiding Data Leakage

- **Always** use cross-validation; never fit on test data
- Feature selection (channel / time selection) **must be inside the CV loop**
- Temporal smoothing or averaging across epochs must respect CV splits
- For temporal generalization: use `cross_val_multiscore` not manual loops
- Permutation test is the gold standard for chance-level significance (see permutation-testing skill)
