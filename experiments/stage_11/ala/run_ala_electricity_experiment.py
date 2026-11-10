"""
Stage 11 — Workstream C: ALA Real-World Adaptation Validation on Electricity (Elec2).

Executes a prequential (test-then-train) streaming benchmark comparing:
1. Static Incremental Baseline (scikit-learn SGDClassifier partial_fit)
2. Static Hoeffding Tree (AdaptiveClassifier without drift reset)
3. Standard ADWIN Hoeffding Tree (Hoeffding Tree + ADWIN reset, no replay)
4. AdaptiveML ALA Pipeline (AdaptiveClassifier + ReliabilityWeightedADWIN + ClassBalancedReservoirReplay)

Across 10 distinct random seeds on the authentic Electricity dataset (45,312 sequential instances).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, recall_score, precision_score
from sklearn.preprocessing import StandardScaler

# AdaptiveML imports
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay


SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
BATCH_SIZE = 50


def run_prequential_stream(
    model_type: str,
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    batch_size: int = BATCH_SIZE,
) -> Dict[str, Any]:
    n_samples, n_features = X.shape
    n_classes = len(np.unique(y))
    n_batches = n_samples // batch_size

    # Incremental scaler (warm up on first 5 batches = 250 samples)
    scaler = StandardScaler()
    scaler.fit(X[:250])

    # Model initialization
    clf = None
    adwin = None
    replay = None
    drift_resets = 0

    if model_type == "static_sgd":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        clf.partial_fit(scaler.transform(X[:250]), y[:250], classes=np.arange(n_classes))
    elif model_type == "static_hoeffding":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])
    elif model_type == "standard_adwin":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])
    elif model_type == "adaptive_ml_ala":
        clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        replay = ClassBalancedReservoirReplay(capacity=1000, n_classes=n_classes)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])
        replay.add(scaler.transform(X[:250]), y[:250])
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    all_y_true = []
    all_y_pred = []
    t_start = time.perf_counter()

    # Streaming loop starting from batch 5
    for b in range(5, n_batches):
        idx_start = b * batch_size
        idx_end = idx_start + batch_size
        X_b = scaler.transform(X[idx_start:idx_end])
        y_b = y[idx_start:idx_end]

        # 1. Prequential Test Step (Predict before train)
        if model_type == "static_sgd":
            y_pred = clf.predict(X_b)
        else:
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)

        all_y_true.extend(y_b.tolist())
        all_y_pred.extend(y_pred.tolist())

        # 2. Drift Monitoring Step
        errs = (y_pred != y_b).astype(float)
        drift_detected = False
        if adwin is not None:
            for e in errs:
                if adwin.update(e):
                    drift_detected = True

        if drift_detected:
            drift_resets += 1
            if model_type == "standard_adwin":
                # Standard reset: reinitialize classifier
                clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
            elif model_type == "adaptive_ml_ala":
                # AdaptiveML reset: preserve replay buffer, reset tree, and retrain on rehearsal
                clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
                if replay.total_stored >= 100:
                    X_rep, y_rep = replay.sample(min(200, replay.total_stored))
                    clf.partial_fit(X_rep, y_rep)

        # 3. Train Step
        clf.partial_fit(X_b, y_b)

        # Update replay buffer if applicable
        if replay is not None:
            replay.add(X_b, y_b)

    t_total = time.perf_counter() - t_start
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)

    acc = float(accuracy_score(all_y_true, all_y_pred))
    macro_f1 = float(f1_score(all_y_true, all_y_pred, average="macro"))
    bal_acc = float(balanced_accuracy_score(all_y_true, all_y_pred))
    rec_0 = float(recall_score(all_y_true, all_y_pred, pos_label=0))
    rec_1 = float(recall_score(all_y_true, all_y_pred, pos_label=1))

    return {
        "model_type": model_type,
        "seed": seed,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "balanced_accuracy": bal_acc,
        "recall_down_class0": rec_0,
        "recall_up_class1": rec_1,
        "drift_resets": drift_resets,
        "total_time_sec": t_total,
        "samples_per_sec": len(all_y_true) / t_total,
        "evaluated_samples": len(all_y_true),
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Workstream C — ALA Electricity Benchmark")
    print(f"Seeds: {SEEDS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/electricity.csv.gz")
    if not data_file.exists():
        raise FileNotFoundError(f"Electricity dataset {data_file} not found.")

    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X = df[feature_cols].values
    y = df["target"].values

    models = ["static_sgd", "static_hoeffding", "standard_adwin", "adaptive_ml_ala"]
    all_results = []

    for model_type in models:
        print(f"\nEvaluating: {model_type}...")
        model_records = []
        for seed in SEEDS:
            res = run_prequential_stream(model_type, X, y, seed=seed)
            model_records.append(res)
            all_results.append(res)
            print(f"  Seed {seed:4d} | Acc: {res['accuracy']*100:.2f}% | Macro F1: {res['macro_f1']:.4f} | Resets: {res['drift_resets']:2d} | Throughput: {res['samples_per_sec']:,.0f} s/s")

        accs = [r["accuracy"] for r in model_records]
        f1s = [r["macro_f1"] for r in model_records]
        print(f"  --> Mean Accuracy: {np.mean(accs)*100:.2f}% ± {np.std(accs)*100:.2f}% | Mean F1: {np.mean(f1s):.4f} ± {np.std(f1s):.4f}")

    out_dir = Path("experiments/stage_11/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "ala_electricity_results.json"
    out_csv = out_dir / "ala_electricity_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll results saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

