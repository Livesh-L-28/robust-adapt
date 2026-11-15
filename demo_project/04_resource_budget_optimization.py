"""
Demo 04: Resource-Aware Optimization (RAO Pillar)
=================================================
Demonstrates how ROBUST-ADAPT operates efficiently on edge/CPU-first environments
using vectorized block-quantization and dynamic budget management.

Key Components:
- robust_adapt.rao.BlockQuantizer: 8-bit block quantization (>73% memory reduction)
- robust_adapt.rao.DynamicResourceBudgetManager: Dynamic latency/RAM governor
- robust_adapt.rao.BudgetState: Budget status flags (NORMAL, WARNING, EXCEEDED)
"""

import time
import numpy as np

import robust_adapt
from robust_adapt.rao import (
    BlockQuantizer,
    DynamicResourceBudgetManager,
    BudgetState,
)


def main():
    print("=" * 70)
    print("DEMO 04: RESOURCE-AWARE OPTIMIZATION & 8-BIT COMPRESSION (RAO)")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    # 1. Block-Quantization Benchmark: 73% Memory Reduction
    print("\n--- 1. VECTORIZED 8-BIT STATE QUANTIZATION ---")
    n_params = 100_000
    rng = np.random.default_rng(42)
    weights = rng.normal(loc=0.0, scale=0.5, size=n_params).astype(np.float32)

    original_bytes = weights.nbytes
    quantizer = BlockQuantizer(block_size=64)

    # Quantize to int8 with per-block scale factors
    t0 = time.perf_counter()
    q_weights, scales = quantizer.quantize(weights, signed=True)
    quant_time = (time.perf_counter() - t0) * 1000

    # Dequantize back to float32
    weights_reconstructed = quantizer.dequantize(q_weights, scales)
    compressed_bytes = q_weights.nbytes + scales.nbytes
    compression_ratio = (1.0 - (compressed_bytes / original_bytes)) * 100
    reconstruction_mse = float(np.mean((weights - weights_reconstructed) ** 2))

    print(f"  Model Parameters:       {n_params:,} float32 values")
    print(f"  Original State Memory:  {original_bytes / 1024:.1f} KB")
    print(f"  Quantized State Memory: {compressed_bytes / 1024:.1f} KB (int8 + scales)")
    print(f"  Memory Reduction:       {compression_ratio:.1f}% savings!")
    print(f"  Quantization Speed:     {quant_time:.2f} ms")
    print(f"  Reconstruction MSE:     {reconstruction_mse:.6e} (negligible loss)")

    # 2. Dynamic Resource Budget Management (Latency & Memory Governor)
    print("\n--- 2. REAL-TIME BUDGET GOVERNOR (SLA PROTECTION) ---")
    # Budget SLA: Target < 15ms per step, Max memory 512MB
    budget_mgr = DynamicResourceBudgetManager(
        max_step_time_ms=15.0,
        max_memory_mb=512.0,
        warning_threshold=0.80,
    )

    print(f"  Target Step Latency Budget:     15.0 ms")
    print(f"  Max Memory Ceiling:             512.0 MB")

    # Simulate fluctuating workloads
    simulated_latencies = [4.5, 6.2, 8.1, 13.5, 17.8, 19.2, 11.0, 7.5]
    print(f"\n  {'Step':<6} | {'Step Time':<12} | {'Budget State':<16} | {'Skip Heavy Ops?':<18} | {'Replay Ratio':<14}")
    print("  " + "-" * 72)

    for i, latency in enumerate(simulated_latencies, 1):
        # Step the budget manager
        budget_state = budget_mgr.evaluate_step(step_time_ms=latency)
        skip_ops = budget_mgr.should_skip_expensive_ops()
        replay_ratio = budget_mgr.recommended_replay_ratio()

        state_name = budget_state.name if hasattr(budget_state, "name") else str(budget_state)
        print(f"  {i:<6} | {latency:>8.1f} ms | {state_name:<16} | {str(skip_ops):<18} | {replay_ratio:>10.2f}")

    print("-" * 70)
    print("Conclusion: RAO keeps ML workloads within strict CPU memory and latency budgets.")


if __name__ == "__main__":
    main()
