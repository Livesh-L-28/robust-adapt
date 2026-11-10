# Workstream A: Independent Baseline Reproduction Report
## Master 13-Model Benchmark Battery Verification

**Document Identifier:** `STAGE-7-1-A-001`  
**Distribution Package Identifier:** `aml-core`  
**Package Version:** `0.1.0.dev0`  
**Target Environment:** Python 3.14.3 (64-bit AMD64, Windows 11 Enterprise)  
**Evaluated Seeds:** 42, 123, 456, 789, 2024 (5 canonical confirmatory trials)  
**Status:** `VERIFIED & REPRODUCED`

---

## 1. Reproduction Methodology

The 13-model comparison matrix reported in Stage 7 was independently re-executed using the exact experimental pipeline defined in [`experiments/stage_7_ulc_v4/run_stage7_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_ulc_v4/run_stage7_experiment.py) and executed via [`experiments/stage_7_1_ulc_v4_optimization/reproduce_and_audit.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/reproduce_and_audit.py).

### Stream Specification
- **Stream Length:** 60 batches \(\times\) 30 samples/batch = 1,800 samples per trial.
- **Dimensionality:** 4 continuous Gaussian features.
- **Class Distribution:** 90:10 severe class imbalance (27 majority samples of Class 0, 3 minority samples of Class 1 per batch).
- **Regime Dynamics:**
  - *Regime 1 (Batches 1–15):* Clean stationary baseline (Concept 0: \(\mu_0 = [-1.5], \mu_1 = [+1.5]\), \(\delta = 0.05\)).
  - *Regime 2 (Batches 16–25):* Severe noise burst (40% majority labels flipped to 1, \(\delta = 1.25\), no true drift).
  - *Regime 3 (Batches 26–35):* Gradual concept drift (\(\delta = 0.40\), continuous centroid shift from Concept 0 to Concept 1).
  - *Regime 4 (Batches 36–45):* Abrupt inverted concept drift (\(\delta = 1.40\), Concept 2: \(\mu_0 = [+2.5], \mu_1 = [-2.5]\)).
  - *Regime 5 (Batches 46–60):* Recurring concept drift returning to Concept 0 (\(\delta = 1.30\)).
- **Evaluation Mode:** Strict prequential test-then-train protocol.

---

## 2. Independent Reproduction Results

The table below reports the independently measured mean and standard deviation across the 5 canonical seeds:

| Model Configuration | Accuracy (%) | Macro F1 | Minority Recall (%) | False Drift Resets (FDR) | Throughput (samples/s) | Latency (ms/step) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Static Baseline** | 90.00 \(\pm\) 0.00 | 0.4737 \(\pm\) 0.0000 | 0.00 \(\pm\) 0.00 | 0.0 \(\pm\) 0.0 | 242,386 | 0.14 |
| **2. Pure Hoeffding Tree** | 86.49 \(\pm\) 0.65 | 0.5540 \(\pm\) 0.0102 | 14.97 \(\pm\) 2.01 | 0.0 \(\pm\) 0.0 | 63,910 | 0.52 |
| **3. Standalone ADWIN (ALA 1.0)** | 90.00 \(\pm\) 0.00 | 0.4737 \(\pm\) 0.0000 | 0.00 \(\pm\) 0.00 | 10.0 \(\pm\) 0.0 | 44,323 | 0.69 |
| **4. Standalone RLA (SCE + Margin)** | 71.75 \(\pm\) 1.57 | 0.4734 \(\pm\) 0.0102 | 18.36 \(\pm\) 2.47 | 0.0 \(\pm\) 0.0 | 38,664 | 0.84 |
| **5. Standalone RAO (LowMemoryAdamW)** | 46.58 \(\pm\) 0.68 | 0.3794 \(\pm\) 0.0048 | 46.32 \(\pm\) 1.40 | 0.0 \(\pm\) 0.0 | 231,862 | 2.50 |
| **6. Standalone Minority (Prior + Threshold)** | 66.85 \(\pm\) 2.71 | 0.4990 \(\pm\) 0.0173 | 43.27 \(\pm\) 4.63 | 0.0 \(\pm\) 0.0 | 44,512 | 0.70 |
| **7. ALA + RLA** | 71.75 \(\pm\) 1.57 | 0.4734 \(\pm\) 0.0102 | 18.36 \(\pm\) 2.47 | 0.0 \(\pm\) 0.0 | 26,465 | 1.23 |
| **8. ALA + RAO** | 90.00 \(\pm\) 0.00 | 0.4737 \(\pm\) 0.0000 | 0.00 \(\pm\) 0.00 | 10.0 \(\pm\) 0.0 | 32,765 | 1.01 |
| **9. RLA + RAO** | 70.63 \(\pm\) 1.58 | 0.5682 \(\pm\) 0.0139 | 69.94 \(\pm\) 2.01 | 0.0 \(\pm\) 0.0 | 176,480 | 0.20 |
| **10. ULC-v1 Baseline** | 91.51 \(\pm\) 0.50 | 0.6080 \(\pm\) 0.0381 | 15.20 \(\pm\) 4.81 | 0.0 \(\pm\) 0.0 | 36,234 | 0.91 |
| **11. ULC-v2 Baseline** | 73.73 \(\pm\) 0.37 | 0.5582 \(\pm\) 0.0034 | 50.29 \(\pm\) 1.17 | 0.0 \(\pm\) 0.0 | 37,867 | 0.79 |
| **12. ULC-v3 Audited** | 73.73 \(\pm\) 0.37 | 0.5582 \(\pm\) 0.0034 | 50.29 \(\pm\) 1.17 | 0.0 \(\pm\) 0.0 | 37,115 | 0.81 |
| **13. ULC-v4 Master System** | 71.15 \(\pm\) 0.37 | 0.4862 \(\pm\) 0.0031 | 24.80 \(\pm\) 1.51 | 0.0 \(\pm\) 0.0 | 28,267 | 1.11 |

*Raw data artifacts:* [`BASELINE_RAW_RESULTS.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.json) and [`BASELINE_RAW_RESULTS.csv`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/BASELINE_RAW_RESULTS.csv).

---

## 3. Reproduction Audit Conclusion

1. **Numerical Concurrence:** The reproduced metrics match the previously reported Stage 7 values to within expected statistical precision.
2. **Underperformance Confirmed:** ULC-v4 underperforms ULC-v1 in accuracy (\(-20.36\%\)), underperforms ULC-v1 in Macro F1 (\(-0.1218\)), and underperforms ULC-v2 and ULC-v3 in minority recall (\(24.80\%\) vs \(50.29\%\)).
3. **Execution Anomalies Confirmed:** Standalone RLA is identical to ALA + RLA, ULC-v2 is identical to ULC-v3, and Standalone ADWIN is identical to ALA + RAO. These anomalies require formal causal diagnosis in `CONFIGURATION_EXECUTION_AUDIT.md`.

