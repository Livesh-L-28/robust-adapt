# Stage 7.2 Independent Baseline & ULC-v4.1 Reproduction Report

**Author:** AdaptiveML Independent Verification & Research Team  
**Artifact Path:** [BASELINE_REPRODUCTION.md](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/BASELINE_REPRODUCTION.md)  
**Raw Results Path:** [RAW_REPRODUCTION_RESULTS.csv](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/RAW_REPRODUCTION_RESULTS.csv) | [RAW_REPRODUCTION_RESULTS.json](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/RAW_REPRODUCTION_RESULTS.json)  
**Parent Workspace:** `C:\projects\AdaptiveML`  
**Execution Date:** 2026-11-06  
**Runtime:** Python 3.14.3 (AMD64, Windows 11 Enterprise)

---

## 1. Executive Summary

This report establishes the independent, freshly executed reproduction of the 6 core benchmark architectures evaluated in Stage 7 and Stage 7.1:
1. **Static Baseline:** Non-adaptive classifier trained solely on initial batches.
2. **ULC-v1 Baseline:** First-generation heuristic controller.
3. **ULC-v2 Baseline:** Second-generation rule-based controller.
4. **ULC-v3 Audited:** Third-generation evidence-based controller with selective replay purge.
5. **ULC-v4 Original:** Fourth-generation controller with 10D evidence and 12-state automaton.
6. **ULC-v4.1 Hybrid:** Remediated candidate controller incorporating spatial feature discordance, Hoeffding tie-breaking, and calibrated threshold smoothing.

Every experiment was executed de novo using the verified runtime environment. Historical data files were **not** reused.

---

## 2. Prequential Benchmark Results

### 2.1. Confirmatory Trials (Canonical Seeds: 42, 123, 456, 789, 2024)

| Model Architecture | Accuracy (%) | Acc Std | Macro F1 | F1 Std | Minority Recall (%) | Recall Std | Minority Precision (%) | False Drift Resets (FDR) | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Static Baseline** | $90.00$ | $0.00$ | $0.4737$ | $0.0000$ | $0.00$ | $0.00$ | $0.00$ | $0$ | $0.092$ |
| **ULC-v1 Baseline** | $91.51$ | $0.50$ | $0.6079$ | $0.0375$ | $15.20$ | $4.81$ | $98.75$ | $0$ | $0.582$ |
| **ULC-v2 Baseline** | $73.73$ | $0.37$ | $0.5582$ | $0.0026$ | $50.29$ | $1.17$ | $19.10$ | $0$ | $0.756$ |
| **ULC-v3 Audited** | $73.73$ | $0.37$ | $0.5582$ | $0.0026$ | $50.29$ | $1.17$ | $19.10$ | $0$ | $0.778$ |
| **ULC-v4 Original** | $71.15$ | $0.37$ | $0.4865$ | $0.0033$ | $24.80$ | $1.51$ | $10.40$ | $0$ | $0.720$ |
| **ULC-v4.1 Hybrid** | $\mathbf{86.47}$ | $\mathbf{0.70}$ | $\mathbf{0.7003}$ | $\mathbf{0.0161}$ | $\mathbf{62.22}$ | $\mathbf{5.78}$ | $\mathbf{38.94}$ | $\mathbf{0}$ | $\mathbf{0.902}$ |

---

### 2.2. Exploratory Trials (Unseen Seeds: 999, 101, 7)

| Seed | Architecture | Accuracy (%) | Macro F1 | Minority Recall (%) | Minority Precision (%) | False Drift Resets (FDR) | Latency (ms) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **999** | Static Baseline | $90.00$ | $0.4737$ | $0.00$ | $0.00$ | $0$ | $0.142$ |
| | ULC-v1 Baseline | $90.94$ | $0.5620$ | $9.36$ | $100.00$ | $0$ | $1.607$ |
| | ULC-v2 Baseline | $75.20$ | $0.5540$ | $42.69$ | $18.30$ | $0$ | $2.009$ |
| | ULC-v3 Audited | $75.20$ | $0.5540$ | $42.69$ | $18.30$ | $0$ | $2.082$ |
| | ULC-v4 Original | $72.87$ | $0.4820$ | $19.30$ | $9.19$ | $0$ | $1.846$ |
| | **ULC-v4.1 Hybrid** | $\mathbf{86.73}$ | $\mathbf{0.7030}$ | $\mathbf{61.99}$ | $\mathbf{39.55}$ | $\mathbf{0}$ | $\mathbf{2.060}$ |
| **101** | Static Baseline | $90.00$ | $0.4737$ | $0.00$ | $0.00$ | $0$ | $0.092$ |
| | ULC-v1 Baseline | $91.52$ | $0.6090$ | $15.20$ | $100.00$ | $0$ | $0.708$ |
| | ULC-v2 Baseline | $71.17$ | $0.5490$ | $55.56$ | $18.55$ | $0$ | $0.837$ |
| | ULC-v3 Audited | $71.17$ | $0.5490$ | $55.56$ | $18.55$ | $0$ | $0.960$ |
| | ULC-v4 Original | $71.23$ | $0.4860$ | $24.56$ | $10.37$ | $0$ | $0.992$ |
| | **ULC-v4.1 Hybrid** | $\mathbf{85.50}$ | $\mathbf{0.6850}$ | $\mathbf{60.23}$ | $\mathbf{36.40}$ | $\mathbf{0}$ | $\mathbf{2.040}$ |
| **7** | Static Baseline | $90.00$ | $0.4737$ | $0.00$ | $0.00$ | $0$ | $0.095$ |
| | ULC-v1 Baseline | $91.35$ | $0.5960$ | $13.45$ | $100.00$ | $0$ | $0.582$ |
| | ULC-v2 Baseline | $74.62$ | $0.5470$ | $41.52$ | $17.53$ | $0$ | $0.919$ |
| | ULC-v3 Audited | $74.62$ | $0.5470$ | $41.52$ | $17.53$ | $0$ | $1.613$ |
| | ULC-v4 Original | $71.29$ | $0.4850$ | $23.98$ | $10.20$ | $0$ | $1.095$ |
| | **ULC-v4.1 Hybrid** | $\mathbf{89.24}$ | $\mathbf{0.7100}$ | $\mathbf{49.71}$ | $\mathbf{46.45}$ | $\mathbf{0}$ | $\mathbf{1.305}$ |

---

### 2.3. Grand 8-Seed Summary (Canonical + Exploratory)

| Architecture | 8-Seed Accuracy (%) | 8-Seed Macro F1 | 8-Seed Minority Recall (%) | 8-Seed Minority Precision (%) | False Resets (FDR) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Static Baseline** | $90.00 \pm 0.00$ | $0.4737 \pm 0.0000$ | $0.00 \pm 0.00$ | $0.00 \pm 0.00$ | $0 \pm 0$ |
| **ULC-v1 Baseline** | $91.42 \pm 0.44$ | $0.6008 \pm 0.0350$ | $14.25 \pm 4.31$ | $99.22 \pm 2.21$ | $0 \pm 0$ |
| **ULC-v2 Baseline** | $73.71 \pm 1.25$ | $0.5555 \pm 0.0050$ | $48.91 \pm 4.79$ | $18.66 \pm 0.67$ | $0 \pm 0$ |
| **ULC-v3 Audited** | $73.71 \pm 1.25$ | $0.5555 \pm 0.0050$ | $48.91 \pm 4.79$ | $18.66 \pm 0.67$ | $0 \pm 0$ |
| **ULC-v4 Original** | $71.39 \pm 0.67$ | $0.4858 \pm 0.0035$ | $23.98 \pm 2.22$ | $10.15 \pm 0.59$ | $0 \pm 0$ |
| **ULC-v4.1 Hybrid** | $\mathbf{86.72 \pm 1.23}$ | $\mathbf{0.7001 \pm 0.0150}$ | $\mathbf{60.10 \pm 6.46}$ | $\mathbf{39.58 \pm 3.19}$ | $\mathbf{0 \pm 0}$ |

---

## 3. Analysis of Independent Reproduction Claims

1. **Reproduction Accuracy:** The freshly computed metrics match the Stage 7.1 reported numbers to within exact floating-point rounding precision.
2. **Degeneracy of Static & ULC-v1 Baselines:**
   - The Static Baseline achieves $90.00\%$ accuracy by predicting Class 0 for every instance, giving $0.00\%$ minority recall.
   - ULC-v1 achieves $91.42\%$ accuracy because it fails to adapt its tree to minority splits, yielding an unacceptable $14.25\%$ minority recall.
3. **Confirmation of ULC-v4 Regression:** ULC-v4 Original repeatedly collapses to $71.39\%$ accuracy, $0.4858$ Macro F1, and $23.98\%$ minority recall due to the Scenario A adaptation deadlock.
4. **Generalization of ULC-v4.1:** Across all 8 seeds, ULC-v4.1 Hybrid uniformly surpasses all other architectures in Macro F1 ($0.7001$) and Minority Recall ($60.10\%$) with zero false drift resets ($0.0$).

