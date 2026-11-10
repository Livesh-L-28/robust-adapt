"""
Stage 11 — Workstream D: RLA Real-World Robustness Validation on Spambase.

Evaluates RLA against standard baselines under clean conditions and controlled
symmetric and asymmetric label corruption (10%, 20%, 40%) applied strictly to
the training set while keeping the test set 100% clean.

Models evaluated:
1. Standard ERM (Logistic Regression / standard cross-entropy)
2. Class-Weighted Classifier (cost-sensitive adjustment)
3. Generalized Cross-Entropy Loss (GCE baseline, q=0.7)
4. AdaptiveML RLA Pipeline (MultiSignalReliabilityEngine + SymmetricCrossEntropyLoss)

Across 10 distinct random seeds on Spambase (4,601 instances, 57 features).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, precision_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler

# AdaptiveML imports
from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from adaptive_ml.rla.losses import SymmetricCrossEntropyLoss


SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
NOISE_RATES = [0.0, 0.10, 0.20, 0.40]
NOISE_TYPES = ["symmetric", "asymmetric"]


def inject_label_noise(
    y: np.ndarray,
    noise_rate: float,
    noise_type: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Injects controlled label noise into training labels.

    Returns:
        (y_noisy, corrupted_mask)
    """
    if noise_rate == 0.0:
        return y.copy(), np.zeros(len(y), dtype=bool)

    rng = np.random.default_rng(seed)
    y_noisy = y.copy()
    n_samples = len(y)
    corrupted_mask = np.zeros(n_samples, dtype=bool)

    if noise_type == "symmetric":
        # Random uniform label flip (binary: flip 0 <-> 1)
        flip_indices = rng.choice(n_samples, size=int(n_samples * noise_rate), replace=False)
        y_noisy[flip_indices] = 1 - y_noisy[flip_indices]
        corrupted_mask[flip_indices] = True
    elif noise_type == "asymmetric":
        # Evasion attack: Spam (1) disguised as Ham (0)
        spam_indices = np.where(y == 1)[0]
        n_flip = min(len(spam_indices), int(len(spam_indices) * noise_rate * 2))
        flip_indices = rng.choice(spam_indices, size=n_flip, replace=False)
        y_noisy[flip_indices] = 0
        corrupted_mask[flip_indices] = True
    else:
        raise ValueError(f"Unknown noise_type: {noise_type}")

    return y_noisy, corrupted_mask


def evaluate_single_run(
    model_type: str,
    X_train: np.ndarray,
    y_train_noisy: np.ndarray,
    X_test: np.ndarray,
    y_test_clean: np.ndarray,
    seed: int,
) -> Dict[str, Any]:
    t0 = time.perf_counter()

    if model_type == "standard_erm":
        clf = LogisticRegression(max_iter=500, random_state=seed)
        clf.fit(X_train, y_train_noisy)
        y_pred = clf.predict(X_test)
        retained_fraction = 1.0

    elif model_type == "class_weighted":
        clf = LogisticRegression(class_weight="balanced", max_iter=500, random_state=seed)
        clf.fit(X_train, y_train_noisy)
        y_pred = clf.predict(X_test)
        retained_fraction = 1.0

    elif model_type == "gce_surrogate":
        # Approximate GCE by fitting with sample weights inversely proportional to margin
        base_clf = LogisticRegression(max_iter=300, random_state=seed)
        base_clf.fit(X_train, y_train_noisy)
        train_probs = base_clf.predict_proba(X_train)
        p_y = train_probs[np.arange(len(y_train_noisy)), y_train_noisy]
        # GCE weighting: w_i = p_i^(q) with q=0.7
        gce_weights = np.clip(p_y ** 0.7, 0.1, 1.0)
        clf = LogisticRegression(max_iter=500, random_state=seed)
        clf.fit(X_train, y_train_noisy, sample_weight=gce_weights)
        y_pred = clf.predict(X_test)
        retained_fraction = 1.0

    elif model_type == "adaptive_ml_rla":
        # RLA pipeline: warm-up probabilities + spatial reliability scoring + threshold filtering
        base_clf = LogisticRegression(max_iter=300, random_state=seed)
        base_clf.fit(X_train, y_train_noisy)
        probas_train = base_clf.predict_proba(X_train)

        engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=5, buffer_size=500)
        # Compute composite reliability scores
        reliabilities = engine.compute_reliability(X_train, y_train_noisy, probas_train)

        # Filter out suspected noisy samples with reliability < 0.40
        keep_mask = reliabilities >= 0.40
        retained_fraction = float(np.mean(keep_mask))

        if np.sum(keep_mask) < 20 or len(np.unique(y_train_noisy[keep_mask])) < 2:
            # Fallback if over-filtered
            keep_mask = np.ones(len(y_train_noisy), dtype=bool)
            sample_weights = reliabilities
        else:
            sample_weights = reliabilities[keep_mask]

        X_train_filtered = X_train[keep_mask]
        y_train_filtered = y_train_noisy[keep_mask]

        clf = LogisticRegression(max_iter=500, random_state=seed)
        clf.fit(X_train_filtered, y_train_filtered, sample_weight=sample_weights)
        y_pred = clf.predict(X_test)

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    t_elapsed = time.perf_counter() - t0

    return {
        "accuracy": float(accuracy_score(y_test_clean, y_pred)),
        "macro_f1": float(f1_score(y_test_clean, y_pred, average="macro")),
        "balanced_accuracy": float(balanced_accuracy_score(y_test_clean, y_pred)),
        "precision_spam": float(precision_score(y_test_clean, y_pred, pos_label=1, zero_division=0)),
        "recall_spam": float(recall_score(y_test_clean, y_pred, pos_label=1, zero_division=0)),
        "retained_fraction": retained_fraction,
        "runtime_sec": t_elapsed,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Workstream D — RLA Spambase Robustness Benchmark")
    print(f"Seeds: {SEEDS} | Noise rates: {NOISE_RATES} | Noise types: {NOISE_TYPES}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/spambase.csv.gz")
    if not data_file.exists():
        raise FileNotFoundError(f"Spambase dataset {data_file} not found.")

    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X_raw = df[feature_cols].values
    y_raw = df["target"].values

    models = ["standard_erm", "class_weighted", "gce_surrogate", "adaptive_ml_rla"]
    all_results = []

    for noise_type in NOISE_TYPES:
        for noise_rate in NOISE_RATES:
            print(f"\n========================================================")
            print(f"Condition: {noise_type.upper()} Noise @ {noise_rate*100:.0f}%")
            print(f"========================================================")

            for model_type in models:
                model_runs = []
                for seed in SEEDS:
                    # Stratified 70/30 split
                    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=seed)
                    train_idx, test_idx = next(sss.split(X_raw, y_raw))

                    scaler = StandardScaler()
                    X_train = scaler.fit_transform(X_raw[train_idx])
                    X_test = scaler.transform(X_raw[test_idx])
                    y_train = y_raw[train_idx]
                    y_test_clean = y_raw[test_idx]

                    # Inject noise strictly into train labels
                    y_train_noisy, _ = inject_label_noise(y_train, noise_rate, noise_type, seed=seed)

                    metrics = evaluate_single_run(
                        model_type=model_type,
                        X_train=X_train,
                        y_train_noisy=y_train_noisy,
                        X_test=X_test,
                        y_test_clean=y_test_clean,
                        seed=seed,
                    )
                    record = {
                        "noise_type": noise_type,
                        "noise_rate": noise_rate,
                        "model_type": model_type,
                        "seed": seed,
                        **metrics,
                    }
                    model_runs.append(record)
                    all_results.append(record)

                mean_acc = np.mean([r["accuracy"] for r in model_runs])
                std_acc = np.std([r["accuracy"] for r in model_runs])
                mean_f1 = np.mean([r["macro_f1"] for r in model_runs])
                std_f1 = np.std([r["macro_f1"] for r in model_runs])
                mean_ret = np.mean([r["retained_fraction"] for r in model_runs])
                print(f"  {model_type:18s} | Acc: {mean_acc*100:5.2f}% ± {std_acc*100:4.2f}% | F1: {mean_f1:6.4f} ± {std_f1:6.4f} | Retained: {mean_ret*100:5.1f}%")

    out_dir = Path("experiments/stage_11/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "rla_spambase_results.json"
    out_csv = out_dir / "rla_spambase_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll RLA results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

