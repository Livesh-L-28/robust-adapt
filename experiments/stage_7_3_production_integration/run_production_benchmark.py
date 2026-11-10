"""
Stage 7.3 Workstream I: Post-Integration Benchmark Reproduction.
===============================================================
Evaluates the production-promoted ULC-v4.1 (UnifiedLearningControllerV4_1)
against historical baselines (ULC-v1, v2, v3, v4) and the experimental candidate
(HybridMasterControllerV4_1) across the 5 canonical seeds:
    42, 123, 456, 789, 2024
and exploratory seeds:
    999, 101, 7.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.concept_memory import ConceptMemory
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4

from experiments.stage_7_ulc_v4.run_stage7_experiment import (
    SEEDS,
    BATCH_SIZE,
    N_FEATURES,
    LinearSurrogate,
    generate_stream,
)
from experiments.stage_7_1_ulc_v4_optimization.candidate_controllers import (
    HybridMasterControllerV4_1,
)

CANONICAL_SEEDS = [42, 123, 456, 789, 2024]
EXPLORATORY_SEEDS = [999, 101, 7]
ALL_SEEDS = CANONICAL_SEEDS + EXPLORATORY_SEEDS

MODELS = [
    "ULC-v1 Baseline",
    "ULC-v2 Baseline",
    "ULC-v3 Audited",
    "ULC-v4 Original",
    "ULC-v4.1 Candidate (Experimental)",
    "ULC-v4.1 Production (Integrated)",
]


def calculate_comprehensive_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate accuracy, balanced accuracy, macro F1, minority precision/recall, PR-AUC, Brier score, and ECE."""
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_pred, dtype=int)
    y_prob_1 = np.asarray(y_prob, dtype=float)

    acc = float(np.mean(y_t == y_p))

    # Confusion matrix
    tp = float(np.sum((y_t == 1) & (y_p == 1)))
    fp = float(np.sum((y_t == 0) & (y_p == 1)))
    fn = float(np.sum((y_t == 1) & (y_p == 0)))
    tn = float(np.sum((y_t == 0) & (y_p == 0)))

    recall_1 = tp / max(1.0, tp + fn)
    precision_1 = tp / max(1.0, tp + fp)
    f1_1 = 2 * (precision_1 * recall_1) / max(1e-12, precision_1 + recall_1)

    recall_0 = tn / max(1.0, tn + fp)
    precision_0 = tn / max(1.0, tn + fn)
    f1_0 = 2 * (precision_0 * recall_0) / max(1e-12, precision_0 + recall_0)

    balanced_acc = float(0.5 * (recall_0 + recall_1))
    macro_f1 = float(0.5 * (f1_0 + f1_1))

    # Brier score
    brier = float(np.mean((y_prob_1 - y_t) ** 2))

    # Simplified PR-AUC via numerical integration across 10 thresholds
    thresholds = np.linspace(0.0, 1.0, 11)
    precisions = []
    recalls = []
    for th in thresholds:
        pred_th = (y_prob_1 >= th).astype(int)
        th_tp = float(np.sum((y_t == 1) & (pred_th == 1)))
        th_fp = float(np.sum((y_t == 0) & (pred_th == 1)))
        th_fn = float(np.sum((y_t == 1) & (pred_th == 0)))
        precisions.append(th_tp / max(1.0, th_tp + th_fp))
        recalls.append(th_tp / max(1.0, th_tp + th_fn))
    # Order by recall ascending for trapezoidal integration
    sorted_indices = np.argsort(recalls)
    sorted_recalls = np.array(recalls)[sorted_indices]
    sorted_precisions = np.array(precisions)[sorted_indices]
    pr_auc = float(np.trapezoid(sorted_precisions, sorted_recalls)) if hasattr(np, "trapezoid") else float(np.trapz(sorted_precisions, sorted_recalls))

    # Expected Calibration Error (ECE) with 10 bins
    bin_boundaries = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for i in range(10):
        in_bin = (y_prob_1 >= bin_boundaries[i]) & (y_prob_1 < bin_boundaries[i + 1])
        prop_in_bin = float(np.mean(in_bin))
        if prop_in_bin > 0:
            accuracy_in_bin = float(np.mean(y_t[in_bin]))
            confidence_in_bin = float(np.mean(y_prob_1[in_bin]))
            ece += np.abs(accuracy_in_bin - confidence_in_bin) * prop_in_bin

    return {
        "accuracy": acc * 100.0,
        "balanced_accuracy": balanced_acc * 100.0,
        "macro_f1": macro_f1,
        "minority_precision": precision_1 * 100.0,
        "minority_recall": recall_1 * 100.0,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "ece": float(ece),
    }


def run_benchmark_trial(model_key: str, stream: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
    all_y_clean: List[int] = []
    all_y_pred: List[int] = []
    all_y_prob: List[float] = []
    total_drift_alarms = 0
    false_drift_resets = 0
    step_latencies_ms: List[float] = []

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
    opt = LowMemoryAdamW([surr], lr=0.01)

    if model_key == "ULC-v1 Baseline":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)
        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            t0 = time.perf_counter()
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            all_y_prob.extend(probs[:, 1])

            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elif model_key in ("ULC-v2 Baseline", "ULC-v3 Audited"):
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)
        purge_pol = "partial" if model_key == "ULC-v2 Baseline" else "selective"
        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            t0 = time.perf_counter()
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.purge_replay(policy=purge_pol, keep_minority=True)
                opt.reset_momenta()
            elif dir_res.state != ControllerState.NOISE_BURST:
                clf.partial_fit(X_b, y_obs)
            step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            all_y_prob.extend(probs[:, 1])

    elif model_key == "ULC-v4 Original":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
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
            t0 = time.perf_counter()
            probs = clf.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf.state_dict(), X_b, y_obs)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            thresh.update_from_priors(prior.priors)
            step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            all_y_prob.extend(probs[:, 1])

            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elif model_key == "ULC-v4.1 Candidate (Experimental)":
        clf_opt = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, tau_tie=0.10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf_opt.fit(init_X, init_y)
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
            t0 = time.perf_counter()
            probs = clf_opt.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf_opt.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf_opt.state_dict(), X_b, y_obs)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            all_y_prob.extend(probs[:, 1])

            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elif model_key == "ULC-v4.1 Production (Integrated)":
        clf_prod = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, tau_tie=0.10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf_prod.fit(init_X, init_y)
        prior = OnlineClassPriorTracker(n_classes=2)
        thresh = AdaptiveThresholdManager(n_classes=2, gamma=0.5)
        concept_mem = ConceptMemory(max_concepts=5)
        config = ULCv41Config(
            spatial_k=5,
            spatial_discordance_threshold=0.25,
            tau_tie=0.10,
            gamma_smoothing=0.50,
            generate_explanations=False,
        )
        ctrl = UnifiedLearningControllerV4_1(
            config=config,
            classifier=clf_prod,
            optimizer=opt,
            pipeline=RobustLearningPipeline(2),
            budget_manager=DynamicResourceBudgetManager(max_memory_mb=4096.0),
            prior_tracker=prior,
            threshold_manager=thresh,
            concept_memory=concept_mem,
        )
        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            t0 = time.perf_counter()
            probs = clf_prod.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf_prod.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf_prod.state_dict(), X_b, y_obs)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            all_y_prob.extend(probs[:, 1])

            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    metrics = calculate_comprehensive_metrics(np.array(all_y_clean), np.array(all_y_pred), np.array(all_y_prob))
    lat_arr = np.array(step_latencies_ms)

    return {
        "model": model_key,
        "seed": seed,
        "is_canonical": seed in CANONICAL_SEEDS,
        "accuracy": metrics["accuracy"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "macro_f1": metrics["macro_f1"],
        "minority_precision": metrics["minority_precision"],
        "minority_recall": metrics["minority_recall"],
        "pr_auc": metrics["pr_auc"],
        "brier_score": metrics["brier_score"],
        "ece": metrics["ece"],
        "drift_alarms": total_drift_alarms,
        "false_drift_resets": false_drift_resets,
        "mean_latency_ms": float(np.mean(lat_arr)),
        "p50_latency_ms": float(np.percentile(lat_arr, 50)),
        "p95_latency_ms": float(np.percentile(lat_arr, 95)),
        "p99_latency_ms": float(np.percentile(lat_arr, 99)),
        "throughput_samples_sec": float((len(all_y_clean) / (np.sum(lat_arr) / 1000.0))),
    }


def main() -> None:
    print("=" * 80)
    print("Executing Stage 7.3 Post-Integration Production Benchmark")
    print("=" * 80)

    raw_results: List[Dict[str, Any]] = []

    for seed in ALL_SEEDS:
        print(f"\n--- Generating synthetic benchmark stream for Seed {seed} ---")
        stream = generate_stream(seed=seed)

        for model_name in MODELS:
            res = run_benchmark_trial(model_name, stream, seed)
            raw_results.append(res)
            print(f"  [{model_name:<34}] Acc: {res['accuracy']:.2f}% | F1: {res['macro_f1']:.4f} | "
                  f"MinRec: {res['minority_recall']:.2f}% | FalseResets: {res['false_drift_resets']} | "
                  f"MeanLat: {res['mean_latency_ms']:.3f}ms")

    # Save JSON and CSV
    out_dir = Path("experiments/stage_7_3_production_integration")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "PRODUCTION_INTEGRATION_RESULTS.json"
    with open(json_path, "w") as f:
        json.dump(raw_results, f, indent=2)

    csv_path = out_dir / "PRODUCTION_INTEGRATION_RESULTS.csv"
    if raw_results:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(raw_results[0].keys()))
            writer.writeheader()
            writer.writerows(raw_results)

    print("\n" + "=" * 80)
    print("Benchmark Aggregation across 5 Canonical Seeds (42, 123, 456, 789, 2024):")
    print("=" * 80)

    canonical_res = [r for r in raw_results if r["is_canonical"]]
    for model_name in MODELS:
        m_runs = [r for r in canonical_res if r["model"] == model_name]
        accs = [r["accuracy"] for r in m_runs]
        f1s = [r["macro_f1"] for r in m_runs]
        recs = [r["minority_recall"] for r in m_runs]
        false_resets = [r["false_drift_resets"] for r in m_runs]
        lats = [r["mean_latency_ms"] for r in m_runs]
        p99s = [r["p99_latency_ms"] for r in m_runs]

        print(f"{model_name:<34} | Acc: {np.mean(accs):.2f}% +/- {np.std(accs):.2f}% | "
              f"F1: {np.mean(f1s):.4f} +/- {np.std(f1s):.4f} | "
              f"MinRec: {np.mean(recs):.2f}% +/- {np.std(recs):.2f}% | "
              f"F-Resets: {np.mean(false_resets):.1f} | Lat: {np.mean(lats):.3f}ms (P99: {np.mean(p99s):.3f}ms)")


if __name__ == "__main__":
    main()

