"""
Stage 10 — Latency Distribution and Performance Engineering Benchmark.

Profiles operation latencies (Mean, Median, P50, P90, P95, P99) and throughput
across core streaming operations:
1. AdaptiveClassifier single-sample & batch inference (B=1, 16, 64, 256)
2. AdaptiveClassifier streaming training (partial_fit)
3. ReliabilityWeightedADWIN streaming drift updates
4. MultiSignalReliabilityEngine spatial discordance & reliability scoring
5. TorchSymmetricCrossEntropyLoss forward & backward passes
6. LowMemoryAdamW parameter update steps
7. Checkpoint state serialization & deserialization with SHA-256 verification
8. Full ULC-v4.1 integrated four-pillar step arbitration
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

# AdaptiveML imports
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from adaptive_ml.integrations import TorchSymmetricCrossEntropyLoss, create_torch_low_memory_adamw
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.state.serializer import save_state, load_state


def compute_distribution(latencies_sec: list[float]) -> dict[str, float]:
    arr_us = np.array(latencies_sec) * 1e6  # convert to microseconds
    return {
        "mean_us": float(np.mean(arr_us)),
        "std_us": float(np.std(arr_us)),
        "median_us": float(np.median(arr_us)),
        "p50_us": float(np.percentile(arr_us, 50)),
        "p90_us": float(np.percentile(arr_us, 90)),
        "p95_us": float(np.percentile(arr_us, 95)),
        "p99_us": float(np.percentile(arr_us, 99)),
        "min_us": float(np.min(arr_us)),
        "max_us": float(np.max(arr_us)),
        "throughput_ops_per_sec": float(len(arr_us) / np.sum(latencies_sec)) if np.sum(latencies_sec) > 0 else 0.0,
    }


def benchmark_inference():
    print("Benchmarking AdaptiveClassifier inference...")
    clf = AdaptiveClassifier(n_features=8, n_classes=2, grace_period=20)
    # Train warm-up
    X_warm = np.random.randn(200, 8)
    y_warm = (X_warm[:, 0] + X_warm[:, 1] > 0).astype(int)
    clf.partial_fit(X_warm, y_warm)

    results = {}
    for batch_size in [1, 16, 64, 256]:
        latencies = []
        n_iters = 1000 if batch_size <= 64 else 500
        for _ in range(n_iters):
            X = np.random.randn(batch_size, 8)
            t0 = time.perf_counter()
            _ = clf.predict_proba(X)
            t1 = time.perf_counter()
            latencies.append(t1 - t0)
        dist = compute_distribution(latencies)
        dist["samples_per_sec"] = dist["throughput_ops_per_sec"] * batch_size
        results[f"inference_batch_{batch_size}"] = dist
        print(f"  Batch {batch_size:3d}: P50 = {dist['p50_us']:8.2f} us | P99 = {dist['p99_us']:8.2f} us | {dist['samples_per_sec']:,.0f} samples/sec")

    return results


def benchmark_tree_training():
    print("Benchmarking AdaptiveClassifier partial_fit training...")
    clf = AdaptiveClassifier(n_features=8, n_classes=2, grace_period=20)
    results = {}
    for batch_size in [1, 16, 64]:
        latencies = []
        n_iters = 1000 if batch_size <= 16 else 500
        for _ in range(n_iters):
            X = np.random.randn(batch_size, 8)
            y = (X[:, 0] + X[:, 1] > 0).astype(int)
            t0 = time.perf_counter()
            clf.partial_fit(X, y)
            t1 = time.perf_counter()
            latencies.append(t1 - t0)
        dist = compute_distribution(latencies)
        dist["samples_per_sec"] = dist["throughput_ops_per_sec"] * batch_size
        results[f"train_batch_{batch_size}"] = dist
        print(f"  Batch {batch_size:3d}: P50 = {dist['p50_us']:8.2f} us | P99 = {dist['p99_us']:8.2f} us | {dist['samples_per_sec']:,.0f} samples/sec")

    return results


def benchmark_adwin():
    print("Benchmarking ReliabilityWeightedADWIN updates...")
    adwin = ReliabilityWeightedADWIN(delta=0.002)
    latencies = []
    n_iters = 5000
    for i in range(n_iters):
        val = 1.0 if (i % 20 == 0) else 0.0
        rel = 0.95 if val == 0.0 else 0.40
        t0 = time.perf_counter()
        adwin.update(val, reliability=rel)
        t1 = time.perf_counter()
        latencies.append(t1 - t0)
    dist = compute_distribution(latencies)
    print(f"  ADWIN update: P50 = {dist['p50_us']:8.2f} us | P99 = {dist['p99_us']:8.2f} us | {dist['throughput_ops_per_sec']:,.0f} ops/sec")
    return {"adwin_update": dist}


def benchmark_reliability_engine():
    print("Benchmarking MultiSignalReliabilityEngine (k=5 spatial discordance)...")
    engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=5, buffer_size=300)
    # Warm up buffer
    X_warm = np.random.randn(300, 8)
    y_warm = (X_warm[:, 0] > 0).astype(int)
    p_warm = np.column_stack([1 - (X_warm[:, 0] > 0).astype(float), (X_warm[:, 0] > 0).astype(float)])
    engine.compute_reliability(X_warm, y_warm, p_warm)

    results = {}
    for batch_size in [1, 16, 64]:
        latencies = []
        n_iters = 1000 if batch_size <= 16 else 500
        for _ in range(n_iters):
            X = np.random.randn(batch_size, 8)
            y = (X[:, 0] > 0).astype(int)
            p = np.full((batch_size, 2), 0.5)
            t0 = time.perf_counter()
            _ = engine.compute_reliability(X, y, p)
            t1 = time.perf_counter()
            latencies.append(t1 - t0)
        dist = compute_distribution(latencies)
        results[f"reliability_batch_{batch_size}"] = dist
        print(f"  Batch {batch_size:3d}: P50 = {dist['p50_us']:8.2f} us | P99 = {dist['p99_us']:8.2f} us | {dist['throughput_ops_per_sec']:,.0f} ops/sec")

    return results


def benchmark_torch_loss_and_optimizer():
    print("Benchmarking TorchSymmetricCrossEntropyLoss and LowMemoryAdamW...")
    model = nn.Sequential(
        nn.Linear(8, 32),
        nn.ReLU(),
        nn.Linear(32, 2)
    )
    criterion = TorchSymmetricCrossEntropyLoss(alpha=0.1, beta=1.0)
    optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, weight_decay=1e-4)

    loss_latencies = []
    opt_latencies = []
    n_iters = 1000

    for _ in range(n_iters):
        x = torch.randn(32, 8)
        y = torch.randint(0, 2, (32,))
        out = model(x)

        # Measure loss forward + backward
        t0 = time.perf_counter()
        loss = criterion(out, y)
        loss.backward()
        t1 = time.perf_counter()
        loss_latencies.append(t1 - t0)

        # Measure optimizer step
        t2 = time.perf_counter()
        optimizer.step()
        optimizer.zero_grad()
        t3 = time.perf_counter()
        opt_latencies.append(t3 - t2)

    loss_dist = compute_distribution(loss_latencies)
    opt_dist = compute_distribution(opt_latencies)
    print(f"  Loss (B=32 Fwd+Bwd): P50 = {loss_dist['p50_us']:8.2f} us | P99 = {loss_dist['p99_us']:8.2f} us | {loss_dist['throughput_ops_per_sec']:,.0f} ops/sec")
    print(f"  LowMemoryAdamW step: P50 = {opt_dist['p50_us']:8.2f} us | P99 = {opt_dist['p99_us']:8.2f} us | {opt_dist['throughput_ops_per_sec']:,.0f} ops/sec")

    return {
        "torch_symmetric_ce_loss_b32": loss_dist,
        "torch_low_memory_adamw_step": opt_dist,
    }


def benchmark_checkpoint_io():
    print("Benchmarking SafeTensors Checkpoint save and load with SHA-256 verification...")
    # Prepare realistic state dict
    state_dict = {
        f"layer_{i}_weights": np.random.randn(128, 128).astype(np.float32)
        for i in range(10)
    }
    state_dict["bias_vector"] = np.random.randn(128).astype(np.float32)

    save_latencies = []
    load_latencies = []
    n_iters = 100

    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx in range(n_iters):
            ckpt_path = Path(tmp_dir) / f"model_ckpt_{idx}.safetensors"

            # Measure save with SHA-256 hashing
            t0 = time.perf_counter()
            save_state(ckpt_path, state_dict, metadata={"epoch": idx, "step": idx * 100})
            t1 = time.perf_counter()
            save_latencies.append(t1 - t0)

            # Measure load with SHA-256 integrity verification
            t2 = time.perf_counter()
            loaded, meta = load_state(ckpt_path)
            t3 = time.perf_counter()
            load_latencies.append(t3 - t2)

    save_dist = compute_distribution(save_latencies)
    load_dist = compute_distribution(load_latencies)
    print(f"  Save (10 layers + SHA256): P50 = {save_dist['p50_us']:8.2f} us | P99 = {save_dist['p99_us']:8.2f} us | {save_dist['throughput_ops_per_sec']:,.1f} saves/sec")
    print(f"  Load (10 layers + SHA256): P50 = {load_dist['p50_us']:8.2f} us | P99 = {load_dist['p99_us']:8.2f} us | {load_dist['throughput_ops_per_sec']:,.1f} loads/sec")

    return {
        "checkpoint_save_sha256": save_dist,
        "checkpoint_load_sha256": load_dist,
    }


def benchmark_ulc_controller_step():
    print("Benchmarking ULC-v4.1 integrated four-pillar step arbitration...")
    classifier = AdaptiveClassifier(n_features=8, n_classes=2, grace_period=20)
    adwin = ReliabilityWeightedADWIN(delta=0.002)
    pipeline = MultiSignalReliabilityEngine(n_classes=2, buffer_size=300)
    budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=2048.0)
    ctrl = UnifiedLearningControllerV4_1(
        config=ULCv41Config(max_history_len=500),
        classifier=classifier,
        adwin=adwin,
        pipeline=pipeline,
        budget_manager=budget,
    )

    results = {}
    for batch_size in [1, 16, 64]:
        latencies = []
        n_iters = 1000 if batch_size <= 16 else 500
        for _ in range(n_iters):
            X = np.random.randn(batch_size, 8)
            y = (X[:, 0] + X[:, 1] > 0).astype(int)
            t0 = time.perf_counter()
            _, _ = ctrl.step(X, y)
            t1 = time.perf_counter()
            latencies.append(t1 - t0)
        dist = compute_distribution(latencies)
        dist["samples_per_sec"] = dist["throughput_ops_per_sec"] * batch_size
        results[f"ulc_step_batch_{batch_size}"] = dist
        print(f"  Batch {batch_size:3d}: P50 = {dist['p50_us']:8.2f} us | P99 = {dist['p99_us']:8.2f} us | {dist['samples_per_sec']:,.0f} samples/sec")

    return results


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 10: Performance & Latency Distribution Benchmark")
    print(f"Python: {sys.version.split()[0]} on {sys.platform}")
    print("=====================================================================")

    all_results = {}
    all_results.update(benchmark_inference())
    all_results.update(benchmark_tree_training())
    all_results.update(benchmark_adwin())
    all_results.update(benchmark_reliability_engine())
    all_results.update(benchmark_torch_loss_and_optimizer())
    all_results.update(benchmark_checkpoint_io())
    all_results.update(benchmark_ulc_controller_step())

    out_dir = Path("experiments/stage_10_production_reliability")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "performance_distribution_results.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nAll benchmark results successfully written to: {out_file}")


if __name__ == "__main__":
    main()
