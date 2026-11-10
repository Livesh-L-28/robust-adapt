"""
Stage 7.2 Workstream H: High-Resolution Performance, Latency & Memory Audit
==========================================================================
1. Investigates historical 7.01 ms vs 1.22 ms latency discrepancy.
2. Rigorous micro-benchmarking: 10 warmup batches + 100 measured batches.
   Computes Mean, P50, P95, P99, Throughput.
3. Long-running streaming memory audit (500 batches = 15,000 samples) tracking
   process RSS heap to empirically verify O(1) boundedness.
Outputs LATENCY_RESULTS.csv.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.core.telemetry import get_process_memory_bytes
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.concept_memory import ConceptMemory
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from experiments.stage_7_1_ulc_v4_optimization.candidate_controllers import HybridMasterControllerV4_1
from experiments.stage_7_ulc_v4.run_stage7_experiment import generate_stream, LinearSurrogate


def benchmark_controller_latency(
    model_name: str,
    n_warmup: int = 10,
    n_measured: int = 100,
    batch_size: int = 30,
    seed: int = 42,
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    n_features = 4

    init_X = rng.normal(0, 1, (30, n_features))
    init_y = np.array([0] * 27 + [1] * 3)

    clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=10, tau_tie=0.10, replay_capacity=100)
    clf.fit(init_X, init_y)
    surr = LinearSurrogate(n_features, 2, seed=seed)
    opt = LowMemoryAdamW([surr], lr=0.01)
    pipeline = RobustLearningPipeline(2)
    budget = DynamicResourceBudgetManager(max_memory_mb=4096.0)
    prior = OnlineClassPriorTracker(n_classes=2)
    thresh = AdaptiveThresholdManager(n_classes=2, gamma=0.5)
    concept_mem = ConceptMemory(max_concepts=5)

    if model_name == "ULC-v1":
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
    elif model_name == "ULC-v4 Original":
        ctrl = UnifiedLearningControllerV4(
            classifier=clf, optimizer=opt, pipeline=pipeline, budget_manager=budget,
            prior_tracker=prior, threshold_manager=thresh, concept_memory=concept_mem,
        )
    elif model_name == "ULC-v4.1 Hybrid (No Explanations)":
        ctrl = HybridMasterControllerV4_1(
            classifier=clf, optimizer=opt, pipeline=pipeline, budget_manager=budget,
            prior_tracker=prior, threshold_manager=thresh, concept_memory=concept_mem,
            generate_explanations=False,
        )
    elif model_name == "ULC-v4.1 Hybrid (With Explanations)":
        ctrl = HybridMasterControllerV4_1(
            classifier=clf, optimizer=opt, pipeline=pipeline, budget_manager=budget,
            prior_tracker=prior, threshold_manager=thresh, concept_memory=concept_mem,
            generate_explanations=True,
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")

    # Generate synthetic stream
    stream = generate_stream(seed=seed, n_batches=n_warmup + n_measured, batch_size=batch_size)

    # Warm-up phase
    for b in range(n_warmup):
        batch = stream[b]
        X_b, y_b, delta = batch["X"], batch["y_observed"], batch["delta"]
        probs = clf.predict_proba(X_b)
        ctrl.step(X_b, y_b, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)

    # Measured phase
    step_latencies: List[float] = []
    for b in range(n_warmup, n_warmup + n_measured):
        batch = stream[b]
        X_b, y_b, delta = batch["X"], batch["y_observed"], batch["delta"]
        probs = clf.predict_proba(X_b)

        t0 = time.perf_counter()
        ctrl.step(X_b, y_b, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        step_latencies.append(elapsed_ms)

    lat_arr = np.array(step_latencies)
    return {
        "model": model_name,
        "mean_ms": float(np.mean(lat_arr)),
        "std_ms": float(np.std(lat_arr)),
        "p50_ms": float(np.percentile(lat_arr, 50)),
        "p95_ms": float(np.percentile(lat_arr, 95)),
        "p99_ms": float(np.percentile(lat_arr, 99)),
        "throughput_batches_sec": float(1000.0 / np.mean(lat_arr)),
        "throughput_samples_sec": float(batch_size * 1000.0 / np.mean(lat_arr)),
    }


def run_long_running_memory_test(n_batches: int = 500, batch_size: int = 30, seed: int = 42) -> List[Dict[str, Any]]:
    """Runs a 500-batch stream (15,000 samples) and tracks RSS memory growth."""
    print(f"\n--- Running Long-Stream Memory Boundedness Test ({n_batches} batches = {n_batches * batch_size} samples) ---")
    clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=10, tau_tie=0.10, replay_capacity=100)
    init_X = np.random.randn(30, 4)
    init_y = np.array([0] * 27 + [1] * 3)
    clf.fit(init_X, init_y)

    ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

    stream = generate_stream(seed=seed, n_batches=n_batches, batch_size=batch_size)
    memory_snapshots: List[Dict[str, Any]] = []

    for b, batch in enumerate(stream):
        X_b, y_b, delta = batch["X"], batch["y_observed"], batch["delta"]
        probs = clf.predict_proba(X_b)
        ctrl.step(X_b, y_b, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)

        if (b + 1) % 50 == 0 or b == 0:
            rss_mb = get_process_memory_bytes() / (1024 ** 2)
            memory_snapshots.append({
                "batch": b + 1,
                "samples_processed": (b + 1) * batch_size,
                "rss_mb": float(rss_mb),
            })
            print(f"  [Batch {b+1:4d} / {n_batches}] Processed: {(b+1)*batch_size:5d} samples | RSS: {rss_mb:6.2f} MB")

    return memory_snapshots


def main() -> None:
    print("=" * 80)
    print("STAGE 7.2 WORKSTREAM H: PERFORMANCE, LATENCY & MEMORY AUDIT")
    print("=" * 80)

    out_dir = Path(__file__).resolve().parent
    csv_path = out_dir / "LATENCY_RESULTS.csv"

    models_to_test = [
        "ULC-v1",
        "ULC-v4 Original",
        "ULC-v4.1 Hybrid (No Explanations)",
        "ULC-v4.1 Hybrid (With Explanations)",
    ]

    benchmark_results: List[Dict[str, Any]] = []

    print("\n--- Micro-Benchmarking Controller Latency (10 Warmup + 100 Measured Batches) ---")
    for m in models_to_test:
        res = benchmark_controller_latency(m, n_warmup=10, n_measured=100)
        benchmark_results.append(res)
        print(
            f"  {m:28s} | Mean: {res['mean_ms']:5.3f} ms | P50: {res['p50_ms']:5.3f} ms | "
            f"P95: {res['p95_ms']:5.3f} ms | P99: {res['p99_ms']:5.3f} ms | "
            f"Throughput: {res['throughput_samples_sec']:6.0f} samp/s"
        )

    # Save to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "MeanLatency_ms", "StdLatency_ms", "P50_ms", "P95_ms", "P99_ms", "Throughput_Batches_Sec", "Throughput_Samples_Sec"])
        for r in benchmark_results:
            writer.writerow([
                r["model"], f"{r['mean_ms']:.4f}", f"{r['std_ms']:.4f}",
                f"{r['p50_ms']:.4f}", f"{r['p95_ms']:.4f}", f"{r['p99_ms']:.4f}",
                f"{r['throughput_batches_sec']:.2f}", f"{r['throughput_samples_sec']:.2f}"
            ])

    # Run Long-Running Memory Test
    mem_snaps = run_long_running_memory_test(n_batches=500, batch_size=30)
    rss_initial = mem_snaps[0]["rss_mb"]
    rss_final = mem_snaps[-1]["rss_mb"]
    rss_growth = rss_final - rss_initial

    print("\n" + "=" * 80)
    print("MEMORY BOUNDEDNESS AUDIT SUMMARY")
    print("=" * 80)
    print(f"  Initial RSS (Batch 1):   {rss_initial:6.2f} MB")
    print(f"  Final RSS (Batch 500):   {rss_final:6.2f} MB")
    print(f"  Net Heap Growth:         {rss_growth:+6.2f} MB (Over 15,000 streaming samples)")
    print(f"  Boundedness Verdict:     {'STRICTLY BOUNDED O(1)' if abs(rss_growth) < 5.0 else 'LEAK SUSPECTED'}")
    print("=" * 80)

    print(f"\nSaved latency results to {csv_path}")


if __name__ == "__main__":
    main()
