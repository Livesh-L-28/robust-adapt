# Tutorial 07: PyTorch Integration

**Objective**: Train a multi-layer perceptron in PyTorch combining `LowMemoryAdamW` with `TorchSymmetricCrossEntropyLoss`.

---

## 1. Setup & Imports

```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw
from robust_adapt.integrations.torch_module import TorchSymmetricCrossEntropyLoss

# Define PyTorch neural network
model = nn.Sequential(
    nn.Linear(16, 32),
    nn.ReLU(),
    nn.Linear(32, 2)
)

criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, block_size=32)
```

---

## 2. Training Loop with Noisy Labels

```python
torch.manual_seed(42)

for epoch in range(1, 6):
    inputs = torch.randn(32, 16)
    # Synthetic labels with 10% label corruption
    targets = (inputs[:, 0] > 0.0).long()
    noise_mask = torch.rand(32) < 0.10
    targets[noise_mask] = 1 - targets[noise_mask]

    optimizer.zero_grad()
    logits = model(inputs)
    loss = criterion(logits, targets)
    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch:02d} | Loss: {loss.item():.4f}")
```

**Output**:
```
Epoch 01 | Loss: 1.4820
Epoch 02 | Loss: 1.3412
Epoch 03 | Loss: 1.2185
Epoch 04 | Loss: 1.1090
Epoch 05 | Loss: 1.0124
```
The PyTorch neural network converges smoothly despite label noise, requiring only $2.125\text{ B/param}$ of optimizer state memory.
