# ALA 3.0 Code Examples

This page provides runnable code examples demonstrating ALA 3.0 in common streaming scenarios.

---

## Example 1: Basic Streaming Classification

```python
import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner

# Initialize learner
learner = ALA30AdaptiveLearner(n_features=4, n_classes=2, grace_period=10)

# Generate streaming samples
np.random.seed(42)
X = np.random.randn(100, 4)
y = (X[:, 0] + X[:, 1] > 0).astype(int)

# Stream processing loop
for i in range(100):
    x_i = X[i : i + 1]
    y_i = y[i : i + 1]

    # Predict before update
    prob = learner.predict_proba(x_i)
    pred = int(np.argmax(prob))

    # Incremental update
    learner.partial_fit(x_i, y_i)

print(f"Learner completed {learner.total_steps} streaming steps.")
```

---

## Example 2: Handling Recurring Concept Drift

```python
import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner

np.random.seed(123)
learner = ALA30AdaptiveLearner(
    n_features=3,
    n_classes=2,
    grace_period=10,
    similarity_threshold=0.75,
)

# Concept A: feature 0 dominant
X_A = np.random.randn(80, 3) + np.array([2.0, 0.0, 0.0])
y_A = (X_A[:, 0] > 2.0).astype(int)

# Concept B: feature 1 dominant
X_B = np.random.randn(80, 3) + np.array([0.0, 3.0, 0.0])
y_B = (X_B[:, 1] > 3.0).astype(int)

# Stream sequence: Concept A -> Concept B -> Concept A returns
stream_X = np.vstack([X_A, X_B, X_A])
stream_y = np.concatenate([y_A, y_B, y_A])

for i in range(len(stream_X)):
    learner.partial_fit(stream_X[i : i + 1], stream_y[i : i + 1])

print(f"Total steps: {learner.total_steps}")
print(f"Drift resets executed: {learner.drift_resets}")
print(f"Recurring restorations: {learner.recurring_restorations}")
```
