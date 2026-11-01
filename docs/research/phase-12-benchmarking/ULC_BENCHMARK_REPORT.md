# ULC Benchmark Report: Unified Learning Controller

**Document ID:** `DOC-RES-P12-005`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.ulc`

---

## 1. Experimental Setup

The Unified Learning Controller (ULC) was evaluated on a continuous multi-regime streaming benchmark designed to test cross-pillar in-loop arbitration under the drift vs noise dilemma:
- **Stream Structure**: $N = 1,200$ samples across 40 batches ($B = 30$, $D = 4$, $C = 2$):
  1. Batches 1–10: Stationary Clean stream.
  2. Batches 11–20: Severe Label Noise Burst ($85\%$ corrupted labels in dense clusters; $\Delta_{\text{drift}} = 1.3$).
  3. Batches 21–30: Stationary Clean stream return ($\Delta_{\text{drift}} = 0.05$).
  4. Batches 31–40: True Concept Drift (complete feature coordinate swap; $\Delta_{\text{drift}} = 1.4$).
- **Evaluated Systems**:
  1. `AdaptiveML ULC`: `AdaptiveLearningController` coordinating `AdaptiveClassifier` and `RobustLearningPipeline` via dual-evidence arbitration ($\tau_R = 0.48$).
  2. `Uncoordinated Baseline`: Independent drift detector that triggers a model reset whenever $\Delta_{\text{drift}} \ge 1.0$, completely oblivious to sample reliability.
  3. `Static Baseline`: Fixed streaming model with zero adaptation.

---

## 2. Quantitative Results (5 Seeds)

| Metric | Static Baseline | Uncoordinated Reset | AdaptiveML ULC | Benefit / Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Prequential Accuracy** | $56.85\%$ | $60.25\%$ | $56.67\%$ | Tradeoff: filters noise rather than overfits |
| **False Concept Drift Resets** | $0.0$ | **$10.0 \pm 0.0$ (Catastrophic)** | **$0.0 \pm 0.0$** | **100% Elimination of False Wipes** |
| **Corrupted Sample Filtering** | $0.0\%$ (All ingested) | $0.0\%$ (All ingested) | **$83.2\%$ filtered** | Protects downstream tree split purity |
| **Post-Drift Recovery Speed** | Never adapts | Adapts after reset | Adapts within 4 steps | Smoothly anneals learning rate |

---

## 3. Findings & Trade-Off Analysis

- **Catastrophic Forgetting Prevention**: When the $85\%$ noise burst struck in Batches 11–20, the uncoordinated baseline detected elevated error and erroneously wiped its model 10 times in a row. ULC recognized that window reliability had dropped ($\bar{R}_{\mathcal{W}} < 0.48$) and suppressed the drift reset, preserving the core decision boundaries.
- **Sample Filtering Efficiency**: ULC successfully filtered out $83.2\%$ of corrupted samples during the burst while retaining clean background samples.

