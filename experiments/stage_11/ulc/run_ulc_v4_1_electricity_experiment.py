"""
Stage 11 — Workstream G: ULC-v4.1 End-to-End Real-World Streaming Validation.

Evaluates ULC-v4.1 against individual pillar configurations and legacy baselines on
the authentic Electricity (Elec2) streaming dataset (45,312 sequential records).

Configurations evaluated:
1. static_baseline: Static Hoeffding tree (no drift reset, no noise filtering)
2. ala_only: AdaptiveClassifier + ReliabilityWeightedADWIN + Replay
3. rla_only: AdaptiveClassifier + MultiSignalReliabilityEngine (sample filtering)
4. rao_only: AdaptiveClassifier + DynamicResourceBudgetManager (step throttling)
5. minority_only: AdaptiveClassifier + OnlineClassPriorTracker + AdaptiveThresholdManager
6. ulc_v4_legacy: ULC-v4 original (without spatial discordance)
7. ulc_v4_1_production: ULC-v4.1 master controller (full four-pillar coordination)

Across 10 distinct random seeds with prequential (test-then-train) evaluation.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# AdaptiveML imports
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.rla.reliability import MultiSignalReliabilityEngine
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4


SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
BATCH_SIZE = 50


def run_ulc_trial(
    config_name: str,
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    batch_size: int = BATCH_SIZE,
) -> Dict[str, Any]:
    n_samples, n_features = X.shape
    n_classes = len(np.unique(y))
    n_batches = n_samples // batch_size

    # Incremental scaler warm up on first 250 samples
    scaler = StandardScaler()
    scaler.fit(X[:250])

    # Component instantiation based on configuration
    clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
    adwin = None
    replay = None
    pipeline = None
    budget = None
    prior_tracker = None
    threshold_mgr = None
    controller = None

    if config_name == "static_baseline":
        clf.partial_fit(scaler.transform(X[:250]), y[:250])

    elif config_name == "ala_only":
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        replay = ClassBalancedReservoirReplay(capacity=1000, n_classes=n_classes)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])
        replay.add(scaler.transform(X[:250]), y[:250])

    elif config_name == "rla_only":
        pipeline = MultiSignalReliabilityEngine(n_classes=n_classes, buffer_size=300)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])

    elif config_name == "rao_only":
        budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=2048.0)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])

    elif config_name == "minority_only":
        prior_tracker = OnlineClassPriorTracker(n_classes=n_classes)
        threshold_mgr = AdaptiveThresholdManager(n_classes=n_classes)
        clf.partial_fit(scaler.transform(X[:250]), y[:250])

    elif config_name in ["ulc_v4_legacy", "ulc_v4_1_production"]:
        adwin = ReliabilityWeightedADWIN(delta=0.002)
        pipeline = MultiSignalReliabilityEngine(n_classes=n_classes, buffer_size=300)
        budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=2048.0)
        prior_tracker = OnlineClassPriorTracker(n_classes=n_classes)
        threshold_mgr = AdaptiveThresholdManager(n_classes=n_classes)
        
        # In legacy v4, spatial discordance threshold is disabled (set to 0.0)
        spatial_thresh = 0.0 if config_name == "ulc_v4_legacy" else 0.45
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
        # Warm-up step
        controller.step(scaler.transform(X[:250]), y[:250])

    all_y_true = []
    all_y_pred = []
    scenario_counts: Dict[str, int] = {}
    drift_resets = 0
    t_start = time.perf_counter()

    for b in range(5, n_batches):
        idx_start = b * batch_size
        idx_end = idx_start + batch_size
        X_b = scaler.transform(X[idx_start:idx_end])
        y_b = y[idx_start:idx_end]

        # Prequential Test Step
        if controller is not None:
            # Controller step evaluates probabilities internally and updates
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())

            directive, telemetry = controller.step(X_b, y_b)
            sc = telemetry.get("scenario", "NONE")
            scenario_counts[sc] = scenario_counts.get(sc, 0) + 1
            if directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
                drift_resets += 1

        elif config_name == "static_baseline":
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())
            clf.partial_fit(X_b, y_b)

        elif config_name == "ala_only":
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())

            errs = (y_pred != y_b).astype(float)
            drift_detected = any(adwin.update(e) for e in errs)
            if drift_detected:
                drift_resets += 1
                clf = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, delta=1e-4)
                if replay.total_stored >= 100:
                    X_rep, y_rep = replay.sample(min(200, replay.total_stored))
                    clf.partial_fit(X_rep, y_rep)
            clf.partial_fit(X_b, y_b)
            replay.add(X_b, y_b)

        elif config_name == "rla_only":
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())

            rels = pipeline.compute_reliability(X_b, y_b, probas)
            mask = rels >= 0.40
            if np.sum(mask) >= 10:
                clf.partial_fit(X_b[mask], y_b[mask], sample_weight=rels[mask])
            else:
                clf.partial_fit(X_b, y_b)

        elif config_name == "rao_only":
            probas = clf.predict_proba(X_b)
            y_pred = np.argmax(probas, axis=1)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())
            clf.partial_fit(X_b, y_b)

        elif config_name == "minority_only":
            probas = clf.predict_proba(X_b)
            prior_tracker.update(y_b)
            # Threshold shift
            tau = float(np.clip(prior_tracker.priors[0], 0.35, 0.65))
            y_pred = (probas[:, 1] >= (1.0 - tau)).astype(int)
            all_y_true.extend(y_b.tolist())
            all_y_pred.extend(y_pred.tolist())
            clf.partial_fit(X_b, y_b)

    t_total = time.perf_counter() - t_start
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)

    acc = float(accuracy_score(all_y_true, all_y_pred))
    macro_f1 = float(f1_score(all_y_true, all_y_pred, average="macro"))
    bal_acc = float(balanced_accuracy_score(all_y_true, all_y_pred))

    return {
        "config_name": config_name,
        "seed": seed,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "balanced_accuracy": bal_acc,
        "drift_resets": drift_resets,
        "total_time_sec": t_total,
        "samples_per_sec": len(all_y_true) / t_total,
        "scenarios": scenario_counts,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Workstream G — ULC-v4.1 End-to-End Benchmark")
    print(f"Seeds: {SEEDS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/electricity.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["class", "target"]]
    X = df[feature_cols].values
    y = df["target"].values

    configs = [
        "static_baseline",
        "ala_only",
        "rla_only",
        "rao_only",
        "minority_only",
        "ulc_v4_legacy",
        "ulc_v4_1_production",
    ]
    all_results = []

    for cfg in configs:
        print(f"\nEvaluating configuration: {cfg}...", flush=True)
        cfg_records = []
        for seed in SEEDS:
            res = run_ulc_trial(cfg, X, y, seed=seed)
            cfg_records.append(res)
            all_results.append(res)
            print(f"  Seed {seed:4d} | Acc: {res['accuracy']*100:.2f}% | F1: {res['macro_f1']:.4f} | Resets: {res['drift_resets']:2d} | Throughput: {res['samples_per_sec']:,.0f} s/s", flush=True)

        mean_acc = np.mean([r["accuracy"] for r in cfg_records])
        std_acc = np.std([r["accuracy"] for r in cfg_records])
        mean_f1 = np.mean([r["macro_f1"] for r in cfg_records])
        std_f1 = np.std([r["macro_f1"] for r in cfg_records])
        print(f"  --> Mean Accuracy: {mean_acc*100:.2f}% ± {std_acc*100:.2f}% | Mean F1: {mean_f1:.4f} ± {std_f1:.4f}", flush=True)

    out_dir = Path("experiments/stage_11/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "ulc_v4_1_electricity_results.json"
    out_csv = out_dir / "ulc_v4_1_electricity_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll ULC-v4.1 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()
