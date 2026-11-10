"""
Workstream E: ULC Implementation and Causal Ablation Audit Script.
Generates state transition matrices, extracts full runtime execution traces,
executes 6 causal ablations, and generates ULC architectural figures.
"""

import csv
import json
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

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

def execute_ulc_audit():
    print("================================================================================")
    print("WORKSTREAM E: ULC IMPLEMENTATION & CAUSAL ABLATION AUDIT")
    print("================================================================================\n")
    
    # 1. Trace Runtime Execution on Seed 42
    stream = generate_stream(seed=42, n_batches=50, batch_size=30, n_features=4)
    clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20,
                             enable_drift_detection=True, random_state=42)
    pipeline = RobustLearningPipeline(n_classes=2)
    p_wrapper = ParamWrapper(np.random.RandomState(42).randn(4, 2) * 0.01)
    opt = LowMemoryAdamW([p_wrapper], lr=0.01)
    controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
    
    runtime_trace = []
    state_transitions = []
    prev_state = "STABLE"
    
    states_list = ["STABLE", "DRIFT_SUSPECTED", "CONFIRMED_DRIFT", "RECOVERY", "NOISE_BURST"]
    trans_counts = {s1: {s2: 0 for s2 in states_list} for s1 in states_list}
    
    for b_idx, batch in enumerate(stream, start=1):
        X_b = batch["X"]
        y_obs = batch["y_observed"]
        y_clean = batch["y_clean"]
        delta = batch["delta"]
        is_noise = batch["is_noise_burst"]
        
        if clf.samples_seen_ > 0:
            probs_clf = clf.predict_proba(X_b)
            logits_aligned = np.log(np.clip(probs_clf, 1e-12, 1.0))
        else:
            logits_aligned = np.zeros((len(X_b), 2))
            
        directive, info = controller.step(X_b, y_obs, logits=logits_aligned, delta_drift=delta)
        cur_state = directive.state.name
        
        # Track transitions
        if cur_state in states_list and prev_state in states_list:
            trans_counts[prev_state][cur_state] += 1
            if cur_state != prev_state:
                state_transitions.append({
                    "batch": b_idx,
                    "from_state": prev_state,
                    "to_state": cur_state,
                    "delta_drift": delta,
                    "mean_reliability": info["mean_reliability"]
                })
        prev_state = cur_state
        
        # Interventions
        purged = False
        if directive.purge_replay:
            if hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                clf._replay_buffer.clear()
                purged = True
                
        tree_reset = False
        momenta_cleared = False
        if directive.state == ControllerState.CONFIRMED_DRIFT:
            clf.reset()
            tree_reset = True
            opt.state.clear()
            momenta_cleared = True
            
        # Update linear surrogate
        logits_lin = X_b @ p_wrapper.data
        p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
        p_lin /= np.sum(p_lin, axis=1, keepdims=True)
        
        if directive.state == ControllerState.NOISE_BURST:
            weights = np.where(info["mean_reliability"] >= 0.45, 1.0, 0.2)
        else:
            weights = 1.0
        p_wrapper.grad = ((X_b.T @ (p_lin - np.eye(2)[y_obs])) * weights) / len(y_obs)
        opt.step()
        
        runtime_trace.append({
            "batch_idx": b_idx,
            "regime": "clean" if b_idx <= 15 else ("noise" if b_idx <= 25 else ("gradual" if b_idx <= 35 else "abrupt")),
            "state": cur_state,
            "delta_drift": delta,
            "mean_reliability": float(info["mean_reliability"]),
            "retained_samples": info["n_retained_samples"],
            "action_purge_replay": purged,
            "action_tree_reset": tree_reset,
            "action_momenta_cleared": momenta_cleared
        })
        
    # Write runtime trace JSON
    trace_json = "experiments/ulc_v3_independent_audit/ulc_runtime_trace.json"
    with open(trace_json, "w", encoding="utf-8") as f:
        json.dump({
            "audit_seed": 42,
            "n_batches": 50,
            "runtime_trace": runtime_trace,
            "state_transitions": state_transitions
        }, f, indent=2)
    print(f"[OK] Wrote ULC runtime trace to {trace_json}")
    
    # Write State Transition Matrix CSV
    matrix_csv = "experiments/ulc_v3_independent_audit/ulc_state_transition_matrix.csv"
    with open(matrix_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_state"] + states_list)
        for s1 in states_list:
            w.writerow([s1] + [trans_counts[s1][s2] for s2 in states_list])
    print(f"[OK] Wrote State Transition Matrix to {matrix_csv}")
    
    # 2. Causal Ablations (6 Conditions across 5 Seeds)
    ablation_conditions = [
        "1_Full_ULC_v3",
        "2_No_Replay_Purge",
        "3_No_Tree_Reset",
        "4_No_Momenta_Flush",
        "5_Tree_Only_No_Ensemble",
        "6_No_RLA_Sample_Filter"
    ]
    
    abl_results = {cond: [] for cond in ablation_conditions}
    
    for cond in ablation_conditions:
        for seed in SEEDS:
            stream = generate_stream(seed=seed, n_batches=50, batch_size=30, n_features=4)
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
            
            for b_idx, batch in enumerate(stream, start=1):
                t_start = time.perf_counter()
                X_b = batch["X"]
                y_obs = batch["y_observed"]
                y_clean = batch["y_clean"]
                delta = batch["delta"]
                is_noise = batch["is_noise_burst"]
                
                # Prediction
                if cond == "5_Tree_Only_No_Ensemble":
                    if clf.samples_seen_ > 0:
                        p_pred = clf.predict(X_b)
                        p_prob = clf.predict_proba(X_b)
                    else:
                        p_pred = np.zeros(len(X_b), dtype=np.int64)
                        p_prob = np.zeros((len(X_b), 2)) + 0.5
                else:
                    if clf.samples_seen_ > 0:
                        p_tree = clf.predict_proba(X_b)
                    else:
                        p_tree = np.zeros((len(X_b), 2)) + 0.5
                    logits_lin = X_b @ p_wrapper.data
                    p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
                    p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                    p_prob = 0.50 * p_tree + 0.50 * p_lin
                    p_pred = np.argmax(p_prob, axis=1)
                    
                if b_idx > 1:
                    all_y_true.extend(y_clean.tolist())
                    all_y_pred.extend(p_pred.tolist())
                    all_y_prob.extend(p_prob.tolist())
                    
                # Controller Step
                if clf.samples_seen_ > 0:
                    logits_aligned = np.log(np.clip(clf.predict_proba(X_b), 1e-12, 1.0))
                else:
                    logits_aligned = np.zeros((len(X_b), 2))
                directive, info = controller.step(X_b, y_obs, logits=logits_aligned, delta_drift=delta)
                
                if is_noise and directive.state == ControllerState.CONFIRMED_DRIFT:
                    false_resets += 1
                    
                # Interventions according to condition
                if cond != "2_No_Replay_Purge":
                    if directive.purge_replay and hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                        clf._replay_buffer.clear()
                        
                if cond != "3_No_Tree_Reset":
                    if directive.state == ControllerState.CONFIRMED_DRIFT:
                        clf.reset()
                        
                if cond != "4_No_Momenta_Flush":
                    if directive.state == ControllerState.CONFIRMED_DRIFT:
                        opt.state.clear()
                        
                # Linear update
                logits_lin = X_b @ p_wrapper.data
                p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
                p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                
                if cond != "6_No_RLA_Sample_Filter" and directive.state == ControllerState.NOISE_BURST:
                    weights = np.where(info["mean_reliability"] >= 0.45, 1.0, 0.2)
                else:
                    weights = 1.0
                p_wrapper.grad = ((X_b.T @ (p_lin - np.eye(2)[y_obs])) * weights) / len(y_obs)
                opt.step()
                
                latencies.append((time.perf_counter() - t_start) * 1000.0)
                
            metrics = calculate_metrics(np.array(all_y_true), np.array(all_y_pred), np.array(all_y_prob), latencies)
            metrics["false_resets"] = false_resets
            abl_results[cond].append(metrics)
            
    # Write ulc_ablation_results.csv
    abl_csv_path = "experiments/ulc_v3_independent_audit/ulc_ablation_results.csv"
    csv_rows = []
    for cond in ablation_conditions:
        accs = [m["accuracy"] for m in abl_results[cond]]
        mf1s = [m["macro_f1"] for m in abl_results[cond]]
        recs = [m["minority_recall"] for m in abl_results[cond]]
        briers = [m["brier_score"] for m in abl_results[cond]]
        f_res = [m["false_resets"] for m in abl_results[cond]]
        lats = [m["latency_mean_ms"] for m in abl_results[cond]]
        
        csv_rows.append({
            "ablation_condition": cond,
            "accuracy_mean": f"{np.mean(accs):.6f}",
            "accuracy_std": f"{np.std(accs, ddof=1):.6f}",
            "macro_f1_mean": f"{np.mean(mf1s):.6f}",
            "macro_f1_std": f"{np.std(mf1s, ddof=1):.6f}",
            "minority_recall_mean": f"{np.mean(recs):.6f}",
            "minority_recall_std": f"{np.std(recs, ddof=1):.6f}",
            "brier_score_mean": f"{np.mean(briers):.6f}",
            "false_resets_mean": f"{np.mean(f_res):.2f}",
            "latency_mean_ms": f"{np.mean(lats):.4f}"
        })
        
    with open(abl_csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    print(f"[OK] Wrote ULC Ablation CSV to {abl_csv_path}")
    
    # Generate Figures
    fig_dir = "experiments/ulc_v3_independent_audit/figures/ulc"
    os.makedirs(fig_dir, exist_ok=True)
    
    # Fig 1: Ablation Macro F1
    cond_labels = [c.replace("_", " ") for c in ablation_conditions]
    mf1_means = [float(r["macro_f1_mean"]) for r in csv_rows]
    plt.figure(figsize=(10, 5))
    bars = plt.barh(cond_labels, mf1_means, color=["darkgreen", "teal", "navy", "purple", "darkred", "darkorange"])
    plt.xlabel("Macro F1")
    plt.title("ULC-v3 Causal Ablation: Marginal Impact on Macro F1")
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 0.005, bar.get_y() + bar.get_height() / 2.0, f"{w:.3f}", ha="left", va="center", fontweight="bold")
    plt.xlim(0, 0.75)
    plt.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "ablation_macro_f1.png"), dpi=200)
    plt.close()
    
    # Fig 2: State Transitions Heatmap / Bar
    plt.figure(figsize=(8, 6))
    matrix_data = np.array([[trans_counts[s1][s2] for s2 in states_list] for s1 in states_list])
    plt.imshow(matrix_data, cmap="Blues")
    plt.xticks(range(len(states_list)), states_list, rotation=30, ha="right")
    plt.yticks(range(len(states_list)), states_list)
    plt.title("ULC Finite-State Machine Transition Counts (50 Batches)")
    for i in range(len(states_list)):
        for j in range(len(states_list)):
            plt.text(j, i, str(matrix_data[i, j]), ha="center", va="center", color="black" if matrix_data[i, j] < 20 else "white")
    plt.colorbar(label="Transition Count")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "state_transitions.png"), dpi=200)
    plt.close()
    
    print(f"[OK] Generated ULC figures in {fig_dir}")

if __name__ == "__main__":
    execute_ulc_audit()
