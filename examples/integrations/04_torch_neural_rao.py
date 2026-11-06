"""
Example 04: PyTorch Neural Network Training with RAO Optimization.

Demonstrates training a PyTorch neural network with ROBUST-ADAPT's 8-bit
block-quantized LowMemoryAdamW and TorchTrainingBudgetHook for memory and latency management.
"""

from __future__ import annotations

import time
import torch
import torch.nn as nn

from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw
from robust_adapt.integrations.torch_callback import TorchTrainingBudgetHook
from robust_adapt.rao.budget import DynamicResourceBudgetManager


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 04: PyTorch Neural RAO Optimization")
    print("=====================================================================")

    torch.manual_seed(42)

    n_features = 24
    n_hidden = 64
    n_classes = 4
    n_steps = 150
    initial_batch_size = 64

    # 1. Define neural architecture
    model = nn.Sequential(
        nn.Linear(n_features, n_hidden),
        nn.ReLU(),
        nn.Linear(n_hidden, n_hidden),
        nn.ReLU(),
        nn.Linear(n_hidden, n_classes),
    )

    criterion = nn.CrossEntropyLoss()

    # 2. Instantiate 8-bit quantized LowMemoryAdamW
    print("Initializing 8-bit Block-Quantized LowMemoryAdamW optimizer...")
    optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, weight_decay=1e-4)

    # 3. Instantiate Dynamic Budget Manager & PyTorch Hook
    budget_mgr = DynamicResourceBudgetManager(
        max_step_time_ms=50.0,
        max_memory_mb=4096.0,
        min_batch_size=16,
        max_batch_size=128,
    )
    budget_hook = TorchTrainingBudgetHook(budget_mgr)

    print("Beginning training loop with runtime budget monitoring...")
    total_loss = 0.0

    for step in range(1, n_steps + 1):
        curr_batch_size = budget_hook.recommended_batch_size

        # Synthetic micro-batch
        x_batch = torch.randn(curr_batch_size, n_features)
        y_batch = torch.randint(0, n_classes, (curr_batch_size,), dtype=torch.long)

        budget_hook.on_step_begin()

        optimizer.zero_grad()
        logits = model(x_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()

        state = budget_hook.on_step_end()
        total_loss += loss.item()

        if step % 30 == 0:
            avg_loss = total_loss / 30.0
            total_loss = 0.0
            avg_latency = sum(budget_hook.step_latencies[-30:]) / 30.0
            print(f"Step {step:03d}/{n_steps} | Loss: {avg_loss:.4f} | Latency: {avg_latency:.2f} ms | Budget: {state.value} | Batch Size: {curr_batch_size}")

    print("\nTraining Completed Successfully:")
    print(f"  Total Steps: {len(budget_hook.step_latencies)}")
    print(f"  Overall Median Step Latency: {sorted(budget_hook.step_latencies)[len(budget_hook.step_latencies)//2]:.2f} ms")
    print(f"  Final Recommended Batch Size: {budget_hook.recommended_batch_size}")


if __name__ == "__main__":
    main()
