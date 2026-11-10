"""
Minority Class Investigation and Threshold Calibration Audit for ULC-v3.
Analyzes precision-recall curves, decision thresholds, regime-specific recall,
and documentation discrepancies.
"""

import json
import os
import sys
import numpy as np
import time
from sklearn.metrics import precision_recall_curve, roc_curve, auc, f1_score, recall_score, precision_score

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import (
    generate_stream,
    ParamWrapper,
    AdaptiveClassifier,
    LowMemoryAdamW,
    RobustLearningPipeline,
    AdaptiveLearningController,
    ControllerState
)

def run_minority_audit():
    print("================================================================================")
    print("SECTION 5: MINORITY CLASS INVESTIGATION & THRESHOLD AUDIT")
    print("================================================================================\n")
    
    val_seeds = [42, 101, 2024, 7, 99]
    test_seeds = [13, 21, 55, 88, 144]
    
    def run_ulc_v3_prob_stream(seed: int):
        stream_data = generate_stream(seed=seed, n_batches=50, batch_size=30, n_features=4)
        clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20,
                                 enable_drift_detection=True, random_state=seed)
        pipeline = RobustLearningPipeline(n_classes=2)
        p_wrapper = ParamWrapper(np.random.RandomState(seed).randn(4, 2) * 0.01)
        opt = LowMemoryAdamW([p_wrapper], lr=0.01)
        controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
        
        all_y_clean = []
        all_p_tree = []
        all_p_lin = []
        all_p_ens = []
        
        regime_labels = {"clean": [], "noise": [], "gradual": [], "abrupt": []}
        regime_probs = {"clean": [], "noise": [], "gradual": [], "abrupt": []}
        
        for b_idx, batch in enumerate(stream_data, start=1):
            X_b = batch["X"]
            y_obs = batch["y_observed"]
            y_clean = batch["y_clean"]
            delta = batch["delta"]
            is_noise = batch["is_noise_burst"]
            is_drift = batch["is_true_drift"]
            
            # Predictions
            if clf.samples_seen_ > 0:
                p_tree = clf.predict_proba(X_b)
            else:
                p_tree = np.zeros((len(X_b), 2)) + 0.5
                
            logits_lin = X_b @ p_wrapper.data
            p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
            p_lin /= np.sum(p_lin, axis=1, keepdims=True)
            
            p_ens = 0.50 * p_tree + 0.50 * p_lin
            
            if b_idx > 1:
                all_y_clean.extend(y_clean.tolist())
                all_p_tree.extend(p_tree[:, 1].tolist())
                all_p_lin.extend(p_lin[:, 1].tolist())
                all_p_ens.extend(p_ens[:, 1].tolist())
                
                if b_idx <= 15:
                    reg = "clean"
                elif b_idx <= 25:
                    reg = "noise"
                elif b_idx <= 35:
                    reg = "gradual"
                else:
                    reg = "abrupt"
                regime_labels[reg].extend(y_clean.tolist())
                regime_probs[reg].extend(p_ens[:, 1].tolist())
                
            # Controller step
            if clf.samples_seen_ > 0:
                logits_aligned = np.log(np.clip(p_tree, 1e-12, 1.0))
            else:
                logits_aligned = np.zeros((len(X_b), 2))
                
            directive, info = controller.step(X_b, y_obs, logits=logits_aligned, delta_drift=delta)
            
            if directive.purge_replay:
                if hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                    clf._replay_buffer.clear()
                    
            if directive.state == ControllerState.CONFIRMED_DRIFT:
                clf.reset()
                opt.state.clear()
                
            # Update linear surrogate model
            if directive.state == ControllerState.NOISE_BURST:
                weights = np.where(info["mean_reliability"] >= 0.45, 1.0, 0.2)
            else:
                weights = 1.0
            p_wrapper.grad = ((X_b.T @ (p_lin - np.eye(2)[y_obs])) * weights) / len(y_obs)
            opt.step()
            
        return {
            "y_clean": np.array(all_y_clean),
            "p_tree": np.array(all_p_tree),
            "p_lin": np.array(all_p_lin),
            "p_ens": np.array(all_p_ens),
            "regime_labels": regime_labels,
            "regime_probs": regime_probs
        }
        
    print("Running evaluation across validation seeds ...")
    val_runs = [run_ulc_v3_prob_stream(s) for s in val_seeds]
    
    # Analyze documentation discrepancy
    print("--------------------------------------------------------------------------------")
    print("AUDIT DISCREPANCY FINDING: ENSEMBLE SPECIFICATION")
    print("--------------------------------------------------------------------------------")
    print("  * In ULC_DIAGNOSTICS.md, the formula claimed: p_ens = 0.65 * p_tree + 0.35 * p_lin, threshold theta* = 0.35")
    print("  * In actual production/runner code (run_experiments.py:266-267):")
    print("    p_ens = 0.50 * p_tree + 0.50 * p_lin, p_pred = argmax(p_ens) (i.e. threshold theta* = 0.50)")
    print("  * Empirical result of 24.90% minority recall was produced by theta* = 0.50, NOT 0.35!\n")
    
    # Threshold sweep on validation set
    thresholds = np.linspace(0.05, 0.95, 19)
    sweep_results = {}
    for t in thresholds:
        macro_f1s = []
        min_f1s = []
        min_recs = []
        min_precs = []
        accs = []
        for r in val_runs:
            y_t = r["y_clean"]
            y_p = (r["p_ens"] >= t).astype(int)
            macro_f1s.append(f1_score(y_t, y_p, average="macro", zero_division=0))
            min_f1s.append(f1_score(y_t, y_p, pos_label=1, zero_division=0))
            min_recs.append(recall_score(y_t, y_p, pos_label=1, zero_division=0))
            min_precs.append(precision_score(y_t, y_p, pos_label=1, zero_division=0))
            accs.append(np.mean(y_t == y_p))
            
        sweep_results[t] = {
            "macro_f1": float(np.mean(macro_f1s)),
            "minority_f1": float(np.mean(min_f1s)),
            "minority_recall": float(np.mean(min_recs)),
            "minority_precision": float(np.mean(min_precs)),
            "accuracy": float(np.mean(accs))
        }
        
    print(f"{'Threshold':10s} | {'Accuracy':10s} | {'Macro F1':10s} | {'Minority F1':12s} | {'Min Recall':12s} | {'Min Precision':14s}")
    print("-" * 75)
    best_t_macro = max(sweep_results, key=lambda k: sweep_results[k]["macro_f1"])
    for t in thresholds:
        s = sweep_results[t]
        tag = ""
        if abs(t - 0.50) < 1e-4:
            tag = " <-- ACTUAL USED (0.50)"
        elif abs(t - 0.35) < 1e-4:
            tag = " <-- CLAIMED (0.35)"
        elif t == best_t_macro:
            tag = " <-- PEAK MACRO F1"
        print(f"{t:10.2f} | {s['accuracy']*100:9.2f}% | {s['macro_f1']:10.4f} | {s['minority_f1']:12.4f} | {s['minority_recall']*100:11.2f}% | {s['minority_precision']*100:13.2f}%{tag}")
        
    # Evaluate generalization on test seeds
    print("\n--------------------------------------------------------------------------------")
    print("UNSEEN TEST SEEDS GENERALIZATION (N=5): COMPARING THRESHOLDS")
    print("--------------------------------------------------------------------------------")
    test_runs = [run_ulc_v3_prob_stream(s) for s in test_seeds]
    
    for eval_t, label in [(0.50, "Actual Baseline Threshold (0.50)"), (0.35, "Claimed Documented Threshold (0.35)"), (best_t_macro, f"Validation Tuned Threshold ({best_t_macro:.2f})")]:
        m_f1s, recs, precs, f1s = [], [], [], []
        for r in test_runs:
            y_t = r["y_clean"]
            y_p = (r["p_ens"] >= eval_t).astype(int)
            m_f1s.append(f1_score(y_t, y_p, average="macro", zero_division=0))
            recs.append(recall_score(y_t, y_p, pos_label=1, zero_division=0))
            precs.append(precision_score(y_t, y_p, pos_label=1, zero_division=0))
            f1s.append(f1_score(y_t, y_p, pos_label=1, zero_division=0))
            
        print(f"{label}:")
        print(f"  Macro F1: {np.mean(m_f1s):.4f} ± {np.std(m_f1s, ddof=1):.4f}")
        print(f"  Minority Recall: {np.mean(recs)*100:5.2f}% ± {np.std(recs, ddof=1)*100:4.2f}% | Precision: {np.mean(precs)*100:5.2f}% ± {np.std(precs, ddof=1)*100:4.2f}% | F1: {np.mean(f1s):.4f}\n")
        
    # Regime breakdown analysis
    print("--------------------------------------------------------------------------------")
    print("REGIME-SPECIFIC MINORITY RECALL & PRECISION (AT THRESHOLD 0.50)")
    print("--------------------------------------------------------------------------------")
    regime_stats = {}
    for reg in ["clean", "noise", "gradual", "abrupt"]:
        recs, precs = [], []
        for r in val_runs:
            y_t = np.array(r["regime_labels"][reg])
            y_p = (np.array(r["regime_probs"][reg]) >= 0.50).astype(int)
            recs.append(recall_score(y_t, y_p, pos_label=1, zero_division=0))
            precs.append(precision_score(y_t, y_p, pos_label=1, zero_division=0))
        regime_stats[reg] = {
            "recall_mean": float(np.mean(recs)),
            "recall_std": float(np.std(recs, ddof=1)),
            "precision_mean": float(np.mean(precs)),
            "precision_std": float(np.std(precs, ddof=1))
        }
        print(f"  Regime {reg.upper():8s}: Recall = {np.mean(recs)*100:5.2f}% ± {np.std(recs, ddof=1)*100:4.2f}% | Precision = {np.mean(precs)*100:5.2f}% ± {np.std(precs, ddof=1)*100:4.2f}%")
        
    out_file = "experiments/ulc_v3_independent_audit/minority_class_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "threshold_sweep_val": {str(k): v for k, v in sweep_results.items()},
            "best_threshold_macro": best_t_macro,
            "regime_stats": regime_stats
        }, f, indent=2)
    print(f"\nMinority class audit data saved to {out_file}")

if __name__ == "__main__":
    run_minority_audit()
