"""
Fine-Grained Controller Ablation Study for ULC-v1 to ULC-v3 Evolution.
Measures the isolated marginal delta of each bug fix and algorithmic component.
"""

import json
import os
import sys
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import (
    generate_stream,
    ParamWrapper,
    AdaptiveClassifier,
    LowMemoryAdamW,
    RobustLearningPipeline,
    AdaptiveLearningController,
    ControllerState,
    calculate_metrics
)

SEEDS = [42, 101, 2024, 7, 99]

def run_controller_ablation():
    print("================================================================================")
    print("SECTION 6: ULC IMPLEMENTATION AUDIT & STEP-BY-STEP ABLATION")
    print("================================================================================\n")
    
    stages = [
        "Stage_1_ULC_v1_Baseline",
        "Stage_2_Add_Replay_Purge_Fix",
        "Stage_3_Add_Tree_Adaptation",
        "Stage_4_Add_Optimizer_Momenta_Reset",
        "Stage_5_Full_ULC_v3_Ensemble"
    ]
    
    results = {st: [] for st in stages}
    
    for stage in stages:
        print(f"--> Evaluating Ablation Stage: {stage:35s} ...", end=" ", flush=True)
        t0 = time.time()
        
        for seed in SEEDS:
            stream_data = generate_stream(seed=seed, n_batches=50, batch_size=30, n_features=4)
            clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20,
                                     enable_drift_detection=True, random_state=seed)
            pipeline = RobustLearningPipeline(n_classes=2)
            p_wrapper = ParamWrapper(np.random.RandomState(seed).randn(4, 2) * 0.01)
            opt = LowMemoryAdamW([p_wrapper], lr=0.01)
            controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
            
            all_y_true = []
            all_y_pred = []
            all_y_prob = []
            latencies = []
            false_resets = 0
            
            for b_idx, batch in enumerate(stream_data, start=1):
                t_start = time.perf_counter()
                X_b = batch["X"]
                y_obs = batch["y_observed"]
                y_clean = batch["y_clean"]
                delta = batch["delta"]
                is_noise = batch["is_noise_burst"]
                
                # 1. Prediction Phase
                if stage == "Stage_5_Full_ULC_v3_Ensemble":
                    if clf.samples_seen_ > 0:
                        p_tree = clf.predict_proba(X_b)
                    else:
                        p_tree = np.zeros((len(X_b), 2)) + 0.5
                    logits_lin = X_b @ p_wrapper.data
                    p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
                    p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                    p_prob = 0.50 * p_tree + 0.50 * p_lin
                    p_pred = np.argmax(p_prob, axis=1)
                else:
                    if clf.samples_seen_ > 0:
                        p_pred = clf.predict(X_b)
                        p_prob = clf.predict_proba(X_b)
                    else:
                        p_pred = np.zeros(len(X_b), dtype=np.int64)
                        p_prob = np.zeros((len(X_b), 2)) + 0.5
                        
                if b_idx > 1:
                    all_y_true.extend(y_clean.tolist())
                    all_y_pred.extend(p_pred.tolist())
                    all_y_prob.extend(p_prob.tolist())
                    
                # 2. Controller Arbitration Phase
                logits_ulc = X_b @ p_wrapper.data
                probs_ulc = np.exp(logits_ulc - np.max(logits_ulc, axis=1, keepdims=True))
                probs_ulc /= np.sum(probs_ulc, axis=1, keepdims=True)
                
                if stage in ("Stage_4_Add_Optimizer_Momenta_Reset", "Stage_5_Full_ULC_v3_Ensemble"):
                    # Logit alignment with tree
                    if clf.samples_seen_ > 0:
                        logits_aligned = np.log(np.clip(clf.predict_proba(X_b), 1e-12, 1.0))
                    else:
                        logits_aligned = np.zeros((len(X_b), 2))
                    directive, info = controller.step(X_b, y_obs, logits=logits_aligned, delta_drift=delta)
                else:
                    directive, info = controller.step(X_b, y_obs, logits=logits_ulc, delta_drift=delta)
                    
                if is_noise and directive.state == ControllerState.CONFIRMED_DRIFT:
                    false_resets += 1
                    
                # Stage-specific intervention logic
                # Stage 2+: Fix replay buffer purge
                if stage in ("Stage_2_Add_Replay_Purge_Fix", "Stage_3_Add_Tree_Adaptation", 
                             "Stage_4_Add_Optimizer_Momenta_Reset", "Stage_5_Full_ULC_v3_Ensemble"):
                    if directive.purge_replay and hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                        clf._replay_buffer.clear()
                        
                # Stage 3+: Add tree reset on confirmed drift
                if stage in ("Stage_3_Add_Tree_Adaptation", "Stage_4_Add_Optimizer_Momenta_Reset", "Stage_5_Full_ULC_v3_Ensemble"):
                    if directive.state == ControllerState.CONFIRMED_DRIFT:
                        clf.reset()
                        
                # Stage 4+: Add optimizer state clearing on confirmed drift
                if stage in ("Stage_4_Add_Optimizer_Momenta_Reset", "Stage_5_Full_ULC_v3_Ensemble"):
                    if directive.state == ControllerState.CONFIRMED_DRIFT:
                        opt.state.clear()
                        
                # Linear optimizer update
                p_wrapper.grad = (X_b.T @ (probs_ulc - np.eye(2)[y_obs])) / len(y_obs)
                opt.step()
                
                latencies.append((time.perf_counter() - t_start) * 1000.0)
                
            metrics = calculate_metrics(np.array(all_y_true), np.array(all_y_pred), np.array(all_y_prob), latencies)
            metrics["false_resets"] = false_resets
            results[stage].append(metrics)
            
        print(f"Done in {time.time() - t0:.2f}s")
        
    print("\n--------------------------------------------------------------------------------")
    print("STEP-BY-STEP CONTROLLER ABLATION RESULTS (Mean across 5 Seeds):")
    print("--------------------------------------------------------------------------------")
    print(f"{'Stage':35s} | {'Accuracy':10s} | {'Macro F1':10s} | {'Min Recall':12s} | {'Brier':8s} | {'False Resets':12s}")
    print("-" * 95)
    
    summary = {}
    for stage in stages:
        acc = float(np.mean([r["accuracy"] for r in results[stage]]))
        mf1 = float(np.mean([r["macro_f1"] for r in results[stage]]))
        rec = float(np.mean([r["minority_recall"] for r in results[stage]]))
        brier = float(np.mean([r["brier_score"] for r in results[stage]]))
        f_res = float(np.mean([r["false_resets"] for r in results[stage]]))
        
        summary[stage] = {
            "accuracy": acc,
            "macro_f1": mf1,
            "minority_recall": rec,
            "brier_score": brier,
            "false_resets": f_res
        }
        print(f"{stage:35s} | {acc*100:9.2f}% | {mf1:10.4f} | {rec*100:11.2f}% | {brier:8.4f} | {f_res:12.1f}")
        
    out_file = "experiments/ulc_v3_independent_audit/controller_ablation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nAblation data saved to {out_file}")

if __name__ == "__main__":
    run_controller_ablation()

