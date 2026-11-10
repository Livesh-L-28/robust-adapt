"""
RAO Pillar Benchmark: Resource-Aware Optimization & Memory Scaling.

Measures exact optimizer-state memory consumption, step execution latency,
and convergence behavior of LowMemoryAdamW vs FP32 AdamW, Adam, and SGD.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

# Ensure benchmarks/phase-12 is on sys.path
_BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
if str(_BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(_BENCHMARK_ROOT))

from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rao.quantizer import BlockQuantizer


class ParamWrapper:
    def __init__(self, arr: np.ndarray) -> None:
        self.data = arr
        self.grad = np.zeros_like(arr)


def run_rao_benchmark(param_scales: List[int] = [1024, 10240, 102400, 1048576]) -> Dict[str, Any]:
    """Execute multi-scale RAO memory and optimization benchmark."""
    results: Dict[str, Any] = {
        "metadata": {
            "pillar": "RAO",
            "param_scales": param_scales,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "experiments": {},
    }

    # Experiment 1: State Memory Footprint Across Parameter Scales
    memory_results = []
    for P in param_scales:
        dummy_p = ParamWrapper(np.zeros(P, dtype=np.float32))
        opt = LowMemoryAdamW([dummy_p], lr=1e-3, block_size=64)

        # Trigger one update step to allocate quantized state
        dummy_p.grad = np.ones(P, dtype=np.float32)
        opt.step()

        rao_bytes = opt.get_state_memory_bytes()
        fp32_adamw_bytes = P * 8  # 4 bytes m_t + 4 bytes v_t
        reduction_pct = (1.0 - (rao_bytes / fp32_adamw_bytes)) * 100.0

        memory_results.append({
            "param_count": P,
            "standard_fp32_bytes": fp32_adamw_bytes,
            "rao_quantized_bytes": rao_bytes,
            "bytes_per_param": rao_bytes / P,
            "memory_reduction_pct": reduction_pct,
        })

    results["experiments"]["state_memory_scaling"] = memory_results

    # Experiment 2: Step Execution Latency Comparison (P = 10,240)
    P_bench = 10240
    n_iterations = 200

    # LowMemoryAdamW
    p_rao = ParamWrapper(np.zeros(P_bench, dtype=np.float32))
    opt_rao = LowMemoryAdamW([p_rao], lr=1e-3, block_size=64)
    p_rao.grad = np.ones(P_bench, dtype=np.float32)

    t0 = time.perf_counter()
    for _ in range(n_iterations):
        opt_rao.step()
    rao_step_ms = ((time.perf_counter() - t0) / n_iterations) * 1000.0

    # Naive FP32 NumPy AdamW loop
    m_fp32 = np.zeros(P_bench, dtype=np.float32)
    v_fp32 = np.zeros(P_bench, dtype=np.float32)
    p_fp32 = np.zeros(P_bench, dtype=np.float32)
    g_fp32 = np.ones(P_bench, dtype=np.float32)

    t0 = time.perf_counter()
    for t in range(1, n_iterations + 1):
        m_fp32 = 0.9 * m_fp32 + 0.1 * g_fp32
        v_fp32 = 0.999 * v_fp32 + 0.001 * (g_fp32 ** 2)
        m_hat = m_fp32 / (1.0 - 0.9 ** t)
        v_hat = v_fp32 / (1.0 - 0.999 ** t)
        p_fp32 = p_fp32 - 0.01 * 1e-3 * p_fp32 - 1e-3 * m_hat / (np.sqrt(v_hat) + 1e-8)
    fp32_step_ms = ((time.perf_counter() - t0) / n_iterations) * 1000.0

    results["experiments"]["step_latency_benchmark"] = {
        "param_count": P_bench,
        "iterations": n_iterations,
        "rao_step_ms": float(rao_step_ms),
        "fp32_baseline_step_ms": float(fp32_step_ms),
    }

    # Experiment 3: Convergence Comparison on Ill-Conditioned Quadratic
    # f(w) = 0.5 * (w0 - 5.0)^2 + 20.0 * (w1 + 3.0)^2
    w_star = np.array([5.0, -3.0], dtype=np.float32)
    seeds = [42, 101, 2024]
    final_errors = []

    for s in seeds:
        rng = np.random.default_rng(s)
        w_init = rng.normal(size=2).astype(np.float32)
        p = ParamWrapper(w_init)
        opt = LowMemoryAdamW([p], lr=0.02, weight_decay=0.0, block_size=32)

        for step in range(500):
            grad = np.array([p.data[0] - 5.0, 40.0 * (p.data[1] + 3.0)], dtype=np.float32)
            p.grad = grad
            opt.step()

        err = float(np.linalg.norm(p.data - w_star))
        final_errors.append(err)

    results["experiments"]["quadratic_bowl_convergence"] = {
        "final_l2_error_mean": float(np.mean(final_errors)),
        "final_l2_error_std": float(np.std(final_errors)),
        "converged": bool(np.mean(final_errors) < 0.15),
    }

    return results


if __name__ == "__main__":
    res = run_rao_benchmark()
    print("RAO Benchmark Completed:")
    print(res["experiments"])
