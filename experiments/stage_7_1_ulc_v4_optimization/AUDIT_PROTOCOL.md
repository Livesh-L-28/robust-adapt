# Stage 7.1 Independent Audit & Reproduction Protocol

**Author:** AdaptiveML Independent Verification & Audit Team  
**Scope:** Formal Verification Procedure, Reproduction Steps & Verification Checksums  
**Artifact Path:** [AUDIT_PROTOCOL.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/AUDIT_PROTOCOL.md)  
**Target Environment:** Windows 11 Enterprise (AMD64), Python 3.14.3

---

## 1. Audit Overview

This protocol defines the formal, step-by-step procedure for an independent auditor or the Project Owner to reproduce every numerical claim, state transition, and benchmark result generated during **Stage 7.1**.

### Mandatory Verification Principles:
1. **Zero Production Mutation:** The production source tree (`adaptive_ml/`) must remain bit-for-bit identical to Git baseline commit `67e9ef1b347ca223828a1f225e85e35a086a1f30`.
2. **Determinism:** All synthetic streams, noise injections, and initializations are governed by explicit random seeds ($42, 123, 456, 789, 2024, 999, 101, 7$).
3. **Prequential Integrity:** Evaluation strictly enforces the prequential (test-then-train) protocol over non-stationary data streams.

---

## 2. Environment Verification

Before executing any experiment scripts, verify that the environment meets the exact audited specifications:

```powershell
# 1. Verify Git commit and working tree status
git rev-parse HEAD
# Expected Output: 67e9ef1b347ca223828a1f225e85e35a086a1f30

git branch --show-current
# Expected Output: master

# 2. Verify Python runtime version
py -3.14 --version
# Expected Output: Python 3.14.3

# 3. Verify core test suite integrity (All 110 tests must pass)
py -3.14 -m pytest tests/
# Expected Output: 110 passed in ~5-10s
```

---

## 3. Step-by-Step Reproduction Procedure

### Step 3.1: Reproduce Baseline Stage 7 Benchmark & Audit
Execute the automated reproduction script to re-run the 11 configurations from Stage 7 and regenerate baseline audit data:

```powershell
py -3.14 experiments/stage_7_1_ulc_v4_optimization/reproduce_and_audit.py
```
**Generated Artifacts:**
- [`BASELINE_RAW_RESULTS.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.json)
- [`BASELINE_RAW_RESULTS.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.csv)
- [`SEED_42_DETAILED_TRACE.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/SEED_42_DETAILED_TRACE.json)

**Expected Audit Checksums:**
- `ULC-v1 Baseline` Mean Accuracy: $91.51\% \pm 0.50\%$
- `ULC-v2 Baseline` Mean Accuracy: $73.73\% \pm 0.37\%$
- `ULC-v4 Original` Mean Accuracy: $71.15\% \pm 0.37\%$
- `ULC-v4 Original` Minority Recall: $24.80\% \pm 1.51\%$

---

### Step 3.2: Reproduce Fine-Grained Latency & Profiling Breakdown
Execute the micro-profiler to measure execution overhead across each sub-component:

```powershell
py -3.14 experiments/stage_7_1_ulc_v4_optimization/profile_ulc_v4.py
```
**Generated Artifacts:**
- [`ULC_V4_PROFILING_RESULTS.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ULC_V4_PROFILING_RESULTS.json)
- [`INTERVENTION_CONFLICT_MATRIX.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/INTERVENTION_CONFLICT_MATRIX.csv)

**Expected Invariants:**
- `percentage_in_controller_overhead`: $< 5.0\%$ (typically $\approx 3.55\%$)
- `percentage_in_explainer`: $< 0.5\%$ (typically $\approx 0.29\%$)

---

### Step 3.3: Reproduce Controlled Component Ablations
Execute the 8-condition ablation protocol across the 5 canonical seeds to verify the "Bottleneck Masking Effect":

```powershell
py -3.14 experiments/stage_7_1_ulc_v4_optimization/run_ablations.py
```
**Generated Artifacts:**
- [`COMPONENT_ABLATION_RESULTS.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/COMPONENT_ABLATION_RESULTS.csv)

**Expected Invariant:**
- Across all 7 component ablation conditions, accuracy remains locked at $71.15\% \pm 0.37\%$ and minority recall remains at $24.80\% \pm 1.51\%$, confirming that the Scenario A deadlock dominates all sub-mechanisms.

---

### Step 3.4: Reproduce Candidate Optimization Benchmark (Confirmatory + Exploratory)
Execute the multi-candidate evaluation script across 8 seeds:

```powershell
py -3.14 experiments/stage_7_1_ulc_v4_optimization/run_candidate_benchmark.py
```
**Generated Artifacts:**
- [`ULC_GENERATION_COMPARISON.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/ULC_GENERATION_COMPARISON.csv)

**Expected Invariants:**
- `ULC-v4.1 Hybrid` Mean Accuracy: $\mathbf{86.47\% \pm 0.70\%}$ (5-seed) / $\mathbf{86.72\% \pm 1.23\%}$ (8-seed)
- `ULC-v4.1 Hybrid` Mean Macro F1: $\mathbf{0.7003 \pm 0.0161}$ (5-seed) / $\mathbf{0.7001 \pm 0.0150}$ (8-seed)
- `ULC-v4.1 Hybrid` Mean Minority Recall: $\mathbf{62.22\% \pm 5.78\%}$ (5-seed) / $\mathbf{60.10\% \pm 6.46}$ (8-seed)
- `ULC-v4.1 Hybrid` False Drift Resets: $\mathbf{0.0}$ across all seeds

---

## 4. Mathematical Audit Formulas

Auditors must verify that all metric calculation functions conform to standard prequential stream definitions:

1. **Prequential Accuracy:**
   $$\text{Accuracy} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}\{\hat{y}_i = y_i^*\}$$
2. **Class-Specific Recall ($c=1$):**
   $$\text{Recall}_1 = \frac{\sum_{i=1}^{N} \mathbf{1}\{\hat{y}_i = 1 \land y_i^* = 1\}}{\sum_{i=1}^{N} \mathbf{1}\{y_i^* = 1\}}$$
3. **Macro F1 Score:**
   $$\text{Macro F1} = \frac{\text{F1}_0 + \text{F1}_1}{2}$$
4. **Spatial Feature Discordance:**
   $$\mathcal{D}_{\text{spatial}}(B) = \frac{1}{|B|} \sum_{i=1}^{|B|} \frac{1}{k} \sum_{j \in \mathcal{N}_k(x_i)} \mathbf{1}\{y_j \neq y_i\}$$

---

## 5. Governance Audit Checklist

- [x] Baseline Git commit preserved (`67e9ef1b347ca223828a1f225e85e35a086a1f30`)
- [x] Package distribution name verified as `aml-core` (`0.1.0.dev0`)
- [x] Production directory `adaptive_ml/` unmodified
- [x] DEF-004 remains OPEN and UNRESOLVED
- [x] Phase 17 remains LOCKED and UNAUTHORIZED
- [x] Zero Git commits, amends, tags, or remote pushes created
- [x] All 110 unit and integration tests passing without warning

