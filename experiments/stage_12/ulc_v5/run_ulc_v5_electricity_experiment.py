"""
Stage 12 — Workstream E: ULC-v5 Electricity Empirical Benchmark.

Evaluates:
1. static_baseline: Continuous split streaming Hoeffding tree (no resets)
2. ulc_v4_legacy: Stage 11 ULC-v4 legacy automaton (frequent resets)
3. ulc_v4_1_production: Stage 11 ULC-v4.1 master controller (276 resets)
4. ulc_v5_calibrated: Next-generation ULC-v5 with multi-tier utility calibration

Protocol:
- Authentic Electricity stream (45,312 observations)
- Prequential evaluation (test-then-train)
- 10 paired seeds: [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
- Metrics: Accuracy, Macro F1, Balanced Accuracy, Resets, Restorations, Tier distributions, Throughput
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4
from experiments.stage_12.ulc_v5.calibrated_ulc_v5 import UnifiedLearningControllerV5

SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
BATCH_SIZE = 50


def run_trial(model_type: str, X: np.ndarray, y: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_samples, n_features = X.shape
    n_batches = n_samples // BATCH_SIZE

    y_true_all: List[int] = []
    y_pred_all: List[int] = []
    drift_resets = 0
    concept_restorations = 0
    tier_counts: Dict[str, int] = {}

    t_start = time.perf_counter()

    if model_type == "ulc_v5_calibrated":
        controller = UnifiedLearningControllerV5(
            n_features=n_features,
            n_classes=2,
            similarity_threshold=0.82,
            base_cooldown=5,
        )
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = controller.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            directive, telemetry = controller.step(X_b, y_b)

        drift_resets = controller.total_resets
        concept_restorations = controller.total_restores
        tier_counts = controller.tier_counts

    elif model_type in ["ulc_v4_legacy", "ulc_v4_1_production"]:
        clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        pipeline = MultiSignalReliabilityEngine(n_classes=2, buffer_size=300)
        budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=2048.0)
        prior_tracker = OnlineClassPriorTracker(n_classes=2)
        threshold_mgr = AdaptiveThresholdManager(n_classes=2)

        spatial_thresh = 0.0 if model_type == "ulc_v4_legacy" else 0.45
        ulc_config = ULCv41Config(
            max_history_len=500,
            max_noise_dwell=15,
            spatial_discordance_threshold=spatial_thresh,
        )
        controller = UnifiedLearningControllerV4_1(
            config=ulc_config,
            classifier=clf,
            adwin=adwin,
            pipeline=pipeline,
            budget_manager=budget,
            prior_tracker=prior_tracker,
            threshold_manager=threshold_mgr,
        )
        # Warmup
        controller.step(X[:BATCH_SIZE], y[:BATCH_SIZE])

        for b in range(1, n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())

            directive, telemetry = controller.step(X_b, y_b)
            if directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
                drift_resets += 1

    elif model_type == "static_baseline":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            clf.partial_fit(X_b, y_b)

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    t_total = time.perf_counter() - t_start
    y_true_arr = np.array(y_true_all)
    y_pred_arr = np.array(y_pred_all)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    macro_f1 = float(f1_score(y_true_arr, y_pred_arr, average="macro"))
    bal_acc = float(balanced_accuracy_score(y_true_arr, y_pred_arr))

    return {
        "model_type": model_type,
        "seed": seed,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "balanced_accuracy": bal_acc,
        "drift_resets": drift_resets,
        "concept_restorations": concept_restorations,
        "tier_counts": tier_counts,
        "total_time_sec": t_total,
        "samples_per_sec": len(y_true_arr) / t_total,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream E — ULC-v5 Electricity Benchmark")
    print(f"Seeds: {SEEDS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/electricity.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X_raw = df[feature_cols].values
    y = df["target"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    models = ["static_baseline", "ulc_v4_legacy", "ulc_v4_1_production", "ulc_v5_calibrated"]
    all_results = []

    for model in models:
        print(f"\nEvaluating: {model}...", flush=True)
        records = []
        for seed in SEEDS:
            res = run_trial(model, X, y, seed)
            records.append(res)
            all_results.append(res)
            print(
                f"  Seed {seed:4d} | Acc: {res['accuracy']*100:5.2f}% | F1: {res['macro_f1']:.4f} | "
                f"Resets: {res['drift_resets']:3d} | Restores: {res['concept_restorations']:2d} | "
                f"Throughput: {res['samples_per_sec']:,.0f} s/s",
                flush=True,
            )

        mean_acc = np.mean([r["accuracy"] for r in records])
        std_acc = np.std([r["accuracy"] for r in records])
        mean_f1 = np.mean([r["macro_f1"] for r in records])
        std_f1 = np.std([r["macro_f1"] for r in records])
        mean_resets = np.mean([r["drift_resets"] for r in records])
        mean_restores = np.mean([r["concept_restorations"] for r in records])
        print(
            f"  --> Mean Acc: {mean_acc*100:5.2f}% ± {std_acc*100:4.2f}% | F1: {mean_f1:.4f} ± {std_f1:.4f} | "
            f"Mean Resets: {mean_resets:.1f} | Mean Restores: {mean_restores:.1f}",
            flush=True,
        )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "ulc_v5_electricity_results.json"
    out_csv = out_dir / "ulc_v5_electricity_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll ULC-v5 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

