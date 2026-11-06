# Tutorial 01: Your First AdaptiveML Workflow

**Objective**: Build, train, and evaluate your first incremental machine learning model using AdaptiveML in pure Python.

---

## 1. Setup & Imports

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier

# Initialize the classifier
clf = AdaptiveClassifier(
    max_depth=5,
    grace_period=20,
    confidence_delta=0.01,
    buffer_capacity=500
)
```

---

## 2. Ingesting Streaming Batches

```python
# Generate synthetic streaming classification data
np.random.seed(42)

for batch_idx in range(5):
    # 50 samples with 8 features
    X_batch = np.random.randn(50, 8).astype(np.float32)
    # Decision boundary: x0 + x1 > 0
    y_batch = (X_batch[:, 0] + X_batch[:, 1] > 0.0).astype(np.int64)

    # Update model incrementally
    metrics = clf.partial_fit(X_batch, y_batch)
    print(f"Batch {batch_idx + 1:02d} | Ingested: {metrics['n_samples']} samples | Accuracy: {metrics['accuracy']:.1%}")
```

---

## 3. Real-Time Inference

```python
# Test on unseen query points
X_query = np.array([
    [1.5, 1.2, 0.0, -0.5, 0.2, 0.1, -0.3, 0.4],
    [-1.2, -1.5, 0.3, 0.2, -0.1, 0.0, 0.5, -0.2]
], dtype=np.float32)

preds = clf.predict(X_query)
probs = clf.predict_proba(X_query)

print("Predictions:", preds)
print("Class Probabilities:\n", probs)
```

**Output**:
```
Batch 01 | Ingested: 50 samples | Accuracy: 84.0%
Batch 02 | Ingested: 100 samples | Accuracy: 90.0%
Batch 03 | Ingested: 150 samples | Accuracy: 92.0%
Batch 04 | Ingested: 200 samples | Accuracy: 94.0%
Batch 05 | Ingested: 250 samples | Accuracy: 94.0%
Predictions: [1 0]
```
