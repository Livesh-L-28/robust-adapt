"""
Comprehensive Statistical Audit for Four-Pillar Validation v2.
Recalculates paired tests, checks assumptions, applies Holm-Bonferroni correction,
and runs an extended N=20 seed validation study.
"""

import json
import os
import sys
import numpy as np
import scipy.stats as stats
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import run_single_model_stream

EXTENDED_SEEDS = [
    42, 101, 2024, 7, 99,
    13, 21, 55, 88, 144,
    233, 377, 610, 987, 1597,
    2584, 4181, 6765, 10946, 17711
]

def load_reproduced_data():
    with open("experiments/ulc_v3_independent_audit/reproduced_study_results.json", "r", encoding="utf-8") as f:
        return json.load(f)["reproduced_models"]

def perform_statistical_audit():
    print("================================================================================")
    print("SECTION 3: STATISTICAL AUDIT & RE-ANALYSIS (N=5 SEEDS)")
    print("================================================================================\n")
    
    models = load_reproduced_data()
    
    comparisons = [
        ("MultiObjective_ULC_v3", "Static_Baseline"),
        ("MultiObjective_ULC_v3", "ALA_Only"),
        ("MultiObjective_ULC_v3", "Uncoordinated_Three_Pillars"),
        ("MultiObjective_ULC_v3", "Full_ULC_v1"),
    ]
    
    metrics_to_audit = ["macro_f1", "balanced_accuracy", "brier_score", "accuracy"]
    
    audit_results = {}
    
    for metric in metrics_to_audit:
        print(f"\n--- AUDITING METRIC: {metric.upper()} ---")
        p_values = []
        comp_records = []
        
        for target, baseline in comparisons:
            v_target = np.array(models[target][metric]["raw_values"])
            v_base = np.array(models[baseline][metric]["raw_values"])
            diffs = v_target - v_base
            
            n = len(diffs)
            df = n - 1
            mean_diff = float(np.mean(diffs))
            std_diff = float(np.std(diffs, ddof=1))
            se_diff = std_diff / np.sqrt(n)
            
            # Paired t-test
            t_stat = float(mean_diff / se_diff if se_diff > 0 else 0.0)
            p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df)))
            
            # Wilcoxon signed-rank test (non-parametric check)
            try:
                w_stat, p_val_wilcoxon = stats.wilcoxon(diffs)
            except Exception:
                w_stat, p_val_wilcoxon = 0.0, 1.0
                
            # Normality of differences (Shapiro-Wilk)
            shapiro_stat, shapiro_p = stats.shapiro(diffs)
            
            # Effect size: Cohen's d_z and Hedges' g
            cohens_d = float(mean_diff / std_diff if std_diff > 0 else 0.0)
            hedges_g = float(cohens_d * (1 - 3 / (4 * df - 1)) if df > 1 else cohens_d)
            
            # 95% Confidence Interval for mean difference
            t_crit = float(stats.t.ppf(0.975, df=df))
            ci_lower = float(mean_diff - t_crit * se_diff)
            ci_upper = float(mean_diff + t_crit * se_diff)
            
            p_values.append(p_val)
            comp_records.append({
                "target": target,
                "baseline": baseline,
                "mean_target": float(np.mean(v_target)),
                "mean_baseline": float(np.mean(v_base)),
                "mean_diff": mean_diff,
                "std_diff": std_diff,
                "t_stat": t_stat,
                "p_val_raw": p_val,
                "p_val_wilcoxon": float(p_val_wilcoxon),
                "shapiro_p": float(shapiro_p),
                "normality_tenable": bool(shapiro_p > 0.05),
                "cohens_d_z": cohens_d,
                "hedges_g": hedges_g,
                "ci95_diff": [ci_lower, ci_upper]
            })
            
        # Apply Holm-Bonferroni correction
        sorted_indices = np.argsort(p_values)
        m = len(p_values)
        holm_p_values = [0.0] * m
        
        running_max = 0.0
        for rank, idx in enumerate(sorted_indices):
            adjusted_p = min(1.0, p_values[idx] * (m - rank))
            running_max = max(running_max, adjusted_p)
            holm_p_values[idx] = min(1.0, running_max)
            
        for i, rec in enumerate(comp_records):
            rec["p_val_holm"] = float(holm_p_values[i])
            rec["passes_raw_p01"] = bool(rec["p_val_raw"] < 0.01)
            rec["passes_raw_p05"] = bool(rec["p_val_raw"] < 0.05)
            rec["passes_holm_p01"] = bool(rec["p_val_holm"] < 0.01)
            rec["passes_holm_p05"] = bool(rec["p_val_holm"] < 0.05)
            
            print(f"Comparison: {rec['target']} vs {rec['baseline']}")
            print(f"  Δ = {rec['mean_diff']:+.4f} (95% CI: [{rec['ci95_diff'][0]:+.4f}, {rec['ci95_diff'][1]:+.4f}])")
            print(f"  t({df}) = {rec['t_stat']:.3f}, Raw p = {rec['p_val_raw']:.4f}, Holm p = {rec['p_val_holm']:.4f}")
            print(f"  Wilcoxon p = {rec['p_val_wilcoxon']:.4f}, Shapiro p = {rec['shapiro_p']:.4f} (Normality: {rec['normality_tenable']})")
            print(f"  Effect Size: Cohen's d_z = {rec['cohens_d_z']:.3f}, Hedges' g = {rec['hedges_g']:.3f}")
            print(f"  Verdicts: Raw p<0.01: {rec['passes_raw_p01']} | Holm p<0.01: {rec['passes_holm_p01']} | Raw p<0.05: {rec['passes_raw_p05']} | Holm p<0.05: {rec['passes_holm_p05']}")
            
        audit_results[metric] = comp_records
        
    print("\n================================================================================")
    print("SECTION 3B: EXTENDED SEED STUDY (N=20 SEEDS, df=19)")
    print("================================================================================\n")
    print(f"Running extended evaluation across {len(EXTENDED_SEEDS)} seeds ...")
    
    extended_models = ["Static_Baseline", "ALA_Only", "Uncoordinated_Three_Pillars", "Full_ULC_v1", "MultiObjective_ULC_v3"]
    extended_results = {m: [] for m in extended_models}
    
    t0 = time.time()
    for m in extended_models:
        print(f"--> Running {m:30s} over 20 seeds ...", end=" ", flush=True)
        m_t0 = time.time()
        for seed in EXTENDED_SEEDS:
            res, _ = run_single_model_stream(m, seed=seed)
            extended_results[m].append(res)
        print(f"Done in {time.time() - m_t0:.2f}s")
        
    print(f"Extended 20-seed runs complete in {time.time() - t0:.2f}s.\n")
    
    extended_tests = {}
    for baseline in ["Static_Baseline", "ALA_Only", "Uncoordinated_Three_Pillars", "Full_ULC_v1"]:
        v_target = np.array([r["macro_f1"] for r in extended_results["MultiObjective_ULC_v3"]])
        v_base = np.array([r["macro_f1"] for r in extended_results[baseline]])
        diffs = v_target - v_base
        
        n = len(diffs)
        df = n - 1
        mean_diff = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1))
        se_diff = std_diff / np.sqrt(n)
        t_stat = float(mean_diff / se_diff)
        p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df)))
        
        cohens_d = float(mean_diff / std_diff if std_diff > 0 else 0.0)
        hedges_g = float(cohens_d * (1 - 3 / (4 * df - 1)))
        
        t_crit = float(stats.t.ppf(0.975, df=df))
        ci_lower = float(mean_diff - t_crit * se_diff)
        ci_upper = float(mean_diff + t_crit * se_diff)
        
        extended_tests[f"ULC_v3_vs_{baseline}"] = {
            "n": int(n),
            "df": int(df),
            "target_mean": float(np.mean(v_target)),
            "target_std": float(np.std(v_target, ddof=1)),
            "baseline_mean": float(np.mean(v_base)),
            "baseline_std": float(np.std(v_base, ddof=1)),
            "mean_diff": mean_diff,
            "std_diff": std_diff,
            "t_stat": t_stat,
            "p_val": p_val,
            "passes_p01": bool(p_val < 0.01),
            "passes_p001": bool(p_val < 0.001),
            "cohens_d_z": cohens_d,
            "hedges_g": hedges_g,
            "ci95_diff": [ci_lower, ci_upper]
        }
        
        print(f"Extended Test (N=20, df=19): ULC_v3 vs {baseline} (Macro F1)")
        print(f"  Target: {np.mean(v_target):.4f} ± {np.std(v_target, ddof=1):.4f} | Baseline: {np.mean(v_base):.4f} ± {np.std(v_base, ddof=1):.4f}")
        print(f"  Δ = {mean_diff:+.4f} (95% CI: [{ci_lower:+.4f}, {ci_upper:+.4f}])")
        print(f"  t(19) = {t_stat:.3f}, p = {p_val:.6e} (Passes p < 0.01: {p_val < 0.01})")
        print(f"  Effect Size: Cohen's d_z = {cohens_d:.3f}, Hedges' g = {hedges_g:.3f}\n")
        
    out_file = "experiments/ulc_v3_independent_audit/statistical_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "n5_audit": audit_results,
            "n20_audit": extended_tests,
            "extended_seeds": EXTENDED_SEEDS
        }, f, indent=2)
    print(f"Statistical audit data saved to {out_file}")

if __name__ == "__main__":
    perform_statistical_audit()
