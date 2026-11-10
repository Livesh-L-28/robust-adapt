# Workstream B: Conflict Resolution Audit
## Audit of Scenarios A through J in Cross-Pillar Conflict Resolution

**Document Identifier:** `STAGE-7-1-B-004`  
**Distribution Package Identifier:** `aml-core`  
**Target:** [`CrossPillarConflictResolver`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/conflict_resolver.py#L25)  
**Status:** `AUDITED & SCENARIO A GATING BUG DOCUMENTED`

---

## 1. Audit Matrix: Scenarios A through J

| Scenario | Cross-Pillar Conflict | Implementation Rule | Unit Test Target | Audit Finding |
| :--- | :--- | :--- | :--- | :--- |
| **A** | Drift Alarm during Noise Burst | `delta >= 1.0 and mean_rel < 0.65` | `test_scenario_a...` | **Critical Bug:** Misclassifies abrupt concept drift as noise burst. |
| **B** | Extreme Imbalance with Drift | `(imbalance_ratio >= 5.0 or is_emerging) and delta >= 1.0 and mean_rel >= 0.65` | `test_scenario_b...` | **Sound:** Protects minority samples from being purged. |
| **C** | Budget Ceiling Breached in Drift | `resource_util >= 0.85 and delta >= 1.0` | `test_scenario_c...` | **Sound:** Scales batch size by 0.50x and sheds compute. |
| **D** | Recurring Concept Drift | `recurring_similarity >= 0.75 and delta >= 0.50` | `test_scenario_d...` | **Sound:** Fast-path restoration of historical model state. |
| **E** | Epistemic Boundary Uncertainty | `predictive_entropy >= 0.75 and mean_rel >= 0.70` | `test_scenario_e...` | **Sound:** Prevents false alarms on boundary samples. |
| **F** | Adversarial Inverted Labels | `asymmetric_noise_rate >= 0.40 and mean_rel < 0.30` | `test_scenario_f...` | **Sound:** Triggers evidence-based label correction. |
| **G** | Delayed Labels in Recovery | `observed_delay > 0.0 and state == RECOVERY` | `test_scenario_g...` | **Sound:** Enqueues delayed labels for matching. |
| **H** | Emerging Class Under Pressure | `is_emerging and resource_util >= 0.80` | `test_scenario_h...` | **Sound:** Protects emerging class slots in replay. |
| **I** | Asymmetric Noise Mitigation | `asymmetric_noise_rate >= 0.20` | `test_scenario_i...` | **Sound:** Class-conditional loss weighting. |
| **J** | Multi-Detector Disagreement | `state == ADAPTATION_PENDING` | `test_scenario_j...` | **Sound:** Collects secondary batch before acting. |

---

## 2. In-Depth Diagnosis of the Scenario A Gating Bug

In [`adaptive_ml/ulc/conflict_resolver.py#L43-L54`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/conflict_resolver.py#L43-L54):

```python
# Scenario A: Drift Alarm during Severe Noise Burst
if evidence.delta_drift >= 1.0 and evidence.mean_reliability < 0.65:
    resolved = DirectiveV4(
        state=AutomatonStateV4.NOISE_BURST,
        learning_rate_scale=1.0,
        suppress_adwin=True,
        freeze_buffer=True,
        sample_filter_threshold=0.65,
        correct_labels=True,
        confidence=confidence.suppress_noise,
        message="[Scenario A] Drift alarm during noise burst: suppressing drift reset and filtering noise.",
    )
    return resolved, "Scenario A: Noise vs Drift"
```

### Why this rule fails during genuine drift:
1. `mean_reliability` is derived from `DensityAwareMarginScorer`.
2. When true drift occurs, the classifier predicts old class boundaries, so logit margin is negative.
3. Therefore, `mean_reliability < 0.65` is **always true** during an abrupt concept drift before adaptation!
4. Because `delta >= 1.0` is also true, Scenario A intercepts the directive and forcibly overrides it to `NOISE_BURST`.
5. In doing so, it sets `sample_filter_threshold = 0.65`. All genuine instances of the new concept are discarded.
6. The classifier is starved of training data and never learns the new concept.

### The Required Fix:
Scenario A must verify that the label corruption is actually label noise (i.e. feature discordance is high), rather than concept drift (where feature discordance is low and feature centroids have shifted).

