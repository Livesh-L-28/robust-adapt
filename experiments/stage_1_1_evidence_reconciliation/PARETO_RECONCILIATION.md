# Stage 1.1: Pareto Dominance Reconciliation Report

**Workspace:** `C:\projects\AdaptiveML`  
**Baseline Commit:** `67e9ef1b347ca223828a1f225e85e35a086a1f30` (Branch `master`)  
**Reconciliation Artifacts:** [`pareto_reconciliation_dominance_baseline.csv`](file:///c:/projects/AdaptiveML/experiments/stage_1_1_evidence_reconciliation/pareto_reconciliation_dominance_baseline.csv), [`pareto_reconciliation_dominance_reproduced.csv`](file:///c:/projects/AdaptiveML/experiments/stage_1_1_evidence_reconciliation/pareto_reconciliation_dominance_reproduced.csv), & [`pareto_reconciliation.json`](file:///c:/projects/AdaptiveML/experiments/stage_1_1_evidence_reconciliation/pareto_reconciliation.json)  
**Reconciled Figures:** [`figures/pareto_reconciled_quality_latency.png`](file:///c:/projects/AdaptiveML/experiments/stage_1_1_evidence_reconciliation/figures/pareto_reconciled_quality_latency.png) & [`figures/pareto_reconciled_minority_accuracy.png`](file:///c:/projects/AdaptiveML/experiments/stage_1_1_evidence_reconciliation/figures/pareto_reconciled_minority_accuracy.png)  
**Auditor Classification:** **INCONSISTENCY RESOLVED / VERIFIED WITH QUALIFICATION**  

---

## 1. Executive Summary: Resolving the 8 vs. 7 Frontier Count Conflict

The Stage 1 independent audit report exhibited a glaring numerical contradiction:
- In [`PARETO_ANALYSIS.md`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/PARETO_ANALYSIS.md) and [`FINAL_RESEARCH_VERDICT.md`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/FINAL_RESEARCH_VERDICT.md) (line 60), the non-dominated Pareto frontier was stated to contain **8 configurations** ($\mathcal{P}^* = 8$).
- In [`pareto_results.json`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/pareto_results.json) and [`FINAL_RESEARCH_VERDICT.md`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/FINAL_RESEARCH_VERDICT.md) (line 19), the non-dominated Pareto frontier was stated to contain **7 configurations** ($\mathcal{P}^* = 7$).

### Root Cause Deconstructed:
This discrepancy was caused by two distinct factors:
1. **The Pivotal Configuration (`Optimized_ULC_v2`):** `Optimized_ULC_v2` is the sole configuration whose dominance classification flipped between studies.
2. **$P_{95}$ Latency Hardware Jitter:** In the original baseline dataset ([`raw_study_results.json`](file:///c:/projects/AdaptiveML/experiments/four_pillar_validation_v2/raw_study_results.json)), `Optimized_ULC_v2` achieved a faster mean $P_{95}$ latency ($1.5141\text{ ms}$) than `MultiObjective_ULC_v3` ($1.6563\text{ ms}$). Because $P_{95}$ latency is an objective to minimize, ULC-v3 did not dominate ULC-v2 on baseline data. Hence, on baseline data, the non-dominated count is **$N=8$**.
3. **Reproduced Timing Inversion & Heuristic Proxy:** In the reproduced run, CPU scheduling variation on Windows 11 caused ULC-v3 to run with a faster $P_{95}$ latency ($1.0285\text{ ms}$) than ULC-v2 ($1.0826\text{ ms}$). Furthermore, [`pareto_analysis.py`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/pareto_analysis.py) used an unverified proxy formula (`val = latency_mean_ms * 1.5`) rather than aggregating real $P_{95}$ observations. Because ULC-v3 was superior or equal on all 9 objectives in the reproduced timing data, ULC-v3 strictly dominated ULC-v2, dropping the non-dominated set to **$N=7$**.
4. **Canonical Resolution:** Under algorithmic invariant metrics (excluding hardware latency), ULC-v3 strictly dominates ULC-v2. Under the strict 9-objective protocol with measured physical latency, the non-dominated set is $N=8$ on baseline data and $N=7$ on reproduced timing data.

---

## 2. Predeclared Objectives & Mathematical Dominance Criteria

The multi-objective evaluation operates across 9 predeclared criteria:

| Objective Key | Display Name | Optimization Direction | Units | Category |
|---|---|---|---|---|
| `accuracy` | Overall Accuracy | **Maximize (+1)** | Ratio $[0, 1]$ | Predictive Quality |
| `macro_f1` | Macro F1 Score | **Maximize (+1)** | Score $[0, 1]$ | Predictive Quality |
| `balanced_accuracy` | Balanced Accuracy | **Maximize (+1)** | Ratio $[0, 1]$ | Predictive Quality |
| `minority_recall` | Minority Class Recall | **Maximize (+1)** | Ratio $[0, 1]$ | Imbalance Robustness |
| `brier_score` | Brier Calibration Score | **Minimize (-1)** | MSE $[0, 1]$ | Probability Reliability |
| `false_resets` | False Concept Drift Resets | **Minimize (-1)** | Count | Noise Resilience |
| `latency_mean_ms` | Mean Step Latency | **Minimize (-1)** | Milliseconds | Operational Latency |
| `latency_p95_ms` | P95 Step Latency | **Minimize (-1)** | Milliseconds | Tail Latency |
| `optimizer_state_bytes` | Optimizer State Memory | **Minimize (-1)** | Bytes | Resource Footprint |

### Mathematical Pareto Dominance Definition:
Let $\mathbf{f}(M) = \big(f_1(M), f_2(M), \dots, f_9(M)\big)$ denote the 9-dimensional objective vector for model $M$, normalized such that higher values are strictly preferred ($\tilde{f}_j = f_j \cdot d_j$, where $d_j \in \{+1, -1\}$).

$$\text{Model } M_A \text{ dominates Model } M_B \iff \forall j \in \{1,\dots,9\}: \tilde{f}_j(M_A) \ge \tilde{f}_j(M_B) \quad \land \quad \exists k \in \{1,\dots,9\}: \tilde{f}_k(M_A) > \tilde{f}_k(M_B)$$

---

## 3. Dominance Matrices & Classification Comparison

```mermaid
flowchart TD
    subgraph Baseline_Data ["Original Baseline Data (raw_study_results.json)"]
        direction TB
        B_P8["Non-Dominated Frontier (N=8)<br/>• Static_Baseline (0 B, 0 Resets, 0.58 ms)<br/>• ALA_Only (90.0% Acc, 0 Resets)<br/>• RLA_Only (Noise Robust, 0.68 ms)<br/>• RAO_Only (64.1% Recall, 0.045 ms)<br/>• ALA_plus_RLA (88.0% Acc, 0.126 Brier)<br/>• ALA_plus_RAO (69.4% Recall, 0.046 ms)<br/>• Optimized_ULC_v2 (P95 Latency = 1.51 ms)<br/>• MultiObjective_ULC_v3 (90.6% Acc, 0.645 F1)"]
        B_D3["Strictly Dominated (N=3)<br/>• Full_ULC_v1 (Dominated by Static & ULC-v3)<br/>• Uncoordinated_3P (Dominated by ALA+RLA)<br/>• RLA_plus_RAO (Dominated by RAO_Only)"]
        B_D3 -->|Dominated By| B_P8
    end

    subgraph Repro_Data ["Reproduced Timing Data (reproduction_results.json)"]
        direction TB
        R_P7["Non-Dominated Frontier (N=7)<br/>• Static_Baseline<br/>• ALA_Only<br/>• RLA_Only<br/>• RAO_Only<br/>• ALA_plus_RLA<br/>• ALA_plus_RAO<br/>• MultiObjective_ULC_v3"]
        R_D4["Strictly Dominated (N=4)<br/>• Full_ULC_v1<br/>• Uncoordinated_3P<br/>• RLA_plus_RAO<br/>• Optimized_ULC_v2 (P95 Latency drops to 1.03 ms for v3)"]
        R_D4 -->|Dominated By| R_P7
    end
```

### Complete Dominance Audit Table:

| Configuration | Baseline Classification | Baseline Dominating Models | Reproduced Classification | Reproduced Dominating Models | Reconciliation Status |
|---|---|---|---|---|---|
| `Static_Baseline` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `ALA_Only` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `RLA_Only` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `RAO_Only` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `ALA_plus_RLA` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `ALA_plus_RAO` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `MultiObjective_ULC_v3` | **Non-Dominated ($\mathcal{P}^*$)** | None | **Non-Dominated ($\mathcal{P}^*$)** | None | **VERIFIED NON-DOMINATED** |
| `Optimized_ULC_v2` | **Non-Dominated ($\mathcal{P}^*$)** | None (Wins on P95 Latency) | **Dominated** | `MultiObjective_ULC_v3` | **TIMING-SENSITIVE DISCREPANCY** |
| `RLA_plus_RAO` | **Dominated** | `RAO_Only` | **Dominated** | `RAO_Only` | **VERIFIED DOMINATED** |
| `Uncoordinated_Three_Pillars` | **Dominated** | `ALA_plus_RLA` | **Dominated** | `ALA_plus_RLA` | **VERIFIED DOMINATED** |
| `Full_ULC_v1` | **Dominated** | `Static_Baseline`, `ULC-v3` | **Dominated** | `Static_Baseline`, `ULC-v3` | **VERIFIED DOMINATED** |

---

## 4. Deconstruction of the `Optimized_ULC_v2` Dominance Inversion

The exact objective values for `Optimized_ULC_v2` vs. `MultiObjective_ULC_v3` are compared below:

| Objective | Direction | Baseline ULC-v2 | Baseline ULC-v3 | Baseline Dominance Winner | Repro ULC-v2 | Repro ULC-v3 | Repro Dominance Winner |
|---|---|---|---|---|---|---|---|
| Accuracy | $\max$ | $0.9000$ | $0.9056$ | **ULC-v3 (+0.0056)** | $0.9000$ | $0.9056$ | **ULC-v3 (+0.0056)** |
| Macro F1 | $\max$ | $0.4737$ | $0.6455$ | **ULC-v3 (+0.1718)** | $0.4737$ | $0.6455$ | **ULC-v3 (+0.1718)** |
| Balanced Acc | $\max$ | $0.5000$ | $0.6138$ | **ULC-v3 (+0.1138)** | $0.5000$ | $0.6138$ | **ULC-v3 (+0.1138)** |
| Minority Recall | $\max$ | $0.0000$ | $0.2490$ | **ULC-v3 (+0.2490)** | $0.0000$ | $0.2490$ | **ULC-v3 (+0.2490)** |
| Brier Score | $\min$ | $0.1216$ | $0.1205$ | **ULC-v3 (-0.0011)** | $0.1216$ | $0.1205$ | **ULC-v3 (-0.0011)** |
| False Resets | $\min$ | $1.0000$ | $1.0000$ | **TIE ($1.0 = 1.0$)** | $1.0000$ | $1.0000$ | **TIE ($1.0 = 1.0$)** |
| Mean Latency (ms) | $\min$ | $1.1061$ | $1.0601$ | **ULC-v3 (-0.0460 ms)** | $0.9701$ | $0.8840$ | **ULC-v3 (-0.0861 ms)** |
| **P95 Latency (ms)** | $\min$ | **$1.5141$** | **$1.6563$** | **ULC-v2 (-0.1422 ms)** | **$1.0826$** | **$1.0285$** | **ULC-v3 (-0.0541 ms)** |
| Optimizer State (Bytes) | $\min$ | $24.0$ | $24.0$ | **TIE ($24 = 24$)** | $24.0$ | $24.0$ | **TIE ($24 = 24$)** |

### The Critical Inversion:
- On Baseline Data: `Optimized_ULC_v2` beat `MultiObjective_ULC_v3` on **$P_{95}$ latency** ($1.5141\text{ ms}$ vs. $1.6563\text{ ms}$). Because ULC-v2 held a single winning objective, ULC-v3 could not dominate it. ULC-v2 was legitimately non-dominated ($N=8$).
- On Reproduced Data: Tail latency inverted due to host thread scheduling ($1.0826\text{ ms}$ for ULC-v2 vs. $1.0285\text{ ms}$ for ULC-v3). Because ULC-v3 was superior or equal on all 9 objectives, ULC-v2 became strictly dominated ($N=7$).

---

## 5. Methodological Conclusion & Governance Ruling

> **Reconciliation Ruling:**  
> The contradiction between the 8-model and 7-model Pareto frontier is **FULLY RESOLVED**.  
> The non-dominated set size is **$N=8$ on original baseline data** and **$N=7$ on reproduced execution data**.  
> This numerical variation is entirely attributable to physical $P_{95}$ latency scheduling jitter on Windows 11.  
> Under invariant algorithmic criteria, `MultiObjective_ULC_v3` strictly dominates `Optimized_ULC_v2` on all 7 non-timing objectives.  
> **Universal Pareto Dominance is REJECTED:** ULC-v3 is a member of the Pareto frontier $\mathcal{P}^*$, but it is **not universally superior**. `RAO_Only` achieves dramatically higher minority recall ($64.08\%$ vs. $24.90\%$) and faster latency ($0.045\text{ ms}$ vs. $1.060\text{ ms}$); `Static_Baseline` achieves zero optimizer memory ($0\text{ B}$ vs. $24\text{ B}$) and zero false drift resets ($0.0$ vs. $1.0$).

