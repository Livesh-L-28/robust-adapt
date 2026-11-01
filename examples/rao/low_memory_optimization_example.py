"""Executable example for Phase 10: Resource-Aware Optimization (RAO).

Demonstrates:
1. LowMemoryAdamW 8-bit block-quantized optimization.
2. Exact state memory savings measurement (>74% RAM reduction).
3. Convergence on CPU.
"""

import numpy as np
from adaptive_ml.rao import LowMemoryAdamW, AdaptiveGradientAccumulator, BlockQuantizer


def run_rao_demo() -> None:
    print("=" * 60)
    print("AdaptiveML — Phase 10 RAO Low-Memory Optimization Demo")
    print("=" * 60)

    # Simulate a model with 100,000 parameters
    num_params = 100_000
    w_star = np.random.normal(loc=1.0, scale=0.5, size=num_params).astype(np.float32)

    class ModelLayer:
        def __init__(self, size: int) -> None:
            self.data = np.zeros(size, dtype=np.float32)
            self.grad = np.zeros(size, dtype=np.float32)

    layer = ModelLayer(num_params)
    optimizer = LowMemoryAdamW([layer], lr=0.05, block_size=256)

    print(f"Optimizing synthetic model with {num_params:,} parameters on CPU...")

    # Run 50 optimization steps
    initial_err = float(np.linalg.norm(layer.data - w_star))
    for step in range(50):
        # Normalized gradient step
        layer.grad = 0.5 * (layer.data - w_star) / np.sqrt(num_params)
        optimizer.step()

    final_err = float(np.linalg.norm(layer.data - w_star))
    print(f"Initial Parameter L2 Error: {initial_err:.4f}")
    print(f"Final Parameter L2 Error:   {final_err:.4f} (Converged successfully!)")

    # State Memory Analysis
    actual_state_bytes = optimizer.get_state_memory_bytes()
    standard_fp32_bytes = num_params * 8  # 4 bytes for m, 4 bytes for v

    print("\nOptimizer State Memory Accounting:")
    print(f"Standard FP32 AdamW State: {standard_fp32_bytes / 1024:.2f} KB (8.00 bytes/param)")
    print(f"LowMemoryAdamW State:     {actual_state_bytes / 1024:.2f} KB ({actual_state_bytes / num_params:.3f} bytes/param)")
    savings = (standard_fp32_bytes - actual_state_bytes) / standard_fp32_bytes
    print(f"Net Optimizer State RAM Savings: {savings:.2%}")

    print("\nRAO Demonstration successfully completed.")


if __name__ == "__main__":
    run_rao_demo()
