# Workstream C: Root-Cause Analysis of Performance Degradation
## Deep Forensic Investigation into ULC-v4 Underperformance

**Document Identifier:** `STAGE-7-1-C-001`  
**Distribution Package Identifier:** `aml-core`  
**Status:** `CONFIRMED & EMPIRICALLY VERIFIED`

---

## 1. Executive Summary

The empirical underperformance of ULC-v4 relative to its predecessors (reported as 71.15% accuracy vs 91.51% for ULC-v1, 0.486 vs 0.608 Macro F1, and 24.80% vs 50.29% minority recall) is not caused by random variance, metric calculation errors, or hardware platform issues.

Our forensic investigation using fine-grained step-level tracing on Seed 42 reveals **four specific structural root causes**:

1. **Root Cause 1 (Primary): Perverse Adaptation Deadlock via Margin Circularity in Scenario A.**
   In [`adaptive_ml/ulc/conflict_resolver.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/conflict_resolver.py#L43), Scenario A classifies any batch with \(\delta \ge 1.0\) and \(\bar{r} < 0.65\) as a `NOISE_BURST`. However, because \(\bar{r}\) is derived from model margin, whenever an unadapted classifier encounters a genuine abrupt concept drift, its margin drops to zero (\(\bar{r} = 0.05\)). The controller misclassifies the true drift as a noise burst, freezes the replay buffer, suppresses adaptation, and filters out 100% of the genuine concept samples. The model gets 0.0% accuracy on Batches 36–45.

2. **Root Cause 2: The Degenerate Majority Baseline Illusion in ULC-v1.**
   In ULC-v1, the Hoeffding tree collapsed into predicting the majority class (Class 0) on every single instance (`[30, 0]` predictions). Because the stream is 90% Class 0 (27 Class 0, 3 Class 1), predicting exclusively Class 0 produces a baseline accuracy of \(27 / 30 = 90.00\%\) by default. ULC-v1 achieved 91.51% accuracy not because of superior adaptation, but because it acted as a trivial, unadapted majority-class classifier with near-zero minority recall (15.20%).

3. **Root Cause 3: The Absorbing Trapping Loop in `v4_automaton.py`.**
   In [`adaptive_ml/ulc/v4_automaton.py#L174-L179`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_automaton.py#L174-L179), `NOISE_BURST` can only exit to `STABLE` if \(\bar{r} \ge \tau_R \land \delta < 0.50\). Because samples are filtered during `NOISE_BURST`, the model cannot train on the new concept, so \(\bar{r}\) remains \(0.05 < \tau_R\) indefinitely. The state machine deadlocks in `NOISE_BURST` until an external stream shift occurs.

4. **Root Cause 4: Asymmetric Prior Tracker Contamination.**
   During Regime 2 (noise burst), 11 majority instances were flipped to Class 1. Because the prior tracker was updated on observed labels without spatial filtering, the estimated prior for Class 1 surged from 0.10 to 0.45. This caused the adaptive threshold manager to shift the decision threshold asymmetrically, suppressing minority recall on subsequent clean batches.

---

## 2. Forensic Evidence: Seed 42 Regime-by-Regime Analysis

The table below traces the exact step-by-step behavior of ULC-v4 on Seed 42 across the critical regime boundaries:

| Batch Range | Stream Regime | Ground-Truth Dynamic | ULC-v4 Controller State | Model Margin Reliability (\(\bar{r}\)) | Batch Accuracy | Forensic Diagnosis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1–15** | Stationary Concept 0 | \(\mu_0 = -1.5, \mu_1 = 1.5\) | `STABLE` | 0.985 | 100.0% | Normal operation; high accuracy. |
| **16–25** | Severe Noise Burst | 40% majority labels flipped | `NOISE_BURST` | 0.525 | 90.0% | **Successful noise suppression:** 0 false resets. |
| **26–33** | Early Gradual Drift | \(\delta = 0.40\) | `STABLE` | 0.890 | 96.7% | Gradual centroid shift tracked well. |
| **34–35** | Late Gradual Drift | Centroid inverted | `NOISE_BURST` | 0.081 | 3.3% | Accuracy drops \(\to\) misclassified as noise. |
| **36–45** | Abrupt Inverted Drift | \(\mu_0 = 2.5, \mu_1 = -2.5\) | `NOISE_BURST` (TRAPPED) | **0.050** | **0.0%** | **Deadlock:** All 300 clean samples filtered out. |
| **46–60** | Recurring Drift to Concept 0 | Stream returns to Concept 0 | `COOLDOWN` | 0.985 | 100.0% | Concept memory restores weights; instant recovery. |

### Visualizing the Deadlock Phenomenon

```mermaid
graph TD
    A["True Concept Shift Occurs (delta >= 1.0)"] --> B["Unadapted Model Generates Wrong Predictions"]
    B --> C["Model Logit Margins Collapse (rel < 0.05)"]
    C --> D["Scenario A Rule Triggers: delta >= 1.0 AND rel < 0.65"]
    D --> E["Controller Enters NOISE_BURST State"]
    E --> F["sample_filter_threshold = 0.65 Discards ALL New Samples"]
    F --> G["Model Is Starved of Data; Remains Unadapted"]
    G --> B
```

---

## 3. The Degenerate Majority Baseline Illusion

To verify Root Cause 2, we analyzed the class prediction distribution of `ULC-v1 Baseline`:
```text
Batch 34 preds: [30 Class 0, 0 Class 1] -> True Labels: [27 Class 0, 3 Class 1] -> Accuracy = 27/30 (90.0%)
Batch 35 preds: [30 Class 0, 0 Class 1] -> True Labels: [27 Class 0, 3 Class 1] -> Accuracy = 27/30 (90.0%)
Batch 36 preds: [30 Class 0, 0 Class 1] -> True Labels: [27 Class 0, 3 Class 1] -> Accuracy = 27/30 (90.0%)
...
Batch 45 preds: [30 Class 0, 0 Class 1] -> True Labels: [27 Class 0, 3 Class 1] -> Accuracy = 27/30 (90.0%)
```

ULC-v1 achieved 90% accuracy on the inverted concept solely because:
1. 90% of the stream instances are Class 0.
2. ULC-v1 collapsed into an unadapted majority classifier.
3. It achieved 0% minority recall throughout the entire drift period.

In contrast, ULC-v4 actively deployed minority intelligence ([`AdaptiveThresholdManager`](file:///c:/projects/AdaptiveML/adaptive_ml/minority/threshold.py)). When the unadapted classifier saw features at `+2.5` (which was Class 1 under Concept 0), it predicted Class 1. But under the inverted concept, `+2.5` was actually Class 0! Because ULC-v4 was not trapped in a majority-class collapse, its lack of adaptation caused it to predict Class 1 for all majority instances, resulting in 0% accuracy.

---

## 4. Remediation Strategy

To resolve the root causes without compromising safety, we must implement:
1. **Spatial Feature Discordance \(\mathcal{D}_{\text{spatial}}\):** Evaluate whether labels agree with nearest neighbors in feature space \(X\), rather than relying on model output margin \(z_y - \max z_j\).
   - If \(\mathcal{D}_{\text{spatial}} > 0.30\): True Label Noise Burst \(\implies\) `NOISE_BURST`.
   - If \(\mathcal{D}_{\text{spatial}} \le 0.15\): True Concept Drift \(\implies\) `CONFIRMED_DRIFT` (adapt!).
2. **NOISE_BURST Dwell Timeout:** Add a maximum dwell counter (e.g. 5 steps) to `NOISE_BURST`. If low reliability persists for 5 consecutive batches, it cannot be a temporary noise burst; it must be treated as concept drift.
3. **Robust Prior Tracking:** Gate updates to `OnlineClassPriorTracker` using spatial reliability to prevent noise bursts from distorting minority priors.

