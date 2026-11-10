"""
Workstream A: Independent Experiment Reproduction Script.
Executes all 11 configurations across 5 original seeds [42, 101, 2024, 7, 99],
logs raw seed-level metrics, and compares against raw_study_results.json.
"""

import csv
import json
import os
import sys
import time
import numpy as np
import torch

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import (
    run_single_model_stream
)

MODELS = [
    "Static_Baseline",
    "ALA_Only",
    "RLA_Only",
    "RAO_Only",
    "ALA_plus_RLA",
    "ALA_plus_RAO",
    "RLA_plus_RAO",
    "Uncoordinated_Three_Pillars",
    "Full_ULC_v1",
    "Optimized_ULC_v2",
    "MultiObjective_ULC_v3",
]

SEEDS = [42, 101, 2024, 7, 99]

# Reference reported values from Section 2.1 of User Request
REPORTED_REFERENCE = {
    "Static_Baseline": {"accuracy": 0.8106, "balanced_accuracy": 0.5658, "minority_recall": 0.2599, "macro_f1": 0.555, "brier_score": 0.163, "false_resets": 0.0, "latency_mean_ms": 0.577},
    "ALA_Only": {"accuracy": 0.9000, "balanced_accuracy": 0.5000, "minority_recall": 0.0000, "macro_f1": 0.474, "brier_score": 0.125, "false_resets": 10.0, "latency_mean_ms": 0.697},
    "RLA_Only": {"accuracy": 0.8105, "balanced_accuracy": 0.5446, "minority_recall": 0.2122, "macro_f1": 0.538, "brier_score": 0.160, "false_resets": 0.0, "latency_mean_ms": 0.683},
    "RAO_Only": {"accuracy": 0.6486, "balanced_accuracy": 0.6451, "minority_recall": 0.6408, "macro_f1": 0.518, "brier_score": 0.255, "false_resets": 0.0, "latency_mean_ms": 0.045},
    "ALA_plus_RLA": {"accuracy": 0.8804, "balanced_accuracy": 0.5000, "minority_recall": 0.0245, "macro_f1": 0.485, "brier_score": 0.126, "false_resets": 10.0, "latency_mean_ms": 0.784},
    "ALA_plus_RAO": {"accuracy": 0.7000, "balanced_accuracy": 0.6973, "minority_recall": 0.6939, "macro_f1": 0.562, "brier_score": 0.211, "false_resets": 10.0, "latency_mean_ms": 0.046},
    "RLA_plus_RAO": {"accuracy": 0.6422, "balanced_accuracy": 0.6385, "minority_recall": 0.6340, "macro_f1": 0.513, "brier_score": 0.261, "false_resets": 0.0, "latency_mean_ms": 0.171},
    "Uncoordinated_Three_Pillars": {"accuracy": 0.8804, "balanced_accuracy": 0.5000, "minority_recall": 0.0245, "macro_f1": 0.485, "brier_score": 0.126, "false_resets": 10.0, "latency_mean_ms": 0.901},
    "Full_ULC_v1": {"accuracy": 0.7369, "balanced_accuracy": 0.5110, "minority_recall": 0.2286, "macro_f1": 0.500, "brier_score": 0.204, "false_resets": 1.0, "latency_mean_ms": 1.374},
    "Optimized_ULC_v2": {"accuracy": 0.9000, "balanced_accuracy": 0.5000, "minority_recall": 0.0000, "macro_f1": 0.474, "brier_score": 0.122, "false_resets": 1.0, "latency_mean_ms": 1.106},
    "MultiObjective_ULC_v3": {"accuracy": 0.9056, "balanced_accuracy": 0.6138, "minority_recall": 0.2490, "macro_f1": 0.645, "brier_score": 0.120, "false_resets": 1.0, "latency_mean_ms": 1.060},
}

def execute_reproduction():
    log_file = "experiments/ulc_v3_independent_audit/logs/reproduction.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as log_f:
        def log(msg):
            print(msg)
            log_f.write(msg + "\n")
            
        log("================================================================================")
        log("WORKSTREAM A: INDEPENDENT REPRODUCTION AUDIT")
        log(f"Execution Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        log(f"Host: Windows 11 AMD64, Python {sys.version.split()[0]}, PyTorch {torch.__version__}")
        log("================================================================================\n")
        
        reproduction_results = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "seeds": SEEDS,
                "n_seeds": len(SEEDS),
                "configurations": MODELS,
                "environment": {
                    "python": sys.version,
                    "pytorch": torch.__version__,
                    "platform": sys.platform
                }
            },
            "seed_level_data": {},
            "aggregate_data": {},
            "comparison_with_reported": {}
        }
        
        seed_rows = []
        comparison_rows = []
        
        for config_name in MODELS:
            log(f"--> Executing Configuration: {config_name:30s} ...")
            t0 = time.time()
            seed_metrics = []
            
            for seed in SEEDS:
                metrics, diagnostics = run_single_model_stream(config_name, seed=seed)
                seed_metrics.append(metrics)
                
                # Flat CSV row
                seed_rows.append({
                    "configuration": config_name,
                    "seed": seed,
                    "accuracy": f"{metrics['accuracy']:.6f}",
                    "balanced_accuracy": f"{metrics['balanced_accuracy']:.6f}",
                    "minority_recall": f"{metrics['minority_recall']:.6f}",
                    "minority_precision": f"{metrics['minority_precision']:.6f}",
                    "minority_f1": f"{metrics['minority_f1']:.6f}",
                    "macro_f1": f"{metrics['macro_f1']:.6f}",
                    "brier_score": f"{metrics['brier_score']:.6f}",
                    "false_resets": metrics["false_resets"],
                    "detection_delay": metrics["drift_detection_delay"],
                    "recovery_batches": metrics["recovery_batches"],
                    "latency_mean_ms": f"{metrics['latency_mean_ms']:.4f}",
                    "latency_p50_ms": f"{metrics['latency_p50_ms']:.4f}",
                    "latency_p95_ms": f"{metrics['latency_p95_ms']:.4f}",
                    "latency_p99_ms": f"{metrics['latency_p99_ms']:.4f}",
                    "latency_max_ms": f"{metrics['latency_max_ms']:.4f}",
                    "optimizer_state_bytes": metrics["optimizer_state_bytes"]
                })
                
            elapsed = time.time() - t0
            log(f"    Completed 5 seeds in {elapsed:.2f}s.")
            
            reproduction_results["seed_level_data"][config_name] = seed_metrics
            
            # Aggregate metrics
            def agg(key):
                vals = np.array([m[key] for m in seed_metrics])
                return {
                    "mean": float(np.mean(vals)),
                    "std": float(np.std(vals, ddof=1)),
                    "median": float(np.median(vals)),
                    "min": float(np.min(vals)),
                    "max": float(np.max(vals)),
                    "raw": [float(x) for x in vals]
                }
                
            agg_summary = {
                "accuracy": agg("accuracy"),
                "balanced_accuracy": agg("balanced_accuracy"),
                "minority_recall": agg("minority_recall"),
                "minority_precision": agg("minority_precision"),
                "minority_f1": agg("minority_f1"),
                "macro_f1": agg("macro_f1"),
                "brier_score": agg("brier_score"),
                "false_resets": agg("false_resets"),
                "latency_mean_ms": agg("latency_mean_ms"),
                "optimizer_state_bytes": agg("optimizer_state_bytes")
            }
            reproduction_results["aggregate_data"][config_name] = agg_summary
            
            # Comparison against reported reference
            ref = REPORTED_REFERENCE.get(config_name, {})
            comp = {}
            for metric_key, ref_val in ref.items():
                rep_val = agg_summary[metric_key]["mean"]
                abs_diff = rep_val - ref_val
                rel_diff = (abs_diff / ref_val * 100.0) if ref_val != 0 else (0.0 if abs_diff == 0 else float("inf"))
                status = "EXACT_MATCH" if abs(abs_diff) < 1e-3 else "DISCREPANCY"
                
                comp[metric_key] = {
                    "reported": ref_val,
                    "reproduced": rep_val,
                    "abs_diff": abs_diff,
                    "rel_diff_pct": rel_diff,
                    "status": status
                }
                
                comparison_rows.append({
                    "configuration": config_name,
                    "metric": metric_key,
                    "reported_reference": f"{ref_val:.4f}",
                    "reproduced_mean": f"{rep_val:.4f}",
                    "absolute_difference": f"{abs_diff:+.6f}",
                    "relative_difference_pct": f"{rel_diff:+.2f}%" if rel_diff != float("inf") else "N/A",
                    "verification_status": status
                })
                
            reproduction_results["comparison_with_reported"][config_name] = comp
            
        # Write JSON results
        json_path = "experiments/ulc_v3_independent_audit/reproduction_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(reproduction_results, f, indent=2)
        log(f"\n[OK] Wrote JSON reproduction results to {json_path}")
        
        # Write Seed-Level CSV
        seed_csv_path = "experiments/ulc_v3_independent_audit/reproduction_seed_results.csv"
        if seed_rows:
            with open(seed_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(seed_rows[0].keys()))
                writer.writeheader()
                writer.writerows(seed_rows)
            log(f"[OK] Wrote Seed-Level CSV to {seed_csv_path} ({len(seed_rows)} rows)")
            
        # Write Comparison CSV
        comp_csv_path = "experiments/ulc_v3_independent_audit/reproduction_comparison.csv"
        if comparison_rows:
            with open(comp_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
                writer.writeheader()
                writer.writerows(comparison_rows)
            log(f"[OK] Wrote Comparison CSV to {comp_csv_path} ({len(comparison_rows)} rows)")
            
        # Summary log output
        log("\n--------------------------------------------------------------------------------")
        log("REPRODUCTION COMPARISON SUMMARY TABLE:")
        log(f"{'Configuration':30s} | {'Acc (Rep/Ref)':18s} | {'Macro F1':15s} | {'Recall':15s} | {'Resets':10s} | {'Match Status'}")
        log("-" * 105)
        for m in MODELS:
            c = reproduction_results["comparison_with_reported"][m]
            acc_str = f"{c['accuracy']['reproduced']*100:.2f}%/{c['accuracy']['reported']*100:.2f}%"
            mf1_str = f"{c['macro_f1']['reproduced']:.3f}/{c['macro_f1']['reported']:.3f}"
            rec_str = f"{c['minority_recall']['reproduced']*100:.2f}%/{c['minority_recall']['reported']*100:.2f}%"
            res_str = f"{c['false_resets']['reproduced']:.1f}/{c['false_resets']['reported']:.1f}"
            all_match = all(v["status"] == "EXACT_MATCH" for v in c.values())
            match_status = "INDEPENDENTLY_REPRODUCED" if all_match else "DISCREPANCY"
            log(f"{m:30s} | {acc_str:18s} | {mf1_str:15s} | {rec_str:15s} | {res_str:10s} | {match_status}")
            
    print("\nReproduction process completed successfully.")

if __name__ == "__main__":
    execute_reproduction()
