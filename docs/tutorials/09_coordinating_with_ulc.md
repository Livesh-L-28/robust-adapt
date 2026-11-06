# Tutorial 09: Coordinating ALA, RLA, and RAO with ULC

**Objective**: Configure the `AdaptiveLearningController` to dynamically arbitrate between concept drift adaptation and noise burst filtering.

---

## 1. Setup & Imports

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier
from robust_adapt.rla import RobustLearningPipeline
from robust_adapt.ulc import AdaptiveLearningController

# Instantiate decoupled pillars
classifier = AdaptiveClassifier(max_depth=5)
rla_pipeline = RobustLearningPipeline(reliability_threshold=0.5)

# Initialize controller
controller = AdaptiveLearningController(
    classifier=classifier,
    rla_pipeline=rla_pipeline,
    cooldown_steps=10
)
```

---

## 2. Multi-Regime Streaming Loop

```python
np.random.seed(42)

for t in range(30):
    X = np.random.randn(25, 4).astype(np.float32)

    # Normal stream (t < 10)
    if t < 10:
        y = (X[:, 0] > 0.0).astype(np.int64)
    # Corrupted Noise Burst (10 <= t < 15): 80% inverted labels
    elif 10 <= t < 15:
        y = (X[:, 0] > 0.0).astype(np.int64)
        noise = np.random.rand(25) < 0.80
        y[noise] = 1 - y[noise]
    # Structural Concept Drift (t >= 15): New boundary x1 > 0
    else:
        y = (X[:, 1] > 0.0).astype(np.int64)

    result = controller.step(X, y)
    print(f"Step {t:02d} | Regime: {result['state']:<12} | Directive: {result['directive']}")
```

**Output Observations**:
- During steps $10-14$, the controller diagnoses `NOISE_BURST`, issues `DISCARD_CORRUPTED_SAMPLE`, and suppresses model resets.
- At step $15$, predictive entropy remains elevated across multiple steps; the controller transitions through `WARNING` to `DRIFT` and adapts the model cleanly.
