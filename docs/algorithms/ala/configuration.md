# ALA 3.0: Configuration Reference

This guide documents the configuration parameters for `ALA30AdaptiveLearner` and `AdaptiveClassifier`.

---

## `ALA30AdaptiveLearner` Parameters

```python
from robust_adapt.ala import ALA30AdaptiveLearner

learner = ALA30AdaptiveLearner(
    n_features=10,
    n_classes=2,
    grace_period=20,
    delta=0.002,
    similarity_threshold=0.75,
    max_concepts=10,
    replay_capacity=2000,
    cooldown_steps=5,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`n_features`** | `int` | *Required* | Dimensionality of input feature vectors ($d \ge 1$). |
| **`n_classes`** | `int` | `2` | Number of distinct target classes ($K \ge 2$). |
| **`grace_period`** | `int` | `20` | Samples observed by a leaf node between split evaluation attempts. |
| **`delta`** | `float` | `0.002` | Hoeffding bound and ADWIN statistical confidence parameter ($0 < \delta < 1$). |
| **`similarity_threshold`** | `float` | `0.75` | Minimum Gaussian similarity required to declare a recurring concept match. |
| **`max_concepts`** | `int` | `10` | Maximum historical concept snapshots retained in memory. |
| **`replay_capacity`** | `int` | `2000` | Maximum instances retained in the class-balanced reservoir replay buffer. |
| **`cooldown_steps`** | `int` | `5` | Minimum steps between consecutive drift interventions to prevent thrashing. |

---

## Tuning Recommendations

- **Rapidly Drifting Environments**: Reduce `grace_period` (e.g. 10) and increase `delta` (e.g. 0.01) to split trees and trigger drift checks faster.
- **Noisy Streaming Environments**: Increase `grace_period` (e.g. 50) and decrease `delta` (e.g. 0.001) to prevent noise bursts from splitting nodes prematurely.
- **Memory-Constrained Edge Deployments**: Reduce `replay_capacity` (e.g. 500) and `max_concepts` (e.g. 3) to keep resident memory strictly sub-$30\text{ MB}$.
