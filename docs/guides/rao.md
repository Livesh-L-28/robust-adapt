# Resource-Aware Optimization (RAO) User Guide

This guide covers memory-efficient optimizer state quantization, micro-batch scheduling, and CPU performance tuning.

---

## 1. LowMemoryAdamW Usage

`LowMemoryAdamW` drops optimizer state RAM by $73.44\%$ across NumPy and PyTorch models:

```python
import numpy as np
from adaptive_ml.rao import LowMemoryAdamW

# Optimize parameters
weights = np.random.randn(1000).astype(np.float32)

class Wrapper:
    def __init__(self, arr):
        self.arr = arr
        self.grad = np.zeros_like(arr)
    @property
    def data(self):
        return self.arr

p = Wrapper(weights)
optimizer = LowMemoryAdamW([p], lr=0.01, block_size=64)

# Training step
p.grad = 0.1 * p.arr
optimizer.step()
```

---

## 2. Resource Budget Management

```python
from adaptive_ml.rao.memory import ResourceBudget

# Set budget: max 256MB RAM and 20ms per step
budget = ResourceBudget(max_rss_mb=256.0, max_step_time_ms=20.0)

with budget.track_step():
    # Execute batch training operation
    pass

metrics = budget.get_telemetry()
print(f"Current Process RSS: {metrics['current_rss_mb']:.1f} MB")
```
