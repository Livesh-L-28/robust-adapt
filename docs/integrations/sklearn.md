# scikit-learn Integration Guide

AdaptiveML integrates directly into the scikit-learn ecosystem, adhering to standard estimator, predictor, and transformer protocols.

---

## 1. Available scikit-learn Adapters

Exported from [`adaptive_ml.integrations.sklearn`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py):

| Class | Base Class | Protocol | Key Features |
|:---|:---|:---|:---|
| [`SklearnAdaptiveClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `ClassifierMixin` | Estimator / Predictor | `fit`, `predict`, `predict_proba`, `partial_fit`, `score`, `clone()` |
| [`SklearnDriftDetectorTransformer`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `TransformerMixin` | Transformer | Online statistical drift tracking on continuous feature streams via ADWIN |
| [`SklearnReliabilityFilter`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/sklearn.py) | `BaseEstimator`, `TransformerMixin` | Transformer | Sample reliability scoring and filtering of label noise bursts |

---

## 2. Using `SklearnAdaptiveClassifier`

### Classical Batch Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier

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

```python
clf = SklearnAdaptiveClassifier(n_features=8, n_classes=3, grace_period=20)

for X_batch, y_batch in stream_generator():
    # Update model incrementally with incoming batch
    clf.partial_fit(X_batch, y_batch, classes=[0, 1, 2])
    print(f"Processed: {clf.samples_seen_} samples | Drifts adapted: {clf.drift_count_}")
```

---

## 3. Detecting Distribution Shifts with `SklearnDriftDetectorTransformer`

Insert `SklearnDriftDetectorTransformer` into your scikit-learn pipeline to automatically track concept drift on critical features without interrupting data flow:

```python
from robust_adapt.integrations.sklearn import SklearnDriftDetectorTransformer

stream_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("drift_monitor", SklearnDriftDetectorTransformer(delta=0.001, monitored_feature_index=0)),
    ("classifier", SklearnAdaptiveClassifier(n_features=4, n_classes=2)),
])

for X_batch, y_batch in stream:
    # Transform scales and checks drift
    X_proc = stream_pipe.named_steps["scaler"].partial_fit(X_batch).transform(X_batch)
    X_mon = stream_pipe.named_steps["drift_monitor"].transform(X_proc)
    stream_pipe.named_steps["classifier"].partial_fit(X_mon, y_batch, classes=[0, 1])

    if stream_pipe.named_steps["drift_monitor"].last_drift_detected_:
        print(f"ALERT: Drift detected at batch! Total events: {stream_pipe.named_steps['drift_monitor'].drift_count_}")
```

---

## 4. Hyperparameter Tuning and Cloning

`SklearnAdaptiveClassifier` implements full parameter introspection via `get_params()` and `set_params()`:

```python
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV

param_grid = {
    "classifier__grace_period": [20, 50, 100],
    "classifier__delta": [1e-3, 1e-4, 1e-5],
}

search = GridSearchCV(pipe, param_grid, cv=3)
search.fit(X, y)
print("Best Parameters:", search.best_params_)

# Cloned instances maintain parameters with freshly initialized weights
cloned_model = clone(search.best_estimator_)
```
