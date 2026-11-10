"""
Stage 12 — Workstream B: RLA 3.0 Spambase Empirical Benchmark.

Evaluates:
1. standard_erm: Standard empirical risk minimization (no noise filtering)
2. gce_surrogate: Loss-based surrogate robustness
3. adaptive_ml_rla_v2: Stage 11 MultiSignalReliabilityEngine (pure spatial filtering)
4. rla_3_0_asymmetric: Next-generation RLA with class-conditional reliability & minority protection

Noise conditions evaluated across 10 paired seeds:
- clean: 0% noise
- symmetric_20: 20% uniform label flipping
- asymmetric_20: 20% evasion noise (spam flipped to ham)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from experiments.stage_12.rla_3_0.asymmetric_rla import RLA30RobustLearner

SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
NOISE_CONDITIONS = ["clean", "symmetric_20", "asymmetric_20"]
BATCH_SIZE = 64


def inject_noise(y: np.ndarray, noise_type: str, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Injects noise and returns (noisy_labels, noise_mask)."""
    np.random.seed(seed)
    y_noisy = y.copy()
    n_samples = len(y)
    noise_mask = np.zeros(n_samples, dtype=bool)

    if noise_type == "clean":
        return y_noisy, noise_mask

    elif noise_type == "symmetric_20":
        flip_indices = np.random.choice(n_samples, size=int(0.20 * n_samples), replace=False)
        y_noisy[flip_indices] = 1 - y_noisy[flip_indices]
        noise_mask[flip_indices] = True
        return y_noisy, noise_mask

    elif noise_type == "asymmetric_20":
        # Evasion attack: spam (class 1) flipped to ham (class 0)
        spam_indices = np.where(y == 1)[0]
        n_flip = int(0.20 * len(spam_indices))
        flip_indices = np.random.choice(spam_indices, size=n_flip, replace=False)
        y_noisy[flip_indices] = 0
        noise_mask[flip_indices] = True
        return y_noisy, noise_mask

    else:
        raise ValueError(f"Unknown noise condition: {noise_type}")


def run_trial(
    model_type: str,
    noise_type: str,
    X_train: np.ndarray,
    y_train_noisy: np.ndarray,
    noise_mask: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    seed: int,
) -> Dict[str, Any]:
    np.random.seed(seed)
    t_start = time.perf_counter()
    n_batches = int(np.ceil(len(X_train) / BATCH_SIZE))

    if model_type == "rla_3_0_asymmetric":
        learner = RLA30RobustLearner(n_classes=2, minority_class=1, reliability_threshold=0.40)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = min(idx_start + BATCH_SIZE, len(X_train))
            learner.fit_batch(X_train[idx_start:idx_end], y_train_noisy[idx_start:idx_end])
        preds = learner.predict(X_test)
        retained_samples = learner.retained_samples

    elif model_type == "adaptive_ml_rla_v2":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        pipeline = MultiSignalReliabilityEngine(n_classes=2, buffer_size=300)
        retained_samples = 0

        # Warm-up batch
        clf.partial_fit(X_train[:BATCH_SIZE], y_train_noisy[:BATCH_SIZE], classes=np.array([0, 1]))
        retained_samples += BATCH_SIZE

        for b in range(1, n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = min(idx_start + BATCH_SIZE, len(X_train))
            X_b = X_train[idx_start:idx_end]
            y_b = y_train_noisy[idx_start:idx_end]

            probas = clf.predict_proba(X_b)
            rels = pipeline.compute_reliability(X_b, y_b, probas)
            mask = rels >= 0.40
            n_keep = int(np.sum(mask))
            retained_samples += n_keep

            if n_keep >= 5:
                clf.partial_fit(X_b[mask], y_b[mask], sample_weight=rels[mask])
            else:
                clf.partial_fit(X_b, y_b)
        preds = clf.predict(X_test)

    elif model_type == "standard_erm":
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        clf.fit(X_train, y_train_noisy)
        preds = clf.predict(X_test)
        retained_samples = len(X_train)

    elif model_type == "gce_surrogate":
        # Generalized Cross-Entropy surrogate approximation via loss truncation
        clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        clf.fit(X_train, y_train_noisy)
        probas = clf.predict_proba(X_train)
        confidences = probas[np.arange(len(y_train_noisy)), y_train_noisy]
        keep = confidences >= 0.20
        retained_samples = int(np.sum(keep))
        clf2 = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=seed)
        clf2.fit(X_train[keep], y_train_noisy[keep])
        preds = clf2.predict(X_test)

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    t_total = time.perf_counter() - t_start

    acc = float(accuracy_score(y_test, preds))
    macro_f1 = float(f1_score(y_test, preds, average="macro"))
    rec = float(recall_score(y_test, preds, pos_label=1))
    prec = float(precision_score(y_test, preds, pos_label=1, zero_division=0))
    min_f1 = float(f1_score(y_test, preds, pos_label=1))

    return {
        "model_type": model_type,
        "noise_condition": noise_type,
        "seed": seed,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "minority_recall": rec,
        "minority_precision": prec,
        "minority_f1": min_f1,
        "retained_samples": retained_samples,
        "total_time_sec": t_total,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream B — RLA 3.0 Spambase Benchmark")
    print(f"Seeds: {SEEDS} | Conditions: {NOISE_CONDITIONS}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/spambase.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X_raw = df[feature_cols].values
    y = df["target"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    models = ["standard_erm", "gce_surrogate", "adaptive_ml_rla_v2", "rla_3_0_asymmetric"]
    all_results = []

    for noise_type in NOISE_CONDITIONS:
        print(f"\n=================== NOISE REGIME: {noise_type.upper()} ===================", flush=True)
        for model in models:
            records = []
            for seed in SEEDS:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.30, random_state=seed, stratify=y
                )
                y_train_noisy, mask = inject_noise(y_train, noise_type, seed)
                res = run_trial(model, noise_type, X_train, y_train_noisy, mask, X_test, y_test, seed)
                records.append(res)
                all_results.append(res)

            mean_acc = np.mean([r["accuracy"] for r in records])
            std_acc = np.std([r["accuracy"] for r in records])
            mean_rec = np.mean([r["minority_recall"] for r in records])
            std_rec = np.std([r["minority_recall"] for r in records])
            mean_f1 = np.mean([r["minority_f1"] for r in records])
            std_f1 = np.std([r["minority_f1"] for r in records])
            print(
                f"  {model:22s} | Acc: {mean_acc*100:5.2f}% ± {std_acc*100:4.2f}% | "
                f"Recall: {mean_rec*100:5.2f}% ± {std_rec*100:4.2f}% | Minority F1: {mean_f1:.4f} ± {std_f1:.4f}",
                flush=True,
            )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "rla_3_0_spambase_results.json"
    out_csv = out_dir / "rla_3_0_spambase_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll RLA 3.0 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

