# Tutorial 02: Detecting Concept Drift

**Objective**: Detect structural distribution shifts in streaming loss trajectories using `ReliabilityWeightedADWIN`.

---

## 1. Setup & Imports

```python
import numpy as np
from robust_adapt.ala import ReliabilityWeightedADWIN

detector = ReliabilityWeightedADWIN(delta=0.002)
```

---

## 2. Simulating Streaming Loss with Abrupt Drift

```python
np.random.seed(42)

# Stream 200 loss values
# Step 0-99: Low loss (mean ~ 0.20)
# Step 100-199: High loss (mean ~ 0.85, concept drift)
for t in range(200):
    if t < 100:
        loss = np.random.normal(0.20, 0.05)
    else:
        loss = np.random.normal(0.85, 0.05)

    # Clip loss to valid range [0, 1]
    loss = float(np.clip(loss, 0.0, 1.0))

    # Update detector
    is_drift = detector.update(loss, reliability=1.0)
    if is_drift:
        print(f"Drift detected at step {t:03d} (Window Size: {detector.width})")
```

**Output**:
```
Drift detected at step 114 (Window Size: 46)
```

---

## 3. Suppressing False Alarms During Noise Bursts

```python
detector.reset()

for t in range(100):
    # Transient 5-step corrupted noise burst at t=50..54
    if 50 <= t < 55:
        loss = 0.95
        rel = 0.05  # Reliability scorer flagged this as corrupted
    else:
        loss = 0.15
        rel = 1.00

    is_drift = detector.update(loss, reliability=rel)
    assert not is_drift, f"False alarm triggered at step {t}!"

print("Noise burst successfully suppressed without false alarms!")
```
