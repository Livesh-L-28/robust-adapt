# Stage 3: Verification Protocol & Acceptance Criteria
## Adaptive Minority Intelligence Subsystem

**Document Identifier:** `VERIF-STAGE-3-002`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Mathematical Formulation & Verification Gates

### 1.1 Gate Matrix

| Gate ID | Subsystem Component | Verification Method | Pass Criterion |
| :--- | :--- | :--- | :--- |
| **GATE-3.1** | Online Class Prior Tracking | `test_imbalanced_stream_convergence` | Convergence to true streaming class prior within 30 batches; imbalance ratio $> 9.0$. |
| **GATE-3.2** | Emerging Class Detection | `test_emerging_class_detection` | Automatically detects newly arriving class ($C=2$) in mature stream without pre-declaration. |
| **GATE-3.3** | Adaptive Decision Threshold | `test_dynamic_threshold_shifts_with_prior` | Shifts decision threshold $\tau_1 < 0.30$ when minority prior drops to $0.05$. |
| **GATE-3.4** | Cost-Sensitive Thresholding | `test_cost_sensitive_threshold` | Derives Bayes-optimal threshold $\tau^* = \frac{C_{FP}}{C_{FP} + C_{FN}}$ matching exact analytical value. |
| **GATE-3.5** | Validation $F_1$ Tuning | `test_optimize_on_validation_window` | Finds optimal threshold on validation batch; achieves test $F_1 > 0.80$ with zero test-set leakage. |
| **GATE-3.6** | Threshold Rollback | `test_threshold_rollback` | Restores previous threshold vector upon metric degradation signal. |
| **GATE-3.7** | Extreme Imbalance Retention | `test_extreme_imbalance_retention` | $100\%$ retention of minority class instances under $200:1$ and $1000:1$ majority flood. |
| **GATE-3.8** | RLA Noise Suppression in Replay | `test_reliability_noise_filtering` | Rejects low-reliability corrupt minority candidates ($r < 0.5$). |
| **GATE-3.9** | Balanced Replay Extraction | `test_sample_balanced_stratification` | Returns batch with $\ge 40\%$ minority representation despite extreme stream imbalance. |
| **GATE-3.10** | Probability Temperature Calibration | `test_temperature_scaling_reduces_ece` | Decreases Expected Calibration Error (ECE) on overconfident streaming predictions by $> 30\%$. |
