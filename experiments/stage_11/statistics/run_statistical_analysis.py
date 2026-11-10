"""
Stage 11 — Workstream H: Comprehensive Confirmatory Statistical Analysis.

Performs rigorous statistical testing across all Stage 11 experimental families:
1. Family 1: ALA Adaptation on Electricity (Elec2)
2. Family 2: RLA Robustness on Spambase
3. Family 3: Minority Intelligence on Credit Card Fraud (ULB)
4. Family 4: RAO Resource Efficiency on CoverType
5. Family 5: ULC-v4.1 End-to-End Coordination on Electricity

Computes:
- Mean, Std, Median, 95% Confidence Intervals
- Paired Cohen's dz effect sizes
- Paired Student's t-tests
- Wilcoxon signed-rank tests
- Holm-Bonferroni step-down family-wise error rate corrections
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats


def holm_bonferroni(p_values: List[float]) -> List[float]:
    """Applies Holm-Bonferroni step-down correction to a list of raw p-values."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0

    for rank, (orig_idx, p) in enumerate(indexed):
        adj_p = min(1.0, (m - rank) * p)
        running_max = max(running_max, adj_p)
        adjusted[orig_idx] = running_max

    return adjusted


def compute_paired_stats(
    arr_a: np.ndarray,
    arr_b: np.ndarray,
    name_a: str,
    name_b: str,
    metric_name: str,
    family_name: str,
) -> Dict[str, Any]:
    n = len(arr_a)
    diffs = arr_a - arr_b
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    sem = std_diff / np.sqrt(n) if n > 1 else 0.0

    # 95% Confidence interval
    t_crit = float(stats.t.ppf(0.975, df=n - 1)) if n > 1 else 1.96
    ci_lower = mean_diff - t_crit * sem
    ci_upper = mean_diff + t_crit * sem

    # Effect size: paired Cohen's dz
    cohens_dz = float(mean_diff / std_diff) if std_diff > 1e-12 else 0.0

    # Paired Student's t-test
    if std_diff > 1e-12:
        t_stat, p_val_t = stats.ttest_rel(arr_a, arr_b)
    else:
        t_stat, p_val_t = 0.0, 1.0

    # Wilcoxon signed-rank test
    try:
        w_stat, p_val_w = stats.wilcoxon(diffs, zero_method="wilcox")
    except Exception:
        w_stat, p_val_w = 0.0, 1.0

    return {
        "family": family_name,
        "metric": metric_name,
        "candidate": name_a,
        "baseline": name_b,
        "n_seeds": n,
        "mean_candidate": float(np.mean(arr_a)),
        "std_candidate": float(np.std(arr_a, ddof=1)),
        "mean_baseline": float(np.mean(arr_b)),
        "std_baseline": float(np.std(arr_b, ddof=1)),
        "mean_diff": mean_diff,
        "std_diff": std_diff,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "cohens_dz": cohens_dz,
        "t_statistic": float(t_stat),
        "raw_p_value_ttest": float(p_val_t),
        "wilcoxon_statistic": float(w_stat),
        "raw_p_value_wilcoxon": float(p_val_w),
    }


def analyze_ala_family(results_dir: Path) -> List[Dict[str, Any]]:
    ala_file = results_dir / "ala_electricity_results.json"
    if not ala_file.exists():
        return []
    with open(ala_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    cand_acc = df[df["model_type"] == "adaptive_ml_ala"].sort_values("seed")["accuracy"].values
    cand_f1 = df[df["model_type"] == "adaptive_ml_ala"].sort_values("seed")["macro_f1"].values

    comparisons = []
    for base in ["standard_adwin", "static_hoeffding", "static_sgd"]:
        base_df = df[df["model_type"] == base].sort_values("seed")
        base_acc = base_df["accuracy"].values
        base_f1 = base_df["macro_f1"].values

        comparisons.append(compute_paired_stats(cand_acc, base_acc, "adaptive_ml_ala", base, "accuracy", "Family 1: ALA Electricity"))
        comparisons.append(compute_paired_stats(cand_f1, base_f1, "adaptive_ml_ala", base, "macro_f1", "Family 1: ALA Electricity"))

    return comparisons


def analyze_rla_family(results_dir: Path) -> List[Dict[str, Any]]:
    rla_file = results_dir / "rla_spambase_results.json"
    if not rla_file.exists():
        return []
    with open(rla_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    comparisons = []
    # Analyze symmetric 10% and 20% noise
    for n_rate in [0.10, 0.20]:
        sub = df[(df["noise_type"] == "symmetric") & (df["noise_rate"] == n_rate)]
        cand_acc = sub[sub["model_type"] == "adaptive_ml_rla"].sort_values("seed")["accuracy"].values
        cand_f1 = sub[sub["model_type"] == "adaptive_ml_rla"].sort_values("seed")["macro_f1"].values

        for base in ["standard_erm", "gce_surrogate"]:
            base_acc = sub[sub["model_type"] == base].sort_values("seed")["accuracy"].values
            base_f1 = sub[sub["model_type"] == base].sort_values("seed")["macro_f1"].values

            comparisons.append(compute_paired_stats(cand_acc, base_acc, "adaptive_ml_rla", base, f"accuracy_sym_{int(n_rate*100)}pct", "Family 2: RLA Spambase"))
            comparisons.append(compute_paired_stats(cand_f1, base_f1, "adaptive_ml_rla", base, f"macro_f1_sym_{int(n_rate*100)}pct", "Family 2: RLA Spambase"))

    return comparisons


def analyze_minority_family(results_dir: Path) -> List[Dict[str, Any]]:
    min_file = results_dir / "minority_creditcard_results.json"
    if not min_file.exists():
        return []
    with open(min_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    cand_rec = df[df["model_type"] == "adaptive_ml_minority"].sort_values("seed")["minority_recall"].values
    cand_f1 = df[df["model_type"] == "adaptive_ml_minority"].sort_values("seed")["minority_f1"].values
    cand_fp = df[df["model_type"] == "adaptive_ml_minority"].sort_values("seed")["false_positives"].values

    comparisons = []
    for base in ["standard_unweighted", "class_weighted", "random_oversampling"]:
        base_df = df[df["model_type"] == base].sort_values("seed")
        base_rec = base_df["minority_recall"].values
        base_f1 = base_df["minority_f1"].values
        base_fp = base_df["false_positives"].values

        comparisons.append(compute_paired_stats(cand_rec, base_rec, "adaptive_ml_minority", base, "minority_recall", "Family 3: Minority CreditCard"))
        comparisons.append(compute_paired_stats(cand_f1, base_f1, "adaptive_ml_minority", base, "minority_f1", "Family 3: Minority CreditCard"))
        comparisons.append(compute_paired_stats(cand_fp, base_fp, "adaptive_ml_minority", base, "false_positives", "Family 3: Minority CreditCard"))

    return comparisons


def analyze_rao_family(results_dir: Path) -> List[Dict[str, Any]]:
    rao_file = results_dir / "rao_resource_results.json"
    if not rao_file.exists():
        return []
    with open(rao_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    cand_df = df[df["optimizer"] == "adaptive_ml_low_memory_adamw"].sort_values("seed")
    base_df = df[df["optimizer"] == "standard_adamw"].sort_values("seed")

    comparisons = []
    # Optimizer state bytes
    comparisons.append(compute_paired_stats(
        cand_df["optimizer_state_mb"].values,
        base_df["optimizer_state_mb"].values,
        "adaptive_ml_low_memory_adamw",
        "standard_adamw",
        "optimizer_state_mb",
        "Family 4: RAO CoverType",
    ))
    # Throughput
    comparisons.append(compute_paired_stats(
        cand_df["throughput_samples_per_sec"].values,
        base_df["throughput_samples_per_sec"].values,
        "adaptive_ml_low_memory_adamw",
        "standard_adamw",
        "throughput_samples_per_sec",
        "Family 4: RAO CoverType",
    ))
    # Latency P50
    comparisons.append(compute_paired_stats(
        cand_df["p50_latency_us"].values,
        base_df["p50_latency_us"].values,
        "adaptive_ml_low_memory_adamw",
        "standard_adamw",
        "p50_latency_us",
        "Family 4: RAO CoverType",
    ))
    return comparisons


def analyze_ulc_family(results_dir: Path) -> List[Dict[str, Any]]:
    ulc_file = results_dir / "ulc_v4_1_electricity_results.json"
    if not ulc_file.exists():
        return []
    with open(ulc_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    cand_acc = df[df["config_name"] == "ulc_v4_1_production"].sort_values("seed")["accuracy"].values
    cand_f1 = df[df["config_name"] == "ulc_v4_1_production"].sort_values("seed")["macro_f1"].values

    comparisons = []
    for base in ["ulc_v4_legacy", "ala_only", "rla_only", "static_baseline"]:
        base_df = df[df["config_name"] == base].sort_values("seed")
        base_acc = base_df["accuracy"].values
        base_f1 = base_df["macro_f1"].values

        comparisons.append(compute_paired_stats(cand_acc, base_acc, "ulc_v4_1_production", base, "accuracy", "Family 5: ULC-v4.1 Electricity"))
        comparisons.append(compute_paired_stats(cand_f1, base_f1, "ulc_v4_1_production", base, "macro_f1", "Family 5: ULC-v4.1 Electricity"))

    return comparisons


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Workstream H — Confirmatory Statistical Analysis")
    print("=====================================================================")

    results_dir = Path("experiments/stage_11/results")
    all_comparisons = []

    all_comparisons.extend(analyze_ala_family(results_dir))
    all_comparisons.extend(analyze_rla_family(results_dir))
    all_comparisons.extend(analyze_minority_family(results_dir))
    all_comparisons.extend(analyze_rao_family(results_dir))
    all_comparisons.extend(analyze_ulc_family(results_dir))

    # Apply Holm-Bonferroni correction within each family
    families = sorted(list(set(c["family"] for c in all_comparisons)))
    for fam in families:
        fam_comps = [c for c in all_comparisons if c["family"] == fam]
        raw_p_ttest = [c["raw_p_value_ttest"] for c in fam_comps]
        raw_p_wilc = [c["raw_p_value_wilcoxon"] for c in fam_comps]

        adj_p_ttest = holm_bonferroni(raw_p_ttest)
        adj_p_wilc = holm_bonferroni(raw_p_wilc)

        for i, c in enumerate(fam_comps):
            c["holm_bonferroni_p_ttest"] = adj_p_ttest[i]
            c["holm_bonferroni_p_wilcoxon"] = adj_p_wilc[i]
            c["is_significant_adj_05"] = bool(adj_p_wilc[i] < 0.05)

    out_json = results_dir / "statistical_summary_results.json"
    out_csv = results_dir / "statistical_summary_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_comparisons, f, indent=2)

    pd.DataFrame(all_comparisons).to_csv(out_csv, index=False)
    print(f"Processed {len(all_comparisons)} pairwise comparisons across {len(families)} families.")
    print(f"Results saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()
