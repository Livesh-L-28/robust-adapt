# Minority Intelligence: Configuration Reference

This guide details configuration parameters for `MinorityIntelligence20Learner`, `BetaBinomialPriorTracker`, and `DynamicFPBudgetThresholdManager`.

---

## `MinorityIntelligence20Learner` Parameters

```python
from robust_adapt.minority import MinorityIntelligence20Learner

learner = MinorityIntelligence20Learner(
    target_fp_budget_per_1k=1.5,
    sublinear_cost_power=0.52,
    base_threshold=0.50,
    min_threshold=0.15,
    max_threshold=0.85,
    lr=0.01,
    minority_class=1,
    random_state=42,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`target_fp_budget_per_1k`** | `float` | `1.5` | Target allowable false alarms per 1,000 negative samples. |
| **`sublinear_cost_power`** | `float` | `0.52` | Exponent $\alpha$ in sublinear cost scaling $w_1 = (1/\pi)^\alpha$. |
| **`base_threshold`** | `float` | `0.50` | Initial classification decision threshold. |
| **`min_threshold`** | `float` | `0.15` | Lower boundary clamp on decision threshold. |
| **`max_threshold`** | `float` | `0.85` | Upper boundary clamp on decision threshold. |
| **`lr`** | `float` | `0.01` | Online learning rate for parameter updates. |
| **`minority_class`** | `int` | `1` | Target class index corresponding to the rare minority class. |
| **`random_state`** | `Optional[int]` | `42` | Seed for reproducible initialization. |

---

## `DynamicFPBudgetThresholdManager` Parameters

```python
from robust_adapt.minority import DynamicFPBudgetThresholdManager

manager = DynamicFPBudgetThresholdManager(
    target_fp_budget_per_1k=1.5,
    base_threshold=0.5,
    kp=0.5,
    ki=0.05,
    kd=0.02,
    min_threshold=0.15,
    max_threshold=0.85,
    anti_windup_max=0.2,
    deadband=0.0002,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`kp`** | `float` | `0.5` | Proportional PID gain. |
| **`ki`** | `float` | `0.05` | Integral PID gain. |
| **`kd`** | `float` | `0.02` | Derivative PID gain. |
| **`anti_windup_max`** | `float` | `0.2` | Maximum allowable accumulator for the integral term. |
| **`deadband`** | `float` | `0.0002` | Error magnitude threshold below which PID updates are zeroed. |
