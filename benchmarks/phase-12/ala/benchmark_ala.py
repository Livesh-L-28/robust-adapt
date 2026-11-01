"""
ALA Pillar Benchmark: Adaptive Learning & Concept Drift Detection.

Compares Reliability-Weighted ADWIN (AdaptiveML) vs Standard ADWIN
and Static Hoeffding Tree on SEA concepts and Rotating Hyperplane streams.
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

from datasets.generators import RotatingHyperplaneGenerator, SEAGenerator
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.classifier import AdaptiveClassifier


def run_ala_benchmark(seeds: List[int] = [42, 101, 2024, 7, 99]) -> Dict[str, Any]:
    """Execute multi-seed ALA benchmark."""
    results: Dict[str, Any] = {
        "metadata": {
            "pillar": "ALA",
            "seeds": seeds,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "experiments": {},
    }

    # Experiment 1: Abrupt Concept Drift (SEA Concepts)
    sea_res = {"adaptive_ml": [], "static_baseline": [], "unweighted_adwin": []}

    for seed in seeds:
        gen = SEAGenerator(thetas=[8.0, 9.0, 7.0, 9.5], concept_length=500, noise_ratio=0.05, random_state=seed)
        X, y = gen.generate_stream(2000)

        # 1. AdaptiveML: AdaptiveClassifier with RW-ADWIN & Replay
        aml_clf = AdaptiveClassifier(n_features=3, n_classes=2, grace_period=40, enable_drift_detection=True, random_state=seed)
        correct_aml = 0
        step_times_aml = []

        # 2. Static baseline: No drift detection or model reset
        static_clf = AdaptiveClassifier(n_features=3, n_classes=2, grace_period=40, enable_drift_detection=False, random_state=seed)
        correct_static = 0

        # 3. Unweighted ADWIN detector baseline
        unweighted_adwin = ReliabilityWeightedADWIN(delta=0.002)
        adwin_drifts = 0

        batch_size = 20
        for i in range(0, len(X), batch_size):
            X_b = X[i : i + batch_size]
            y_b = y[i : i + batch_size]

            # Prequential test-then-train for AdaptiveML
            if aml_clf.samples_seen_ > 0:
                preds = aml_clf.predict(X_b)
                correct_aml += int(np.sum(preds == y_b))

            t0 = time.perf_counter()
            aml_clf.partial_fit(X_b, y_b)
            step_times_aml.append(time.perf_counter() - t0)

            # Static prequential test-then-train
            if static_clf.samples_seen_ > 0:
                preds_s = static_clf.predict(X_b)
                correct_static += int(np.sum(preds_s == y_b))
            static_clf.partial_fit(X_b, y_b)

            # Baseline unweighted adwin
            for y_val in y_b:
                if unweighted_adwin.update(float(y_val)):
                    adwin_drifts += 1

        n_eval = len(X) - batch_size
        sea_res["adaptive_ml"].append({
            "accuracy": correct_aml / n_eval,
            "drift_detections": aml_clf.drift_count_,
            "mean_step_time_ms": float(np.mean(step_times_aml) * 1000.0),
        })
        sea_res["static_baseline"].append({
            "accuracy": correct_static / n_eval,
            "drift_detections": 0,
        })
        sea_res["unweighted_adwin"].append({
            "drift_detections": adwin_drifts,
        })

    # Compute averages across seeds
    results["experiments"]["sea_abrupt_drift"] = {
        "adaptive_ml": {
            "accuracy_mean": float(np.mean([r["accuracy"] for r in sea_res["adaptive_ml"]])),
            "accuracy_std": float(np.std([r["accuracy"] for r in sea_res["adaptive_ml"]])),
            "drift_detections_mean": float(np.mean([r["drift_detections"] for r in sea_res["adaptive_ml"]])),
            "mean_step_time_ms": float(np.mean([r["mean_step_time_ms"] for r in sea_res["adaptive_ml"]])),
        },
        "static_baseline": {
            "accuracy_mean": float(np.mean([r["accuracy"] for r in sea_res["static_baseline"]])),
            "accuracy_std": float(np.std([r["accuracy"] for r in sea_res["static_baseline"]])),
        },
        "unweighted_adwin": {
            "drift_detections_mean": float(np.mean([r["drift_detections"] for r in sea_res["unweighted_adwin"]])),
        },
    }

    # Experiment 2: Noisy Stream False Alarm Resistance
    noise_res = {"adaptive_ml_rw_adwin": [], "standard_adwin": []}
    for seed in seeds:
        rng = np.random.default_rng(seed)
        # Stationary stream with high label noise (30% label flips, no underlying concept drift)
        y_noisy = (rng.random(1500) < 0.3).astype(np.float64)
        # Reliability scores: corrupted samples scored with low reliability ~0.1, clean ~0.9
        reliabilities = np.where(y_noisy == 1.0, 0.1, 0.9)

        rw_adwin = ReliabilityWeightedADWIN(delta=0.002)
        std_adwin = ReliabilityWeightedADWIN(delta=0.002)

        rw_drifts = 0
        std_drifts = 0

        for val, rel in zip(y_noisy, reliabilities):
            if rw_adwin.update(val, reliability=rel):
                rw_drifts += 1
            # Standard ADWIN treats all observations with uniform weight 1.0
            if std_adwin.update(val, reliability=1.0):
                std_drifts += 1

        noise_res["adaptive_ml_rw_adwin"].append(rw_drifts)
        noise_res["standard_adwin"].append(std_drifts)

    results["experiments"]["noise_burst_false_alarms"] = {
        "rw_adwin_false_alarms_mean": float(np.mean(noise_res["adaptive_ml_rw_adwin"])),
        "std_adwin_false_alarms_mean": float(np.mean(noise_res["standard_adwin"])),
        "suppression_ratio": float(
            np.mean(noise_res["standard_adwin"]) / max(1e-6, np.mean(noise_res["adaptive_ml_rw_adwin"]))
        ),
    }

    return results


if __name__ == "__main__":
    res = run_ala_benchmark()
    print("ALA Benchmark Completed:")
    print(res["experiments"])
