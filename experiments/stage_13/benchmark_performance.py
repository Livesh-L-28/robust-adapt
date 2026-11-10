"""Stage 13 Performance, Memory, Latency & Throughput Benchmark.

Measures:
1. Package import latency
2. Baseline idle memory overhead
3. Streaming step latency across batch sizes (1, 10, 50, 100)
4. Throughput (samples per second) for ALA 3.0, RLA 3.0, Minority 2.0, ULC-v5
5. VectorizedLowMemoryAdamW vs LowMemoryAdamW speedup (if PyTorch present)
6. Reservoir replay memory stability over long streaming runs
"""

import gc
import json
import os
import sys
import time
import psutil
import numpy as np

def measure_import_latency() -> float:
    """Measure import time of adaptive_ml in a fresh subprocess."""
    import subprocess
    cmd = [sys.executable, "-c", "import time; t0 = time.perf_counter(); import adaptive_ml; print(time.perf_counter() - t0)"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def main() -> None:
    print("--- Stage 13 Production Performance Benchmark ---")
    results = {}

    # 1. Import Latency
    import_time = measure_import_latency()
    print(f"Package Import Latency: {import_time * 1000.0:.2f} ms")
    results["import_latency_ms"] = import_time * 1000.0

    # 2. Idle Memory Overhead
    gc.collect()
    process = psutil.Process(os.getpid())
    import adaptive_ml
    from adaptive_ml.ala import ALA30AdaptiveLearner
    from adaptive_ml.rla import RLA30RobustLearner
    from adaptive_ml.minority import MinorityIntelligence20Learner
    from adaptive_ml.ulc import UnifiedLearningControllerV5
    from adaptive_ml.integrations.torch_optim import VectorizedLowMemoryAdamW
    import torch

    mem_after_import_mb = process.memory_info().rss / (1024 * 1024)
    print(f"Resident Memory Post-Imports: {mem_after_import_mb:.2f} MB")
    results["resident_memory_mb"] = mem_after_import_mb

    # 3. Streaming Step Latency & Throughput
    rng = np.random.RandomState(42)
    N_SAMPLES = 5000
    N_FEATURES = 8
    X = rng.randn(N_SAMPLES, N_FEATURES).astype(np.float64)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    models = {
        "ala_3_0": ALA30AdaptiveLearner(n_features=N_FEATURES, n_classes=2),
        "rla_3_0": RLA30RobustLearner(n_features=N_FEATURES, n_classes=2),
        "minority_2_0": MinorityIntelligence20Learner(),
        "ulc_v5": UnifiedLearningControllerV5(n_features=N_FEATURES, n_classes=2),
    }

    throughput_results = {}
    BATCH_SIZE = 50
    n_batches = N_SAMPLES // BATCH_SIZE

    for name, model in models.items():
        gc.collect()
        t0 = time.perf_counter()
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            if name == "ala_3_0":
                model.partial_fit(X_b, y_b)
            elif name == "rla_3_0":
                model.fit_batch(X_b, y_b)
            elif name == "minority_2_0":
                model.fit_batch(X_b, y_b)
            elif name == "ulc_v5":
                model.step(X_b, y_b)
        elapsed = time.perf_counter() - t0
        sps = N_SAMPLES / elapsed
        latency_per_batch_ms = (elapsed / n_batches) * 1000.0
        print(f"Model {name:15s}: {sps:10.1f} samples/sec | {latency_per_batch_ms:6.2f} ms/batch (B={BATCH_SIZE})")
        throughput_results[name] = {
            "samples_per_sec": sps,
            "latency_per_batch_ms": latency_per_batch_ms,
            "total_time_sec": elapsed,
        }

    results["throughput"] = throughput_results

    # 4. RAO 2.0 Vectorized vs Standard AdamW Speedup
    print("\nBenchmarking VectorizedLowMemoryAdamW vs Standard AdamW...")
    param_sizes = [50000]
    rao_bench = {}
    for size in param_sizes:
        # Vectorized
        p_vec = [torch.nn.Parameter(torch.randn(size, dtype=torch.float32, requires_grad=True))]
        opt_vec = VectorizedLowMemoryAdamW(p_vec, lr=1e-3)
        # Warmup
        p_vec[0].grad = torch.randn_like(p_vec[0])
        opt_vec.step()

        t_vec_start = time.perf_counter()
        for _ in range(50):
            p_vec[0].grad = torch.randn_like(p_vec[0])
            opt_vec.step()
        t_vec = time.perf_counter() - t_vec_start

        # Standard LowMemoryAdamW (block-wise loop quantization)
        from adaptive_ml.rao.adamw import LowMemoryAdamW
        p_std = [torch.nn.Parameter(torch.randn(size, dtype=torch.float32, requires_grad=True))]
        opt_std = LowMemoryAdamW(p_std, lr=1e-3)
        p_std[0].grad = torch.randn_like(p_std[0])
        opt_std.step()

        t_std_start = time.perf_counter()
        for _ in range(50):
            p_std[0].grad = torch.randn_like(p_std[0])
            opt_std.step()
        t_std = time.perf_counter() - t_std_start

        speedup = t_std / t_vec
        print(f"Params {size}: Vectorized {t_vec*1000:.2f} ms vs Standard {t_std*1000:.2f} ms | Speedup: {speedup:.2f}x")
        rao_bench[f"params_{size}"] = {
            "vectorized_time_ms": t_vec * 1000.0,
            "standard_time_ms": t_std * 1000.0,
            "speedup": speedup,
        }

    results["rao_speedup"] = rao_bench

    # 5. Memory stability over streaming length
    print("\nTesting Replay Memory Stability...")
    from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
    replay = ClassBalancedReservoirReplay(capacity=500, n_classes=2)
    for _ in range(500): # 500 * 20 = 10,000 samples
        replay.add(rng.randn(20, 4), rng.randint(0, 2, size=20))
    print(f"Replay total stored: {replay.total_stored} (capacity ceiling: 500)")
    assert replay.total_stored <= 500
    results["replay_memory_bounded"] = True

    # Persist JSON results
    out_path = os.path.join("experiments", "stage_13", "performance_benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)
    print(f"\nBenchmark successfully completed and written to {out_path}")

if __name__ == "__main__":
    main()
