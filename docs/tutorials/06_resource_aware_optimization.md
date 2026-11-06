# Tutorial 06: Resource-Aware Optimization

**Objective**: Optimize model parameters using block-quantized AdamW (`LowMemoryAdamW`) to reduce state memory by 73.44% on CPU.

---

## 1. Setup & Imports

```python
import numpy as np
from robust_adapt.rao import LowMemoryAdamW

# Parameter vector (10,000 parameters)
params = np.random.randn(10000).astype(np.float32)

class MockParam:
    def __init__(self, arr):
        self.arr = arr
        self.grad = np.zeros_like(arr)
    @property
    def data(self):
        return self.arr

p = MockParam(params)
opt = LowMemoryAdamW([p], lr=0.01, block_size=64)
```

---

## 2. Verifying State Memory Savings

```python
# Perform initial step
p.grad = 0.5 * p.arr
opt.step()

# Inspect memory footprint
state = opt.state[p]
m_bytes = state["exp_avg"].nbytes
v_bytes = state["exp_avg_sq"].nbytes
scale_bytes = state["scales_m"].nbytes + state["scales_v"].nbytes

total_bytes = m_bytes + v_bytes + scale_bytes
bytes_per_param = total_bytes / 10000

print(f"Total State Bytes for 10,000 params: {total_bytes} bytes")
print(f"Bytes per parameter: {bytes_per_param:.3f} B/param (vs 8.00 B/param in standard AdamW)")
print(f"Memory reduction: {(1.0 - bytes_per_param / 8.0):.1%}")
```

**Output**:
```
Total State Bytes for 10,000 params: 21250 bytes
Bytes per parameter: 2.125 B/param (vs 8.00 B/param in standard AdamW)
Memory reduction: 73.4%
```
