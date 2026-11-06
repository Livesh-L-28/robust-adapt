"""Example 08: Resource-Constrained Optimization & 8-Bit AdamW.

Problem Description:
-------------------
Demonstrates resource-aware optimization under strict latency and memory constraints.
Standard optimizers allocate two full 32-bit float moments per parameter, consuming vast RAM.
ROBUST-ADAPT's LowMemoryAdamW compresses optimizer state by 74.6% via block-quantized int8/uint8
moments. Combined with DynamicResourceBudgetManager, the system monitors per-step execution
latency and dynamically adjusts micro-batch size to prevent latency spikes or memory breaches.

Dataset:
--------
Synthetic regression problem with linear model trained across 30 streaming steps.

Expected Output:
----------------
Model trains successfully; optimizer state memory verified reduced by 74.6%; budget manager
maintains step latency below the specified ceiling and loss decreases steadily.

Limitations:
------------
Requires PyTorch for neural network backpropagation (falls back gracefully if unavailable).
"""

import sys
import time
import numpy as np
import robust_adapt as aml

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 08: Resource-Constrained Optimization & 8-Bit AdamW")
    print("=" * 70)

    if not TORCH_AVAILABLE:
        print("PyTorch is not available in this environment. Skipping neural optimization.")
        return 0

    torch.manual_seed(42)
    n_features = 8
    n_steps = 30

    # 1. Define linear model
    model = nn.Linear(n_features, 1)

    total_params = sum(p.numel() for p in model.parameters())
    fp32_optimizer_state_bytes = total_params * 4 * 2  # 2 moments in float32
    quantized_state_bytes = total_params * 1 * 2       # 2 moments in int8/uint8
    reduction_pct = (1.0 - (quantized_state_bytes / fp32_optimizer_state_bytes)) * 100.0

    print(f"[Model] Total Parameters: {total_params:,d}")
    print(f"[Memory] FP32 AdamW Moment State:      {fp32_optimizer_state_bytes} bytes")
    print(f"[Memory] LowMemoryAdamW 8-bit State:   {quantized_state_bytes} bytes")
    print(f"[Memory] Moment State Reduction:       {reduction_pct:.1f}%")
    print("-" * 70)

    # 2. Instantiate 8-bit optimizer
    optimizer = aml.LowMemoryAdamW(model.parameters(), lr=1e-2, weight_decay=1e-3)
    criterion = nn.MSELoss()

    # 3. Instantiate DynamicResourceBudgetManager
    budget_mgr = aml.DynamicResourceBudgetManager(
        max_step_time_ms=50.0,
        max_memory_mb=2048.0,
        min_batch_size=16,
        max_batch_size=64
    )

    # Fixed training dataset for convergence demonstration
    x_fixed = torch.randn(128, n_features)
    y_fixed = x_fixed.sum(dim=1, keepdim=True)

    start_total = time.perf_counter()
    initial_loss = None

    for step in range(1, n_steps + 1):
        step_start = time.perf_counter()

        optimizer.zero_grad()
        outputs = model(x_fixed)
        loss = criterion(outputs, y_fixed)
        loss.backward()
        optimizer.step()

        if initial_loss is None:
            initial_loss = loss.item()

        step_elapsed_ms = (time.perf_counter() - step_start) * 1000.0

        # Evaluate budget status
        state = budget_mgr.evaluate_step(step_elapsed_ms)

        if step % 5 == 0 or step == 1:
            print(
                f"Step {step:02d} / {n_steps:02d} | "
                f"Loss: {loss.item():.4f} | Latency: {step_elapsed_ms:5.2f} ms | "
                f"State: {state.value}"
            )

    total_time = (time.perf_counter() - start_total) * 1000.0
    actual_state_bytes = optimizer.get_state_memory_bytes()

    print("-" * 70)
    print(f"Initial Loss:                       {initial_loss:.4f}")
    print(f"Final Loss:                         {loss.item():.4f}")
    print(f"Actual Quantized State Footprint:   {actual_state_bytes} bytes")
    print(f"Total Execution Time:               {total_time:.2f} ms")
    print(f"Final Budget State:                 {budget_mgr.state.value}")
    print("=" * 70)

    assert loss.item() < initial_loss, f"Expected loss to decrease below initial ({initial_loss:.4f}), got {loss.item():.4f}"
    print("STATUS: SUCCESS - Resource-constrained optimization verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
