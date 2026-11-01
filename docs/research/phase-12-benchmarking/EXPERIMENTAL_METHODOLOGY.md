# Phase 12 Experimental Methodology

**Document ID:** `DOC-RES-P12-006`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Research Questions & Hypotheses

| ID | Research Question | Null Hypothesis ($H_0$) | Alternative Hypothesis ($H_1$) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **RQ-ALA-1** | Does reliability weighting in ADWIN reduce false positive drift detections under noise? | Reliability weighting does not alter false alarm rate. | Reliability weighting significantly reduces false positive cuts under label noise. | **Supported** |
| **RQ-RLA-1** | Does density-aware margin moderation prevent minority class purging? | Minority recall under RLA matches standard empirical risk minimization ($H_0: \text{Recall}_{\text{RLA}} \le \text{Recall}_{\text{CE}}$). | Density moderation significantly improves minority class recall under extreme imbalance. | **Supported (Theorem 2 Confirmed)** |
| **RQ-RAO-1** | Does 8-bit block quantization achieve $>70\%$ state RAM reduction without divergence? | State memory reduction $\le 70\%$ or optimization diverges. | State memory reduction exceeds $70\%$ while achieving convergence on ill-conditioned quadratics. | **Supported ($73.44\%$ RAM saved, $L_2 = 0.033$)** |
| **RQ-ULC-1** | Does dual-evidence arbitration suppress false resets during label noise bursts? | ULC resets at the same frequency as uncoordinated drift detectors. | ULC suppresses false drift resets during noise bursts while enabling legitimate adaptation. | **Supported ($0.0$ vs $10.0$ false resets)** |

---

## 2. Evaluation Protocols & Seeds

1. **Repetitions**: Every stochastic experiment was executed across 5 independent random seeds: `[42, 101, 2024, 7, 99]`.
2. **Prequential Protocol**: Streaming evaluations adhere to the standard Dawid (1984) prequential test-then-train protocol, where each incoming instance or batch is used for prediction evaluation prior to updating model parameters.
3. **Data Isolation**: Synthetic stream generators isolate training and test distributions; evaluation sets are never exposed during training.

