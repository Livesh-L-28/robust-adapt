"""
Example 05: PyTorch Robust Neural Training under Label Noise.

Demonstrates training neural networks with corrupted training labels using
TorchSymmetricCrossEntropyLoss and TorchGeneralizedCrossEntropyLoss from ROBUST-ADAPT RLA.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import numpy as np

from robust_adapt.integrations.torch_module import (
    TorchGeneralizedCrossEntropyLoss,
    TorchSymmetricCrossEntropyLoss,
)


def create_mlp(in_features: int, hidden: int, num_classes: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(in_features, hidden),
        nn.ReLU(),
        nn.Linear(hidden, hidden),
        nn.ReLU(),
        nn.Linear(hidden, num_classes),
    )


def train_model(model: nn.Module, criterion: nn.Module, x_train: torch.Tensor, y_train: torch.Tensor, steps: int = 100) -> float:
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    model.train()
    for _ in range(steps):
        optimizer.zero_grad()
        out = model(x_train)
        loss = criterion(out, y_train)
        loss.backward()
        optimizer.step()
    return loss.item()


def evaluate(model: nn.Module, x_test: torch.Tensor, y_test: torch.Tensor) -> float:
    model.eval()
    with torch.no_grad():
        preds = model(x_test).argmax(dim=-1)
        acc = (preds == y_test).float().mean().item()
    return acc


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 05: PyTorch Robust Learning (RLA) under Noise")
    print("=====================================================================")

    torch.manual_seed(42)
    rng = np.random.default_rng(42)

    n_samples = 1500
    n_features = 12
    n_classes = 3

    # Generate synthetic clustering dataset
    X_raw = rng.standard_normal((n_samples, n_features)).astype(np.float32)
    # True latent labels based on feature clusters
    true_labels = np.argmax(X_raw[:, :3], axis=1).astype(np.int64)

    # Inject 30% symmetric label noise into training labels
    corrupted_labels = true_labels.copy()
    noise_mask = rng.random(n_samples) < 0.30
    corrupted_labels[noise_mask] = rng.integers(0, n_classes, size=np.sum(noise_mask))

    split = 1000
    X_train_t = torch.from_numpy(X_raw[:split])
    y_train_clean = torch.from_numpy(true_labels[:split])
    y_train_noisy = torch.from_numpy(corrupted_labels[:split])

    X_test_t = torch.from_numpy(X_raw[split:])
    y_test_t = torch.from_numpy(true_labels[split:])

    print(f"Dataset: {n_samples} samples, {n_features} features, {n_classes} classes.")
    print(f"Training split: {split} samples with {np.mean(noise_mask[:split])*100:.1f}% corrupted labels.")
    print(f"Clean test split: {n_samples - split} samples.\n")

    # 1. Baseline: Standard Cross-Entropy Loss
    model_baseline = create_mlp(n_features, 48, n_classes)
    loss_base = train_model(model_baseline, nn.CrossEntropyLoss(), X_train_t, y_train_noisy)
    acc_base = evaluate(model_baseline, X_test_t, y_test_t)
    print(f"Standard nn.CrossEntropyLoss:           Test Accuracy = {acc_base * 100:.2f}% (Final Loss: {loss_base:.4f})")

    # 2. ROBUST-ADAPT: TorchGeneralizedCrossEntropyLoss (q=0.7)
    model_gce = create_mlp(n_features, 48, n_classes)
    loss_gce = train_model(model_gce, TorchGeneralizedCrossEntropyLoss(q=0.7), X_train_t, y_train_noisy)
    acc_gce = evaluate(model_gce, X_test_t, y_test_t)
    print(f"TorchGeneralizedCrossEntropyLoss (q=0.7): Test Accuracy = {acc_gce * 100:.2f}% (Final Loss: {loss_gce:.4f})")

    # 3. ROBUST-ADAPT: TorchSymmetricCrossEntropyLoss (alpha=1.0, beta=1.0)
    model_sce = create_mlp(n_features, 48, n_classes)
    loss_sce = train_model(model_sce, TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=1.0), X_train_t, y_train_noisy)
    acc_sce = evaluate(model_sce, X_test_t, y_test_t)
    print(f"TorchSymmetricCrossEntropyLoss (a=1,b=1): Test Accuracy = {acc_sce * 100:.2f}% (Final Loss: {loss_sce:.4f})")

    print("\nConclusion: Robust losses prevent the neural network from memorizing noisy labels.")


if __name__ == "__main__":
    main()
