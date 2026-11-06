# Tutorial 3: Robust Learning Under Label Noise & Class Imbalance

Learn how `DensityAwareMarginScorer` and `SymmetricCrossEntropyLoss` preserve minority classes while filtering corrupt annotations.

---

## 1. The Minority Class Dilemma (Theorem 2)

Standard label-cleaning heuristics discard samples with negative margins. However, extreme minority instances naturally live near decision boundaries in low-density feature space. Naive filtering purges rare classes, accelerating model collapse.

AdaptiveML introduces density penalty moderation:
$$\psi(\delta_k) = -\ln(\delta_k + \epsilon)$$
In low-density regions ($\delta_k \ll 1$), $\psi(\delta_k) > 0$, awarding a protective margin bonus that prevents rare samples from being purged.

---

## 2. Using RobustLearningPipeline

```python
import numpy as np
from robust_adapt.rla.pipeline import RobustLearningPipeline

# Initialize for a 3-class problem
pipeline = RobustLearningPipeline(
    n_classes=3,
    alpha=1.0,         # Cross-Entropy weight
    beta=0.5,          # Reverse Cross-Entropy weight
    gamma_density=0.8, # Tail minority protection
)

# Evaluate a mini-batch
X = np.random.randn(30, 4)
logits = np.random.randn(30, 3)
y = np.random.choice([0, 1, 2], size=30)

loss, grad_logits, reliabilities = pipeline.evaluate_batch(X, logits, y)

print(f"Batch Loss: {loss:.4f}")
print(f"Sample Reliabilities: min={reliabilities.min():.3f}, max={reliabilities.max():.3f}")
```

Executable demo available at [`examples/rla/robust_learning_example.py`](file:///c:/projects/AdaptiveML/examples/rla/robust_learning_example.py).
