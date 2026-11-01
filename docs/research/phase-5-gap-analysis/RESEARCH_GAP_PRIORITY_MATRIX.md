# AdaptiveML — Phase 5: Research Gap Priority Matrix

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-006`  
> **Last Updated**: 2026-11-01  
> **Scoring Dimensions**: 8 criteria scored from 1 (Lowest) to 5 (Highest); Maximum possible score = 40

---

## 1. Prioritization Scoring Dimensions

1. **Research Significance (SIG)**: Scientific importance and depth of theoretical challenge.
2. **Evidence Strength (EVD)**: Quality and consistency of empirical evidence supporting the gap.
3. **Practical Impact (IMP)**: Real-world value to production practitioners and developers.
4. **Differentiation Potential (DIFF)**: Opportunity to distinguish AdaptiveML from River, Cleanlab, bitsandbytes.
5. **Technical Feasibility (FEAS)**: Engineering tractability within Python/NumPy/PyTorch CPU constraints.
6. **Evaluation Feasibility (EVAL)**: Ability to measure outcomes using standardized public benchmarks.
7. **Ecosystem Relevance (ECO)**: Direct alignment with target users (ML engineers, data scientists, researchers).
8. **Risk Level (RSK)**: Low operational/convergence risk (scored 5 for lowest risk, 1 for highest risk).

---

## 2. Research Gap Scoring Matrix

| Gap ID | Pillar | Research Gap Description | SIG | EVD | IMP | DIFF | FEAS | EVAL | ECO | RSK | Total (/40) | Confidence | Priority |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **GAP-01** | RLA | **Small-Loss Failure in Imbalanced Noise**: Density-aware margin scoring to protect rare tail classes. | 5 | 5 | 5 | 5 | 4 | 5 | 5 | 4 | **38** | High | **P0 (Critical)** |
| **GAP-02** | ULC | **Drift-Noise Retraining Collision**: Gating drift alarms with sample reliability distributions. | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 4 | **37** | High | **P0 (Critical)** |
| **GAP-03** | RAO | **CPU Optimizer State Memory Overhead**: Pure Python/NumPy block-quantized AdamW ($30\%–50\%$ memory cut). | 4 | 5 | 5 | 5 | 5 | 5 | 5 | 4 | **38** | High | **P0 (Critical)** |
| **GAP-04** | ALA | **Vectorized 2D NumPy Stream Ingestion**: scikit-learn `partial_fit` matrix processing on streams. | 3 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | **37** | High | **P1 (High)** |
| **GAP-05** | ALA | **Noise-Resilient Concept Drift Detector**: Extending ADWIN to weighted empirical averages. | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **32** | High | **P1 (High)** |
| **GAP-06** | RAO | **Adafactor Momentum-Drop Instability**: Restoring convergence via quantized 8-bit momentum. | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | **31** | Medium | **P1 (High)** |
| **GAP-07** | ULC | **Resource-Gated Plasticity Buffer**: Dynamic RAM allocation for edge replay buffers. | 3 | 4 | 3 | 3 | 4 | 4 | 3 | 4 | **28** | Medium | **P2 (Secondary)** |
| **GAP-08** | RLA | **Self-Tuning Robust Loss Parameter**: Automatic estimation of noise rate parameter $q$. | 4 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | **25** | Medium | **P2 (Secondary)** |
| **GAP-09** | ULC | **Autonomous Multi-Task Architecture NAS**: Automated hyperparameter/architecture search. | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | **14** | Low | **REJECTED** |

---

## 3. Priority Tier Assignments

### Priority P0 (Critical Foundation — Mandatory for Initial Release)
- **GAP-01 (RLA Small-Loss Imbalance)**: The definitive algorithmic contribution solving minority pruning.
- **GAP-02 (ULC Drift-Noise Collision)**: The definitive multi-objective contribution preventing corrupted retraining.
- **GAP-03 (RAO CPU Low-Memory AdamW)**: The definitive accessibility contribution enabling local CPU training.

### Priority P1 (High-Priority Research — Target Initial Release)
- **GAP-04 (ALA Vectorized Streams)**: Replacing single-instance dict loops with 2D NumPy array matrix processing.
- **GAP-05 (ALA Noise-Resilient Drift)**: Reliability-weighted statistical window cutting.
- **GAP-06 (RAO Momentum-Preserving Quantization)**: 8-bit first moment retention avoiding Adafactor stalls.

### Formally Rejected Directions
- **GAP-09 (Autonomous NAS / AutoML)**: Competing with Optuna / Ray Tune violates project focus; permanently rejected.
