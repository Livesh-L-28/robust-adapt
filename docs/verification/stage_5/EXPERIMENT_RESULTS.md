# Stage 5: Empirical Experiment Results
## RLA 2.0 (Advanced Robust Learning Algorithms)

**Document Identifier:** `VERIF-STAGE-5-006`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Target Script:** [`experiments/stage_5_rla_v2/run_stage5_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_5_rla_v2/run_stage5_experiment.py)<br>
**Raw Evidence:** [`stage5_rla_results.json`](file:///c:/projects/AdaptiveML/experiments/stage_5_rla_v2/stage5_rla_results.json), [`stage5_rla_results.csv`](file:///c:/projects/AdaptiveML/experiments/stage_5_rla_v2/stage5_rla_results.csv)<br>
**Status:** `EMPIRICALLY VERIFIED`

---

## 1. Quantitative Benchmark Results

### 1.1 Multi-Signal Reliability Scoring on 30% Corrupted Stream

| Partition | Mean Reliability Score ($r$) | Corruption Detection Accuracy | Per-Sample Scoring Latency |
| :--- | :--- | :--- | :--- |
| **Clean Samples** (70%) | **$0.8200$** | **$100.0\%$** | **$7.19\text{ }\mu\text{s}$** |
| **Corrupted Samples** (30%) | **$0.2600$** | (Separation Gap: $+0.5600$) | — |

---

### 1.2 Noise Taxonomy Classification

| Test Regime | Injected Noise Mechanism | Estimated Noise Rate | Classified Taxonomy | Correct? |
| :--- | :--- | :--- | :--- | :--- |
| **Regime 1** | Clean baseline stream | $0.0\%$ | `NoiseType.CLEAN` | **Yes** |
| **Regime 2** | Symmetric random flip ($25\%$) | $29.5\%$ | `NoiseType.UNIFORM_RANDOM` | **Yes** |
| **Regime 3** | Class 0 corrupted to class 1 ($40\%$) | $19.75\%$ | `NoiseType.CLASS_CONDITIONAL` | **Yes** |

---

### 1.3 Outlier vs Rare Valid Pattern Discrimination

Evaluating 50 genuine rare minority instances and 50 corrupt outliers:

| Pattern Category | Evaluation Metric | Measured Success Rate | Assessment |
| :--- | :--- | :--- | :--- |
| **Rare Valid Patterns** | Retention Rate | **$100.0\%$ (50/50 retained)** | Preserves valid rare instances |
| **Corrupt Outliers** | Rejection Rate | **$100.0\%$ (50/50 rejected)** | Rejects spurious label noise |

---

### 1.4 Loss Portfolio Comparison under 35% Label Noise

| Loss Function | Measured Loss Value | Analytical Gradient Norm ($\|\nabla_z \mathcal{L}\|$) | Bounded Under Noise? |
| :--- | :--- | :--- | :--- |
| **Symmetric Cross Entropy (SCE)** | $3.1179$ | $0.1577$ | **Yes** |
| **Generalized Cross Entropy (GCE)** | $0.5625$ | $0.0282$ | **Yes** |
| **Focal Loss (FL)** | $0.4492$ | $0.0600$ | **Yes** |
| **Reliability-Weighted Loss (RWL)** | **$0.4570$** | **$0.0656$** | **Zeroes corrupt gradients** |

---

### 1.5 Evidence-Based Label Correction

| Evaluation Metric | Measured Value | Unit |
| :--- | :--- | :--- |
| **Ground Truth Corrupted Instances** | 32 | samples |
| **Corrections Proposed** | 32 | samples |
| **Correction Precision** | **$1.0000$ ($100.0\%$)** | ratio |
| **Correction Recall** | **$1.0000$ ($100.0\%$)** | ratio |
| **Audit Trail Recorded** | 32 records | full reversible history |
