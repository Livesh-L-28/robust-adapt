# Minority Intelligence 2.0 Code Examples

This page demonstrates using Adaptive Minority Intelligence 2.0 on an imbalanced streaming classification task ($0.5\%$ minority class).

---

## Example 1: Imbalanced Streaming Classification

```python
import numpy as np
from robust_adapt.minority import MinorityIntelligence20Learner

# Set random seed for reproducibility
np.random.seed(42)
n_samples = 1000
n_features = 4

# Generate highly imbalanced stream (99.5% negative, 0.5% positive)
X = np.random.randn(n_samples, n_features)
y = np.zeros(n_samples, dtype=int)
# 5 minority events out of 1,000 samples
minority_indices = [50, 220, 480, 710, 930]
for idx in minority_indices:
    X[idx] += np.array([2.5, 2.5, 0.0, 0.0])  # Shift feature distribution
    y[idx] = 1

# Initialize learner with 2.0 false positive budget per 1,000 samples
learner = MinorityIntelligence20Learner(
    target_fp_budget_per_1k=2.0,
    sublinear_cost_power=0.52,
    lr=0.02,
    random_state=42,
)

# Stream processing loop
batch_size = 50
for start in range(0, n_samples, batch_size):
    end = start + batch_size
    X_b = X[start:end]
    y_b = y[start:end]

    # Fit micro-batch
    learner.partial_fit(X_b, y_b)

# Final evaluation
predictions = learner.predict(X)
detected_minority = np.where((predictions == 1) & (y == 1))[0]
false_alarms = np.where((predictions == 1) & (y == 0))[0]

print("--------------------------------------------------")
print(f"Total Stream Samples:    {n_samples}")
print(f"True Minority Count:     {len(minority_indices)}")
print(f"Minority Events Caught:  {len(detected_minority)} / {len(minority_indices)}")
print(f"False Positives Triggered: {len(false_alarms)}")
print(f"Operational Threshold:   {learner.threshold_manager.current_threshold:.3f}")
print("Minority streaming demonstration complete!")
```
