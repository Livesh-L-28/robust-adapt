"""
AdaptiveML Example: PyTorch Deep Learning Integration.

Demonstrates training a PyTorch neural network using LowMemoryAdamW
and TorchSymmetricCrossEntropyLoss under synthetic label noise.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from adaptive_ml.integrations.torch_module import TorchSymmetricCrossEntropyLoss
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw


def main() -> None:
    print("=" * 80)
    print("AdaptiveML: PyTorch Neural Network Integration Example")
    print("LowMemoryAdamW + TorchSymmetricCrossEntropyLoss")
    print("=" * 80)

    torch.manual_seed(42)

    # 1. Model Architecture
    model = nn.Sequential(
        nn.Linear(8, 32),
        nn.ReLU(),
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 2),
    )

    # 2. AdaptiveML Quantized Optimizer & Robust Loss
    optimizer = create_torch_low_memory_adamw(model.parameters(), lr=0.001, block_size=64)
    loss_fn = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)

    # 3. Synthetic Batch with Injected Label Noise
    X = torch.randn(128, 8)
    y_true = (X[:, 0] + X[:, 1] > 0.0).long()
    # Flip 20% of labels to simulate noise
    noise_mask = torch.rand(128) < 0.2
    y_noisy = y_true.clone()
    y_noisy[noise_mask] = 1 - y_noisy[noise_mask]

    print(f"Training MLP with {sum(p.numel() for p in model.parameters())} parameters...")
    print(f"Initial State RAM: {optimizer.get_state_memory_bytes()} bytes")

    # 4. Training Loop
    for epoch in range(1, 21):
        optimizer.zero_grad()
        logits = model(X)
        loss = loss_fn(logits, y_noisy)
        loss.backward()
        optimizer.step()

        if epoch % 5 == 0 or epoch == 1:
            preds = torch.argmax(logits, dim=-1)
            clean_acc = (preds == y_true).float().mean().item()
            print(f"Epoch {epoch:02d} | Loss: {loss.item():.4f} | Clean Accuracy: {clean_acc * 100:.2f}%")

    print("-" * 80)
    print(f"Final Optimizer State RAM: {optimizer.get_state_memory_bytes()} bytes (~2.12 bytes/param)")
    print("=" * 80)
    print("PyTorch Integration Example Completed Successfully!")


if __name__ == "__main__":
    main()
