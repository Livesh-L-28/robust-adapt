# Adaptive Learning Algorithms (ALA) User Guide

This guide covers the implementation, configuration, and practical usage of AdaptiveML's adaptive learning algorithms.

---

## 1. Quick Example: AdaptiveClassifier

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier

# Create an adaptive classifier with Hoeffding tree core
clf = AdaptiveClassifier(
    n_features=6,
    n_classes=2,
    grace_period=20,
    delta=0.01,
)

# Stream training data
for batch_idx in range(10):
    X = np.random.randn(30, 6).astype(np.float32)
    y = (X[:, 0] > 0.5).astype(np.int64)

    # Incremental update
    metrics = clf.partial_fit(X, y)
    print(f"Batch {batch_idx}: Accuracy={metrics['accuracy']:.2f}")

# Inference
predictions = clf.predict(np.random.randn(5, 6).astype(np.float32))
print("Predictions:", predictions)
```

---

## 2. Using ReliabilityWeightedADWIN Standalone

```python
from robust_adapt.ala import ReliabilityWeightedADWIN

detector = ReliabilityWeightedADWIN(delta=0.002)

# Stream losses with simulated noise burst
for i in range(100):
    # Simulated loss value
    loss = 0.2 if i < 50 else 0.8
    # Estimated reliability (low during noise)
    reliability = 0.1 if (45 <= i < 55) else 1.0

    drift_detected = detector.update(loss, reliability=reliability)
    if drift_detected:
        print(f"Concept drift confirmed at step {i}!")
```
