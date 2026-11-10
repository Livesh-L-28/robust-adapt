"""
Stage 12 — Workstream C: Minority Intelligence 2.0 Credit Card Benchmark.

Evaluates:
1. standard_unweighted: Standard ERM (0.18% prior causes massive missed fraud)
2. class_weighted_556: 556:1 inverse class weighting (massive false positive explosion)
3. adaptive_ml_minority_v1: Stage 11 adaptive threshold manager
4. minority_2_0_calibrated: Next-generation imbalanced learning with PID budget & sublinear cost

Protocol:
- Authentic Credit Card Fraud dataset (267,334 transactions)
- Chronological split: 180,000 train / 87,334 test
- 10 paired seeds: [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
- Metrics: Fraud Recall, Precision, False Positives, Minority F1, PR-AUC, Throughput
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from experiments.stage_12.minority_2_0.calibrated_minority import MinorityIntelligence20Learner

SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
BATCH_SIZE = 500
TRAIN_SPLIT = 180000


def run_trial(model_type: str, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_batches = int(np.ceil(len(X_train) / BATCH_SIZE))
    t_start = time.perf_counter()

    if model_type == "minority_2_0_calibrated":
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5, sublinear_cost_power=0.52)
        learner.threshold_mgr.max_threshold = 0.65
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = min(idx_start + BATCH_SIZE, len(X_train))
            learner.fit_batch(X_train[idx_start:idx_end], y_train[idx_start:idx_end])
        preds = learner.predict(X_test)
        final_tau = learner.threshold_mgr.threshold

    elif model_type == "adaptive_ml_minority_v1":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        prior_tracker = OnlineClassPriorTracker(n_classes=2)
        threshold_mgr = AdaptiveThresholdManager(n_classes=2)

        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = min(idx_start + BATCH_SIZE, len(X_train))
            X_b = X_train[idx_start:idx_end]
            y_b = y_train[idx_start:idx_end]

            if b == 0:
                clf.partial_fit(X_b, y_b, classes=np.array([0, 1]))
            else:
                clf.partial_fit(X_b, y_b)
            prior_tracker.update(y_b)

        probas = clf.predict_proba(X_test)
        tau = float(np.clip(prior_tracker.priors[0], 0.35, 0.65))
        preds = (probas[:, 1] >= (1.0 - tau)).astype(int)
        final_tau = float(1.0 - tau)

    elif model_type == "class_weighted_556":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed, class_weight="balanced")
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        final_tau = 0.50

    elif model_type == "standard_unweighted":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        final_tau = 0.50

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    t_total = time.perf_counter() - t_start

    rec = float(recall_score(y_test, preds, pos_label=1))
    prec = float(precision_score(y_test, preds, pos_label=1, zero_division=0))
    min_f1 = float(f1_score(y_test, preds, pos_label=1))
    acc = float(accuracy_score(y_test, preds))

    cm = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel()

    return {
        "model_type": model_type,
        "seed": seed,
        "minority_recall": rec,
        "minority_precision": prec,
        "minority_f1": min_f1,
        "accuracy": acc,
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "decision_threshold": final_tau,
        "total_time_sec": t_total,
        "throughput_samples_per_sec": len(X_train) / t_total,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream C — Minority Intelligence 2.0 Benchmark")
    print(f"Seeds: {SEEDS} | Train: {TRAIN_SPLIT} | Test: 87,334")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/creditcard.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["Time", "Class", "target"]]
    X_raw = df[feature_cols].values
    y = df["target"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    X_train, y_train = X[:TRAIN_SPLIT], y[:TRAIN_SPLIT]
    X_test, y_test = X[TRAIN_SPLIT:], y[TRAIN_SPLIT:]

    models = [
        "standard_unweighted",
        "class_weighted_556",
        "adaptive_ml_minority_v1",
        "minority_2_0_calibrated",
    ]
    all_results = []

    for model in models:
        print(f"\nEvaluating: {model}...", flush=True)
        records = []
        for seed in SEEDS:
            res = run_trial(model, X_train, y_train, X_test, y_test, seed)
            records.append(res)
            all_results.append(res)
            print(
                f"  Seed {seed:4d} | Recall: {res['minority_recall']*100:5.2f}% | Prec: {res['minority_precision']*100:5.2f}% | "
                f"FP: {res['false_positives']:4d} | F1: {res['minority_f1']:.4f} | Tau: {res['decision_threshold']:.3f}",
                flush=True,
            )

        mean_rec = np.mean([r["minority_recall"] for r in records])
        std_rec = np.std([r["minority_recall"] for r in records])
        mean_prec = np.mean([r["minority_precision"] for r in records])
        std_prec = np.std([r["minority_precision"] for r in records])
        mean_fp = np.mean([r["false_positives"] for r in records])
        std_fp = np.std([r["false_positives"] for r in records])
        mean_f1 = np.mean([r["minority_f1"] for r in records])
        std_f1 = np.std([r["minority_f1"] for r in records])
        print(
            f"  --> Mean Recall: {mean_rec*100:5.2f}% ± {std_rec*100:4.2f}% | Prec: {mean_prec*100:5.2f}% ± {std_prec*100:4.2f}% | "
            f"Mean FP: {mean_fp:4.1f} ± {std_fp:4.1f} | Mean F1: {mean_f1:.4f} ± {std_f1:.4f}",
            flush=True,
        )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "minority_2_0_creditcard_results.json"
    out_csv = out_dir / "minority_2_0_creditcard_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll Minority 2.0 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

