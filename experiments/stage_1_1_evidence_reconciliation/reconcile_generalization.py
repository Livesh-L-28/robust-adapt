"""
Stage 1.1: Generalization Evidence Reconciliation Script.
Audits the provenance, dataset identity, licensing, and synthetic vs real-world status
of all streams in the generalization test battery, classifying each claim under strict audit criteria.
"""

import os
import sys
import json
import csv

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = "experiments/stage_1_1_evidence_reconciliation"
os.makedirs(OUT_DIR, exist_ok=True)

with open("experiments/ulc_v3_independent_audit/generalization_battery_results.json", "r", encoding="utf-8") as f:
    battery_data = json.load(f)

# Dataset Provenance and Audit Evaluation
datasets = [
    {
        "domain_or_regime": "Concept Drift (Abrupt)",
        "generator_function": "gen_drift_stream(drift_type='abrupt')",
        "data_provenance": "Synthetic generator in audit_generalization.py (np.random.RandomState)",
        "license": "N/A (In-memory generated)",
        "real_world_status": "SYNTHETIC",
        "sample_count": 1500,
        "feature_dim": 4,
        "class_imbalance": "90:10",
        "temporal_controls": "Strict causal sequential streaming (batch by batch)",
        "ulc_v3_macro_f1": battery_data["drift_variations"]["abrupt"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["drift_variations"]["abrupt"]["Uncoordinated_Three_Pillars"]["macro_f1"],
        "verification_verdict": "VERIFIED (SYNTHETIC SIMULATION)",
        "scientific_finding": "ULC-v3 lags uncoordinated three pillars (0.509 vs 0.548) due to 3-step warning deadband delay."
    },
    {
        "domain_or_regime": "Concept Drift (Gradual)",
        "generator_function": "gen_drift_stream(drift_type='gradual')",
        "data_provenance": "Synthetic generator in audit_generalization.py (np.random.RandomState)",
        "license": "N/A (In-memory generated)",
        "real_world_status": "SYNTHETIC",
        "sample_count": 1500,
        "feature_dim": 4,
        "class_imbalance": "90:10",
        "temporal_controls": "Strict causal sequential streaming",
        "ulc_v3_macro_f1": battery_data["drift_variations"]["gradual"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["drift_variations"]["gradual"]["Uncoordinated_Three_Pillars"]["macro_f1"],
        "verification_verdict": "VERIFIED (SYNTHETIC SIMULATION)",
        "scientific_finding": "Continuous models adapt smoothly without requiring discrete resets."
    },
    {
        "domain_or_regime": "Concept Drift (Incremental)",
        "generator_function": "gen_drift_stream(drift_type='incremental')",
        "data_provenance": "Synthetic generator in audit_generalization.py (np.random.RandomState)",
        "license": "N/A (In-memory generated)",
        "real_world_status": "SYNTHETIC",
        "sample_count": 1500,
        "feature_dim": 4,
        "class_imbalance": "90:10",
        "temporal_controls": "Strict causal sequential streaming",
        "ulc_v3_macro_f1": battery_data["drift_variations"]["incremental"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["drift_variations"]["incremental"]["Uncoordinated_Three_Pillars"]["macro_f1"],
        "verification_verdict": "VERIFIED (SYNTHETIC SIMULATION)",
        "scientific_finding": "Linear drift velocity allows continuous tracking."
    },
    {
        "domain_or_regime": "Noise Regime (Burst Noise)",
        "generator_function": "gen_noise_stream(noise_type='noise_burst')",
        "data_provenance": "Synthetic generator in audit_generalization.py (np.random.RandomState)",
        "license": "N/A (In-memory generated)",
        "real_world_status": "SYNTHETIC",
        "sample_count": 1500,
        "feature_dim": 4,
        "class_imbalance": "90:10",
        "temporal_controls": "Strict causal sequential streaming",
        "ulc_v3_macro_f1": battery_data["noise_variations"]["noise_burst"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["noise_variations"]["noise_burst"]["ALA_Only"]["macro_f1"],
        "verification_verdict": "VERIFIED (SYNTHETIC SIMULATION)",
        "scientific_finding": "ULC-v3 suppresses false alarms (1.0 vs 10.0 false resets) via loss-trend gating."
    },
    {
        "domain_or_regime": "Extreme Imbalance (99.9:0.1)",
        "generator_function": "gen_imbalance_stream(imbalance_ratio=0.001)",
        "data_provenance": "Synthetic generator in audit_generalization.py (np.random.RandomState)",
        "license": "N/A (In-memory generated)",
        "real_world_status": "SYNTHETIC",
        "sample_count": 5000,
        "feature_dim": 4,
        "class_imbalance": "99.9:0.1",
        "temporal_controls": "Strict causal sequential streaming",
        "ulc_v3_macro_f1": battery_data["imbalance_variations"]["99.9:0.1"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["imbalance_variations"]["99.9:0.1"]["Static_Baseline"]["macro_f1"],
        "verification_verdict": "VERIFIED (SYNTHETIC SIMULATION)",
        "scientific_finding": "ULC-v3 maintains non-zero minority recall (27.21%) where standard tree models collapse to 0.0%."
    },
    {
        "domain_or_regime": "Financial Transaction Fraud",
        "generator_function": "gen_financial_fraud_stream()",
        "data_provenance": "Synthetic Gaussian generator in audit_generalization.py (rng.randn * 1.2 + mean shift)",
        "license": "NONE (NO EXTERNAL DATASET INGESTED)",
        "real_world_status": "SYNTHETIC SIMULATION (NOT REAL DATA)",
        "sample_count": 2500,
        "feature_dim": 6,
        "class_imbalance": "96:4 (Simulated bursts)",
        "temporal_controls": "Simulated batch sequence",
        "ulc_v3_macro_f1": battery_data["financial_fraud"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["financial_fraud"]["Uncoordinated_Three_Pillars"]["macro_f1"],
        "verification_verdict": "NOT VERIFIABLE AS REAL-WORLD BENCHMARK",
        "scientific_finding": "Claim in FINAL_RESEARCH_VERDICT.md describing this as a 'realistic streaming application' was misleading; code used Gaussian noise generator."
    },
    {
        "domain_or_regime": "Industrial Predictive Maintenance",
        "generator_function": "gen_predictive_maintenance_stream()",
        "data_provenance": "Synthetic sensor degradation generator in audit_generalization.py",
        "license": "NONE (NO EXTERNAL DATASET INGESTED)",
        "real_world_status": "SYNTHETIC SIMULATION (NOT REAL DATA)",
        "sample_count": 2000,
        "feature_dim": 5,
        "class_imbalance": "85:15 (Simulated degradation)",
        "temporal_controls": "Simulated degradation curve",
        "ulc_v3_macro_f1": battery_data["predictive_maintenance"]["MultiObjective_ULC_v3"]["macro_f1"],
        "best_baseline_macro_f1": battery_data["predictive_maintenance"]["Uncoordinated_Three_Pillars"]["macro_f1"],
        "verification_verdict": "NOT VERIFIABLE AS REAL-WORLD BENCHMARK",
        "scientific_finding": "Simulated degradation confirmed in Python code; no industrial telemetry (e.g., NASA C-MAPSS or AI4I) was ingested."
    }
]

# Export Generalization Matrix CSV
csv_path = os.path.join(OUT_DIR, "generalization_evidence_matrix.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(datasets[0].keys()))
    writer.writeheader()
    writer.writerows(datasets)

summary = {
    "audit_id": "STAGE1.1-GENERALIZATION-RECONCILIATION",
    "total_evaluated_regimes": len(datasets),
    "synthetic_benchmarks_verified": 5,
    "real_world_benchmarks_verified": 0,
    "unverifiable_real_world_claims": 2,
    "governance_classification": {
        "synthetic_drift_battery": "VERIFIED (SYNTHETIC SIMULATION)",
        "synthetic_noise_battery": "VERIFIED (SYNTHETIC SIMULATION)",
        "synthetic_imbalance_battery": "VERIFIED (SYNTHETIC SIMULATION)",
        "financial_fraud_stream": "NOT VERIFIABLE AS REAL DATA (SYNTHETIC SIMULATION ONLY)",
        "predictive_maintenance_stream": "NOT VERIFIABLE AS REAL DATA (SYNTHETIC SIMULATION ONLY)"
    },
    "key_architectural_findings": [
        "ULC-v3 excels in streams with simultaneous concept drift and adversarial noise bursts (false resets suppressed to 1.0 vs 10.0).",
        "ULC-v3 retains robust minority detection under extreme class imbalance (99.9:0.1).",
        "ULC-v3 suffers from an adaptation lag in pure noise-free concept drift, trailing uncoordinated gradient models by +0.04 to +0.14 Macro F1 due to 3-step warning deadbands."
    ]
}

json_path = os.path.join(OUT_DIR, "generalization_reconciliation.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("Generalization Evidence Reconciliation:")
print(f"[OK] Wrote generalization matrix CSV to {csv_path}")
print(f"[OK] Wrote summary to {json_path}")
print("\nDataset Status Summary:")
for d in datasets:
    print(f"  * {d['domain_or_regime']:35s} | {d['real_world_status']:30s} | {d['verification_verdict']}")
