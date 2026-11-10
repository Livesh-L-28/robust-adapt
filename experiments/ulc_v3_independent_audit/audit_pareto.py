"""
Pareto Front Multi-Objective Dominance Audit across 11 Configurations.
Defines objectives, computes dominance matrices, and identifies non-dominated sets.
"""

import json
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

def run_pareto_audit():
    print("================================================================================")
    print("SECTION 4: PARETO-FRONT MULTI-OBJECTIVE DOMINANCE AUDIT")
    print("================================================================================\n")
    
    with open("experiments/four_pillar_validation_v2/raw_study_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)["models"]
        
    models = list(data.keys())
    
    # Define objectives
    # Each objective has a direction: 1 for maximize, -1 for minimize
    objectives = {
        "accuracy": ("Accuracy", 1),
        "macro_f1": ("Macro F1", 1),
        "balanced_accuracy": ("Balanced Accuracy", 1),
        "minority_recall": ("Minority Recall", 1),
        "brier_score": ("Brier Score", -1),
        "false_resets": ("False Resets", -1),
        "latency_mean_ms": ("Mean Latency (ms)", -1),
        "latency_p95_ms": ("P95 Latency (ms)", -1),
        "optimizer_state_bytes": ("Optimizer State (Bytes)", -1),
    }
    
    # Extract mean vectors for each model
    profiles = {}
    for m in models:
        agg = data[m]["aggregate"]
        profiles[m] = {obj_key: agg[obj_key]["mean"] for obj_key in objectives}
        
    print(f"Auditing {len(models)} configurations across {len(objectives)} objectives:\n")
    print(f"{'Configuration':30s} | {'Acc':6s} | {'MF1':5s} | {'BalAcc':6s} | {'Recall':6s} | {'Brier':5s} | {'FRes':4s} | {'Lat':5s} | {'MemB':4s}")
    print("-" * 95)
    for m in models:
        p = profiles[m]
        print(f"{m:30s} | {p['accuracy']*100:5.2f}% | {p['macro_f1']:5.3f} | {p['balanced_accuracy']*100:5.2f}% | {p['minority_recall']*100:5.2f}% | {p['brier_score']:5.3f} | {p['false_resets']:4.1f} | {p['latency_mean_ms']:5.3f} | {p['optimizer_state_bytes']:4.0f}")
        
    # Compute Pareto Dominance
    # Model A dominates Model B (A > B) iff:
    # A is at least as good as B on ALL objectives, and strictly better on AT LEAST ONE objective.
    dominance_matrix = {m1: {m2: False for m2 in models} for m1 in models}
    
    for m1 in models:
        p1 = profiles[m1]
        for m2 in models:
            if m1 == m2:
                continue
            p2 = profiles[m2]
            
            at_least_as_good = True
            strictly_better = False
            
            for obj_key, (name, direction) in objectives.items():
                val1 = p1[obj_key] * direction
                val2 = p2[obj_key] * direction
                
                if val1 < val2 - 1e-6:
                    at_least_as_good = False
                    break
                elif val1 > val2 + 1e-6:
                    strictly_better = True
                    
            if at_least_as_good and strictly_better:
                dominance_matrix[m1][m2] = True
                
    # Identify non-dominated configurations (Pareto front)
    pareto_front = []
    dominated_models = {}
    
    for m2 in models:
        dominators = [m1 for m1 in models if dominance_matrix[m1][m2]]
        if not dominators:
            pareto_front.append(m2)
        else:
            dominated_models[m2] = dominators
            
    print("\n--------------------------------------------------------------------------------")
    print("PARETO DOMINANCE AUDIT RESULTS:")
    print("--------------------------------------------------------------------------------")
    print(f"\n>>> NON-DOMINATED CONFIGURATIONS (PARETO FRONTIER, N={len(pareto_front)}):")
    for m in pareto_front:
        print(f"    * {m}")
        
    print(f"\n>>> DOMINATED CONFIGURATIONS (N={len(dominated_models)}):")
    for m, doms in dominated_models.items():
        print(f"    * {m} is strictly dominated by: {', '.join(doms)}")
        
    print("\n--------------------------------------------------------------------------------")
    print("EXAMINATION OF 'UNIVERSAL PARETO-OPTIMALITY' CLAIM FOR ULC-v3:")
    print("--------------------------------------------------------------------------------")
    ulc_v3_profile = profiles["MultiObjective_ULC_v3"]
    
    tradeoffs = []
    for m in models:
        if m == "MultiObjective_ULC_v3":
            continue
        pm = profiles[m]
        # Check where other models outperform ULC-v3
        advantages = []
        if pm["minority_recall"] > ulc_v3_profile["minority_recall"]:
            advantages.append(f"Minority Recall ({pm['minority_recall']*100:.2f}% vs {ulc_v3_profile['minority_recall']*100:.2f}%)")
        if pm["false_resets"] < ulc_v3_profile["false_resets"]:
            advantages.append(f"False Resets ({pm['false_resets']:.1f} vs {ulc_v3_profile['false_resets']:.1f})")
        if pm["latency_mean_ms"] < ulc_v3_profile["latency_mean_ms"]:
            advantages.append(f"Mean Latency ({pm['latency_mean_ms']:.3f}ms vs {ulc_v3_profile['latency_mean_ms']:.3f}ms)")
        if pm["optimizer_state_bytes"] < ulc_v3_profile["optimizer_state_bytes"]:
            advantages.append(f"Optimizer Memory ({pm['optimizer_state_bytes']:.0f}B vs {ulc_v3_profile['optimizer_state_bytes']:.0f}B)")
            
        tradeoffs.append({
            "model": m,
            "advantages_over_ulc_v3": advantages
        })
        
        if advantages:
            print(f"  - {m:28s} outperforms ULC-v3 on: {'; '.join(advantages)}")
            
    # Save pareto audit data
    out_file = "experiments/ulc_v3_independent_audit/pareto_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "objectives": {k: v[0] for k, v in objectives.items()},
            "profiles": profiles,
            "pareto_front": pareto_front,
            "dominated_models": dominated_models,
            "tradeoffs_with_ulc_v3": tradeoffs
        }, f, indent=2)
    print(f"\nPareto audit data saved to {out_file}")

if __name__ == "__main__":
    run_pareto_audit()

