# PyTorch Framework Integration Guide

AdaptiveML provides native PyTorch modules, robust autograd loss functions, memory-efficient optimizers, runtime resource budget hooks, and cryptographic safe checkpointing.

---

## 1. Overview of PyTorch Components

Exported from `adaptive_ml.integrations`:

| Component | Type | Primary Purpose |
|:---|:---|:---|
| [`TorchSymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_module.py) | `nn.Module` | Noise-tolerant loss combining Cross-Entropy and Reverse Cross-Entropy ($\alpha, \beta$). |
| [`TorchGeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_module.py) | `nn.Module` | Bounded loss interpolating between MAE and CCE via parameter $q \in (0.0, 1.0]$. |
| [`create_torch_low_memory_adamw`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_optim.py) | Optimizer Factory | 8-bit block-quantized AdamW achieving $75\%$ reduction in optimizer state RAM. |
| [`TorchTrainingBudgetHook`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_callback.py) | Training Callback | Tracks per-step latency and physical RSS RAM; dynamically adapts batch size. |
| [`TorchCheckpointAdapter`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_callback.py) | State Serializer | Safe checkpointing separating neural weights (SafeTensors) from metadata (JSON). |

---

## 2. Robust Loss Functions for Corrupted Labels

Standard neural networks quickly memorize noisy or mislabeled data. AdaptiveML provides two mathematically principled robust loss functions:

### 2.1 Symmetric Cross-Entropy Loss

Combines standard Cross-Entropy $H(p, q)$ with Reverse Cross-Entropy $H(q, p)$:
$$\mathcal{L}_{SCE} = \alpha \cdot \mathcal{L}_{CE} + \beta \cdot \mathcal{L}_{RCE}$$

```python
import torch
from robust_adapt.integrations.torch_module import TorchSymmetricCrossEntropyLoss

criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.8)

logits = model(inputs)
loss = criterion(logits, targets)
loss.backward()
```

### 2.2 Generalized Cross-Entropy Loss

Applies a negative Box-Cox transformation bounding gradients on hard, ambiguous, or corrupted instances:
$$\mathcal{L}_{GCE} = \frac{1 - p_y^q}{q}, \quad q \in (0.0, 1.0]$$

```python
from robust_adapt.integrations.torch_module import TorchGeneralizedCrossEntropyLoss

# q=0.7 is recommended for moderate label corruption
criterion = TorchGeneralizedCrossEntropyLoss(q=0.7)
loss = criterion(logits, targets)
```

---

## 3. 8-Bit Quantized AdamW (`create_torch_low_memory_adamw`)

Standard fp32 AdamW stores two state moments ($m_t, v_t$) per parameter, requiring $8\text{ bytes}$ of optimizer state per parameter (e.g., 800MB for a 100M parameter model). `LowMemoryAdamW` quantizes states into 8-bit dynamic blocks ($B=2048$):

```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw

model = nn.Sequential(
    nn.Linear(128, 256),
    nn.ReLU(),
    nn.Linear(256, 10),
)

optimizer = create_torch_low_memory_adamw(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-2,
)

# Standard training step
optimizer.zero_grad()
loss = criterion(model(x), y)
loss.backward()
optimizer.step()
```

---

## 4. Runtime Budget Management (`TorchTrainingBudgetHook`)

Detect physical RAM pressure and execution latency bottlenecks during neural training:

```python
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.integrations.torch_callback import TorchTrainingBudgetHook

budget_mgr = DynamicResourceBudgetManager(
    max_step_time_ms=50.0,
    max_memory_mb=4096.0,
    min_batch_size=16,
    max_batch_size=128,
)
budget_hook = TorchTrainingBudgetHook(budget_mgr)

for epoch in range(10):
    for batch_idx in range(num_batches):
        curr_batch_size = budget_hook.recommended_batch_size
        x_batch, y_batch = get_batch(curr_batch_size)

        budget_hook.on_step_begin()
        optimizer.zero_grad()
        loss = criterion(model(x_batch), y_batch)
        loss.backward()
        optimizer.step()
        state = budget_hook.on_step_end()

        if state == "PRESSURE_WARNING":
            print("System approaching memory ceiling; batch size throttled automatically.")
```

---

## 5. Safe Checkpointing (`TorchCheckpointAdapter`)

Standard `torch.save(model)` relies on Python `pickle`, introducing arbitrary code execution vulnerabilities. `TorchCheckpointAdapter` serializes tensor weights using HuggingFace `safetensors` and saves controller and optimizer states as readable JSON:

```python
from pathlib import Path
from robust_adapt.integrations.torch_callback import TorchCheckpointAdapter

# Save checkpoint safely
saved_file = TorchCheckpointAdapter.save_hybrid_checkpoint(
    model=model,
    optimizer=optimizer,
    controller=None,
    filepath="checkpoints/model.safetensors",
)

# Restore checkpoint safely
TorchCheckpointAdapter.load_hybrid_checkpoint(
    model=restored_model,
    optimizer=restored_optimizer,
    controller=None,
    filepath="checkpoints/model.safetensors",
)
```
