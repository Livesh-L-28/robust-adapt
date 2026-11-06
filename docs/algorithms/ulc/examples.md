# ULC-v5 Code Examples

This page demonstrates end-to-end multi-pillar coordination using `UnifiedLearningControllerV5`.

---

## Complete Streaming Pipeline Demonstration

```python
import numpy as np
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config, InterventionTier

# 1. Initialize ULC-v5 controller
config = ULCv5Config(
    grace_period=15,
    delta=0.005,
    similarity_threshold=0.75,
    base_cooldown=3,
    replay_capacity=500,
    random_state=42,
)
controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

np.random.seed(42)
n_steps = 100
batch_size = 8

# Generate stream with concept shift at step 40 and recurring return at step 80
w_A = np.array([2.0, -1.0, 0.5, 0.0])
w_B = np.array([-2.0, 1.0, 0.0, 1.5])

print("Processing streaming data through ULC-v5...")

for step in range(n_steps):
    # Active concept selection
    w_active = w_A if (step < 40 or step >= 80) else w_B

    X_b = np.random.randn(batch_size, 4)
    y_b = (X_b @ w_active > 0).astype(int)

    # Process batch
    directive, telemetry = controller.step(X_b, y_b)

    if directive.tier != InterventionTier.TIER_0_NOOP:
        print(f"Step {step:03d} Intervention: {directive.tier.value} | {directive.message}")

print("--------------------------------------------------")
print(f"Total Steps Processed:     {controller.total_steps}")
print(f"Total Interventions:       {controller.tier_counts}")
print(f"Concepts Stored in Memory: {controller.memory.n_stored}")
print("ULC-v5 pipeline execution verified!")
```
