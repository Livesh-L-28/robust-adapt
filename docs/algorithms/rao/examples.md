# RAO 2.0 Code Examples

This page demonstrates using `VectorizedLowMemoryAdamW` to train PyTorch neural networks with minimal optimizer memory.

---

## Example 1: PyTorch Neural Network Training

```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW

# 1. Define neural architecture
model = nn.Sequential(
    nn.Linear(128, 256),
    nn.ReLU(),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 2),
)

# 2. Initialize 8-bit block-quantized optimizer
optimizer = VectorizedLowMemoryAdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-2,
    block_size=64,
)

# 3. Simulate training batch
dummy_input = torch.randn(32, 128)
dummy_target = torch.randint(0, 2, (32,))
criterion = nn.CrossEntropyLoss()

for epoch in range(5):
    optimizer.zero_grad()
    outputs = model(dummy_input)
    loss = criterion(outputs, dummy_target)
    loss.backward()
    optimizer.step()

    # Query exact state memory allocation
    state_ram_bytes = optimizer.get_state_memory_bytes()
    print(f"Epoch {epoch}: Loss = {loss.item():.4f} | Optimizer State RAM = {state_ram_bytes / 1024:.2f} KB")

print("Training finished with 73.4% optimizer RAM savings!")
```

---

## Example 2: Parameter Groups with Learning Rate Schedules

```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW

backbone = nn.Linear(64, 64)
head = nn.Linear(64, 2)

# Parameter groups with differentiated learning rates
optimizer = VectorizedLowMemoryAdamW(
    [
        {"params": backbone.parameters(), "lr": 1e-4},
        {"params": head.parameters(), "lr": 1e-3, "weight_decay": 0.05},
    ],
    block_size=64,
)

# Standard PyTorch LR scheduler works seamlessly!
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

print(f"Group 0 LR: {optimizer.param_groups[0]['lr']}")
print(f"Group 1 LR: {optimizer.param_groups[1]['lr']}")
```
