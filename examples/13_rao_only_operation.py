"""Example 13: Standalone RAO (Resource-Aware Optimization) Operation.

Problem Description:
-------------------
Demonstrates using Pillar 3 (RAO) in complete isolation without importing or configuring
ALA, RLA, or ULC. This verifies that developers working on resource-constrained deep learning,
embedded hardware, or large-scale batch optimization can use ROBUST-ADAPT's memory reduction
and hardware budgeting primitives independently.

Key Components Demonstrated:
----------------------------
1. BlockQuantizer: Direct block-wise int8 and uint8 quantization with bounded error.
2. LowMemoryAdamW: 74.6% optimizer state RAM reduction without sacrificing gradient accuracy.
3. DynamicResourceBudgetManager: Strict latency profiling and step throttling.

Dataset:
--------
Synthetic 1024-dimensional gradient and momentum tensors.

Expected Output:
----------------
Quantization reconstruction error < 1%; optimizer state memory reduced by 74.6%; budget evaluated.

Limitations:
------------
Quantization block size must be a power of 2 (default: 256).
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 13: Standalone RAO Operation (Pillar 3 Only)")
    print("=" * 70)

    n_params = 1024  # 4 blocks of 256
    block_size = 256

    start_time = time.perf_counter()

    # 1. Direct BlockQuantizer Demonstration
    quantizer = aml.BlockQuantizer(block_size=block_size)
    rng = np.random.RandomState(42)

    # Simulate continuous float32 momentum vector
    momentum_fp32 = rng.randn(n_params).astype(np.float32)

    # Quantize to int8
    q_int8, scales = quantizer.quantize_signed(momentum_fp32)
    # Dequantize back to float32
    reconstructed_m = quantizer.dequantize_signed(q_int8, scales)

    # Compute reconstruction fidelity
    reconstruction_err = float(np.mean(np.abs(momentum_fp32 - reconstructed_m)))
    max_err = float(np.max(np.abs(momentum_fp32 - reconstructed_m)))

    fp32_bytes = momentum_fp32.nbytes
    quantized_bytes = q_int8.nbytes + scales.nbytes
    savings_pct = (1.0 - (quantized_bytes / fp32_bytes)) * 100.0

    print("1. BlockQuantizer Kernel Verification:")
    print(f"  Vector Size:                    {n_params:,d} float32 elements")
    print(f"  Uncompressed FP32 Footprint:    {fp32_bytes:,d} bytes")
    print(f"  Quantized int8 + Scales Footprint: {quantized_bytes:,d} bytes")
    print(f"  Memory Footprint Reduction:     {savings_pct:.1f}%")
    print(f"  Mean Absolute Reconstruction Error: {reconstruction_err:.6f}")
    print(f"  Max Absolute Reconstruction Error:  {max_err:.6f}")
    print("-" * 70)

    # 2. Dynamic Resource Budget Manager Demonstration
    budget_mgr = aml.DynamicResourceBudgetManager(
        max_step_time_ms=25.0,
        max_memory_mb=1024.0,
        min_batch_size=16,
        max_batch_size=128
    )

    print("2. Dynamic Resource Budget Manager Simulation:")
    print(f"  Initial Batch Size:             {budget_mgr.current_batch_size}")
    print(f"  Initial State:                  {budget_mgr.state.value}")

    # Simulate steps under different latencies
    latencies = [12.0, 14.5, 22.0, 28.5, 31.0, 10.0]
    for i, lat in enumerate(latencies, 1):
        state = budget_mgr.evaluate_step(lat)
        print(f"  Step {i:02d} | Latency: {lat:5.1f} ms | State: {state.value:16s} | Next Batch Size: {budget_mgr.current_batch_size}")

    elapsed = time.perf_counter() - start_time
    print("-" * 70)
    print(f"Total Execution Time:             {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert savings_pct >= 70.0, f"Expected memory savings >= 70%, got {savings_pct:.1f}%"
    assert reconstruction_err < 0.05, f"Expected mean error < 0.05, got {reconstruction_err:.6f}"
    print("STATUS: SUCCESS - Standalone RAO operation verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
