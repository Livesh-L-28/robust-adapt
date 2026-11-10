"""
Stage 7.2 Workstream A: Independent Baseline & ULC-v4.1 Reproduction Experiment
================================================================================
Independently validates and reproduces:
1. Static Baseline
2. ULC-v1
3. ULC-v2
4. ULC-v3
5. ULC-v4 Original
6. ULC-v4.1 Hybrid

Evaluated across:
- Canonical Seeds: 42, 123, 456, 789, 2024
- Exploratory Seeds: 999, 101, 7
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.concept_memory import ConceptMemory
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4

from experiments.stage_7_ulc_v4.run_stage7_experiment import (
    SEEDS as CANONICAL_SEEDS,
    BATCH_SIZE,
    N_FEATURES,
    LinearSurrogate,
    generate_stream,
    calculate_prequential_metrics,
)
from experiments.stage_7_1_ulc_v4_optimization.candidate_controllers import HybridMasterControllerV4_1

EXPLORATORY_SEEDS = [999, 101, 7]
ALL_SEEDS = CANONICAL_SEEDS + EXPLORATORY_SEEDS

MODELS = [
    "Static Baseline",
    "ULC-v1 Baseline",
    "ULC-v2 Baseline",
    "ULC-v3 Audited",
    "ULC-v4 Original",
    "ULC-v4.1 Hybrid",
]


def run_model_trial(model_name: str, stream: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
    all_y_clean: List[int] = []
    all_y_pred: List[int] = []
    all_probas: List[List[float]] = []
    interventions: List[Dict[str, Any]] = []
    total_drift_alarms = 0
    false_drift_resets = 0

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    start_time = time.perf_counter()

    if model_name == "Static Baseline":
        clf = AdaptiveClassifier(
            n_features=N_FEATURES,
            n_classes=2,
            grace_period=10,
            enable_drift_detection=False,
            random_state=seed,
        )
        clf.fit(init_X, init_y)
        for batch in stream[3:]:
            X_b, y_clean = batch["X"], batch["y_clean"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean.tolist())
            all_y_pred.extend(preds.tolist())
            all_probas.extend(probs.tolist())

    elif model_name == "ULC-v1 Baseline":
        clf = AdaptiveClassifier(
            n_features=N_FEATURES,
            n_classes=2,
            grace_period=10,
            replay_capacity=100,
            enable_drift_detection=True,
            random_state=seed,
        )
        clf.fit(init_X, init_y)
        surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surr], lr=0.01)
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean.tolist())
            all_y_pred.extend(preds.tolist())
            all_probas.extend(probs.tolist())

            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
            interventions.append({
                "batch": batch["batch_idx"],
                "state": dir_res.state.value if hasattr(dir_res.state, "value") else str(dir_res.state),
            })

    elif model_name in ("ULC-v2 Baseline", "ULC-v3 Audited"):
        clf = AdaptiveClassifier(
            n_features=N_FEATURES,
            n_classes=2,
            grace_period=10,
            replay_capacity=100,
            enable_drift_detection=True,
            random_state=seed,
        )
        clf.fit(init_X, init_y)
        surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surr], lr=0.01)
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)
        purge_pol = "partial" if model_name == "ULC-v2 Baseline" else "selective"

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean.tolist())
            all_y_pred.extend(preds.tolist())
            all_probas.extend(probs.tolist())

            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.purge_replay(policy=purge_pol, keep_minority=True)
                opt.reset_momenta()
            elif dir_res.state != ControllerState.NOISE_BURST:
                clf.partial_fit(X_b, y_obs)

            interventions.append({
                "batch": batch["batch_idx"],
                "state": dir_res.state.value if hasattr(dir_res.state, "value") else str(dir_res.state),
            })

    elif model_name == "ULC-v4 Original":
        clf = AdaptiveClassifier(
            n_features=N_FEATURES,
            n_classes=2,
            grace_period=10,
            replay_capacity=100,
            enable_drift_detection=True,
            random_state=seed,
        )
        clf.fit(init_X, init_y)
        surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surr], lr=0.01)
        prior = OnlineClassPriorTracker(n_classes=2)
        thresh = AdaptiveThresholdManager(n_classes=2)
        concept_mem = ConceptMemory(max_concepts=5)

        ctrl = UnifiedLearningControllerV4(
            classifier=clf,
            optimizer=opt,
            pipeline=RobustLearningPipeline(2),
            budget_manager=DynamicResourceBudgetManager(max_memory_mb=4096.0),
            prior_tracker=prior,
            threshold_manager=thresh,
            concept_memory=concept_mem,
        )

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            all_y_clean.extend(y_clean.tolist())
            all_y_pred.extend(preds.tolist())
            all_probas.extend(probs.tolist())

            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf.state_dict(), X_b, y_obs)

            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            thresh.update_from_priors(prior.priors)

            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

            interventions.append({
                "batch": batch["batch_idx"],
                "state": dir_res.state.value if hasattr(dir_res.state, "value") else str(dir_res.state),
                "threshold": float(thresh_val),
            })

    elif model_name == "ULC-v4.1 Hybrid":
        clf_opt = AdaptiveClassifier(
            n_features=N_FEATURES,
            n_classes=2,
            grace_period=10,
            tau_tie=0.10,
            replay_capacity=100,
            enable_drift_detection=True,
            random_state=seed,
        )
        clf_opt.fit(init_X, init_y)
        surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surr], lr=0.01)
        prior = OnlineClassPriorTracker(n_classes=2)
        thresh = AdaptiveThresholdManager(n_classes=2, gamma=0.5)
        concept_mem = ConceptMemory(max_concepts=5)

        ctrl = HybridMasterControllerV4_1(
            classifier=clf_opt,
            optimizer=opt,
            pipeline=RobustLearningPipeline(2),
            budget_manager=DynamicResourceBudgetManager(max_memory_mb=4096.0),
            prior_tracker=prior,
            threshold_manager=thresh,
            concept_memory=concept_mem,
            generate_explanations=False,
        )

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf_opt.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            all_y_clean.extend(y_clean.tolist())
            all_y_pred.extend(preds.tolist())
            all_probas.extend(probs.tolist())

            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf_opt.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf_opt.state_dict(), X_b, y_obs)

            dir_res, telemetry = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)

            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

            interventions.append({
                "batch": batch["batch_idx"],
                "state": dir_res.state.value if hasattr(dir_res.state, "value") else str(dir_res.state),
                "threshold": float(thresh_val),
                "spatial_discordance": float(telemetry.get("spatial_discordance", 0.0)),
            })

    elapsed = time.perf_counter() - start_time
    y_true_arr = np.array(all_y_clean)
    y_pred_arr = np.array(all_y_pred)

    acc, macro_f1, recall_min = calculate_prequential_metrics(y_true_arr, y_pred_arr)

    # Granular class metrics
    tp = int(np.sum((y_true_arr == 1) & (y_pred_arr == 1)))
    fp = int(np.sum((y_true_arr == 0) & (y_pred_arr == 1)))
    fn = int(np.sum((y_true_arr == 1) & (y_pred_arr == 0)))
    tn = int(np.sum((y_true_arr == 0) & (y_pred_arr == 0)))
    prec_min = float(tp / max(1, (tp + fp)))
    fpr = float(fp / max(1, (fp + tn)))
    fnr = float(fn / max(1, (fn + tp)))
    latency_ms = (elapsed / max(1, len(stream) - 3)) * 1000.0

    return {
        "model": model_name,
        "seed": seed,
        "seed_type": "canonical" if seed in CANONICAL_SEEDS else "exploratory",
        "accuracy": acc * 100.0,
        "macro_f1": macro_f1,
        "minority_recall": recall_min * 100.0,
        "minority_precision": prec_min * 100.0,
        "fpr": fpr * 100.0,
        "fnr": fnr * 100.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "drift_alarms": total_drift_alarms,
        "false_drift_resets": false_drift_resets,
        "latency_ms": latency_ms,
        "raw_predictions": all_y_pred,
        "raw_clean_labels": all_y_clean,
        "interventions": interventions,
    }


def main() -> None:
    print("=" * 80)
    print("STAGE 7.2 WORKSTREAM A: INDEPENDENT REPRODUCTION BENCHMARK")
    print("=" * 80)

    out_dir = Path(__file__).resolve().parent
    raw_results: List[Dict[str, Any]] = []

    # Run Canonical Seeds
    print("\n--- Running Confirmatory Trials (Canonical 5 Seeds) ---")
    for seed in CANONICAL_SEEDS:
        stream = generate_stream(seed=seed)
        for m in MODELS:
            res = run_model_trial(m, stream, seed)
            raw_results.append(res)
            print(
                f"  [Canonical Seed {seed:4d}] {m:20s} | "
                f"Acc: {res['accuracy']:5.2f}% | F1: {res['macro_f1']:5.3f} | "
                f"MinRec: {res['minority_recall']:5.2f}% | MinPrec: {res['minority_precision']:5.2f}% | "
                f"FDR: {res['false_drift_resets']:1d} | Lat: {res['latency_ms']:5.3f} ms"
            )

    # Run Exploratory Seeds
    print("\n--- Running Exploratory Trials (Seeds 999, 101, 7) ---")
    for seed in EXPLORATORY_SEEDS:
        stream = generate_stream(seed=seed)
        for m in MODELS:
            res = run_model_trial(m, stream, seed)
            raw_results.append(res)
            print(
                f"  [Exploratory Seed {seed:4d}] {m:20s} | "
                f"Acc: {res['accuracy']:5.2f}% | F1: {res['macro_f1']:5.3f} | "
                f"MinRec: {res['minority_recall']:5.2f}% | MinPrec: {res['minority_precision']:5.2f}% | "
                f"FDR: {res['false_drift_resets']:1d} | Lat: {res['latency_ms']:5.3f} ms"
            )

    # Save RAW_REPRODUCTION_RESULTS.json (compact summary to keep size bounded)
    json_path = out_dir / "RAW_REPRODUCTION_RESULTS.json"
    with open(json_path, "w", encoding="utf-8") as f:
        # Exclude massive raw arrays for the main json or include compact version
        serializable = []
        for r in raw_results:
            c = dict(r)
            # keep first 30 raw predictions for inspection
            c["raw_predictions_sample"] = c.pop("raw_predictions")[:30]
            c["raw_clean_labels_sample"] = c.pop("raw_clean_labels")[:30]
            serializable.append(c)
        json.dump(serializable, f, indent=2)
    print(f"\nSaved raw JSON to {json_path}")

    # Save RAW_REPRODUCTION_RESULTS.csv
    csv_path = out_dir / "RAW_REPRODUCTION_RESULTS.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Model", "Seed", "SeedType", "Accuracy (%)", "Macro F1",
            "Minority Recall (%)", "Minority Precision (%)", "FPR (%)", "FNR (%)",
            "TP", "FP", "FN", "TN", "Drift Alarms", "False Drift Resets", "Step Latency (ms)"
        ])
        for r in raw_results:
            writer.writerow([
                r["model"], r["seed"], r["seed_type"],
                f"{r['accuracy']:.2f}", f"{r['macro_f1']:.4f}",
                f"{r['minority_recall']:.2f}", f"{r['minority_precision']:.2f}",
                f"{r['fpr']:.2f}", f"{r['fnr']:.2f}",
                r["tp"], r["fp"], r["fn"], r["tn"],
                r["drift_alarms"], r["false_drift_resets"],
                f"{r['latency_ms']:.4f}",
            ])
    print(f"Saved raw CSV to {csv_path}")


if __name__ == "__main__":
    main()

