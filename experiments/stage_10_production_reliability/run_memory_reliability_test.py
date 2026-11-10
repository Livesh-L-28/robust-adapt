"""
Stage 10 — Resource and Memory Reliability Long-Running Stress Test.

Executes a 10,000-batch streaming benchmark through the four-pillar system,
monitoring physical RSS, Python tracemalloc heap, replay buffer counts,
and ring-buffer memory bounds across multiple non-stationary phases.
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

# AdaptiveML imports
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.core.telemetry import get_process_memory_bytes


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 10: 10,000-Batch Memory Reliability Benchmark")
    print(f"Python: {sys.version.split()[0]} on {sys.platform}")
    print("=====================================================================")

    out_dir = Path("experiments/stage_10_production_reliability")
    out_dir.mkdir(parents=True, exist_ok=True)

    tracemalloc.start()
    gc.collect()

    initial_rss_mb = get_process_memory_bytes() / (1024 ** 2)
    current_heap, peak_heap = tracemalloc.get_traced_memory()
    initial_heap_mb = current_heap / (1024 ** 2)

    print(f"Initial State: RSS = {initial_rss_mb:.2f} MB | Heap = {initial_heap_mb:.2f} MB\n")

    # Instantiate four-pillar system
    n_features = 8
    n_classes = 2
    batch_size = 50
    n_total_batches = 10_000

    classifier = AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=20,
        delta=1e-4,
    )
    replay_buffer = ClassBalancedReservoirReplay(capacity=2000, n_classes=n_classes)
    adwin = ReliabilityWeightedADWIN(delta=0.002)
    reliability_scorer = MultiSignalReliabilityEngine(n_classes=n_classes, buffer_size=300)
    budget_mgr = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=2048.0)
    config = ULCv41Config(max_history_len=500, max_noise_dwell=15)
    controller = UnifiedLearningControllerV4_1(
        config=config,
        classifier=classifier,
        adwin=adwin,
        pipeline=reliability_scorer,
        budget_manager=budget_mgr,
    )

    rng = np.random.default_rng(42)
    checkpoint_records = []
    t_start = time.perf_counter()

    for batch_idx in range(1, n_total_batches + 1):
        # Inject periodic non-stationary distribution shifts and noise
        phase = (batch_idx // 1000) % 4
        if phase == 0:
            # Concept 1: Clean
            mean_shift = 0.0
            noise_rate = 0.05
        elif phase == 1:
            # Concept 2: Drift
            mean_shift = 2.0
            noise_rate = 0.05
        elif phase == 2:
            # Concept 3: Noise burst
            mean_shift = 0.0
            noise_rate = 0.40
        else:
            # Concept 4: High dimensional shift
            mean_shift = -1.5
            noise_rate = 0.10

        X = rng.normal(loc=mean_shift, scale=1.0, size=(batch_size, n_features))
        y = (X[:, 0] + X[:, 1] > 0).astype(np.int64)

        if noise_rate > 0.0:
            noise_mask = rng.random(batch_size) < noise_rate
            y[noise_mask] = 1 - y[noise_mask]

        # Feed step into controller
        directive, telemetry = controller.step(X, y)

        # Update replay buffer with batch
        replay_buffer.add(X, y)

        # Record telemetry every 1000 batches
        if batch_idx % 1000 == 0 or batch_idx == 100:
            rss_mb = get_process_memory_bytes() / (1024 ** 2)
            cur_h, pk_h = tracemalloc.get_traced_memory()
            record = {
                "batch": batch_idx,
                "elapsed_sec": time.perf_counter() - t_start,
                "rss_mb": rss_mb,
                "heap_current_mb": cur_h / (1024 ** 2),
                "heap_peak_mb": pk_h / (1024 ** 2),
                "replay_count": replay_buffer.total_stored,
                "controller_history_len": len(controller.history_),
                "interventions_len": len(controller.intervention_history_),
                "state": directive.state.value,
            }
            checkpoint_records.append(record)
            print(
                f"Batch {batch_idx:05d}/{n_total_batches} | "
                f"RSS: {rss_mb:.2f} MB | Heap: {record['heap_current_mb']:.2f} MB | "
                f"Replay: {record['replay_count']} | State: {record['state']}"
            )

    t_total = time.perf_counter() - t_start
    print(f"\nCompleted 10,000 batches in {t_total:.2f}s ({n_total_batches * batch_size / t_total:,.1f} samples/sec).")

    # Post-run cleanup evaluation
    gc.collect()
    final_rss_mb = get_process_memory_bytes() / (1024 ** 2)
    cur_h, pk_h = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results = {
        "summary": {
            "total_batches": n_total_batches,
            "total_samples": n_total_batches * batch_size,
            "total_time_sec": t_total,
            "samples_per_sec": (n_total_batches * batch_size) / t_total,
            "initial_rss_mb": initial_rss_mb,
            "final_rss_mb": final_rss_mb,
            "peak_heap_mb": pk_h / (1024 ** 2),
            "replay_buffer_capacity": replay_buffer.capacity,
            "replay_buffer_final_count": replay_buffer.total_stored,
            "controller_history_max": config.max_history_len,
            "controller_history_final": len(controller.history_),
            "memory_bounded_verified": bool(
                replay_buffer.total_stored <= replay_buffer.capacity
                and len(controller.history_) <= config.max_history_len
            ),
        },
        "checkpoints": checkpoint_records,
    }

    out_file = out_dir / "memory_reliability_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results successfully saved to: {out_file}")


if __name__ == "__main__":
    main()
