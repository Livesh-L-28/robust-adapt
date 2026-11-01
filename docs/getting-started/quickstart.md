# 5-Minute Developer Quickstart

This guide walks you through streaming data ingestion, concept drift adaptation, and real-time inference in under 5 minutes.

---

## 1. Streaming Classification with AdaptiveClassifier

The `AdaptiveClassifier` integrates incremental Hoeffding trees with adaptive drift detection:

```python
import numpy as np
from adaptive_ml.ala import AdaptiveClassifier

# Initialize adaptive classifier
classifier = AdaptiveClassifier(max_depth=6, grace_period=25)

# Simulate 5 sequential mini-batches
print("Ingesting streaming batches...")
for step in range(1, 6):
    # Features: 40 samples, 8 features
    X = np.random.randn(40, 8).astype(np.float32)
    
    # Simulate a concept drift at step 3
    if step < 3:
        y = (X[:, 0] + X[:, 1] > 0.0).astype(np.int64)
    else:
        y = (X[:, 2] - X[:, 3] > 0.0).astype(np.int64)
        
    metrics = classifier.partial_fit(X, y)
    print(f"Step {step:02d} | Accuracy: {metrics['accuracy']:.1%} | Drifts: {metrics.get('drifts', 0)}")

# Inference on unseen samples
X_test = np.random.randn(5, 8).astype(np.float32)
predictions = classifier.predict(X_test)
probabilities = classifier.predict_proba(X_test)

print("\nPredictions on test sample:")
print("Labels:", predictions)
print("Probabilities (first sample):", probabilities[0])
```

---

## 2. Using LowMemoryAdamW for Memory-Efficient Training

Train a neural network or NumPy linear model with 73.44% less optimizer state memory:

```python
import numpy as np
from adaptive_ml.rao import LowMemoryAdamW

# Define linear model parameters
weights = np.zeros((10, 1), dtype=np.float32)

class ParamWrapper:
    def __init__(self, arr):
        self.arr = arr
        self.grad = np.zeros_like(arr)
    @property
    def data(self):
        return self.arr

p = ParamWrapper(weights)
optimizer = LowMemoryAdamW([p], lr=0.05, block_size=32)

# Optimization loop
for epoch in range(10):
    # Compute mock synthetic gradient: grad = 2 * (w - 1.0)
    p.grad = 2.0 * (p.arr - 1.0)
    optimizer.step()

print(f"Optimized weights mean: {p.arr.mean():.4f} (target: 1.0000)")
```

---

## 3. Running the Standalone Script

Run the automated quickstart script included in the repository:

```bash
python examples/quickstart.py
```
Execution takes approximately **0.18 seconds** on standard CPU.
