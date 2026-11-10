"""
Stage 12 — Workstream F: Cross-Pillar Research Benchmark.

Evaluates how next-generation pillars interact in combined configurations:
1. ala_3_0_alone: ALA 3.0 Recurring Concept Learner
2. rla_3_0_alone: RLA 3.0 Class-Conditional Robust Learner
3. minority_2_0_alone: Minority Intelligence 2.0 Dynamic Threshold Learner
4. ala_plus_rla: Combined ALA 3.0 adaptation + RLA 3.0 filtering
5. rla_plus_minority: Combined RLA 3.0 filtering + Minority 2.0 cost-weighting
6. full_next_gen_system: ULC-v5 Master Controller coordinating all 4 pillars

Protocol:
- Authentic Electricity stream (45,312 observations)
- 10 paired seeds: [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
- Metrics: Accuracy, Macro F1, Balanced Accuracy, Resets, Restorations, Throughput
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

from experiments.stage_12.ala_3_0.recurrent_ala import ALA30AdaptiveLearner
from experiments.stage_12.rla_3_0.asymmetric_rla import RLA30RobustLearner
from experiments.stage_12.minority_2_0.calibrated_minority import MinorityIntelligence20Learner
from experiments.stage_12.ulc_v5.calibrated_ulc_v5 import UnifiedLearningControllerV5

SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
BATCH_SIZE = 50


def run_cross_pillar_trial(config_name: str, X: np.ndarray, y: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_samples, n_features = X.shape
    n_batches = n_samples // BATCH_SIZE

    y_true_all: List[int] = []
    y_pred_all: List[int] = []
    drift_resets = 0
    concept_restorations = 0

    t_start = time.perf_counter()

    if config_name == "ala_3_0_alone":
        learner = ALA30AdaptiveLearner(n_features=n_features, n_classes=2, similarity_threshold=0.82)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = learner.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            learner.update(X_b, y_b)
        drift_resets = learner.drift_resets
        concept_restorations = learner.recurring_restorations

    elif config_name == "rla_3_0_alone":
        learner = RLA30RobustLearner(n_classes=2, minority_class=1)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = learner.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            learner.fit_batch(X_b, y_b)

    elif config_name == "minority_2_0_alone":
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = learner.predict_proba(X_b)
            y_pred = learner.predict(X_b)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            learner.fit_batch(X_b, y_b)

    elif config_name == "ala_plus_rla":
        ala = ALA30AdaptiveLearner(n_features=n_features, n_classes=2, similarity_threshold=0.82)
        rla = RLA30RobustLearner(n_classes=2, minority_class=1)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = ala.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            # RLA filters sample weights for ALA
            rels, abstain = rla.estimator.compute_reliability(X_b, y_b, probas, asymmetry_ratio=1.0)
            ala.update(X_b[rels >= 0.35], y_b[rels >= 0.35])
        drift_resets = ala.drift_resets
        concept_restorations = ala.recurring_restorations

    elif config_name == "rla_plus_minority":
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5)
        rla = RLA30RobustLearner(n_classes=2, minority_class=1)
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = learner.predict_proba(X_b)
            y_pred = learner.predict(X_b)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            rla.detector.update(y_pred, y_b)
            asym = rla.detector.get_asymmetry_ratio()
            learner.fit_batch(X_b, y_b)

    elif config_name == "full_next_gen_system":
        controller = UnifiedLearningControllerV5(
            n_features=n_features,
            n_classes=2,
            similarity_threshold=0.82,
            base_cooldown=5,
        )
        for b in range(n_batches):
            idx_start = b * BATCH_SIZE
            idx_end = idx_start + BATCH_SIZE
            X_b, y_b = X[idx_start:idx_end], y[idx_start:idx_end]
            probas = controller.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            y_true_all.extend(y_b.tolist())
            y_pred_all.extend(y_pred.tolist())
            controller.step(X_b, y_b)
        drift_resets = controller.total_resets
        concept_restorations = controller.total_restores

    else:
        raise ValueError(f"Unknown config_name: {config_name}")

    t_total = time.perf_counter() - t_start
    y_true_arr = np.array(y_true_all)
    y_pred_arr = np.array(y_pred_all)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    macro_f1 = float(f1_score(y_true_arr, y_pred_arr, average="macro"))
    bal_acc = float(balanced_accuracy_score(y_true_arr, y_pred_arr))

    return {
        "config_name": config_name,
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
    print("AdaptiveML Stage 12: Workstream F — Cross-Pillar Research Benchmark")
    print(f"Seeds: {SEEDS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/electricity.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X_raw = df[feature_cols].values
    y = df["target"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    configs = [
        "ala_3_0_alone",
        "rla_3_0_alone",
        "minority_2_0_alone",
        "ala_plus_rla",
        "rla_plus_minority",
        "full_next_gen_system",
    ]
    all_results = []

    for cfg in configs:
        print(f"\nEvaluating: {cfg}...", flush=True)
        records = []
        for seed in SEEDS:
            res = run_cross_pillar_trial(cfg, X, y, seed)
            records.append(res)
            all_results.append(res)
            print(
                f"  Seed {seed:4d} | Acc: {res['accuracy']*100:5.2f}% | F1: {res['macro_f1']:.4f} | "
                f"Resets: {res['drift_resets']:2d} | Restores: {res['concept_restorations']:2d} | "
                f"Throughput: {res['samples_per_sec']:,.0f} s/s",
                flush=True,
            )

        mean_acc = np.mean([r["accuracy"] for r in records])
        std_acc = np.std([r["accuracy"] for r in records])
        mean_f1 = np.mean([r["macro_f1"] for r in records])
        std_f1 = np.std([r["macro_f1"] for r in records])
        print(
            f"  --> Mean Acc: {mean_acc*100:5.2f}% ± {std_acc*100:4.2f}% | F1: {mean_f1:.4f} ± {std_f1:.4f}",
            flush=True,
        )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "cross_pillar_results.json"
    out_csv = out_dir / "cross_pillar_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll Cross-Pillar results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

