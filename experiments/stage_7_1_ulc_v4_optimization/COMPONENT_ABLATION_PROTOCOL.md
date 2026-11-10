# Workstream D: Component Ablation Protocol
## Systematic Experimental Protocol for Subsystem Isolation

**Document Identifier:** `STAGE-7-1-D-001`  
**Distribution Package Identifier:** `aml-core`  
**Target:** [`run_ablations.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/run_ablations.py)  
**Status:** `VERIFIED`

---

## 1. Experimental Design & Hypotheses

The objective of this ablation study is to quantify the isolated contribution of each ULC-v4 architectural layer:

| Condition | Target Subsystem | Ablation Mutation | Hypothesis |
| :--- | :--- | :--- | :--- |
| **Full ULC-v4 (Baseline)** | Unmodified System | Full 10D evidence, Bayesian confidence, Pareto arbitrator, 12-state FSM, Scenarios A–J. | Benchmark reference. |
| **No Evidence Synthesis** | [`v4_evidence.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_evidence.py) | Replaces 10D normalized vector with raw scalar inputs. | Removing normalization may increase state oscillation. |
| **No Bayesian Confidence** | [`confidence.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/confidence.py) | Sets all posterior confidence scores to flat 0.50 neutral value. | Disables confidence-weighted learning rate surges. |
| **No Pareto Arbitration** | [`arbitrator.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/arbitrator.py) | Forces fixed `"partial"` replay purge without Pareto weighting. | Degrades minority recall during valid concept drift. |
| **No Minority Intelligence** | [`adaptive_ml/minority/`](file:///c:/projects/AdaptiveML/adaptive_ml/minority/) | Disables prior tracking and dynamic thresholding (\(\tau = 0.50\)). | Collapses predictions toward majority class. |
| **No Selective Replay Purge** | [`ClassBalancedReservoirReplay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) | Forces full wipeout of replay buffer on drift alert. | Destroys minority instances upon each drift alarm. |
| **No Resource Budgeting** | [`DynamicResourceBudgetManager`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py) | Unconstrained batch execution without throttling. | Eliminates batch-scale throttling overhead. |
| **On-Demand Explanations** | [`ULCExplainer`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/explainer.py) | Disables step-by-step natural language narrative formatting. | Reduces per-step controller latency. |

---

## 2. Experimental Controls
- **Seeds:** 42, 123, 456, 789, 2024.
- **Data Generator:** Standardized 60-batch imbalanced stream across 5 regimes (Stationary, Noise Burst, Gradual Drift, Abrupt Inverted Drift, Recurring Drift).
- **Metric Accounting:** Strict prequential test-then-train evaluation (prediction precedes label revelation).

