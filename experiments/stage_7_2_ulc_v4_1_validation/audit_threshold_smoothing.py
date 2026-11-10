"""
Stage 7.2 Workstream D: Adaptive Threshold Smoothing Mathematical & Empirical Audit
===================================================================================
Evaluates threshold strategies:
- Static (0.50)
- Class-Aware (theta = pi_1)
- Dynamic gamma in {0.25, 0.50, 0.75, 1.00, 1.50}

Measures: Per-class Precision, Recall, Macro F1, Balanced Accuracy, PR-AUC,
Brier score, Expected Calibration Error (ECE), FPR, FNR, Threshold Stability.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from experiments.stage_7_ulc_v4.run_stage7_experiment import generate_stream


def compute_ece(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error for binary positive class probabilities."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        if i == n_bins - 1:
            mask = mask | (probs == bin_edges[i + 1])
        if np.any(mask):
            bin_conf = float(np.mean(probs[mask]))
            bin_acc = float(np.mean(y_true[mask] == 1))
            ece += (np.sum(mask) / n) * abs(bin_acc - bin_conf)
    return float(ece)


def compute_pr_auc(probs: np.ndarray, y_true: np.ndarray, n_thresholds: int = 50) -> float:
    """Computes area under the precision-recall curve via trapezoidal rule."""
    thresholds = np.linspace(0.0, 1.0, n_thresholds)
    precisions = []
    recalls = []
    for t in thresholds:
        preds = (probs >= t).astype(int)
        tp = np.sum((y_true == 1) & (preds == 1))
        fp = np.sum((y_true == 0) & (preds == 1))
        fn = np.sum((y_true == 1) & (preds == 0))
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        precisions.append(prec)
        recalls.append(rec)

    # Sort by recall ascending
    indices = np.argsort(recalls)
    recalls_sorted = np.array(recalls)[indices]
    precisions_sorted = np.array(precisions)[indices]
    return float(np.trapezoid(precisions_sorted, recalls_sorted))


def run_threshold_trial(
    mode: str,
    gamma: float,
    seed: int,
    n_batches: int = 60,
    batch_size: int = 30,
) -> Dict[str, Any]:
    stream = generate_stream(seed=seed, n_batches=n_batches, batch_size=batch_size)

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    clf = AdaptiveClassifier(
        n_features=4,
        n_classes=2,
        grace_period=10,
        tau_tie=0.10,
        replay_capacity=100,
        enable_drift_detection=True,
        random_state=seed,
    )
    clf.fit(init_X, init_y)

    prior = OnlineClassPriorTracker(n_classes=2)
    thresh = AdaptiveThresholdManager(n_classes=2, mode="fixed" if mode == "fixed" else "dynamic", gamma=gamma)

    all_y_clean: List[int] = []
    all_y_pred: List[int] = []
    all_probs_1: List[float] = []
    threshold_history: List[float] = []

    for batch in stream[3:]:
        X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
        probs = clf.predict_proba(X_b)
        p1 = probs[:, 1]

        if mode == "fixed":
            theta = 0.50
        elif mode == "class_aware":
            theta = float(np.clip(prior.priors[1], 0.05, 0.95))
        else:  # dynamic gamma
            theta = thresh.primary_threshold

        preds = (p1 >= theta).astype(int)

        all_y_clean.extend(y_clean.tolist())
        all_y_pred.extend(preds.tolist())
        all_probs_1.extend(p1.tolist())
        threshold_history.append(theta)

        prior.update(y_obs)
        if mode not in ("fixed", "class_aware"):
            thresh.update_from_priors(prior.priors)

        clf.partial_fit(X_b, y_obs)

    y_true = np.array(all_y_clean)
    y_pred = np.array(all_y_pred)
    probs_1 = np.array(all_probs_1)

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    rec_min = tp / max(1, tp + fn)
    prec_min = tp / max(1, tp + fp)
    f1_min = 2 * prec_min * rec_min / max(1e-6, prec_min + rec_min)

    rec_maj = tn / max(1, tn + fp)
    prec_maj = tn / max(1, tn + fn)
    f1_maj = 2 * prec_maj * rec_maj / max(1e-6, prec_maj + rec_maj)

    macro_f1 = (f1_maj + f1_min) / 2.0
    balanced_acc = (rec_min + rec_maj) / 2.0

    fpr = fp / max(1, fp + tn)
    fnr = fn / max(1, fn + tp)

    brier = float(np.mean((probs_1 - y_true) ** 2))
    ece = compute_ece(probs_1, y_true)
    pr_auc = compute_pr_auc(probs_1, y_true)
    thresh_std = float(np.std(threshold_history))
    thresh_mean = float(np.mean(threshold_history))

    return {
        "mode": mode,
        "gamma": gamma,
        "seed": seed,
        "mean_threshold": thresh_mean,
        "threshold_stability": thresh_std,
        "minority_recall": rec_min * 100.0,
        "minority_precision": prec_min * 100.0,
        "minority_f1": f1_min,
        "majority_recall": rec_maj * 100.0,
        "majority_precision": prec_maj * 100.0,
        "majority_f1": f1_maj,
        "macro_f1": macro_f1,
        "balanced_acc": balanced_acc * 100.0,
        "fpr": fpr * 100.0,
        "fnr": fnr * 100.0,
        "brier_score": brier,
        "ece": ece,
        "pr_auc": pr_auc,
    }


def main() -> None:
    print("=" * 80)
    print("STAGE 7.2 WORKSTREAM D: THRESHOLD SMOOTHING VALIDATION")
    print("=" * 80)

    val_seeds = [1001, 1002, 1003, 1004, 1005]
    configs = [
        ("fixed", 0.0),
        ("class_aware", 0.0),
        ("dynamic", 0.25),
        ("dynamic", 0.50),
        ("dynamic", 0.75),
        ("dynamic", 1.00),
        ("dynamic", 1.50),
    ]

    out_dir = Path(__file__).resolve().parent
    csv_path = out_dir / "THRESHOLD_EXPERIMENTS.csv"

    all_results: List[Dict[str, Any]] = []

    for mode, gamma in configs:
        for seed in val_seeds:
            res = run_threshold_trial(mode=mode, gamma=gamma, seed=seed)
            all_results.append(res)

    # Write to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Mode", "Gamma", "Seed", "MeanThreshold", "ThreshStd",
            "MinorityRecall", "MinorityPrecision", "MinorityF1", "MacroF1",
            "BalancedAcc", "FPR", "FNR", "BrierScore", "ECE", "PR_AUC"
        ])
        for r in all_results:
            writer.writerow([
                r["mode"], r["gamma"], r["seed"], f"{r['mean_threshold']:.4f}",
                f"{r['threshold_stability']:.4f}", f"{r['minority_recall']:.2f}",
                f"{r['minority_precision']:.2f}", f"{r['minority_f1']:.4f}",
                f"{r['macro_f1']:.4f}", f"{r['balanced_acc']:.2f}",
                f"{r['fpr']:.2f}", f"{r['fnr']:.2f}", f"{r['brier_score']:.4f}",
                f"{r['ece']:.4f}", f"{r['pr_auc']:.4f}"
            ])

    # Print summary
    print(f"\n{'Config':18s} | {'Thresh':6s} | {'Min Recall':11s} | {'Min Prec':10s} | {'Macro F1':10s} | {'Bal Acc':9s} | {'FPR (%)':8s} | {'ECE':6s}")
    print("-" * 96)
    for mode, gamma in configs:
        c_runs = [r for r in all_results if r["mode"] == mode and abs(r["gamma"] - gamma) < 1e-4]
        name = f"{mode} (g={gamma:.2f})" if mode == "dynamic" else mode
        t_m = np.mean([r["mean_threshold"] for r in c_runs])
        rec_m = np.mean([r["minority_recall"] for r in c_runs])
        prec_m = np.mean([r["minority_precision"] for r in c_runs])
        f1_m = np.mean([r["macro_f1"] for r in c_runs])
        bal_m = np.mean([r["balanced_acc"] for r in c_runs])
        fpr_m = np.mean([r["fpr"] for r in c_runs])
        ece_m = np.mean([r["ece"] for r in c_runs])

        print(
            f"{name:18s} | {t_m:6.3f} | {rec_m:5.2f}%     | {prec_m:5.2f}%    | "
            f"{f1_m:5.4f}     | {bal_m:5.2f}%   | {fpr_m:5.2f}%   | {ece_m:6.3f}"
        )

    print(f"\nSaved threshold experiments to {csv_path}")


if __name__ == "__main__":
    main()

