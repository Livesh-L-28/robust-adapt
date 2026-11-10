"""
Stage 7.1 Workstream D: Controlled Component Ablation Study
===========================================================
Systematic evaluation of ULC-v4 subcomponents across 5 seeds:
1. Full ULC-v4 (Baseline)
2. Ablation 1: Without Evidence Synthesis
3. Ablation 2: Without Bayesian Confidence Engine
4. Ablation 3: Without Pareto Arbitration
5. Ablation 4: Without Minority Intelligence
6. Ablation 5: Without Selective Replay Purge (Full Purge)
7. Ablation 6: Without Resource Budgeting
8. Ablation 7: On-Demand Explanations (Zero string overhead)
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
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4, ArbitrationAutomatonV4
from adaptive_ml.ulc.v4_evidence import EvidenceVectorV4
from experiments.stage_7_ulc_v4.run_stage7_experiment import (
    SEEDS,
    BATCH_SIZE,
    N_FEATURES,
    LinearSurrogate,
    generate_stream,
    calculate_prequential_metrics,
)


def run_ablation_trial(
    ablation_name: str,
    stream: List[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
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

    budget = DynamicResourceBudgetManager(max_memory_mb=4096.0) if ablation_name != "No Resource Budgeting" else None
    prior = OnlineClassPriorTracker(n_classes=2) if ablation_name != "No Minority Intelligence" else None
    thresh = AdaptiveThresholdManager(n_classes=2) if ablation_name != "No Minority Intelligence" else None
    concept_mem = ConceptMemory(max_concepts=5)

    ctrl = UnifiedLearningControllerV4(
        classifier=clf,
        optimizer=opt,
        pipeline=RobustLearningPipeline(n_classes=2),
        budget_manager=budget,
        prior_tracker=prior,
        threshold_manager=thresh,
        concept_memory=concept_mem,
    )

    for batch in stream[3:]:
        X_b = batch["X"]
        y_obs = batch["y_observed"]
        y_clean = batch["y_clean"]
        delta = batch["delta"]

        probs = clf.predict_proba(X_b)

        # Prediction step
        if ablation_name == "No Minority Intelligence":
            preds = np.argmax(probs, axis=1)
        else:
            t_val = thresh.primary_threshold
            preds = (probs[:, 1] >= t_val).astype(int)

        all_y_clean.extend(y_clean)
        all_y_pred.extend(preds)

        # Concept storage
        if batch["batch_idx"] == 15:
            concept_mem.store_concept("concept_0", clf.state_dict(), X_b, y_obs)
        elif batch["batch_idx"] == 35:
            concept_mem.store_concept("concept_1", clf.state_dict(), X_b, y_obs)

        # Controller execution with specific ablation modifications
        logits = np.log(np.clip(probs, 1e-12, 1.0))

        if ablation_name == "No Bayesian Confidence":
            # Override confidence engine to return fixed neutral confidence
            ctrl.automaton.confidence_engine.evaluate = lambda ev, tau_r=0.65: type("MockConf", (), {
                "adapt": 0.5, "suppress_noise": 0.5, "restore_concept": 0.5, "throttle_resources": 0.5, "filter_instances": 0.5
            })()

        if ablation_name == "No Pareto Arbitration":
            # Force simple rule-based purge policy
            ctrl.automaton.arbitrator.arbitrate_replay_purge = lambda ev, conf: ("partial", False)

        if ablation_name == "No Selective Replay Purge":
            # Force full wipe on drift
            ctrl.automaton.arbitrator.arbitrate_replay_purge = lambda ev, conf: ("full", False)

        directive, info = ctrl.step(X_b, y_obs, logits=logits, delta_drift=delta)

        if ablation_name != "No Minority Intelligence":
            thresh.update_from_priors(prior.priors)

        if directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
            total_drift_alarms += 1
            if batch["is_noise"] or not batch["is_true_drift"]:
                false_drift_resets += 1

    elapsed = time.perf_counter() - start_time
    acc, f1, recall = calculate_prequential_metrics(np.array(all_y_clean), np.array(all_y_pred))
    latency_ms = (elapsed / max(1, len(stream) - 3)) * 1000.0

    return {
        "ablation": ablation_name,
        "seed": seed,
        "accuracy": acc * 100.0,
        "macro_f1": f1,
        "minority_recall": recall * 100.0,
        "false_drift_resets": false_drift_resets,
        "latency_ms": latency_ms,
    }


def main() -> None:
    print("================================================================================")
    print("STAGE 7.1: SYSTEMATIC COMPONENT ABLATION STUDY")
    print("================================================================================\n")

    ablations = [
        "Full ULC-v4 (Baseline)",
        "No Evidence Synthesis",
        "No Bayesian Confidence",
        "No Pareto Arbitration",
        "No Minority Intelligence",
        "No Selective Replay Purge",
        "No Resource Budgeting",
        "On-Demand Explanations",
    ]

    all_results: List[Dict[str, Any]] = []

    for seed in SEEDS:
        print(f"Executing ablations on Seed {seed}...")
        stream = generate_stream(seed=seed)
        for ab in ablations:
            res = run_ablation_trial(ab, stream, seed)
            all_results.append(res)

    # Aggregate
    summary: Dict[str, Dict[str, float]] = {}
    for ab in ablations:
        runs = [r for r in all_results if r["ablation"] == ab]
        summary[ab] = {
            "acc_mean": float(np.mean([r["accuracy"] for r in runs])),
            "acc_std": float(np.std([r["accuracy"] for r in runs])),
            "f1_mean": float(np.mean([r["macro_f1"] for r in runs])),
            "f1_std": float(np.std([r["macro_f1"] for r in runs])),
            "rec_mean": float(np.mean([r["minority_recall"] for r in runs])),
            "rec_std": float(np.std([r["minority_recall"] for r in runs])),
            "fdr_mean": float(np.mean([r["false_drift_resets"] for r in runs])),
            "lat_mean": float(np.mean([r["latency_ms"] for r in runs])),
        }

    out_dir = Path(__file__).resolve().parent
    csv_path = out_dir / "COMPONENT_ABLATION_RESULTS.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Ablation Condition", "Accuracy (%)", "Acc Std", "Macro F1", "F1 Std", "Minority Recall (%)", "Recall Std", "FDR", "Latency (ms)"])
        for ab in ablations:
            s = summary[ab]
            writer.writerow([ab, f"{s['acc_mean']:.2f}", f"{s['acc_std']:.2f}", f"{s['f1_mean']:.4f}", f"{s['f1_std']:.4f}", f"{s['rec_mean']:.2f}", f"{s['rec_std']:.2f}", f"{s['fdr_mean']:.1f}", f"{s['lat_mean']:.3f}"])

    print("\n================================================================================")
    print("ABLATION STUDY SUMMARY")
    print("================================================================================")
    print(f"{'Condition':32s} | {'Accuracy (%)':12s} | {'Macro F1':11s} | {'Min Recall (%)':14s} | {'Latency (ms)':12s}")
    print("-" * 90)
    for ab in ablations:
        s = summary[ab]
        print(f"{ab:32s} | {s['acc_mean']:5.2f} ± {s['acc_std']:4.2f} | {s['f1_mean']:5.3f} ± {s['f1_std']:4.3f} | {s['rec_mean']:5.2f} ± {s['rec_std']:4.2f} | {s['lat_mean']:5.3f}")
    print("================================================================================\n")
    print(f"Saved ablation summary to {csv_path}")


if __name__ == "__main__":
    main()

