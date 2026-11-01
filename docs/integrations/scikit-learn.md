# Scikit-learn Framework Integration

AdaptiveML provides first-class support for scikit-learn workflows via `SklearnAdaptiveClassifier`.

---

## 1. Compliance with Scikit-learn Estimator API

`SklearnAdaptiveClassifier` implements the standard scikit-learn conventions:
- Inherits from `BaseEstimator` and `ClassifierMixin`.
- Standard constructor with direct attribute assignment (supports `sklearn.base.clone()`).
- Implements `fit(X, y)`, `predict(X)`, `predict_proba(X)`, and `score(X, y)`.
- Implements `partial_fit(X, y, classes=...)` for streaming and out-of-core pipelines.

---

## 2. Pipeline Example

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from adaptive_ml.integrations.sklearn import SklearnAdaptiveClassifier

# Build scikit-learn pipeline
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", SklearnAdaptiveClassifier(max_depth=5, grace_period=20))
])

# Training
X = np.random.randn(200, 10)
y = (X[:, 0] + X[:, 1] > 0.0).astype(int)
pipe.fit(X, y)

# Prediction
y_pred = pipe.predict(X[:5])
print("Predicted classes:", y_pred)
```
