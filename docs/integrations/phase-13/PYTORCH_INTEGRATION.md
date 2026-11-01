# PyTorch Integration Specification

**Document ID:** `DOC-INT-P13-003`  
**Phase:** Phase 13 — Framework Integrations  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.integrations.torch_optim`, `adaptive_ml.integrations.torch_module`

---

## 1. PyTorch Optimizer Integration (`LowMemoryAdamW`)

### 1.1 Architecture & Subclassing
- Inherits from `torch.optim.Optimizer` when PyTorch is installed and parameters are instances of `torch.nn.Parameter` or `torch.Tensor`.
- State tensors:
  - First moment $m_t$: Stored as quantized `torch.int8` tensor on active device.
  - Second moment $v_t$: Stored as quantized `torch.uint8` tensor on active device.
  - Scale vectors $s_m, s_v$: Stored as `torch.float32` tensors ($B=64$ parameter blocks).
- Total State Footprint: $2.125\text{ bytes/parameter}$ vs $8.00\text{ bytes/parameter}$ standard FP32 AdamW ($73.44\%$ memory reduction).

### 1.2 Usage Syntax
```python
import torch
import torch.nn as nn
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw

model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 2))
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, block_size=64)

# Standard training step
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

---

## 2. PyTorch Native Robust Loss (`TorchSymmetricCrossEntropyLoss`)

- Inherits from `torch.nn.Module`.
- Combines standard Cross-Entropy with Reverse Cross-Entropy:
  $$\mathcal{L}_{\text{SCE}} = \alpha \cdot \mathcal{L}_{\text{CE}} + \beta \cdot \mathcal{L}_{\text{RCE}}$$
- Strictly bounds gradients against corrupted labels while autograd handles backpropagation.

