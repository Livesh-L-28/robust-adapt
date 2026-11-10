"""
Stage 12 — Workstream H: Confirmatory Statistical Testing and Hypothesis Validation.

Conducts rigorous statistical testing across all Stage 12 research workstreams:
1. Workstream A: ALA 3.0 vs Standard ADWIN and Static Hoeffding (Accuracy, Resets)
2. Workstream B: RLA 3.0 vs RLA 2.0 (Spatial KNN) across Clean, Symmetric 20%, and Asymmetric 20% Noise
3. Workstream C: Minority 2.0 vs Minority 1.0 (556:1 brute weight) and Unweighted
4. Workstream D: RAO 2.0 vs PyTorch native AdamW (Latency, Memory, Loss)
5. Workstream E: ULC-v5 vs ULC-v4.1 and Static Baseline (Accuracy, Resets)
6. Workstream F: Cross-Pillar Interactions (ALA alone vs Full System, etc.)
7. Workstream G: Ablation Studies (Full vs Ablated mechanisms)

Statistical Protocol:
- Paired 2-sample tests across identical seeds
- Paired Mean Difference & 95% Confidence Interval
- Paired Cohen's d_z effect size (d_z = mean(diff) / std(diff, ddof=1))
- Paired Student's t-test (t_stat, p_val)
- Wilcoxon signed-rank test (w_stat, p_val)
- Holm-Bonferroni family-wise p-value adjustment
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats


def holm_bonferroni_adjust(p_values: List[float]) -> List[float]:
    """Applies step-down Holm-Bonferroni adjustment to a list of p-values."""
    m = len(p_values)
    if m == 0:
        return []
    
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    
    for rank, (orig_idx, p) in enumerate(indexed):
        adj_p = min(1.0, (m - rank) * p)
        running_max = max(running_max, adj_p)
        adjusted[orig_idx] = min(1.0, running_max)
        
    return adjusted


def compute_paired_comparison(
    name: str,
    family: str,
    metric_name: str,
    x_name: str,
    x_vals: np.ndarray,
    y_name: str,
    y_vals: np.ndarray,
) -> Dict[str, Any]:
    """Computes paired statistical test between x_vals (treatment) and y_vals (control)."""
    assert len(x_vals) == len(y_vals), f"Lengths differ: {len(x_vals)} vs {len(y_vals)}"
    n = len(x_vals)
    diff = x_vals - y_vals
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1)) if n > 1 else 0.0
    
    # 95% CI
    if n > 1 and std_diff > 1e-12:
        se = std_diff / np.sqrt(n)
        ci_half = stats.t.ppf(0.975, df=n - 1) * se
        ci_lower = mean_diff - ci_half
        ci_upper = mean_diff + ci_half
        cohens_dz = float(mean_diff / std_diff)
    else:
        ci_lower, ci_upper = mean_diff, mean_diff
        cohens_dz = float("inf") if mean_diff > 0 else (float("-inf") if mean_diff < 0 else 0.0)

    # t-test
    if std_diff > 1e-12 and n > 1:
        t_stat, p_ttest = stats.ttest_rel(x_vals, y_vals)
        t_stat = float(t_stat)
        p_ttest = float(p_ttest)
    else:
        t_stat = 0.0
        p_ttest = 1.0 if mean_diff == 0.0 else 0.0

    # Wilcoxon signed-rank test
    if np.all(diff == 0.0) or n < 5:
        w_stat, p_wilcoxon = 0.0, 1.0
    else:
        try:
            res = stats.wilcoxon(x_vals, y_vals, zero_method="pratt")
            w_stat, p_wilcoxon = float(res.statistic), float(res.pvalue)
        except Exception:
            w_stat, p_wilcoxon = 0.0, 1.0

    return {
        "comparison": name,
        "family": family,
        "metric": metric_name,
        "n_seeds": n,
        "treatment_name": x_name,
        "treatment_mean": float(np.mean(x_vals)),
        "treatment_std": float(np.std(x_vals, ddof=1)) if n > 1 else 0.0,
        "control_name": y_name,
        "control_mean": float(np.mean(y_vals)),
        "control_std": float(np.std(y_vals, ddof=1)) if n > 1 else 0.0,
        "mean_diff": mean_diff,
        "std_diff": std_diff,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "cohens_dz": cohens_dz,
        "t_statistic": t_stat,
        "p_ttest": p_ttest,
        "wilcoxon_stat": w_stat,
        "p_wilcoxon": p_wilcoxon,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream H — Confirmatory Statistical Testing")
    print("=====================================================================")

    results_dir = Path("experiments/stage_12/results")
    comparisons: List[Dict[str, Any]] = []

    # 1. Workstream A: ALA 3.0 vs Baselines (Electricity)
    ala_path = results_dir / "ala_3_0_electricity_results.json"
    if ala_path.exists():
        with open(ala_path, "r", encoding="utf-8") as f:
            ala_data = json.load(f)
        df_ala = pd.DataFrame(ala_data)
        
        recurrent_acc = df_ala[df_ala["model_type"] == "ala_3_0_recurrent"].sort_values("seed")["accuracy"].values
        adwin_acc = df_ala[df_ala["model_type"] == "standard_adwin"].sort_values("seed")["accuracy"].values
        static_acc = df_ala[df_ala["model_type"] == "static_hoeffding"].sort_values("seed")["accuracy"].values
        
        recurrent_resets = df_ala[df_ala["model_type"] == "ala_3_0_recurrent"].sort_values("seed")["drift_resets"].values
        adwin_resets = df_ala[df_ala["model_type"] == "standard_adwin"].sort_values("seed")["drift_resets"].values

        comparisons.append(compute_paired_comparison("ALA 3.0 vs ADWIN (Acc)", "ALA_3_0", "Accuracy", "ALA 3.0", recurrent_acc, "Standard ADWIN", adwin_acc))
        comparisons.append(compute_paired_comparison("ALA 3.0 vs Static (Acc)", "ALA_3_0", "Accuracy", "ALA 3.0", recurrent_acc, "Static Hoeffding", static_acc))
        comparisons.append(compute_paired_comparison("ALA 3.0 vs ADWIN (Resets)", "ALA_3_0", "Drift Resets", "ALA 3.0", recurrent_resets, "Standard ADWIN", adwin_resets))

    # 2. Workstream B: RLA 3.0 vs RLA 2.0 (Spambase)
    rla_path = results_dir / "rla_3_0_spambase_results.json"
    if rla_path.exists():
        with open(rla_path, "r", encoding="utf-8") as f:
            rla_data = json.load(f)
        df_rla = pd.DataFrame(rla_data)
        
        for cond in ["clean", "symmetric_20", "asymmetric_20"]:
            df_sub = df_rla[df_rla["noise_condition"] == cond]
            rla3_rec = df_sub[df_sub["model_type"] == "rla_3_0_asymmetric"].sort_values("seed")["minority_recall"].values
            rla2_rec = df_sub[df_sub["model_type"] == "adaptive_ml_rla_v2"].sort_values("seed")["minority_recall"].values
            rla3_f1 = df_sub[df_sub["model_type"] == "rla_3_0_asymmetric"].sort_values("seed")["minority_f1"].values
            rla2_f1 = df_sub[df_sub["model_type"] == "adaptive_ml_rla_v2"].sort_values("seed")["minority_f1"].values

            comparisons.append(compute_paired_comparison(f"RLA 3.0 vs RLA 2.0 [{cond}] (Recall)", "RLA_3_0", f"Minority Recall ({cond})", "RLA 3.0", rla3_rec, "RLA 2.0 Spatial KNN", rla2_rec))
            comparisons.append(compute_paired_comparison(f"RLA 3.0 vs RLA 2.0 [{cond}] (F1)", "RLA_3_0", f"Minority F1 ({cond})", "RLA 3.0", rla3_f1, "RLA 2.0 Spatial KNN", rla2_f1))

    # 3. Workstream C: Minority Intelligence 2.0 (Credit Card)
    min_path = results_dir / "minority_2_0_creditcard_results.json"
    if min_path.exists():
        with open(min_path, "r", encoding="utf-8") as f:
            min_data = json.load(f)
        df_min = pd.DataFrame(min_data)

        cal_rec = df_min[df_min["model_type"] == "minority_2_0_calibrated"].sort_values("seed")["minority_recall"].values
        v1_rec = df_min[df_min["model_type"] == "adaptive_ml_minority_v1"].sort_values("seed")["minority_recall"].values
        unw_rec = df_min[df_min["model_type"] == "standard_unweighted"].sort_values("seed")["minority_recall"].values

        cal_fp = df_min[df_min["model_type"] == "minority_2_0_calibrated"].sort_values("seed")["false_positives"].values
        v1_fp = df_min[df_min["model_type"] == "class_weighted_556"].sort_values("seed")["false_positives"].values

        comparisons.append(compute_paired_comparison("Minority 2.0 vs v1 (Recall)", "Minority_2_0", "Minority Recall", "Minority 2.0 Calibrated", cal_rec, "Minority 1.0 (556:1)", v1_rec))
        comparisons.append(compute_paired_comparison("Minority 2.0 vs Unweighted (Recall)", "Minority_2_0", "Minority Recall", "Minority 2.0 Calibrated", cal_rec, "Unweighted Baseline", unw_rec))
        comparisons.append(compute_paired_comparison("Minority 2.0 vs 556:1 (False Positives)", "Minority_2_0", "False Positives", "Minority 2.0 Calibrated", cal_fp, "Class Weighted 556", v1_fp))

    # 4. Workstream D: RAO 2.0 vs AdamW (CoverTypeMLP)
    rao_path = results_dir / "rao_2_0_covertype_results.json"
    if rao_path.exists():
        with open(rao_path, "r", encoding="utf-8") as f:
            rao_data = json.load(f)
        df_rao = pd.DataFrame(rao_data)

        rao_mem = df_rao[df_rao["optimizer"] == "vectorized_low_memory_adamw"].sort_values("seed")["optimizer_state_mb"].values
        std_mem = df_rao[df_rao["optimizer"] == "standard_adamw"].sort_values("seed")["optimizer_state_mb"].values

        rao_lat = df_rao[df_rao["optimizer"] == "vectorized_low_memory_adamw"].sort_values("seed")["p50_latency_us"].values / 1000.0
        std_lat = df_rao[df_rao["optimizer"] == "standard_adamw"].sort_values("seed")["p50_latency_us"].values / 1000.0

        rao_loss = df_rao[df_rao["optimizer"] == "vectorized_low_memory_adamw"].sort_values("seed")["final_loss"].values
        std_loss = df_rao[df_rao["optimizer"] == "standard_adamw"].sort_values("seed")["final_loss"].values

        comparisons.append(compute_paired_comparison("RAO 2.0 vs AdamW (Memory MB)", "RAO_2_0", "State Memory (MB)", "RAO 2.0 Vectorized", rao_mem, "PyTorch AdamW", std_mem))
        comparisons.append(compute_paired_comparison("RAO 2.0 vs AdamW (P50 Latency ms)", "RAO_2_0", "P50 Latency (ms)", "RAO 2.0 Vectorized", rao_lat, "PyTorch AdamW", std_lat))
        comparisons.append(compute_paired_comparison("RAO 2.0 vs AdamW (Final Loss)", "RAO_2_0", "Final Loss", "RAO 2.0 Vectorized", rao_loss, "PyTorch AdamW", std_loss))

    # 5. Workstream E: ULC-v5 vs ULC-v4.1 (Electricity)
    ulc_path = results_dir / "ulc_v5_electricity_results.json"
    if ulc_path.exists():
        with open(ulc_path, "r", encoding="utf-8") as f:
            ulc_data = json.load(f)
        df_ulc = pd.DataFrame(ulc_data)

        v5_acc = df_ulc[df_ulc["model_type"] == "ulc_v5_calibrated"].sort_values("seed")["accuracy"].values
        v4_acc = df_ulc[df_ulc["model_type"] == "ulc_v4_1_production"].sort_values("seed")["accuracy"].values
        stat_acc = df_ulc[df_ulc["model_type"] == "static_baseline"].sort_values("seed")["accuracy"].values

        v5_resets = df_ulc[df_ulc["model_type"] == "ulc_v5_calibrated"].sort_values("seed")["drift_resets"].values
        v4_resets = df_ulc[df_ulc["model_type"] == "ulc_v4_1_production"].sort_values("seed")["drift_resets"].values

        comparisons.append(compute_paired_comparison("ULC-v5 vs ULC-v4.1 (Acc)", "ULC_v5", "Accuracy", "ULC-v5 Calibrated", v5_acc, "ULC-v4.1 Baseline", v4_acc))
        comparisons.append(compute_paired_comparison("ULC-v5 vs Static (Acc)", "ULC_v5", "Accuracy", "ULC-v5 Calibrated", v5_acc, "Uncontrolled Static", stat_acc))
        comparisons.append(compute_paired_comparison("ULC-v5 vs ULC-v4.1 (Resets)", "ULC_v5", "Drift Resets", "ULC-v5 Calibrated", v5_resets, "ULC-v4.1 Baseline", v4_resets))

    # 6. Workstream F: Cross-Pillar Interactions
    cross_path = results_dir / "cross_pillar_results.json"
    if cross_path.exists():
        with open(cross_path, "r", encoding="utf-8") as f:
            cross_data = json.load(f)
        df_cross = pd.DataFrame(cross_data)

        full_acc = df_cross[df_cross["config_name"] == "full_next_gen_system"].sort_values("seed")["accuracy"].values
        ala_acc = df_cross[df_cross["config_name"] == "ala_3_0_alone"].sort_values("seed")["accuracy"].values
        rla_acc = df_cross[df_cross["config_name"] == "rla_3_0_alone"].sort_values("seed")["accuracy"].values

        comparisons.append(compute_paired_comparison("Full System vs ALA Alone (Acc)", "Cross_Pillar", "Accuracy", "Full Next-Gen System", full_acc, "ALA 3.0 Alone", ala_acc))
        comparisons.append(compute_paired_comparison("Full System vs RLA Alone (Acc)", "Cross_Pillar", "Accuracy", "Full Next-Gen System", full_acc, "RLA 3.0 Alone", rla_acc))

    # 7. Workstream G: Ablations
    ablation_path = results_dir / "ablation_results.json"
    if ablation_path.exists():
        with open(ablation_path, "r", encoding="utf-8") as f:
            ablation_data = json.load(f)
        df_abl = pd.DataFrame(ablation_data)

        # ALA: Full vs No Memory
        ala_full = df_abl[df_abl["variant"] == "ala_full"].sort_values("seed")["primary_metric"].values
        ala_no_mem = df_abl[df_abl["variant"] == "ala_no_memory"].sort_values("seed")["primary_metric"].values
        if len(ala_full) == len(ala_no_mem) and len(ala_full) > 0:
            comparisons.append(compute_paired_comparison("ALA Ablation: Full vs No Memory (Acc)", "Ablations", "Accuracy", "ALA Full", ala_full, "ALA No Memory", ala_no_mem))

        # ALA Resets: Full vs No Memory
        ala_full_res = df_abl[df_abl["variant"] == "ala_full"].sort_values("seed")["resets"].values
        ala_no_mem_res = df_abl[df_abl["variant"] == "ala_no_memory"].sort_values("seed")["resets"].values
        if len(ala_full_res) == len(ala_no_mem_res) and len(ala_full_res) > 0:
            comparisons.append(compute_paired_comparison("ALA Ablation: Full vs No Memory (Resets)", "Ablations", "Resets", "ALA Full", ala_full_res, "ALA No Memory", ala_no_mem_res))

        # Minority: Full vs Linear Cost
        min_full_fp = df_abl[df_abl["variant"] == "min_full"].sort_values("seed")["false_positives"].values
        min_lin_fp = df_abl[df_abl["variant"] == "min_linear_cost"].sort_values("seed")["false_positives"].values
        if len(min_full_fp) == len(min_lin_fp) and len(min_full_fp) > 0:
            comparisons.append(compute_paired_comparison("Minority Ablation: Full vs Linear Cost (FP)", "Ablations", "False Positives", "Min Full", min_full_fp, "Min Linear Cost", min_lin_fp))

        # ULC: Full vs No Utility
        ulc_full = df_abl[df_abl["variant"] == "ulc_v5_full"].sort_values("seed")["primary_metric"].values
        ulc_no_ut = df_abl[df_abl["variant"] == "ulc_v5_no_utility"].sort_values("seed")["primary_metric"].values
        if len(ulc_full) == len(ulc_no_ut) and len(ulc_full) > 0:
            comparisons.append(compute_paired_comparison("ULC Ablation: Full vs No Utility (Acc)", "Ablations", "Accuracy", "ULC-v5 Full", ulc_full, "ULC-v5 No Utility", ulc_no_ut))

    # Apply Holm-Bonferroni correction within each family
    families = set(c["family"] for c in comparisons)
    for fam in families:
        fam_comps = [c for c in comparisons if c["family"] == fam]
        p_ttests = [c["p_ttest"] for c in fam_comps]
        p_wilcox = [c["p_wilcoxon"] for c in fam_comps]
        
        adj_ttest = holm_bonferroni_adjust(p_ttests)
        adj_wilcox = holm_bonferroni_adjust(p_wilcox)
        
        for c, adj_t, adj_w in zip(fam_comps, adj_ttest, adj_wilcox):
            c["p_ttest_holm"] = adj_t
            c["p_wilcoxon_holm"] = adj_w
            c["significant_alpha_05"] = bool(adj_t < 0.05 or adj_w < 0.05)
            c["significant_alpha_01"] = bool(adj_t < 0.01 or adj_w < 0.01)

    # Save to JSON and CSV
    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "stage_12_statistical_summary.json"
    out_csv = out_dir / "stage_12_statistical_summary.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)

    pd.DataFrame(comparisons).to_csv(out_csv, index=False)
    print(f"\nSuccessfully evaluated {len(comparisons)} statistical comparisons across {len(families)} families.")
    print(f"Results written to {out_json} and {out_csv}")

    # Print summary table
    print("\n" + "="*120)
    print(f"{'Comparison':<45s} | {'Diff (95% CI)':<22s} | {'Cohen dz':<9s} | {'p (t-test)':<10s} | {'p (adj)':<10s} | {'Sig (0.01)'}")
    print("="*120)
    for c in comparisons:
        ci_str = f"{c['mean_diff']:+.4f} [{c['ci_95_lower']:+.3f}, {c['ci_95_upper']:+.3f}]"
        sig_str = "YES (***)" if c["significant_alpha_01"] else ("YES (*)" if c["significant_alpha_05"] else "NO")
        print(f"{c['comparison']:<45s} | {ci_str:<22s} | {c['cohens_dz']:+9.2f} | {c['p_ttest']:<10.4e} | {c['p_ttest_holm']:<10.4e} | {sig_str}")
    print("="*120)


if __name__ == "__main__":
    main()
