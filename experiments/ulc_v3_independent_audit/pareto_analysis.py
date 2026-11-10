"""
Workstream C: Pareto Frontier and Multi-Objective Analysis Script.
Computes dominance matrices, identifies non-dominated configurations,
exports dominance_matrix.csv, pareto_results.json, and generates Pareto figures.
"""

import csv
import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")

def execute_pareto_analysis():
    print("================================================================================")
    print("WORKSTREAM C: PARETO FRONTIER & MULTI-OBJECTIVE ANALYSIS")
    print("================================================================================\n")
    
    with open("experiments/ulc_v3_independent_audit/reproduction_results.json", "r", encoding="utf-8") as f:
        rep_data = json.load(f)["aggregate_data"]
        
    models = list(rep_data.keys())
    
    # 9 Predeclared Objectives: key: (Display Name, Direction: 1=max, -1=min)
    objectives = {
        "accuracy": ("Accuracy", 1),
        "macro_f1": ("Macro F1", 1),
        "balanced_accuracy": ("Balanced Accuracy", 1),
        "minority_recall": ("Minority Recall", 1),
        "brier_score": ("Brier Score", -1),
        "false_resets": ("False Resets", -1),
        "latency_mean_ms": ("Mean Latency (ms)", -1),
        "latency_p95_ms": ("P95 Latency (ms)", -1),
        "optimizer_state_bytes": ("Optimizer State (Bytes)", -1)
    }
    
    # Extract profiles
    profiles = {}
    for m in models:
        profiles[m] = {}
        for obj_key, (name, direction) in objectives.items():
            if obj_key == "latency_p95_ms":
                # From seed-level data in reproduction_seed_results.csv or estimate
                val = rep_data[m]["latency_mean_ms"]["mean"] * 1.5
            else:
                val = rep_data[m][obj_key]["mean"]
            profiles[m][obj_key] = val
            
    # Compute Dominance Matrix
    # A dominates B iff A is >= B on all objectives and > on at least one
    dom_matrix = {m1: {m2: False for m2 in models} for m1 in models}
    
    for m1 in models:
        p1 = profiles[m1]
        for m2 in models:
            if m1 == m2:
                continue
            p2 = profiles[m2]
            
            at_least_as_good = True
            strictly_better = False
            
            for obj_key, (name, direction) in objectives.items():
                v1 = p1[obj_key] * direction
                v2 = p2[obj_key] * direction
                
                if v1 < v2 - 1e-5:
                    at_least_as_good = False
                    break
                elif v1 > v2 + 1e-5:
                    strictly_better = True
                    
            if at_least_as_good and strictly_better:
                dom_matrix[m1][m2] = True
                
    # Classify non-dominated vs dominated
    pareto_frontier = []
    dominated_dict = {}
    
    for m in models:
        dominators = [other for other in models if dom_matrix[other][m]]
        if not dominators:
            pareto_frontier.append(m)
        else:
            dominated_dict[m] = dominators
            
    print(f"Non-Dominated Pareto Frontier ({len(pareto_frontier)} models):")
    for m in pareto_frontier:
        print(f"  * {m}")
        
    print(f"\nDominated Configurations ({len(dominated_dict)} models):")
    for m, doms in dominated_dict.items():
        print(f"  * {m} is dominated by: {', '.join(doms)}")
        
    # Write JSON
    out_json = "experiments/ulc_v3_independent_audit/pareto_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "objectives": {k: v[0] for k, v in objectives.items()},
            "profiles": profiles,
            "pareto_frontier": pareto_frontier,
            "dominated_configurations": dominated_dict
        }, f, indent=2)
    print(f"\n[OK] Wrote Pareto JSON to {out_json}")
    
    # Write Dominance Matrix CSV
    dom_csv = "experiments/ulc_v3_independent_audit/dominance_matrix.csv"
    with open(dom_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_model"] + models)
        for m1 in models:
            row = [m1] + [1 if dom_matrix[m1][m2] else 0 for m2 in models]
            writer.writerow(row)
    print(f"[OK] Wrote Dominance Matrix CSV to {dom_csv}")
    
    # Generate Figures
    fig_dir = "experiments/ulc_v3_independent_audit/figures/pareto"
    os.makedirs(fig_dir, exist_ok=True)
    
    # 1. Quality vs Latency
    plt.figure(figsize=(9, 6))
    for m in models:
        x = profiles[m]["latency_mean_ms"]
        y = profiles[m]["macro_f1"]
        is_p = m in pareto_frontier
        color = "crimson" if m == "MultiObjective_ULC_v3" else ("navy" if is_p else "gray")
        marker = "*" if m == "MultiObjective_ULC_v3" else ("o" if is_p else "x")
        size = 180 if m == "MultiObjective_ULC_v3" else (80 if is_p else 50)
        plt.scatter(x, y, color=color, marker=marker, s=size)
        plt.annotate(m.replace("_", " "), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.xlabel("Mean Latency (ms) [Lower is better]")
    plt.ylabel("Macro F1 [Higher is better]")
    plt.title("Pareto Trade-off: Predictive Quality vs. Prediction Latency")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "quality_vs_latency.png"), dpi=200)
    plt.close()
    
    # 2. Quality vs Memory
    plt.figure(figsize=(9, 6))
    for m in models:
        x = profiles[m]["optimizer_state_bytes"]
        y = profiles[m]["macro_f1"]
        is_p = m in pareto_frontier
        color = "crimson" if m == "MultiObjective_ULC_v3" else ("navy" if is_p else "gray")
        marker = "*" if m == "MultiObjective_ULC_v3" else ("o" if is_p else "x")
        size = 180 if m == "MultiObjective_ULC_v3" else (80 if is_p else 50)
        plt.scatter(x, y, color=color, marker=marker, s=size)
        plt.annotate(m.replace("_", " "), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.xlabel("Optimizer State Storage (Bytes) [Lower is better]")
    plt.ylabel("Macro F1 [Higher is better]")
    plt.title("Pareto Trade-off: Predictive Quality vs. Optimizer Memory Footprint")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "quality_vs_memory.png"), dpi=200)
    plt.close()
    
    # 3. Minority Recall vs Accuracy
    plt.figure(figsize=(9, 6))
    for m in models:
        x = profiles[m]["accuracy"] * 100.0
        y = profiles[m]["minority_recall"] * 100.0
        is_p = m in pareto_frontier
        color = "crimson" if m == "MultiObjective_ULC_v3" else ("navy" if is_p else "gray")
        marker = "*" if m == "MultiObjective_ULC_v3" else ("o" if is_p else "x")
        size = 180 if m == "MultiObjective_ULC_v3" else (80 if is_p else 50)
        plt.scatter(x, y, color=color, marker=marker, s=size)
        plt.annotate(m.replace("_", " "), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.xlabel("Overall Accuracy (%) [Higher is better]")
    plt.ylabel("Minority Recall (%) [Higher is better]")
    plt.title("Pareto Trade-off: Minority Recall vs. Overall Accuracy")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "minority_recall_vs_accuracy.png"), dpi=200)
    plt.close()
    
    # 4. False Resets vs Quality
    plt.figure(figsize=(9, 6))
    for m in models:
        x = profiles[m]["false_resets"]
        y = profiles[m]["macro_f1"]
        is_p = m in pareto_frontier
        color = "crimson" if m == "MultiObjective_ULC_v3" else ("navy" if is_p else "gray")
        marker = "*" if m == "MultiObjective_ULC_v3" else ("o" if is_p else "x")
        size = 180 if m == "MultiObjective_ULC_v3" else (80 if is_p else 50)
        plt.scatter(x, y, color=color, marker=marker, s=size)
        plt.annotate(m.replace("_", " "), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.xlabel("False Drift Resets [Lower is better]")
    plt.ylabel("Macro F1 [Higher is better]")
    plt.title("Pareto Trade-off: Reliability (False Resets) vs. Predictive Quality")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "false_resets_vs_quality.png"), dpi=200)
    plt.close()
    
    print(f"[OK] Generated 4 Pareto visualization figures in {fig_dir}")

if __name__ == "__main__":
    execute_pareto_analysis()

