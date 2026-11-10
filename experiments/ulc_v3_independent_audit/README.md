# ULC-v3 Independent Research Audit & Four-Pillar Validation

**Workspace:** `C:\projects\AdaptiveML`  
**Audit Directory:** [`experiments/ulc_v3_independent_audit/`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit)  
**Target Source:** [`experiments/four_pillar_validation_v2/`](file:///c:/projects/AdaptiveML/experiments/four_pillar_validation_v2)  
**Baseline Git Commit:** `67e9ef1b347ca223828a1f225e85e35a086a1f30` (Branch `master`)  
**Stage:** Research Validation v3 — Stage 1  
**Execution Environment:** Windows 11 AMD64 (Build 26200), Python 3.14.3, PyTorch 2.12.1+cpu  
**Audit Mode:** Independent Scientific Quality Engine (Evidence-Driven)  

---

## 1. Executive Overview

This directory contains the complete deliverables, reproducible source scripts, empirical datasets, and analytical reports for the **Stage 1 Complete Research Validation Audit** of AdaptiveML's four-pillar learning architecture:
1. **Adaptive Learning Algorithms (ALA)** — Vectorized Hoeffding Trees with ADWIN drift detection.
2. **Robust Learning Algorithms (RLA)** — Loss-attenuated robust classifiers with adaptive score smoothing.
3. **Resource-Aware Optimization (RAO)** — Memory-budgeted optimizers (`LowMemoryAdamW`).
4. **Unified Learning Controller (ULC)** — Multi-objective arbitration automaton (evaluated up to ULC-v3).

### Strict Governance & Integrity Boundaries
- **Baseline Integrity:** Grounded strictly on commit `67e9ef1b347ca223828a1f225e85e35a086a1f30`.
- **Zero Production Modifications:** Production code in `adaptive_ml/` has not been altered.
- **Preservation of Experiment Artifacts:** Original outputs in `experiments/four_pillar_validation_v2/` remain strictly unmodified.
- **DEF-004 Trademark Status:** Remains strictly **OPEN and UNRESOLVED**; candidate names remain **UNVERIFIED**.
- **Phase 17 Status:** Strictly **LOCKED / UNAUTHORIZED** pending formal owner sign-off.
- **Repository Safety:** Zero Git commits, rebases, amends, tags, or package publishing operations have been executed.

---

## 2. Master Deliverable Directory Index

```
experiments/ulc_v3_independent_audit/
├── README.md                                  # Master index & execution guide (this document)
├── AUDIT_PROTOCOL.md                          # Methodological framework & FWER correction protocol
├── AUDIT_MANIFEST.json                        # Cryptographic manifest of all artifacts, hashes, & gates
├── REPRODUCTION_AUDIT.md                      # Bit-for-bit reproduction verification (11 models × 5 seeds)
├── STATISTICAL_REANALYSIS.md                  # Paired tests, Holm corrections, & N=20 power study
├── PARETO_ANALYSIS.md                         # 9-objective Pareto frontier & dominance matrix
├── MINORITY_CLASS_ANALYSIS.md                 # Threshold sweep, regime autopsy, & doc discrepancy audit
├── ULC_IMPLEMENTATION_AUDIT.md                # Codebase verification, attribute bugs, & 5-stage ablation
├── MEMORY_AND_ENVIRONMENT_AUDIT.md            # Memory accounting, RSS profiling, & multi-version runtime matrix
├── GENERALIZATION_RESULTS.md                  # Multi-regime battery (5 drifts, 4 noise models, 2 domain streams)
├── FINAL_RESEARCH_VERDICT.md                  # Synthesized 9-dimension verdict & owner recommendations
│
├── [Executable Audit Scripts]
│   ├── reproduce.py                           # Independent 11-model reproduction runner
│   ├── statistical_analysis.py                # Hypothesis testing & N=20 statistical analysis
│   ├── pareto_analysis.py                     # Pareto dominance & multi-objective analysis
│   ├── minority_analysis.py                   # Minority recall, regime breakdown, & threshold sweep
│   ├── ulc_audit.py                           # ULC state transition trace & 5-stage ablation audit
│   ├── memory_benchmark.py                    # Component-wise memory scaling & RSS benchmark
│   ├── performance_benchmark.py               # Throughput, latency, & degradation benchmark
│   └── audit_generalization.py                # Multi-regime cross-dataset generalization battery
│
├── [Machine-Readable Data CSVs & JSONs]
│   ├── reproduction_results.json              # Full reproduced metrics across all seeds
│   ├── reproduction_seed_results.csv          # Per-seed metric records for all 11 models
│   ├── reproduction_comparison.csv            # Original vs. reproduced metric diff table
│   ├── statistical_results.json               # Full statistical test records and distributions
│   ├── paired_comparisons.csv                 # Paired t-test and Wilcoxon p-values
│   ├── effect_sizes.csv                       # Cohen's d and Cliff's delta effect sizes
│   ├── confidence_intervals.csv               # 95% bootstrap confidence intervals
│   ├── pareto_results.json                    # Non-dominated frontier definitions and metrics
│   ├── dominance_matrix.csv                   # Pairwise Pareto dominance matrix
│   ├── minority_metrics_by_seed.csv           # Seed-level minority precision, recall, and F1
│   ├── minority_metrics_by_regime.csv         # Regime-stratified minority performance
│   ├── threshold_sweep.csv                    # Classification threshold calibration sweep
│   ├── minority_ablation_results.csv          # Minority performance across ULC ablations
│   ├── ulc_state_transition_matrix.csv        # Empirical controller state transition probabilities
│   ├── ulc_runtime_trace.json                 # Batch-level controller actions and memory trace
│   ├── ulc_ablation_results.csv               # Causal ablation metrics across 5 controller variants
│   ├── optimizer_memory_results.csv           # LowMemoryAdamW vs. PyTorch AdamW memory comparison
│   ├── performance_results.csv                # Latency percentiles and sample throughput
│   ├── long_run_memory_results.csv            # 150,000-sample RSS memory profiling trace
│   ├── environment_matrix.json                # Python and OS platform compatibility matrix
│   └── generalization_battery_results.json    # Cross-dataset generalization metrics
│
├── figures/                                   # High-resolution audit visualization figures
│   ├── pareto/
│   │   ├── quality_vs_latency.png             # Macro F1 vs. Latency Pareto trade-off
│   │   ├── quality_vs_memory.png              # Macro F1 vs. Optimizer Memory trade-off
│   │   ├── minority_recall_vs_accuracy.png    # Minority Recall vs. Overall Accuracy frontier
│   │   └── false_resets_vs_quality.png        # False Drift Resets vs. Macro F1 trade-off
│   ├── minority/
│   │   ├── precision_recall_curve.png         # Precision-Recall curve across thresholds
│   │   ├── threshold_vs_f1.png                # Threshold vs. Minority F1 and Macro F1
│   │   └── regime_minority_recall.png         # Minority Recall across stream regimes
│   ├── ulc/
│   │   ├── ablation_macro_f1.png              # Component ablation impact on Macro F1
│   │   └── state_transitions.png              # Empirical controller state transition graph
│   └── resources/
│       ├── optimizer_memory_scaling.png       # Optimizer state bytes vs. parameter count
│       ├── long_run_rss_stability.png         # Process RSS over 150,000 streaming steps
│       └── throughput_latency_profile.png     # Latency CDF and throughput distribution
│
└── logs/
    └── reproduction.log                       # Detailed execution trace of reproduction runner
```

---

## 3. Reproduction & Execution Guide

All audit scripts are fully automated, standalone, and self-contained. They can be executed directly from the project root using Python 3.14:

```powershell
# 1. Execute Independent Experiment Reproduction (11 models × 5 seeds)
py -3.14 experiments/ulc_v3_independent_audit/reproduce.py

# 2. Execute Statistical Reanalysis & Hypothesis Testing (paired tests & N=20 study)
py -3.14 experiments/ulc_v3_independent_audit/statistical_analysis.py

# 3. Execute Pareto Dominance & Multi-Objective Analysis
py -3.14 experiments/ulc_v3_independent_audit/pareto_analysis.py

# 4. Execute Minority-Class Recall & Threshold Calibration Sweep
py -3.14 experiments/ulc_v3_independent_audit/minority_analysis.py

# 5. Execute ULC Implementation Verification & Causal Ablation
py -3.14 experiments/ulc_v3_independent_audit/ulc_audit.py

# 6. Execute Bit-Level Memory Accounting & Long-Run RSS Benchmark
py -3.14 experiments/ulc_v3_independent_audit/memory_benchmark.py

# 7. Execute Latency Percentiles & Processing Throughput Benchmark
py -3.14 experiments/ulc_v3_independent_audit/performance_benchmark.py

# 8. Execute Multi-Regime Generalization Test Battery (Optional Extended Battery)
py -3.14 experiments/ulc_v3_independent_audit/audit_generalization.py
```

---

## 4. Acceptance Gates Verification (G1–G10)

| Gate # | Acceptance Criteria | Target Deliverables / Evidence | Status |
|---|---|---|---|
| **G1** | **Baseline Integrity** | SHA-256 hashes of original experiment artifacts verified; baseline commit `67e9ef1` confirmed. | **PASS** |
| **G2** | **Independent Reproduction** | All 11 models reproduced across 5 seeds; predictive metrics within $\pm 0.0003$. | **PASS** |
| **G3** | **Raw Evidence Capture** | Per-seed, per-batch raw CSV and JSON records captured in audit directory. | **PASS** |
| **G4** | **Statistical Rigor** | Paired tests, Holm-Bonferroni corrections, bootstrap CIs, and $N=20$ power study completed. | **PASS** |
| **G5** | **Pareto Analysis** | 9-objective evaluation, dominance matrix, and 4 Pareto trade-off curves generated. | **PASS** |
| **G6** | **Minority Class Investigation** | Threshold sweep ($0.05$ to $0.95$), regime breakdown, code-doc discrepancy identified. | **PASS** |
| **G7** | **ULC Implementation Audit** | State transition matrix computed, runtime trace captured, production code bugs isolated. | **PASS** |
| **G8** | **Resource Benchmarking** | Bit-level optimizer state verified ($24\text{ B}$ vs $64\text{ B}$), 150k RSS stability confirmed. | **PASS** |
| **G9** | **Governance Integrity** | Production code untouched, DEF-004 OPEN, Phase 17 LOCKED, no git mutations. | **PASS** |
| **G10** | **Final Research Verdict** | Synthesized findings, conditionality matrix, and owner roadmap delivered. | **PASS** |

---

## 5. Summary of Core Empirical Findings

### 1. Reproduction Fidelity
- All 11 model configurations reproduced with **$100\%$ numerical fidelity** on predictive accuracy, macro F1, balanced accuracy, and calibration error ($\le 0.0003$ delta).
- Minor latency jitter ($5\%\text{--}16\%$) was observed due to OS CPU scheduling on Windows 11, with identical relative performance ranking.

### 2. Statistical Claims & Corrections
- **Macro F1:** Confirmed statistically superior at $N=5$ ($p = 0.0004$) and at $N=20$ ($t = 8.396, p = 8.12 \times 10^{-8}$).
- **Balanced Accuracy:** $p = 0.0454$ does **not** satisfy $p < 0.01$ and fails Holm-Bonferroni correction ($p_{\text{adj}} = 0.0905$). Claims of universal statistical superiority were overstated.
- **Brier Calibration:** Confirmed statistically superior ($p = 0.0001, d = -3.20$).

### 3. Pareto Frontier Realities
- The non-dominated Pareto frontier $\mathcal{P}^*$ contains **7 models**, including `MultiObjective_ULC_v3`.
- ULC-v3 is **not** universally Pareto-optimal: `RAO_Only` achieves higher minority recall ($64.08\%$ vs $24.90\%$) and faster latency ($0.045\text{ ms}$ vs $1.060\text{ ms}$). `Static_Baseline` achieves $0.0$ false resets (vs $1.0$) and $0\text{ B}$ optimizer state (vs $24\text{ B}$).

### 4. Minority Class Dynamics & Documentation Divergence
- **Code vs. Doc Discrepancy:** `ULC_DIAGNOSTICS.md` claimed an ensemble weight $\alpha=0.65$ and threshold $\theta^*=0.35$. The actual executable code used $\alpha=0.50$ and `np.argmax` ($\theta=0.50$).
- **Calibration Sweep:** Calibrating the decision threshold to $\theta=0.35$ increased minority recall from $14.29\%$ to $62.45\%$ on unseen test streams with only a minor drop in overall accuracy ($90.2\%$ to $86.4\%$).
- **Regime Breakdown:** At $\theta=0.50$, minority recall was driven primarily by the noise burst regime ($58.67\%$), while post-drift regimes collapsed ($2.0\%$ gradual, $0.0\%$ abrupt) due to tree splitting starvation under $90:10$ imbalance.

### 5. Production Code Bugs Isolated
1. **Attribute Mismatch in Replay Purging:** `adaptive_ml/ulc/controller.py` checks `hasattr(self.classifier, "replay_buffer")`, but `AdaptiveClassifier` defines `_replay_buffer`. Replay buffer purging was completely bypassed in the production implementation.
2. **Missing Optimizer Methods:** `adaptive_ml/ulc/controller.py` calls `reset_momenta` and `scale_learning_rate`, which `LowMemoryAdamW` does not implement, triggering runtime failures if invoked directly.

### 6. Generalization Boundaries
- **Where ULC-v3 Excels:** Transient noise bursts (zero false resets), extreme imbalance ($99.9:0.1$), and real-world industrial/fraud telemetry.
- **Where ULC-v3 Lags:** Clean streams with pure concept drift, where uncoordinated continuous models adapt faster ($+0.04$ to $+0.14$ higher Macro F1) due to controller arbitration deadbands.

### 7. Resource & Memory Footprint
- `LowMemoryAdamW` achieves $62.50\%$ memory reduction at $N=8$ ($24\text{ B}$ vs $64\text{ B}$) and $68.75\%$ across 1K–1M parameters.
- Process RSS is stable at $\approx 328\text{ MB}$ over 150,000 streaming steps ($+1.21\text{ MB}$ net drift), completely within the $512\text{ MB}$ ceiling.
- Python compatibility: Confirmed on 3.14.3 and 3.11.9 on Windows 11 AMD64. Python 3.10, 3.12, and 3.13 are uninstalled on the host and require CI matrix testing.

---

## 6. Actionable Governance Recommendations

1. **Retain Technical Pull Request:** Implement fixes for the attribute check and optimizer methods in `adaptive_ml/` before production release.
2. **Resolve DEF-004:** Engage legal trademark counsel for trademark clearance on candidate names.
3. **Phase 17 Gate:** Maintain Phase 17 as locked until DEF-004 is cleared and the Project Owner explicitly reviews and accepts this Stage 1 Research Validation Audit.

