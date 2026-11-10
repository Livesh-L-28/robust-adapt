"""
Stage 12 — Workstream A: ALA 3.0 Electricity Empirical Benchmark.

Evaluates:
1. standard_adwin: ADWIN drift resets without replay
2. static_hoeffding: Continuous split Hoeffding tree without drift resets
3. adaptive_ml_ala_v2: AdaptiveML ALA with reservoir replay (Stage 11 baseline)
4. ala_3_0_recurrent: Next-generation ALA with Recurring Concept Memory & Restoration

Protocol:
- Authentic Electricity dataset (45,312 observations)
- Prequential evaluation (test-then-train)
- 10 paired seeds: [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
- Metric outputs: Accuracy, Macro F1, Balanced Accuracy, Resets, Restorations, Throughput
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
from experiments.stage_12.ala_3_0.recurrent_ala import ALA30AdaptiveLearner

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

    t_start = time.perf_counter()

    if model_type == "ala_3_0_recurrent":
        learner = ALA30AdaptiveLearner(
            n_features=n_features,
            n_classes=2,
            similarity_threshold=0.82,
            cooldown_steps=5,
            max_concepts=5,
        )
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = learner.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            learner.update(X_b, y_b)

        drift_resets = learner.drift_resets
        concept_restorations = learner.recurring_restorations

    elif model_type == "adaptive_ml_ala_v2":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        replay = ClassBalancedReservoirReplay(capacity=1000, n_classes=2)

        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())

            errs = (y_pred != y_b).astype(float)
            if any(adwin.update(e) for e in errs):
                drift_resets += 1
                clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
                if replay.total_stored >= 100:
                    X_rep, y_rep = replay.sample(min(200, replay.total_stored))
                    clf.partial_fit(X_rep, y_rep)
                adwin = ReliabilityWeightedADWIN(delta=0.002)

            clf.partial_fit(X_b, y_b)
            replay.add(X_b, y_b)

    elif model_type == "standard_adwin":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
        adwin = ReliabilityWeightedADWIN(delta=0.002)

        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b = X[idx_start:idx_end]
            y_b = y[idx_start:idx_end]

            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())

            errs = (y_pred != y_b).astype(float)
            if any(adwin.update(e) for e in errs):
                drift_resets += 1
                clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=50, delta=0.002)
                adwin = ReliabilityWeightedADWIN(delta=0.002)

            clf.partial_fit(X_b, y_b)

    elif model_type == "static_hoeffding":
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
        "total_time_sec": t_total,
        "samples_per_sec": len(y_true_arr) / t_total,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream A — ALA 3.0 Electricity Benchmark")
    print(f"Seeds: {SEEDS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/electricity.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X_raw = df[feature_cols].values
    y = df["target"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    models = ["standard_adwin", "static_hoeffding", "adaptive_ml_ala_v2", "ala_3_0_recurrent"]
    all_results = []

    for model_type in models:
        print(f"\nEvaluating: {model_type}...", flush=True)
        records = []
        for seed in SEEDS:
            res = run_trial(model_type, X, y, seed)
            records.append(res)
            all_results.append(res)
            print(
                f"  Seed {seed:4d} | Acc: {res['accuracy']*100:.2f}% | F1: {res['macro_f1']:.4f} | "
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
            f"  --> Mean Acc: {mean_acc*100:.2f}% ± {std_acc*100:.2f}% | F1: {mean_f1:.4f} ± {std_f1:.4f} | "
            f"Mean Resets: {mean_resets:.1f} | Mean Restores: {mean_restores:.1f}",
            flush=True,
        )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "ala_3_0_electricity_results.json"
    out_csv = out_dir / "ala_3_0_electricity_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll ALA 3.0 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

