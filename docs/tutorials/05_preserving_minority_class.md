# Tutorial 05: Preserving Minority-Class Examples

**Objective**: Prevent rare minority samples from being falsely discarded during noise cleaning using density-aware margin scoring (Theorem 2).

---

## 1. Setup & Imports

```python
import numpy as np
from adaptive_ml.rla.scorer import DensityAwareMarginScorer

scorer = DensityAwareMarginScorer(k_neighbors=5, alpha=1.0, beta=1.0)
```

---

## 2. Differentiating Noise from Valid Minority Instances

```python
np.random.seed(42)

# Create 100 samples:
# - 90 samples: Class 0 majority cluster centered at (0, 0)
# - 5 samples: Corrupted Class 0 instances mislabeled as Class 1
# - 5 samples: True Class 1 minority instances centered at (4, 4)

X_majority = np.random.normal(0.0, 0.5, size=(90, 2)).astype(np.float32)
y_majority = np.zeros(90, dtype=np.int64)

X_noise = np.random.normal(0.0, 0.5, size=(5, 2)).astype(np.float32)
y_noise = np.ones(5, dtype=np.int64)  # Mislabeled as 1

X_minority = np.random.normal(4.0, 0.5, size=(5, 2)).astype(np.float32)
y_minority = np.ones(5, dtype=np.int64)  # True minority

X = np.vstack([X_majority, X_noise, X_minority])
y = np.concatenate([y_majority, y_noise, y_minority])

# Synthetic model logits
logits = np.zeros((100, 2), dtype=np.float32)
logits[:95, 0] = 3.0   # Predicts Class 0 for majority and noise
logits[95:, 1] = 3.0   # Predicts Class 1 for minority

# Compute reliability scores
reliability = scorer.score_samples(X, y, logits)

mean_noise_rel = np.mean(reliability[90:95])
mean_minority_rel = np.mean(reliability[95:])

print(f"Mean reliability of Corrupted Noise: {mean_noise_rel:.3f} (Filtered out)")
print(f"Mean reliability of Valid Minority:  {mean_minority_rel:.3f} (Preserved)")
assert mean_minority_rel > mean_noise_rel, "Theorem 2 violation!"
```

**Output**:
```
Mean reliability of Corrupted Noise: 0.124 (Filtered out)
Mean reliability of Valid Minority:  0.892 (Preserved)
```
Valid minority instances are preserved while corrupted samples in the dense majority cluster are filtered out.
