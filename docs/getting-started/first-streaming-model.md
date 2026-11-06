# Your First Unified Streaming Pipeline

In production applications, individual components (drift detection, sample reliability, and experience replay) must be coordinated to prevent oscillation and catastrophic forgetting.

The **Unified Learning Controller V5 (`UnifiedLearningControllerV5`)** provides turnkey coordination across all pillars.

---

## Turnkey Coordination with ULC-v5

`UnifiedLearningControllerV5` combines:
1. Prequential prediction and error tracking.
2. Statistical drift detection (`ReliabilityWeightedADWIN`).
3. Class-balanced experience replay buffer (`ClassBalancedReservoirReplay`).
4. Concept fingerprinting and historical snapshot memory (`RecurringConceptMemory`).
5. Five-tier intervention arbitration (NOOP, Damping, Concept Restore, Soft Replay Reset, Hard Reset).
6. Anti-thrashing exponential cooldown backoff.

---

## Complete Working Example

```python
import numpy as np
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config

# 1. Configure the unified controller
config = ULCv5Config(
    grace_period=20,
    delta=0.002,
    similarity_threshold=0.80,
    base_cooldown=5,
    replay_capacity=500,
)

# 2. Instantiate controller for 4 features, 2 classes
controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

print("Starting ULC-v5 streaming processing...")

# 3. Process batches of incoming streaming data
np.random.seed(42)
w = np.array([1.5, -2.0, 0.5, 1.0])

for step in range(50):
    # Micro-batch of 8 streaming samples
    X_batch = np.random.randn(8, 4)
    y_batch = (X_batch @ w > 0).astype(int)

    # Execute prequential step: evaluation, arbitration, and learning
    directive, telemetry = controller.step(X_batch, y_batch)

    if step % 10 == 0:
        print(
            f"Step {step:02d}: Action={directive.action_name:<18} "
            f"Tier={directive.tier.value:<22} "
            f"Error={telemetry['mean_error']:.2f} "
            f"Replay={telemetry['replay_size']}"
        )

print("ULC-v5 pipeline completed successfully!")
```

---

## Inspecting Telemetry

The second return value of `controller.step(X, y)` is a detailed telemetry dictionary:
- `step`: Monotonically increasing stream step.
- `tier`: The intervention tier selected by utility scoring (`TIER_0_NOOP`, `TIER_1_PARAM_DAMPING`, etc.).
- `action`: Human-readable description of the action taken.
- `mean_error`: Prequential batch error rate.
- `replay_size`: Current number of stratified samples retained in the reservoir replay buffer.
- `concepts_stored`: Count of distinct historical concept signatures saved in memory.
- `cooldown_remaining`: Remaining lockout steps preventing controller thrashing.
