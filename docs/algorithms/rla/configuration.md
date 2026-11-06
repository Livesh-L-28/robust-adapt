# RLA 3.0: Configuration Reference

This guide details configuration parameters for `RLA30RobustLearner` and `MultiSignalReliabilityEngine`.

---

## `RLA30RobustLearner` Parameters

```python
from robust_adapt.rla import RLA30RobustLearner

learner = RLA30RobustLearner(
    n_features=8,
    n_classes=2,
    lr=0.01,
    reliability_threshold=0.50,
    security_mode=False,
    minority_class=1,
    random_state=42,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`n_features`** | `int` | *Required* | Dimensionality of input feature vectors ($d \ge 1$). |
| **`n_classes`** | `int` | `2` | Number of distinct target classes ($K \ge 2$). |
| **`lr`** | `float` | `0.01` | Online gradient descent learning rate. |
| **`reliability_threshold`** | `float` | `0.50` | Minimum reliability $r_i$ required to include sample in gradient updates. |
| **`security_mode`** | `bool` | `False` | When `True`, elevates scrutiny on minority class samples to resist targeted poisoning. |
| **`minority_class`** | `int` | `1` | Index of the protected minority class. |
| **`random_state`** | `Optional[int]` | `None` | Seed for reproducible random weight initialization. |

---

## `MultiSignalReliabilityEngine` Parameters

```python
from robust_adapt.rla import MultiSignalReliabilityEngine

engine = MultiSignalReliabilityEngine(
    n_classes=2,
    k_neighbors=5,
    buffer_size=500,
    weight_margin=0.40,
    weight_neighbor=0.40,
    weight_temporal=0.20,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`k_neighbors`** | `int` | `5` | Number of spatial nearest neighbors queried for neighborhood consensus. |
| **`buffer_size`** | `int` | `500` | Maximum recent instances retained in the spatial search ring buffer. |
| **`weight_margin`** | `float` | `0.40` | Weight assigned to model prediction margin/entropy signal. |
| **`weight_neighbor`** | `float` | `0.40` | Weight assigned to spatial neighborhood agreement. |
| **`weight_temporal`** | `float` | `0.20` | Weight assigned to temporal consistency across consecutive samples. |
