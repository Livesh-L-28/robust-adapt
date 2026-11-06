# Tutorial 5: Cross-Pillar Coordination with ULC

Learn how the Unified Learning Controller arbitrates between concept drift adaptation and label noise burst suppression.

---

## 1. The Conflict

When model error surges on a data stream:
- **If caused by concept drift**: The model must adapt immediately, reset obsolete statistics, and purge outdated replay buffers.
- **If caused by a noise burst**: The model must discard corrupted instances and freeze existing weights to prevent catastrophic forgetting.

---

## 2. Using AdaptiveLearningController

The ULC constructs an evidence vector $\mathbf{e}_\tau = [\Delta_{\text{drift}}, \bar{R}_{\mathcal{W}}, \mathcal{H}_{\text{pred}}, \mathcal{T}_{\text{loss}}]^\top$ and drives a 5-state arbitration automaton:

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier
from robust_adapt.rla import RobustLearningPipeline
from robust_adapt.ulc import AdaptiveLearningController
from robust_adapt.core.config import ULCConfig

# Initialize independent components
classifier = AdaptiveClassifier(n_features=4, n_classes=2)
pipeline = RobustLearningPipeline(n_classes=2)

# Wrap in Unified Controller
controller = AdaptiveLearningController(
    classifier=classifier,
    pipeline=pipeline,
    config=ULCConfig(tau_R=0.48, recovery_steps=4),
)

# Process streaming batches
X = np.random.randn(30, 4)
y = np.random.choice([0, 1], size=30)

directive, info = controller.step(X, y)
print(f"Controller State: {directive.state.value}")
print(f"Action: {directive.message}")
print(f"Retained Samples: {info['n_retained_samples']} / {info['n_input_samples']}")
```

Executable demo available at [`examples/ulc/unified_controller_example.py`](file:///c:/projects/AdaptiveML/examples/ulc/unified_controller_example.py).
