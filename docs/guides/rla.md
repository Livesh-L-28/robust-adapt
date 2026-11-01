# Robust Learning Algorithms (RLA) User Guide

This guide covers sample reliability scoring, robust loss functions, and minority class preservation.

---

## 1. RobustLearningPipeline Example

```python
import numpy as np
from adaptive_ml.rla import RobustLearningPipeline

# Initialize pipeline with density-aware scoring and symmetric loss
pipeline = RobustLearningPipeline(
    alpha=1.0,
    beta=0.1,
    reliability_threshold=0.5
)

# Simulated features with 20% noise and 100:1 class imbalance
X = np.random.randn(200, 8).astype(np.float32)
y = np.zeros(200, dtype=np.int64)
y[:5] = 1  # 5 minority samples

# Fit and evaluate
pipeline.fit(X, y)
eval_results = pipeline.evaluate(X, y)

print(f"Clean samples retained: {eval_results['n_clean']} / 200")
print(f"Mean reliability score: {eval_results['mean_reliability']:.3f}")
```

---

## 2. Standalone Loss Functions

AdaptiveML provides pure NumPy implementations of Symmetric Cross-Entropy and Generalized Cross-Entropy with analytical gradients:

```python
import numpy as np
from adaptive_ml.rla import SymmetricCrossEntropyLoss

loss_fn = SymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)

logits = np.random.randn(10, 3).astype(np.float32)
targets = np.random.randint(0, 3, size=10)

loss_value = loss_fn(logits, targets)
grad = loss_fn.backward(logits, targets)

print("Loss:", loss_value)
print("Gradient shape:", grad.shape)
```
