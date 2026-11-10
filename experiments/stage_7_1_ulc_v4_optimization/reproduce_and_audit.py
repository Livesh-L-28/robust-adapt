"""
Stage 7.1 Workstream A: Independent Baseline Reproduction and Execution Audit
=============================================================================
Reproduces the 13-model benchmark across the 5 canonical seeds (42, 123, 456, 789, 2024),
records detailed per-step diagnostic execution traces, and inspects identical configuration results.
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

# Ensure root on path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.concept_memory import ConceptMemory
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.rla.scorer import DensityAwareMarginScorer
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4
from experiments.stage_7_ulc_v4.run_stage7_experiment import (
    SEEDS,
    N_BATCHES,
    BATCH_SIZE,
    N_FEATURES,
    LinearSurrogate,
    generate_stream,
    calculate_prequential_metrics,
)


def run_and_trace_seed42() -> Dict[str, Any]:
    """Execute deep step-level tracing on Seed 42 to diagnose runtime behavior."""
    stream = generate_stream(seed=42)
    models = [
        "Static Baseline",
        "Pure Hoeffding Tree",
        "Standalone ADWIN (ALA 1.0)",
        "Standalone RLA (SCE + Margin)",
        "Standalone RAO (LowMemoryAdamW)",
        "Standalone Minority (Prior + Threshold)",
        "ALA + RLA",
        "ALA + RAO",
        "RLA + RAO",
        "ULC-v1 Baseline",
        "ULC-v2 Baseline",
        "ULC-v3 Audited",
        "ULC-v4 Master System",
    ]

    traces: Dict[str, List[Dict[str, Any]]] = {m: [] for m in models}

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    # Setup instances
    clf_adwin = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_adwin.fit(init_X, init_y)

    clf_rla = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=False, random_state=42)
    clf_rla.fit(init_X, init_y)
    scorer_rla = DensityAwareMarginScorer(n_classes=2)

    clf_ala_rla = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_ala_rla.fit(init_X, init_y)
    scorer_ala_rla = DensityAwareMarginScorer(n_classes=2)

    clf_ala_rao = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_ala_rao.fit(init_X, init_y)
    surr_ala_rao = LinearSurrogate(N_FEATURES, 2, seed=42)
    opt_ala_rao = LowMemoryAdamW([surr_ala_rao], lr=0.01)

    clf_v1 = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_v1.fit(init_X, init_y)
    ctrl_v1 = AdaptiveLearningController(classifier=clf_v1, pipeline=RobustLearningPipeline(n_classes=2), optimizer=LowMemoryAdamW([LinearSurrogate(N_FEATURES, 2, seed=42)], lr=0.01))

    clf_v2 = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_v2.fit(init_X, init_y)
    ctrl_v2 = AdaptiveLearningController(classifier=clf_v2, pipeline=RobustLearningPipeline(n_classes=2), optimizer=LowMemoryAdamW([LinearSurrogate(N_FEATURES, 2, seed=42)], lr=0.01))

    clf_v3 = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_v3.fit(init_X, init_y)
    ctrl_v3 = AdaptiveLearningController(classifier=clf_v3, pipeline=RobustLearningPipeline(n_classes=2), optimizer=LowMemoryAdamW([LinearSurrogate(N_FEATURES, 2, seed=42)], lr=0.01))

    clf_v4 = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=42)
    clf_v4.fit(init_X, init_y)
    surr_v4 = LinearSurrogate(N_FEATURES, 2, seed=42)
    opt_v4 = LowMemoryAdamW([surr_v4], lr=0.01)
    budget_v4 = DynamicResourceBudgetManager(max_memory_mb=4096.0)
    prior_v4 = OnlineClassPriorTracker(n_classes=2)
    thresh_v4 = AdaptiveThresholdManager(n_classes=2)
    concept_v4 = ConceptMemory(max_concepts=5)
    ctrl_v4 = UnifiedLearningControllerV4(
        classifier=clf_v4,
        optimizer=opt_v4,
        pipeline=RobustLearningPipeline(n_classes=2),
        budget_manager=budget_v4,
        prior_tracker=prior_v4,
        threshold_manager=thresh_v4,
        concept_memory=concept_v4,
    )

    for b_idx, batch in enumerate(stream[3:], start=4):
        X_b = batch["X"]
        y_obs = batch["y_observed"]
        y_clean = batch["y_clean"]
        delta = batch["delta"]
        is_noise = batch["is_noise"]
        is_true_drift = batch["is_true_drift"]

        # 1. Standalone RLA
        p_rla = clf_rla.predict_proba(X_b)
        pred_rla = clf_rla.predict(X_b)
        logits_rla = np.log(np.clip(p_rla, 1e-12, 1.0))
        w_rla = scorer_rla.score_samples(X_b, logits_rla, y_obs)
        clf_rla.partial_fit(X_b, y_obs, sample_weight=w_rla)
        traces["Standalone RLA (SCE + Margin)"].append({
            "batch": b_idx, "acc": float(np.mean(pred_rla == y_clean)), "mean_w": float(np.mean(w_rla))
        })

        # 2. ALA + RLA
        p_ar = clf_ala_rla.predict_proba(X_b)
        pred_ar = clf_ala_rla.predict(X_b)
        logits_ar = np.log(np.clip(p_ar, 1e-12, 1.0))
        w_ar = scorer_ala_rla.score_samples(X_b, logits_ar, y_obs)
        mean_w_ar = float(np.mean(w_ar))
        reset_triggered_ar = (delta >= 1.0 and mean_w_ar >= 0.70)
        if reset_triggered_ar:
            clf_ala_rla.reset()
            clf_ala_rla.fit(X_b, y_obs, sample_weight=w_ar)
        else:
            clf_ala_rla.partial_fit(X_b, y_obs, sample_weight=w_ar)
        traces["ALA + RLA"].append({
            "batch": b_idx, "acc": float(np.mean(pred_ar == y_clean)), "mean_w": mean_w_ar, "reset_triggered": reset_triggered_ar
        })

        # 3. ULC-v2
        p_v2 = clf_v2.predict_proba(X_b)
        pred_v2 = np.argmax(p_v2, axis=1)
        dir_v2, info_v2 = ctrl_v2.step(X_b, y_obs, logits=np.log(np.clip(p_v2, 1e-12, 1.0)), delta_drift=delta)
        traces["ULC-v2 Baseline"].append({
            "batch": b_idx, "acc": float(np.mean(pred_v2 == y_clean)), "state": dir_v2.state.name, "delta": delta
        })

        # 4. ULC-v3
        p_v3 = clf_v3.predict_proba(X_b)
        pred_v3 = np.argmax(p_v3, axis=1)
        dir_v3, info_v3 = ctrl_v3.step(X_b, y_obs, logits=np.log(np.clip(p_v3, 1e-12, 1.0)), delta_drift=delta)
        traces["ULC-v3 Audited"].append({
            "batch": b_idx, "acc": float(np.mean(pred_v3 == y_clean)), "state": dir_v3.state.name, "delta": delta
        })

        # 5. ULC-v4
        p_v4 = clf_v4.predict_proba(X_b)
        thresh_val = thresh_v4.primary_threshold
        pred_v4 = (p_v4[:, 1] >= thresh_val).astype(int)
        if b_idx == 15:
            concept_v4.store_concept("concept_0", clf_v4.state_dict(), X_b, y_obs)
        elif b_idx == 35:
            concept_v4.store_concept("concept_1", clf_v4.state_dict(), X_b, y_obs)
        dir_v4, info_v4 = ctrl_v4.step(X_b, y_obs, logits=np.log(np.clip(p_v4, 1e-12, 1.0)), delta_drift=delta)
        thresh_v4.update_from_priors(prior_v4.priors)
        traces["ULC-v4 Master System"].append({
            "batch": b_idx,
            "acc": float(np.mean(pred_v4 == y_clean)),
            "state": dir_v4.state.value,
            "delta": delta,
            "threshold": float(thresh_val),
            "priors": prior_v4.priors.tolist(),
            "mean_rel": info_v4["mean_reliability"],
            "pred_min_count": int(np.sum(pred_v4 == 1)),
            "true_min_count": int(np.sum(y_clean == 1)),
            "entropy": info_v4["evidence"]["predictive_entropy"],
        })

    return traces


def main() -> None:
    print("================================================================================")
    print("STAGE 7.1: INDEPENDENT BASELINE REPRODUCTION & EXECUTION AUDIT")
    print("================================================================================\n")

    out_dir = Path(__file__).resolve().parent
    from experiments.stage_7_ulc_v4.run_stage7_experiment import run_single_model

    models = [
        "Static Baseline",
        "Pure Hoeffding Tree",
        "Standalone ADWIN (ALA 1.0)",
        "Standalone RLA (SCE + Margin)",
        "Standalone RAO (LowMemoryAdamW)",
        "Standalone Minority (Prior + Threshold)",
        "ALA + RLA",
        "ALA + RAO",
        "RLA + RAO",
        "ULC-v1 Baseline",
        "ULC-v2 Baseline",
        "ULC-v3 Audited",
        "ULC-v4 Master System",
    ]

    all_raw_results: List[Dict[str, Any]] = []

    for seed in SEEDS:
        print(f"Reproducing Seed {seed}...")
        stream = generate_stream(seed=seed)
        for m in models:
            res = run_single_model(m, stream, seed)
            all_raw_results.append(res)

    # Save reproduced raw results
    json_path = out_dir / "BASELINE_RAW_RESULTS.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_raw_results, f, indent=2)

    csv_path = out_dir / "BASELINE_RAW_RESULTS.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "model", "accuracy", "macro_f1", "minority_recall", "drift_alarms", "false_drift_resets", "throughput", "latency_ms"])
        for r in all_raw_results:
            writer.writerow([r["seed"], r["model"], f"{r['accuracy']:.2f}", f"{r['macro_f1']:.4f}", f"{r['minority_recall']:.2f}", r["drift_alarms"], r["false_drift_resets"], f"{r['throughput']:.1f}", f"{r['latency_ms']:.3f}"])

    print(f"Saved reproduced baseline to {json_path} and {csv_path}")

    # Deep trace on Seed 42
    print("\nTracing Seed 42 execution behaviors...")
    traces = run_and_trace_seed42()
    trace_path = out_dir / "SEED_42_DETAILED_TRACE.json"
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2)

    print(f"Saved Seed 42 trace to {trace_path}")


if __name__ == "__main__":
    main()

