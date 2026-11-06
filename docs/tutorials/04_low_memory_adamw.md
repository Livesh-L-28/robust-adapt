# Tutorial 4: Resource-Aware Optimization with LowMemoryAdamW

Learn how to save $73.44\%$ of optimizer state memory during neural network and tabular optimization.

---

## 1. The State Memory Bottleneck

Standard AdamW maintains two 32-bit floating-point momentum estimates ($m_t, v_t$) for every trainable parameter, requiring:
$$M_{\text{FP32}} = 4\text{ bytes } (m_t) + 4\text{ bytes } (v_t) = 8.00\text{ bytes/parameter}$$

For a 100M parameter model, optimizer state consumes $800\text{ MB}$. For a 1B parameter model, state consumes $8.0\text{ GB}$.

---

## 2. Using LowMemoryAdamW with Block Quantization

`LowMemoryAdamW` partitions parameters into blocks of size $B=64$, quantizing $m_t$ into signed `int8` ($1\text{ byte}$) and $v_t$ into unsigned `uint8` ($1\text{ byte}$), storing only one `float32` scale factor per block.

Total state memory footprint:
$$M_{\text{RAO}} = 1 + 1 + 2 \times \frac{4}{64} = 2.125\text{ bytes/parameter} \quad (-73.44\% \text{ RAM})$$

### PyTorch Usage
```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw

model = nn.Sequential(nn.Linear(20, 64), nn.ReLU(), nn.Linear(64, 2))
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, block_size=64)

# Standard training step
optimizer.zero_grad()
loss.backward()
optimizer.step()

print(f"State Memory: {optimizer.get_state_memory_bytes()} bytes")
```

Executable demo available at [`examples/rao/low_memory_optimization_example.py`](file:///c:/projects/AdaptiveML/examples/rao/low_memory_optimization_example.py).
