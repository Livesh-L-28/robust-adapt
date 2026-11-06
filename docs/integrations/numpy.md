# Pure NumPy Backend Integration

AdaptiveML's default execution engine is built natively on top of NumPy, requiring zero external C++ extensions or GPU runtimes.

---

## 1. Native Vectorization

All core operations in `adaptive_ml.ala`, `adaptive_ml.rla`, and `adaptive_ml.rao` operate directly on contiguous NumPy `ndarray` buffers:
- **Matrix Vectorization**: Tree split information gain evaluated via SIMD matrix reductions.
- **Quantization**: Block-wise quantization performed via `np.clip` and vectorized scaling.
- **Memory Contiguity**: Buffer copies minimized via in-place views (`np.ndarray.view`).

---

## 2. Example: Standalone NumPy Optimization

```python
import numpy as np
from robust_adapt.rao import LowMemoryAdamW

# Optimize arbitrary NumPy parameter arrays
w = np.zeros(100, dtype=np.float32)

class SimpleParam:
    def __init__(self, data):
        self.data = data
        self.grad = np.zeros_like(data)

param = SimpleParam(w)
opt = LowMemoryAdamW([param], lr=0.01)

# Optimization step
param.grad = np.random.randn(100).astype(np.float32)
opt.step()
```
