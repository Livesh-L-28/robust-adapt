# RLA 3.0 Code Examples

This page provides runnable code examples demonstrating RLA 3.0 in noisy streaming scenarios.

---

## Example 1: Filtering Extreme Label Noise

```python
import numpy as np
from robust_adapt.rla import RLA30RobustLearner

np.random.seed(42)
n_samples = 200
n_features = 4

# Generate separable linear dataset
X = np.random.randn(n_samples, n_features)
y_clean = (X[:, 0] > 0).astype(int)

# Inject 30% random label flips (symmetric noise)
y_noisy = y_clean.copy()
corrupt_indices = np.random.choice(n_samples, size=int(0.3 * n_samples), replace=False)
y_noisy[corrupt_indices] = 1 - y_noisy[corrupt_indices]

# Initialize robust learner with selective abstention
learner = RLA30RobustLearner(
    n_features=n_features,
    n_classes=2,
    lr=0.05,
    reliability_threshold=0.60,
    random_state=42,
)

# Stream processing loop
for i in range(n_samples):
    learner.partial_fit(X[i : i + 1], y_noisy[i : i + 1])

# Evaluate against clean ground truth
acc = learner.score(X, y_clean)

print("--------------------------------------------------")
print(f"Total Stream Samples Seen: {learner.total_samples_seen}")
print(f"Samples Retained:          {learner.retained_samples}")
print(f"Samples Abstained:         {learner.abstained_samples}")
print(f"Accuracy on Clean Labels:  {acc:.2%}")
print("RLA filtering demonstration complete!")
```

---

## Example 2: Standalone Multi-Signal Scoring

```python
import numpy as np
from robust_adapt.rla import MultiSignalReliabilityEngine

engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=3, buffer_size=100)

# Simulate a batch of 4 samples: 3 consistent, 1 blatant outlier
X_batch = np.array([
    [1.0, 1.0],
    [1.1, 0.9],
    [0.9, 1.2],
    [1.0, 1.1],  # Similar features, but mislabeled!
])
y_batch = np.array([1, 1, 1, 0])  # Sample 3 reported as class 0
probs_batch = np.array([
    [0.1, 0.9],
    [0.15, 0.85],
    [0.05, 0.95],
    [0.1, 0.9],  # Model predicts class 1 with 90% confidence!
])

reliabilities = engine.compute_reliability(X_batch, y_batch, probs_batch)

for idx, r in enumerate(reliabilities):
    print(f"Sample {idx}: Reported Label={y_batch[idx]}, Reliability Score={r:.3f}")
```
