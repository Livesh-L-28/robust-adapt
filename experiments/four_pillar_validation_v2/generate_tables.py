"""
Generate formatted Markdown tables from raw_study_results.json.
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def load_data():
    with open("experiments/four_pillar_validation_v2/raw_study_results.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_markdown_tables():
    data = load_data()
    models = data["models"]
    hypothesis_tests = data["hypothesis_tests"]
    
    # 1. Main Performance Comparison Table
    print("### Comprehensive Performance Metrics across 5 Seeds (Mean ± Std)\n")
    print("| Configuration | Accuracy (%) | Balanced Acc (%) | Minority Recall (%) | Minority F1 | Macro F1 | Brier Score | False Resets | Latency (ms) |")
    print("|---|---|---|---|---|---|---|---|---|")
    
    for model_name, m_data in models.items():
        s = m_data["aggregate"]
        acc = f"{s['accuracy']['mean']*100:.2f} ± {s['accuracy']['std']*100:.2f}"
        bacc = f"{s['balanced_accuracy']['mean']*100:.2f} ± {s['balanced_accuracy']['std']*100:.2f}"
        rec = f"{s['minority_recall']['mean']*100:.2f} ± {s['minority_recall']['std']*100:.2f}"
        mf1 = f"{s['minority_f1']['mean']:.3f} ± {s['minority_f1']['std']:.3f}"
        macro_f1 = f"{s['macro_f1']['mean']:.3f} ± {s['macro_f1']['std']:.3f}"
        brier = f"{s['brier_score']['mean']:.3f} ± {s['brier_score']['std']:.3f}"
        f_res = f"{s['false_resets']['mean']:.1f} ± {s['false_resets']['std']:.1f}"
        lat = f"{s['latency_mean_ms']['mean']:.3f} ± {s['latency_mean_ms']['std']:.3f}"
        print(f"| **{model_name}** | {acc} | {bacc} | {rec} | {mf1} | {macro_f1} | {brier} | {f_res} | {lat} |")
        
    print("\n\n### Statistical Significance Tests (Paired Two-Tailed t-Tests on Macro F1 and Balanced Accuracy)\n")
    print("| Comparison (Target vs Baseline) | Metric | Target Mean | Baseline Mean | Diff (Δ) | t-statistic | p-value | Significant (p < 0.05) |")
    print("|---|---|---|---|---|---|---|---|")
    for comp, stats in hypothesis_tests.items():
        for metric in ["macro_f1", "balanced_accuracy"]:
            m_stats = stats[metric]
            t_mean = f"{m_stats['ulc_v3_mean']:.4f}"
            b_mean = f"{m_stats['baseline_mean']:.4f}"
            diff = f"{m_stats['diff_mean']:+.4f}"
            t_stat = f"{m_stats['t_stat']:.3f}"
            p_val = f"{m_stats['p_value']:.4f}"
            sig = "Yes (p < 0.01)" if m_stats["p_value"] < 0.01 else ("Yes (p < 0.05)" if m_stats["p_value"] < 0.05 else "No")
            print(f"| **{comp}** | {metric} | {t_mean} | {b_mean} | {diff} | {t_stat} | {p_val} | {sig} |")
            
    print("\n\n### Latency Distribution and Memory Footprint\n")
    print("| Configuration | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Max Latency (ms) | Optimizer State (Bytes) |")
    print("|---|---|---|---|---|---|")
    for model_name, m_data in models.items():
        s = m_data["aggregate"]
        p50 = f"{s['latency_p50_ms']['mean']:.3f}"
        p95 = f"{s['latency_p95_ms']['mean']:.3f}"
        p99 = f"{s['latency_p99_ms']['mean']:.3f}"
        pmax = f"{s['latency_max_ms']['mean']:.3f}"
        state_b = f"{s['optimizer_state_bytes']['mean']:.0f}"
        print(f"| **{model_name}** | {p50} | {p95} | {p99} | {pmax} | {state_b} |")

if __name__ == "__main__":
    generate_markdown_tables()
