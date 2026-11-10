# Stage 7.1 Experiment Workspace: ULC-v4 Performance Diagnosis, RCA & Optimization

**Directory:** `experiments/stage_7_1_ulc_v4_optimization/`  
**Parent Project:** AdaptiveML (`aml-core` `0.1.0.dev0`)  
**Baseline Git Commit:** `67e9ef1b347ca223828a1f225e85e35a086a1f30` (branch `master`)  
**Python Runtime:** Python 3.14.3 (AMD64, Windows 11 Enterprise)  
**Governance State:** Research Artifacts Isolated — Production `adaptive_ml/` Unmodified — DEF-004 OPEN — Phase 17 LOCKED

---

## 1. Overview & Directory Purpose

This directory contains the complete research, diagnostic, profiling, ablation, optimization, and validation artifacts for **Stage 7.1** of AdaptiveML. 

The primary objectives of Stage 7.1:
1. Diagnose why ULC-v4 underperformed ULC-v1 (accuracy: $71.15\%$ vs $91.51\%$) and ULC-v2/v3 (minority recall: $24.80\%$ vs $50.29\%$).
2. Investigate identical metric phenomena observed in Stage 7 across distinct configurations.
3. Conduct controlled component ablations across all controller sub-modules.
4. Formulate, implement, and benchmark isolated optimization candidates (Candidates 1–7).
5. Deliver a Pareto-optimal controller (`ULC-v4.1 Hybrid`) achieving genuine multi-objective superiority without compromising ALA, RLA, RAO, or Minority Intelligence.

---

## 2. Directory Manifest & Navigation Index

### 2.1. Analytical Research Reports
| Document | Focus & Key Insights |
| :--- | :--- |
| [BASELINE_REPRODUCTION.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_REPRODUCTION.md) | Reproduction of historical Stage 7 baselines across 11 configurations; statistical consistency verification. |
| [CONFIGURATION_EXECUTION_AUDIT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/CONFIGURATION_EXECUTION_AUDIT.md) | Exhaustive mathematical audit explaining why identical metrics appeared between configurations in Stage 7. |
| [ULC_V4_ARCHITECTURE_AUDIT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ULC_V4_ARCHITECTURE_AUDIT.md) | Structural inspection of ULC-v4 components: evidence synthesis, confidence, arbitration, and directives. |
| [STATE_TRANSITION_AUDIT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/STATE_TRANSITION_AUDIT.md) | Empirical tracing of automaton states ($S_0 \to S_6$); discovery of the absorbing `NOISE_BURST` trap. |
| [EVIDENCE_CONFIDENCE_AUDIT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/EVIDENCE_CONFIDENCE_AUDIT.md) | Audit of Bayesian Dirichlet synthesis and Beta-binomial confidence under streaming conditions. |
| [CONFLICT_RESOLUTION_AUDIT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/CONFLICT_RESOLUTION_AUDIT.md) | Audit of Pareto arbitration and rule-based priority overrides across the four pillars. |
| [ROOT_CAUSE_ANALYSIS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ROOT_CAUSE_ANALYSIS.md) | Comprehensive Root-Cause Analysis isolating the four primary failure modes of ULC-v4. |
| [COMPONENT_ABLATION_PROTOCOL.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/COMPONENT_ABLATION_PROTOCOL.md) | Formal design of the 8-condition controlled ablation experiment. |
| [COMPONENT_ABLATION_ANALYSIS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/COMPONENT_ABLATION_ANALYSIS.md) | Empirical analysis of component ablations uncovering the "Bottleneck Masking Effect". |
| [PERFORMANCE_TRADEOFF_ANALYSIS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/PERFORMANCE_TRADEOFF_ANALYSIS.md) | Multi-objective trade-off analysis across Accuracy, Macro F1, Minority Recall, and Latency. |
| [MINORITY_PERFORMANCE_ANALYSIS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/MINORITY_PERFORMANCE_ANALYSIS.md) | Investigation of Class 1 dynamics, precision-recall trade-offs, and class starvation mitigation. |
| [LATENCY_AND_MEMORY_ANALYSIS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/LATENCY_AND_MEMORY_ANALYSIS.md) | Micro-profiling breakdown, $k$-NN computational complexity, and $O(1)$ memory verification. |
| [GENERALIZATION_RESULTS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/GENERALIZATION_RESULTS.md) | 8-seed benchmark results (5 canonical + 3 exploratory) and formal statistical hypothesis testing. |
| [LIMITATIONS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/LIMITATIONS.md) | Mathematical boundaries, curse of dimensionality, sample-size constraints, and governance limits. |
| [FINAL_RESEARCH_VERDICT.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/FINAL_RESEARCH_VERDICT.md) | Formal synthesis of research findings, scorecards, and architectural adoption recommendations. |
| [AUDIT_PROTOCOL.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/AUDIT_PROTOCOL.md) | Step-by-step reproduction instructions and mathematical verification formulas for independent auditors. |

---

### 2.2. Executable Experiment Scripts
- [`reproduce_and_audit.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/reproduce_and_audit.py): Reproduces Stage 7 11-configuration baseline trials and exports raw JSON/CSV traces.
- [`profile_ulc_v4.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/profile_ulc_v4.py): High-resolution micro-profiler measuring execution time of each sub-component.
- [`run_ablations.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/run_ablations.py): Executes the 8-condition component ablation study across 5 random seeds.
- [`candidate_controllers.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py): Python implementations of Candidates 1–7 and the optimized `HybridMasterControllerV4_1`.
- [`run_candidate_benchmark.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/run_candidate_benchmark.py): Evaluates candidate architectures against baselines across 8 seeds.

---

### 2.3. Raw Data Artifacts
- [`BASELINE_RAW_RESULTS.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.json): Raw benchmark outputs for all 11 Stage 7 configurations.
- [`BASELINE_RAW_RESULTS.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.csv): Tabular summary of baseline performance across 5 seeds.
- [`SEED_42_DETAILED_TRACE.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/SEED_42_DETAILED_TRACE.json): Step-by-step state, reliability, and directive traces for Seed 42.
- [`ULC_V4_PROFILING_RESULTS.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ULC_V4_PROFILING_RESULTS.json): Profiling latency breakdown across all 9 pipeline steps.
- [`INTERVENTION_CONFLICT_MATRIX.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/INTERVENTION_CONFLICT_MATRIX.csv): Matrix of conflicting directive requests and resolved directives.
- [`COMPONENT_ABLATION_RESULTS.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/COMPONENT_ABLATION_RESULTS.csv): Prequential performance across the 8 ablation conditions.
- [`ULC_GENERATION_COMPARISON.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ULC_GENERATION_COMPARISON.csv): Authoritative comparison across ULC generations (v1, v2, v3, v4, v4.1).

---

## 3. Quick Reproduction Summary

```powershell
# 1. Run Baseline Reproduction
py -3.14 experiments/stage_7_1_ulc_v4_optimization/reproduce_and_audit.py

# 2. Run Micro-Profiler
py -3.14 experiments/stage_7_1_ulc_v4_optimization/profile_ulc_v4.py

# 3. Run Component Ablations
py -3.14 experiments/stage_7_1_ulc_v4_optimization/run_ablations.py

# 4. Run Candidate Optimizations Benchmark
py -3.14 experiments/stage_7_1_ulc_v4_optimization/run_candidate_benchmark.py
```

