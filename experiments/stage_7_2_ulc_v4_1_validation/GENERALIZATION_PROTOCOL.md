# Stage 7.2 Multi-Dimensional Generalization Protocol

**Author:** AdaptiveML Benchmark Governance & Protocol Architecture Team  
**Artifact Path:** [GENERALIZATION_PROTOCOL.md](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/GENERALIZATION_PROTOCOL.md)  
**Related Script:** [`run_generalization.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/run_generalization.py)  
**Related Results:** [GENERALIZATION_RESULTS.csv](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/GENERALIZATION_RESULTS.csv)

---

## 1. Protocol Architecture & Purpose

The goal of Workstream F is to stress-test the controller beyond the canonical synthetic benchmark stream across five orthogonal axes of streaming complexity:
1. **Class Imbalance Spectrum:** $50:50$ (balanced), $90:10$ (moderate), $99:1$ (severe).
2. **Noise Severity Spectrum:** $0\%, 10\%, 20\%, 40\%, 60\%$ label corruption.
3. **Drift Topology Spectrum:** Stationary, Abrupt inversion, Gradual interpolation, Incremental trajectory shift, Recurring concept re-emergence, and Feature scale drift.
4. **Label Availability Spectrum:** Immediate ground-truth, Delayed feedback ($L=5$ batches latency), Missing feedback ($20\%$ missing rate).
5. **Real-World Streaming Topology:** Credit Card Fraud detection stream with $D=29$ continuous dimensions, $99.8:0.2$ imbalance ratio, and concept shifts.

---

## 2. Experimental Controls & Standards

1. **Independent Evaluation Seeds:** All generalization trials were executed over fresh random seeds ($101, 102, 103$), preserving strict statistical isolation from test sets.
2. **Prequential Evaluation Standard:** On every batch $t$:
   - Prequential predictions are recorded against uncorrupted ground truth: $\hat{y}_t = f_{\theta_{t-1}}(X_t)$.
   - Loss and confusion matrix increments are logged.
   - The controller ingests $(X_t, y^{\text{obs}}_t)$ and updates model state: $\theta_t = \text{step}(\theta_{t-1}, X_t, y^{\text{obs}}_t)$.
3. **Data Provenance:** All synthetic data generators are explicitly documented and fully deterministic. The realistic fraud stream is parameterized directly from the statistical properties (feature dimensions, PCA covariance, imbalance) of the ULB benchmark.

