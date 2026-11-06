# ULC-v5: Configuration Reference

This guide details configuration parameters for `UnifiedLearningControllerV5` and `ULCv5Config`.

---

## `ULCv5Config` Hyperparameters

```python
from robust_adapt.ulc import ULCv5Config, UnifiedLearningControllerV5

config = ULCv5Config(
    grace_period=50,
    delta=0.002,
    similarity_threshold=0.82,
    base_cooldown=5,
    max_concepts=5,
    replay_capacity=1000,
    catastrophic_drift_threshold=0.95,
    gate_rla_on_clean_stream=True,
    random_state=42,
)

controller = UnifiedLearningControllerV5(n_features=8, n_classes=2, config=config)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`grace_period`** | `int` | `50` | Leaf split evaluation grace period for internal Hoeffding tree. |
| **`delta`** | `float` | `0.002` | Statistical confidence parameter for ADWIN and Hoeffding bounds. |
| **`similarity_threshold`**| `float` | `0.82` | Gaussian similarity threshold required to trigger historical concept restoration. |
| **`base_cooldown`** | `int` | `5` | Base lockout step count applied after non-trivial interventions. |
| **`max_concepts`** | `int` | `5` | Maximum historical concept snapshots retained in memory. |
| **`replay_capacity`** | `int` | `1000` | Total capacity of class-balanced experience replay buffer. |
| **`catastrophic_drift_threshold`** | `float` | `0.95` | Confidence threshold required to unlock Tier 4 emergency hard reset. |
| **`gate_rla_on_clean_stream`** | `bool` | `True` | Disables aggressive label filtering on verified clean concept-drifting streams. |
| **`random_state`** | `Optional[int]` | `None` | Seed for deterministic initialization and replay buffer sampling. |
