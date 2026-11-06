# Dynamic Threshold Management & PID Control

Standard classification fixes the decision threshold at $\theta = 0.50$. Under severe class imbalance, this static choice almost guarantees failure:
- If $\theta = 0.50$ is too high, minority recall collapses to $0\%$.
- If $\theta = 0.50$ is arbitrarily lowered (e.g. to $0.10$), false positive alarms surge, overwhelming downstream human fraud review teams.

---

## 1. The PID Regulating Mechanism

`DynamicFPBudgetThresholdManager` treats false positive rate control as an industrial feedback regulation problem:

```
[ Error Signal: e_t = Measured_FPR - Budget_FPR ]
                      |
                      v
      +-------------------------------+
      |  PID Controller Calculation   |
      |  Delta = Kp*e + Ki*Int + Kd*D |
      +-------------------------------+
                      |
                      v
       [ Adjusted Threshold theta_t ]
                      |
                      v
      [ Stream Decision: y_hat = P(y=1) > theta_t ]
```

### Response Characteristics
- **When FPR Spikes Above Budget**: Error $e_t > 0 \implies \Delta \theta > 0$. The threshold slides upward, suppressing false alarms and returning FPR to budget.
- **When FPR Drops Far Below Budget**: Error $e_t < 0 \implies \Delta \theta < 0$. The threshold slides downward, safely recovering additional minority recall without violating the budget ceiling.
- **Deadband Protection**: Prevents jitter from individual random negative samples.

---

## 2. Threshold Calibration Code Example

```python
import numpy as np
from robust_adapt.minority import DynamicFPBudgetThresholdManager

# Target budget: 2.0 false positives per 1,000 samples (FPR = 0.002)
manager = DynamicFPBudgetThresholdManager(target_fp_budget_per_1k=2.0)

print(f"Initial Threshold: {manager.current_threshold:.3f}")

# Simulate a sudden surge in false positives
for step in range(10):
    # False positive rate spikes to 0.010 (5x budget!)
    manager.update(current_fpr=0.010)

print(f"Adjusted Threshold after FP surge: {manager.current_threshold:.3f}")
assert manager.current_threshold > 0.50  # Threshold raised to protect budget!
```
