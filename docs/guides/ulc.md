# Unified Learning Controller (ULC) User Guide

This guide covers coordinating ALA, RLA, and RAO dynamically using the `AdaptiveLearningController`.

---

## 1. End-to-End Orchestrated Pipeline

```python
import numpy as np
from adaptive_ml.ala import AdaptiveClassifier
from adaptive_ml.rla import RobustLearningPipeline
from adaptive_ml.rao import LowMemoryAdamW
from adaptive_ml.ulc import AdaptiveLearningController

# Initialize decoupled components
clf = AdaptiveClassifier(max_depth=4)
pipeline = RobustLearningPipeline()
controller = AdaptiveLearningController(
    classifier=clf,
    rla_pipeline=pipeline,
    cooldown_steps=10
)

# Stream processing loop
for t in range(50):
    X = np.random.randn(20, 4).astype(np.float32)
    y = (X[:, 0] > 0.0).astype(np.int64)
    
    # Controller step evaluates evidence and directs adaptation vs filtering
    result = controller.step(X, y)
    print(f"Step {t:02d} | State: {result['state']} | Directive: {result['directive']}")
```
