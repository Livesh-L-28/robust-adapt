"""
Workstream B: Statistical Reanalysis Script.
Computes paired t-tests, Wilcoxon tests, Holm-Bonferroni adjustments,
Cohen's d_z, Hedges' g, and generates all required statistical CSV and JSON deliverables.
"""

import csv
import json
import os
import sys
import numpy as np
import scipy.stats as stats

sys.stdout.reconfigure(encoding="utf-8")

def execute_statistical_analysis():
    print("================================================================================")
    print("WORKSTREAM B: STATISTICAL REANALYSIS EXECUTION")
    print("================================================================================\n")
    
    with open("experiments/ulc_v3_independent_audit/reproduction_results.json", "r", encoding="utf-8") as f:
        rep_data = json.load(f)["seed_level_data"]
        
    models = ["Static_Baseline", "ALA_Only", "Uncoordinated_Three_Pillars", "Full_ULC_v1"]
    primary_metrics = ["macro_f1", "balanced_accuracy", "minority_recall"]
    secondary_metrics = ["accuracy", "minority_precision", "minority_f1", "brier_score", "false_resets", "latency_mean_ms"]
    all_metrics = primary_metrics + secondary_metrics
    
    paired_comp_rows = []
    effect_size_rows = []
    ci_rows = []
    statistical_results = {}
    
    target_model = "MultiObjective_ULC_v3"
    target_data = rep_data[target_model]
    
    # 1. Primary Hypotheses Evaluation (with Holm-Bonferroni across the 4 baselines per metric)
    for metric in all_metrics:
        statistical_results[metric] = {}
        p_values = []
        temp_records = []
        
        for base_model in models:
            base_data = rep_data[base_model]
            
            y_target = np.array([x[metric] for x in target_data])
            y_base = np.array([x[metric] for x in base_data])
            diffs = y_target - y_base
            
            n = len(diffs)
            df = n - 1
            mean_diff = float(np.mean(diffs))
            std_diff = float(np.std(diffs, ddof=1))
            se_diff = float(std_diff / np.sqrt(n))
            
            # Paired t-test
            t_stat = float(mean_diff / se_diff) if se_diff > 1e-12 else 0.0
            p_raw = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df))) if se_diff > 1e-12 else (0.0 if mean_diff != 0 else 1.0)
            
            # Wilcoxon test
            try:
                w_stat, p_wilcoxon = stats.wilcoxon(diffs)
                w_stat, p_wilcoxon = float(w_stat), float(p_wilcoxon)
            except Exception:
                w_stat, p_wilcoxon = 0.0, 1.0
                
            # Effect sizes: Cohen's d_z and Hedges' g
            cohens_d = float(mean_diff / std_diff) if std_diff > 1e-12 else 0.0
            hedges_g = float(cohens_d * (1 - 3 / (4 * df - 1))) if df > 1 else cohens_d
            
            # 95% Confidence Interval for mean difference
            t_crit = float(stats.t.ppf(0.975, df=df))
            ci_lower = float(mean_diff - t_crit * se_diff)
            ci_upper = float(mean_diff + t_crit * se_diff)
            
            # 95% CI for absolute values
            t_mean = float(np.mean(y_target))
            t_std = float(np.std(y_target, ddof=1))
            b_mean = float(np.mean(y_base))
            b_std = float(np.std(y_base, ddof=1))
            
            p_values.append(p_raw)
            temp_records.append({
                "baseline_model": base_model,
                "t_mean": t_mean,
                "t_std": t_std,
                "t_median": float(np.median(y_target)),
                "t_min": float(np.min(y_target)),
                "t_max": float(np.max(y_target)),
                "b_mean": b_mean,
                "b_std": b_std,
                "b_median": float(np.median(y_base)),
                "b_min": float(np.min(y_base)),
                "b_max": float(np.max(y_base)),
                "mean_diff": mean_diff,
                "std_diff": std_diff,
                "se_diff": se_diff,
                "t_stat": t_stat,
                "p_raw": p_raw,
                "p_wilcoxon": p_wilcoxon,
                "cohens_d": cohens_d,
                "hedges_g": hedges_g,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper
            })
            
        # Holm-Bonferroni correction
        m = len(p_values)
        sorted_indices = np.argsort(p_values)
        holm_p_values = [0.0] * m
        running_max = 0.0
        for rank, idx in enumerate(sorted_indices):
            adjusted_p = min(1.0, p_values[idx] * (m - rank))
            running_max = max(running_max, adjusted_p)
            holm_p_values[idx] = min(1.0, running_max)
            
        for idx, rec in enumerate(temp_records):
            rec["p_holm"] = float(holm_p_values[idx])
            base_model = rec["baseline_model"]
            
            # Determine category
            p_raw = rec["p_raw"]
            p_holm = rec["p_holm"]
            m_diff = rec["mean_diff"]
            
            # Metric direction: for brier_score, false_resets, latency_mean_ms, improvement is negative diff
            is_minimization = metric in ("brier_score", "false_resets", "latency_mean_ms")
            improved = (m_diff < 0) if is_minimization else (m_diff > 0)
            
            if improved:
                if p_holm < 0.01:
                    conclusion = "SUPPORTED"
                elif p_raw < 0.01 and p_holm < 0.05:
                    conclusion = "PARTIALLY_SUPPORTED"
                elif p_raw < 0.05:
                    conclusion = "INCONCLUSIVE"
                else:
                    conclusion = "NOT_SUPPORTED"
            else:
                conclusion = "CONTRADICTED" if p_raw < 0.05 else "NOT_SUPPORTED"
                
            rec["conclusion"] = conclusion
            statistical_results[metric][base_model] = rec
            
            # Row for paired_comparisons.csv
            paired_comp_rows.append({
                "metric": metric,
                "target_model": target_model,
                "baseline_model": base_model,
                "target_mean": f"{rec['t_mean']:.6f}",
                "baseline_mean": f"{rec['b_mean']:.6f}",
                "mean_difference": f"{rec['mean_diff']:+.6f}",
                "t_statistic": f"{rec['t_stat']:.4f}",
                "df": df,
                "raw_p_value": f"{rec['p_raw']:.6f}",
                "holm_p_value": f"{rec['p_holm']:.6f}",
                "wilcoxon_p_value": f"{rec['p_wilcoxon']:.6f}",
                "passes_alpha_01": "TRUE" if rec["p_holm"] < 0.01 else "FALSE",
                "statistical_conclusion": conclusion
            })
            
            # Row for effect_sizes.csv
            effect_size_rows.append({
                "metric": metric,
                "target_model": target_model,
                "baseline_model": base_model,
                "mean_difference": f"{rec['mean_diff']:+.6f}",
                "cohens_d_z": f"{rec['cohens_d']:.4f}",
                "hedges_g": f"{rec['hedges_g']:.4f}",
                "std_difference": f"{rec['std_diff']:.6f}",
                "practical_significance": "HIGH" if abs(rec['hedges_g']) > 0.8 else ("MODERATE" if abs(rec['hedges_g']) > 0.5 else "LOW")
            })
            
            # Row for confidence_intervals.csv
            ci_rows.append({
                "metric": metric,
                "target_model": target_model,
                "baseline_model": base_model,
                "mean_difference": f"{rec['mean_diff']:+.6f}",
                "se_difference": f"{rec['se_diff']:.6f}",
                "ci_95_lower": f"{rec['ci_lower']:+.6f}",
                "ci_95_upper": f"{rec['ci_upper']:+.6f}",
                "target_ci_95": f"[{rec['t_mean'] - t_crit * (rec['t_std']/np.sqrt(n)):.4f}, {rec['t_mean'] + t_crit * (rec['t_std']/np.sqrt(n)):.4f}]",
                "baseline_ci_95": f"[{rec['b_mean'] - t_crit * (rec['b_std']/np.sqrt(n)):.4f}, {rec['b_mean'] + t_crit * (rec['b_std']/np.sqrt(n)):.4f}]"
            })
            
    # Write JSON results
    out_json = "experiments/ulc_v3_independent_audit/statistical_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(statistical_results, f, indent=2)
    print(f"[OK] Wrote JSON statistical results to {out_json}")
    
    # Write CSVs
    def write_csv(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[OK] Wrote {len(rows)} rows to {path}")
        
    write_csv("experiments/ulc_v3_independent_audit/paired_comparisons.csv", paired_comp_rows)
    write_csv("experiments/ulc_v3_independent_audit/effect_sizes.csv", effect_size_rows)
    write_csv("experiments/ulc_v3_independent_audit/confidence_intervals.csv", ci_rows)
    
    print("\nStatistical reanalysis complete.")

if __name__ == "__main__":
    execute_statistical_analysis()

