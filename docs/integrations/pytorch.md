# PyTorch Framework Integration

AdaptiveML provides drop-in PyTorch modules for memory-efficient optimization and noise-tolerant training.

---

## 1. LowMemoryAdamW Optimizer Factory

Create an initialized `LowMemoryAdamW` optimizer for PyTorch neural network parameters:

```python
import torch
import torch.nn as nn
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw

model = nn.Sequential(
    nn.Linear(32, 64),
    nn.ReLU(),
    nn.Linear(64, 2)
)

optimizer = create_torch_low_memory_adamw(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-2,
    block_size=64
)

# Training loop
inputs = torch.randn(16, 32)
outputs = model(inputs)
loss = outputs.sum()

optimizer.zero_grad()
loss.backward()
optimizer.step()
```

---

## 2. TorchSymmetricCrossEntropyLoss Module

Native `nn.Module` computing bounded symmetric cross-entropy with analytical autograd compatibility:

```python
import torch
from adaptive_ml.integrations.torch_module import TorchSymmetricCrossEntropyLoss

criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)

logits = torch.randn(16, 5, requires_grad=True)
targets = torch.randint(0, 5, (16,))

loss = criterion(logits, targets)
loss.backward()

print("Loss value:", loss.item())
print("Gradients computed successfully!")
```
