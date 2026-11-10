"""
Stage 7.1 Workstream F: Benchmark Evaluation of ULC-v4 Optimization Candidates
=============================================================================
Evaluates Candidates against historical ULC baselines (v1, v2, v3, v4) across
the 5 canonical seeds (42, 123, 456, 789, 2024) plus exploratory seeds (999, 101, 7).
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List
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
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4

from experiments.stage_7_ulc_v4.run_stage7_experiment import (
    SEEDS,
    BATCH_SIZE,
    N_FEATURES,
    LinearSurrogate,
    generate_stream,
    calculate_prequential_metrics,
)
from experiments.stage_7_1_ulc_v4_optimization.candidate_controllers import (
    HybridMasterControllerV4_1,
    Candidate5_ConflictResolver,
    Candidate2_AdaptiveConfidence,
    Candidate1_LightweightEvidence,
)

ALL_SEEDS = SEEDS + [999, 101, 7]


def run_model_on_stream(model_key: str, stream: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
    all_y_clean = []
    all_y_pred = []
    total_drift_alarms = 0
    false_drift_resets = 0
    start_time = time.perf_counter()

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
    clf.fit(init_X, init_y)
    surr = LinearSurrogate(N_FEATURES, 2, seed=seed)
    opt = LowMemoryAdamW([surr], lr=0.01)

    if model_key == "ULC-v1 Baseline":
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)
        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elif model_key in ("ULC-v2 Baseline", "ULC-v3 Audited"):
        ctrl = AdaptiveLearningController(classifier=clf, pipeline=RobustLearningPipeline(2), optimizer=opt)
        purge_pol = "partial" if model_key == "ULC-v2 Baseline" else "selective"
        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.purge_replay(policy=purge_pol, keep_minority=True)
                opt.reset_momenta()
            elif dir_res.state != ControllerState.NOISE_BURST:
                clf.partial_fit(X_b, y_obs)

    elif model_key == "ULC-v4 Original":
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
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
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

    elif model_key == "ULC-v4.1 Hybrid (Optimized)":
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
            probs = clf_opt.predict_proba(X_b)
            thresh_val = thresh.primary_threshold
            preds = (probs[:, 1] >= thresh_val).astype(int)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            if batch["batch_idx"] == 15:
                concept_mem.store_concept("concept_0", clf_opt.state_dict(), X_b, y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept("concept_1", clf_opt.state_dict(), X_b, y_obs)
            dir_res, _ = ctrl.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if dir_res.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elapsed = time.perf_counter() - start_time
    acc, f1, recall = calculate_prequential_metrics(np.array(all_y_clean), np.array(all_y_pred))
    latency_ms = (elapsed / max(1, len(stream) - 3)) * 1000.0

    return {
        "model": model_key,
        "seed": seed,
        "accuracy": acc * 100.0,
        "macro_f1": f1,
        "minority_recall": recall * 100.0,
        "drift_alarms": total_drift_alarms,
        "false_drift_resets": false_drift_resets,
        "latency_ms": latency_ms,
    }


def main() -> None:
    print("================================================================================")
    print("STAGE 7.1 WORKSTREAM F: CANDIDATE OPTIMIZATION BENCHMARK")
    print("================================================================================\n")

    models = [
        "ULC-v1 Baseline",
        "ULC-v2 Baseline",
        "ULC-v3 Audited",
        "ULC-v4 Original",
        "ULC-v4.1 Hybrid (Optimized)",
    ]

    # 1. Confirmatory 5 Seeds
    print("--- Running Confirmatory Trials (Canonical 5 Seeds) ---")
    confirmatory_results: List[Dict[str, Any]] = []
    for seed in SEEDS:
        stream = generate_stream(seed=seed)
        for m in models:
            res = run_model_on_stream(m, stream, seed)
            confirmatory_results.append(res)
            print(f"  [Seed {seed:4d}] {m:28s} | Acc: {res['accuracy']:5.2f}% | F1: {res['macro_f1']:5.3f} | MinRec: {res['minority_recall']:5.2f}% | FDR: {res['false_drift_resets']}")

    # 2. Exploratory Additional Seeds
    print("\n--- Running Exploratory Trials (Seeds 999, 101, 7) ---")
    exploratory_results: List[Dict[str, Any]] = []
    for seed in [999, 101, 7]:
        stream = generate_stream(seed=seed)
        for m in models:
            res = run_model_on_stream(m, stream, seed)
            exploratory_results.append(res)
            print(f"  [Seed {seed:4d}] {m:28s} | Acc: {res['accuracy']:5.2f}% | F1: {res['macro_f1']:5.3f} | MinRec: {res['minority_recall']:5.2f}% | FDR: {res['false_drift_resets']}")

    # Save comparison CSV across canonical seeds
    out_dir = Path(__file__).resolve().parent
    csv_path = out_dir / "ULC_GENERATION_COMPARISON.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "Accuracy (%)", "Acc Std", "Macro F1", "F1 Std", "Minority Recall (%)", "Recall Std", "Drift Alarms", "False Drift Resets", "Step Latency (ms)"])
        for m in models:
            m_runs = [r for r in confirmatory_results if r["model"] == m]
            writer.writerow([
                m,
                f"{np.mean([r['accuracy'] for r in m_runs]):.2f}",
                f"{np.std([r['accuracy'] for r in m_runs]):.2f}",
                f"{np.mean([r['macro_f1'] for r in m_runs]):.4f}",
                f"{np.std([r['macro_f1'] for r in m_runs]):.4f}",
                f"{np.mean([r['minority_recall'] for r in m_runs]):.2f}",
                f"{np.std([r['minority_recall'] for r in m_runs]):.2f}",
                f"{np.mean([r['drift_alarms'] for r in m_runs]):.1f}",
                f"{np.mean([r['false_drift_resets'] for r in m_runs]):.1f}",
                f"{np.mean([r['latency_ms'] for r in m_runs]):.3f}",
            ])

    print("\n================================================================================")
    print("CONFIRMATORY 5-SEED COMPARISON SCORECARD")
    print("================================================================================")
    print(f"{'Model':28s} | {'Accuracy (%)':14s} | {'Macro F1':13s} | {'Min Recall (%)':15s} | {'FDR':5s} | {'Latency (ms)':12s}")
    print("-" * 96)
    for m in models:
        m_runs = [r for r in confirmatory_results if r["model"] == m]
        acc_m, acc_s = np.mean([r['accuracy'] for r in m_runs]), np.std([r['accuracy'] for r in m_runs])
        f1_m, f1_s = np.mean([r['macro_f1'] for r in m_runs]), np.std([r['macro_f1'] for r in m_runs])
        rec_m, rec_s = np.mean([r['minority_recall'] for r in m_runs]), np.std([r['minority_recall'] for r in m_runs])
        fdr_m = np.mean([r['false_drift_resets'] for r in m_runs])
        lat_m = np.mean([r['latency_ms'] for r in m_runs])
        print(f"{m:28s} | {acc_m:5.2f} ± {acc_s:4.2f}  | {f1_m:5.3f} ± {f1_s:4.3f} | {rec_m:5.2f} ± {rec_s:4.2f}   | {fdr_m:4.1f} | {lat_m:5.3f}")
    print("================================================================================\n")
    print(f"Results saved to {csv_path}")


if __name__ == "__main__":
    main()
