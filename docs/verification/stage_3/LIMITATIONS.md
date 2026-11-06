# Stage 3: Technical Limitations & Operational Boundaries
## Adaptive Minority Intelligence Subsystem

**Document Identifier:** `VERIF-STAGE-3-007`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Subsystem Scope & Operational Boundaries

### 1.1 Precision vs Recall Trade-offs in Extreme Imbalance
- In severe imbalance regimes ($> 99:1$), dynamically decreasing the decision threshold ($\tau < 0.15$) maximizes minority recall ($\ge 95\% - 100\%$), which is critical for fraud, safety, and anomaly detection. However, this inevitably increases the false positive rate, depressing raw precision. In production systems where false alarms incur operational overhead, cost matrices should be supplied explicitly to `AdaptiveThresholdManager` via `mode="cost_sensitive"`.

### 1.2 Emerging Class Sample Warm-Up
- When an unseen class appears in the stream, `OnlineClassPriorTracker` immediately registers the new class ID and flags it as `is_emerging(class_id) == True`. During the initial warm-up period (until at least 50 instances of the class are observed), its empirical prior estimates exhibit higher variance due to Laplace smoothing. Downstream models should avoid aggressive drift pruning during this initial stabilization window.

### 1.3 Validation Buffer Sizing for Temperature Scaling
- `ClassAwareCalibrator` optimizes class temperatures $T_c$ via gradient descent on streaming validation windows. If a validation batch contains zero instances of a rare class, the gradient for $T_c$ evaluates to zero, leaving that class's temperature unchanged. For optimal calibration of rare classes, validation buffers should either be sampled from `MinorityAwareReplayBuffer` or sized to span $\ge 200$ samples.
