"""Example 18: RAO 2.0 Vectorized Block-Quantized AdamW Optimization.

Demonstrates:
- VectorizedLowMemoryAdamW accelerating 8-bit quantized CPU parameter updates
- Selective preservation of float32 precision for 1D vectors
- Clamped denominator numerical stability under PyTorch
"""

import time
import torch
from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW


def main() -> None:
    print("=== Example 18: RAO 2.0 Vectorized Low-Memory AdamW ===")

    # Define synthetic linear model with 2D weight matrix and 1D bias vector
    torch.manual_seed(42)
    weight = torch.nn.Parameter(torch.randn(100, 200, requires_grad=True))
    bias = torch.nn.Parameter(torch.zeros(100, requires_grad=True))

    optimizer = VectorizedLowMemoryAdamW(
        [weight, bias],
        lr=1e-3,
        weight_decay=1e-2,
        block_size=256,
    )

    print("\n--- Running 20 Vectorized Optimization Steps ---")
    t0 = time.perf_counter()
    for step in range(20):
        # Forward & simulated loss gradient
        weight.grad = torch.randn_like(weight)
        bias.grad = torch.randn_like(bias)

        optimizer.step()
        optimizer.zero_grad()

        if step % 5 == 0:
            print(f"Step {step:2d} | Weight norm: {weight.norm().item():.3f} | Bias norm: {bias.norm().item():.3f}")

    elapsed = time.perf_counter() - t0
    print(f"\nCompleted 20 steps in {elapsed*1000.0:.2f} ms")
    print("RAO 2.0 execution completed successfully.")


if __name__ == "__main__":
    main()
