# Scikit-Learn Framework Integration Guide

AdaptiveML integrates directly into the scikit-learn ecosystem, adhering to standard estimator, predictor, and transformer protocols.

---

## 1. Available Scikit-Learn Adapters

Exported from `adaptive_ml.integrations`:

| Class | Base Class | Protocol | Key Features |
|:---|:---|:---|:---|
| [`SklearnAdaptiveClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `ClassifierMixin` | Estimator / Predictor | `fit`, `predict`, `predict_proba`, `partial_fit`, `score`, `clone()` |
| [`SklearnDriftDetectorTransformer`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `TransformerMixin` | Transformer | Online statistical drift tracking on continuous feature streams via ADWIN |
| [`SklearnReliabilityFilter`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `TransformerMixin` | Transformer | Sample reliability scoring and filtering of label noise bursts |

---

## 2. Using `SklearnAdaptiveClassifier`

### Classical Batch Pipeline

`SklearnAdaptiveClassifier` can be dropped directly into any standard scikit-learn pipeline or cross-validation routine:

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from robust_adapt.integrations import SklearnAdaptiveClassifier

# Synthetic classification dataset
np.random.seed(42)
X_train = np.random.randn(200, 10)
y_train = (X_train[:, 0] + X_train[:, 1] > 0.0).astype(int)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", SklearnAdaptiveClassifier(
        n_features=10,
        n_classes=2,
        grace_period=50,
        delta=1e-4,
        random_state=42,
    )),
])

# Fit and cross-validate
scores = cross_val_score(pipe, X_train, y_train, cv=5)
print(f"5-Fold CV Mean Accuracy: {scores.mean() * 100:.2f}%")
```

### Incremental Streaming with `partial_fit`

In production stream pipelines, use `partial_fit` to continuously update tree splits:

```python
import numpy as np
from robust_adapt.integrations import SklearnAdaptiveClassifier

clf = SklearnAdaptiveClassifier(n_features=10, n_classes=2, grace_period=20)

# Simulate 5 micro-batches of streaming data
for batch_idx in range(5):
    X_batch = np.random.randn(50, 10)
    y_batch = (X_batch[:, 0] > 0.0).astype(int)
    clf.partial_fit(X_batch, y_batch, classes=[0, 1])

y_pred = clf.predict(X_batch[:5])
print("Batch predictions:", y_pred)
```

---

## 3. Detecting Distribution Shifts with `SklearnDriftDetectorTransformer`

Insert `SklearnDriftDetectorTransformer` into your scikit-learn pipeline to automatically track concept drift on critical features without interrupting data flow:

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from robust_adapt.integrations import (
    SklearnAdaptiveClassifier,
    SklearnDriftDetectorTransformer,
)

stream_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("drift_monitor", SklearnDriftDetectorTransformer(delta=0.001, monitored_feature_index=0)),
    ("classifier", SklearnAdaptiveClassifier(n_features=4, n_classes=2)),
])

# Process streaming batches
for step in range(5):
    X_batch = np.random.randn(40, 4)
    y_batch = (X_batch[:, 0] > 0.0).astype(int)

    X_proc = stream_pipe.named_steps["scaler"].partial_fit(X_batch).transform(X_batch)
    X_mon = stream_pipe.named_steps["drift_monitor"].transform(X_proc)
    stream_pipe.named_steps["classifier"].partial_fit(X_mon, y_batch, classes=[0, 1])

    if stream_pipe.named_steps["drift_monitor"].last_drift_detected_:
        print(f"ALERT: Drift detected at batch {step}!")
```

---

## 4. Filtering Label Noise with `SklearnReliabilityFilter`

`SklearnReliabilityFilter` uses spatial $k$-nearest neighbors and prediction margin reliability to drop corrupted observations:

```python
import numpy as np
from robust_adapt.integrations import SklearnReliabilityFilter

filter_step = SklearnReliabilityFilter(n_classes=2, min_reliability=0.35)
X_batch = np.random.randn(50, 4)
y_batch = (X_batch[:, 0] > 0.0).astype(int)

# In streaming scenarios, compute model probabilities or pass initial estimates
probas = np.column_stack([
    1.0 / (1.0 + np.exp(X_batch[:, 0])),
    1.0 / (1.0 + np.exp(-X_batch[:, 0])),
])

# Filter low-reliability noisy samples
X_clean, y_clean, weights_clean = filter_step.filter_batch(X_batch, y_batch, probas)
print(f"Clean samples retained: {len(y_clean)} of {len(y_batch)}")
```
