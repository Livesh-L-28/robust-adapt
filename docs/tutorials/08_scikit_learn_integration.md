# Tutorial 08: Scikit-learn Integration

**Objective**: Integrate `SklearnAdaptiveClassifier` into a scikit-learn preprocessing `Pipeline` and out-of-core streaming workflows.

---

## 1. Setup & Imports

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone
from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier

# Construct Pipeline
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", SklearnAdaptiveClassifier(max_depth=5, grace_period=20))
])
```

---

## 2. Fitting & Cross-Validation Compatibility

```python
np.random.seed(42)

# Training batch
X_train = np.random.randn(200, 10)
y_train = (X_train[:, 0] + X_train[:, 1] > 0.0).astype(int)

# Fit pipeline
pipeline.fit(X_train, y_train)

# Clone pipeline (standard scikit-learn behavior)
cloned_pipe = clone(pipeline)
print("Pipeline successfully cloned!")

# Prediction & Probabilities
X_test = np.random.randn(5, 10)
predictions = pipeline.predict(X_test)
probabilities = pipeline.predict_proba(X_test)

print("Predictions:", predictions)
print("Probabilities shape:", probabilities.shape)
```

---

## 3. Streaming `partial_fit` Support

```python
# Streaming updates through partial_fit
for step in range(3):
    X_stream = np.random.randn(50, 10)
    y_stream = (X_stream[:, 0] + X_stream[:, 1] > 0.0).astype(int)
    pipeline.named_steps["classifier"].partial_fit(X_stream, y_stream, classes=[0, 1])
    print(f"Stream step {step + 1} completed!")
```
