# Pillar Tutorial: Unified Learning Controller (ULC-v4.1)

This tutorial covers the theory, configuration, and integration of the **ULC-v4.1 Hybrid Controller** ([`UnifiedLearningControllerV4_1`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py)), which coordinates Adaptive Learning (ALA), Robust Learning (RLA), and Resource Optimization (RAO).

---

## 1. The Stability-Plasticity-Robustness Dilemma

In streaming machine learning, three critical objectives conflict:
1. **Plasticity (ALA)**: The model must adapt quickly to legitimate concept drift.
2. **Robustness (RLA)**: The model must ignore transient label noise and adversarial corruptions.
3. **Efficiency (RAO)**: The model must operate within strict compute and memory budgets.

Standard algorithms fail when noise is introduced:
- A pure adaptive model treats label noise as concept drift, destroying learned weights.
- A pure robust model rejects genuine drift as noise, failing to adapt.

The **Unified Learning Controller (ULC-v4.1)** resolves this by measuring **Spatial Discordance ($\mathcal{D}_s$)** alongside loss entropy and temporal reliability.

---

## 2. Spatial Discordance & Arbitration Theory

### 2.1 What is Spatial Discordance?
Spatial discordance $\mathcal{D}_s \in [0, 1]$ quantifies the geometric coherence of prediction errors in feature space:
- **True Concept Drift**: Errors are localized and spatially coherent (a whole region of feature space shifts). $\mathcal{D}_s$ is **low** or structured.
- **Label Noise**: Errors are randomly scattered across the feature space without spatial structure. $\mathcal{D}_s$ is **high**.

### 2.2 Dual-Threshold Arbitration
ULC-v4.1 arbitrates using independent, calibrated thresholds:

$$\text{Directive} = \begin{cases}
\text{ADAPT} & \text{if } \Delta_{\text{metric}} \ge \tau_{\text{drift}} \land \mathcal{D}_s \le \tau_{\text{spatial}} \\
\text{NOISE\_FILTER} & \text{if } H_{\text{entropy}} \ge \tau_{\text{noise}} \lor \mathcal{D}_s > \tau_{\text{spatial}} \\
\text{RECOVERY} & \text{if drift resolved and confidence is stabilizing} \\
\text{DEFAULT\_PASS} & \text{otherwise}
\end{cases}$$

---

## 3. Using ULC-v4.1 in Streaming Loops

```python
import numpy as np
from robust_adapt import (
    UnifiedLearningControllerV4_1,
    ULCv41Config,
    Directive,
    AdaptiveClassifier,
    NoiseRobustClassifier
)

# 1. Initialize ULC-v4.1 controller
config = ULCv41Config(
    drift_threshold=0.30,
    noise_threshold=0.60,
    discordance_weight=0.45,
    confidence_decay=0.95,
    hysteresis_steps=3
)
controller = UnifiedLearningControllerV4_1(config=config)

# 2. Initialize sub-system models
adaptive_model = AdaptiveClassifier(n_features=6)
robust_model = NoiseRobustClassifier(n_features=6)

# 3. Streaming coordination loop
for step in range(100):
    X_batch = np.random.randn(32, 6).astype(np.float32)
    y_batch = (X_batch[:, 0] > 0.0).astype(np.int64)

    # Compute streaming telemetry
    metric_delta = float(np.random.uniform(0.05, 0.45))
    sample_entropy = float(np.random.uniform(0.2, 0.8))
    spatial_discordance = float(np.random.uniform(0.1, 0.7))
    reliability_score = float(np.random.uniform(0.4, 0.95))

    # Query controller for directive
    directive, diagnostics = controller.step(
        metric_delta=metric_delta,
        sample_entropy=sample_entropy,
        spatial_discordance=spatial_discordance,
        reliability_score=reliability_score
    )

    # Dispatch action based on controller decision
    if directive == Directive.ADAPT:
        adaptive_model.partial_fit(X_batch, y_batch)
        print(f"Step {step:02d} | Directive: ADAPT -> Triggered tree adaptation")
    elif directive == Directive.NOISE_FILTER:
        robust_model.partial_fit(X_batch, y_batch)
        print(f"Step {step:02d} | Directive: NOISE_FILTER -> Suppressed noisy updates")
    elif directive == Directive.RECOVERY:
        adaptive_model.partial_fit(X_batch, y_batch)
        print(f"Step {step:02d} | Directive: RECOVERY -> Stabilizing transition")
    else:
        adaptive_model.partial_fit(X_batch, y_batch)
```

---

## 4. On-Demand Explainability Diagnostics

ULC-v4.1 includes built-in explainability that can be queried at any step or aggregated over time:

```python
# Query detailed explanation for the most recent step
explanation = controller.explain_last_decision()

print("Decision Justification:")
print(f"  Directive:            {explanation['directive']}")
print(f"  Confidence Score:     {explanation['confidence']:.3f}")
print(f"  Spatial Discordance:  {explanation['spatial_discordance']:.3f}")
print(f"  Dominant Factor:      {explanation['dominant_factor']}")
print(f"  State Machine State:  {explanation['state_name']}")
```

---

## 5. Partial Pillar Configurations

ULC-v4.1 supports partial pillar operation if certain components are disabled:
- **ALA + RLA without RAO**: Operates with full floating-point precision when resources are unconstrained.
- **ALA + RAO without RLA**: Operates on clean streams with aggressive memory optimization.
- **Standalone ALA or Standalone RLA**: Can run completely independently without initializing the controller.
