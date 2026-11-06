# Tutorial 5: Memory-Efficient PyTorch Training with 8-Bit Dynamic Block Quantization

**Domain:** Edge AI, CPU Neural Model Fine-Tuning & Memory-Constrained Devices<br>
**Algorithms:** `VectorizedLowMemoryAdamW`, `TorchTrainingBudgetHook`<br>
**Framework:** PyTorch 2.x<br>

---

## 1. Problem Scenario

When training or fine-tuning neural networks on edge compute instances or CPU workers, the optimizer memory footprint often exceeds the size of the model itself:
- Standard `torch.optim.AdamW` stores two 32-bit floating-point moment tensors ($m_t$ and $v_t$) per parameter.
- This requires $8\text{ bytes}$ of optimizer state per parameter (e.g. 800 MB for a 100M-parameter model).
- On embedded nodes, micro-instances, or containers, this memory expansion triggers immediate Out-Of-Memory (OOM) crashes.

In this tutorial, you will use **AdaptiveML's `VectorizedLowMemoryAdamW`** to:
1. Train a PyTorch neural network with 8-bit dynamic block quantization.
2. Measure exact optimizer state RAM reduction ($> 73\%$).
3. Integrate learning rate scheduling and gradient clipping seamlessly.

---

## 2. Complete Runnable Code

```python
import torch
import torch.nn as nn
from robust_adapt.integrations import VectorizedLowMemoryAdamW

torch.manual_seed(42)

class NeuralClassifier(nn.Module):
    def __init__(self, in_features=128, hidden_dim=256, n_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x):
        return self.net(x)

def main():
    print("--- Starting Low-Memory PyTorch Tutorial ---")

    # 1. Initialize neural architecture
    model = NeuralClassifier(in_features=128, hidden_dim=256, n_classes=10)
    total_params = sum(p.numel() for p in model.parameters())
    standard_adam_bytes = total_params * 8  # 8 bytes per param for fp32 m_t and v_t

    print(f"Model Parameters: {total_params:,}")
    print(f"Standard fp32 AdamW State Footprint: {standard_adam_bytes / 1024:.2f} KB")

    # 2. Initialize 8-Bit Block-Quantized AdamW
    optimizer = VectorizedLowMemoryAdamW(
        model.parameters(),
        lr=1e-3,
        weight_decay=1e-2,
        block_size=64,       # Optimal 64-element block size for CPU L1 cache
        max_grad_norm=1.0,   # Built-in gradient clipping
    )

    criterion = nn.CrossEntropyLoss()

    # 3. Simulate training loop
    for epoch in range(5):
        epoch_loss = 0.0
        for step in range(10):
            # Synthetic batch
            inputs = torch.randn(32, 128)
            targets = torch.randint(0, 10, (32,))

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()

            optimizer.step()
            epoch_loss += loss.item()

        print(f"Epoch {epoch + 1:02d} | Mean Step Loss: {epoch_loss / 10:.4f}")

    # 4. Memory Footprint Verification
    quantized_bytes = optimizer.get_state_memory_bytes()
    compression_ratio = (1.0 - (quantized_bytes / standard_adam_bytes)) * 100

    print("\n--- Memory Verification Audit ---")
    print(f"Standard AdamW State Footprint:  {standard_adam_bytes / 1024:7.2f} KB")
    print(f"Quantized AdamW State Footprint: {quantized_bytes / 1024:7.2f} KB")
    print(f"RAM Reduction:                   {compression_ratio:7.2f}%")
    print("--- Tutorial Completed Successfully ---")

if __name__ == "__main__":
    main()
```

---

## 3. Key Observations

- **73.4%+ RAM Reduction:** Moment states are dynamically quantized into `int8` (momentum) and `uint8` (variance), with per-block float32 scale factors.
- **Drop-In Compatibility:** Functions identically to `torch.optim.Optimizer`, supporting standard loss backwards, `lr_scheduler` hooks, and model checkpoints.
- **Numerical Parity:** Convergence curves track full 32-bit fp32 AdamW within numerical noise tolerance across standard benchmarks.
