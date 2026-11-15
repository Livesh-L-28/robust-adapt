# ROBUST-ADAPT: Interactive Demonstration Project

This standalone demonstration suite showcases the core capabilities, architectural pillars, and production integration patterns of **[`robust-adapt`](https://pypi.org/project/robust-adapt/)** (version `1.0.0`), a Python library for resilient continual learning under real-world non-stationarity, label noise, extreme class imbalance, and strict resource constraints.

---

## Quickstart

### 1. Installation

Install `robust-adapt` directly from PyPI along with the demo dependencies:

```bash
pip install robust-adapt matplotlib scikit-learn numpy scipy safetensors
```

Or install using the provided requirements file:

```bash
pip install -r requirements.txt
```

### 2. Run All Demonstrations

#### From Repository Root:
```bash
# Windows PowerShell (using project venv):
.venv\Scripts\python.exe demo_project\run_all_demos.py

# Or with virtual environment activated / global Python:
python demo_project/run_all_demos.py
```

#### From inside `demo_project/`:
```bash
cd demo_project
python run_all_demos.py
```

#### If Cloning Fresh from GitHub:
```bash
git clone https://github.com/Livesh-L-28/robust-adapt.git
cd robust-adapt/demo_project
python run_all_demos.py
```

Expected output:
```text
================================================================================
 MASTER DEMONSTRATION SUITE EXECUTION SUMMARY
================================================================================
#   | Demo Script                        | Pillar / Module                | Time    | Status
--------------------------------------------------------------------------------
1   | 01_concept_drift_stream.py         | Adaptive Learning Architecture |  0.57s | PASSED [OK]
2   | 02_noisy_labels_defense.py         | Robust Loss & Correction       |  0.42s | PASSED [OK]
3   | 03_imbalanced_fraud_detection.py   | Online Prior & Threshold       |  0.15s | PASSED [OK]
4   | 04_resource_budget_optimization.py | Block Quant & Dynamic Latency  |  0.18s | PASSED [OK]
5   | 05_ulc_drift_vs_noise_burst.py     | Unified Learning Controller    |  0.19s | PASSED [OK]
6   | 06_sklearn_pipeline_integration.py | Ecosystem Compatibility        |  0.89s | PASSED [OK]
7   | 07_tamper_resistant_checkpoint.py  | Zero-Pickle SafeTensors + HMAC |  0.18s | PASSED [OK]
--------------------------------------------------------------------------------
Total Demonstrations: 7 | Passed: 7 | Failed: 0
Cumulative Execution Time: ~2.5 seconds
[SUCCESS] All 7 robust-adapt demonstrations executed with zero errors!
```

---

## Demonstration Catalog

### `01_concept_drift_stream.py` — Concept Drift Adaptation (ALA)
- **Module:** `robust_adapt.ala` (`AdaptiveClassifier`)
- **Problem:** Streaming data distributions shift over time (sudden and gradual concept drifts), degrading static models.
- **Solution:** Dynamically tracks predictive error rates via statistical drift detection and updates decision boundaries online without requiring a full manual retrain.
- **Run:** `python 01_concept_drift_stream.py`
- **Output:** Terminal telemetry table tracking phase transitions, drift detection flags, and an exported plot `01_concept_drift_result.png`.

---

### `02_noisy_labels_defense.py` — Label Noise Resistance & Rectification (RLA)
- **Module:** `robust_adapt.rla` (`GeneralizedCrossEntropyLoss`, `EvidenceBasedLabelCorrector`)
- **Problem:** Data streams often contain corrupted, swapped, or adversarial labels (e.g., up to 35% label noise), leading to catastrophic gradient explosion in standard cross-entropy.
- **Solution:** 
  1. **Generalized Cross-Entropy (GCE):** Provides bounded gradients that prevent noisy outliers from skewing model weights.
  2. **Evidence-Based Corrector:** Computes Bayesian belief states over sample confidence and neighborhood reliability to flip corrupted labels back to ground truth before updating.
- **Run:** `python 02_noisy_labels_defense.py`

---

### `03_imbalanced_fraud_detection.py` — Extreme Class Imbalance Mitigation (Minority)
- **Module:** `robust_adapt.minority` (`OnlineClassPriorTracker`, `AdaptiveThresholdManager`)
- **Problem:** Extreme class rarity (e.g., 2% fraud rate) causes fixed-threshold classifiers (0.5) to suffer high false-negative rates.
- **Solution:** Exponentially tracks streaming class priors and dynamically shifts the decision threshold to maximize minority-class recall while controlling false alarms.
- **Run:** `python 03_imbalanced_fraud_detection.py`
- **Metric:** Boosts minority fraud recall by +20.0% compared to a static decision threshold.

---

### `04_resource_budget_optimization.py` — Edge Quantization & Latency Budgets (RAO)
- **Module:** `robust_adapt.rao` (`BlockQuantizer`, `DynamicResourceBudgetManager`)
- **Problem:** Continual learning models deployed on constrained edge hardware or micro-services encounter latency spikes and memory ceilings.
- **Solution:**
  1. **8-bit Block Quantizer:** Compresses float32 model vectors into int8 representations, achieving **73.4% memory reduction** with virtually zero reconstruction error ($MSE \approx 8.9 \times 10^{-6}$).
  2. **Dynamic Latency Governor:** Enforces SLA thresholds (e.g., 10ms per batch), automatically throttling background operations and adjusting replay buffer ratios when latency pressure increases.
- **Run:** `python 04_resource_budget_optimization.py`

---

### `05_ulc_drift_vs_noise_burst.py` — Noise Bursts vs. Concept Drift Arbitration (ULC-v5)
- **Module:** `robust_adapt.ulc` (`UnifiedLearningControllerV5`, `ULCv5Config`, `ULCv5Directive`)
- **Problem:** Naive drift detectors trigger false alarms during temporary noise bursts, inducing catastrophic forgetting.
- **Solution:** Multi-tier hypothesis arbitration evaluates incoming streaming batches using both statistical divergence and directional cosine similarity:
  - *Transient Noise Burst:* Dispatches `TIER_1_FILTER_SAMPLE` (quarantines corrupted samples).
  - *Genuine Concept Drift:* Dispatches `TIER_3_ADAPT_LEARNER` (re-allocates learning rates and adjusts boundaries).
- **Run:** `python 05_ulc_drift_vs_noise_burst.py`

---

### `06_sklearn_pipeline_integration.py` — Scikit-Learn Compatibility
- **Module:** `robust_adapt.integrations.sklearn` (`SklearnAdaptiveClassifier`)
- **Problem:** Production ML pipelines require standard Scikit-Learn estimator semantics (`fit`, `partial_fit`, `predict`, `predict_proba`).
- **Solution:** Seamlessly embeds `robust-adapt` into `sklearn.pipeline.Pipeline` with transformers like `StandardScaler`, supporting incremental mini-batch updates via `partial_fit`.
- **Run:** `python 06_sklearn_pipeline_integration.py`

---

### `07_tamper_resistant_checkpoint.py` — Zero-Pickle SafeTensors + HMAC-SHA256
- **Module:** `robust_adapt.security` (`save_state`, `load_state`, `SecurityError`, `TamperError`)
- **Problem:** Standard Python `pickle` serialization exposes systems to remote code execution (RCE) vulnerabilities; unauthenticated model files risk silent adversarial tampering.
- **Solution:**
  - 100% Zero-Pickle: All weight tensors are persisted via **HuggingFace SafeTensors**.
  - Metadata and integrity hashes are verified with **HMAC-SHA256**.
  - Rejects corrupted or byte-tampered files with immediate `TamperError`.
- **Run:** `python 07_tamper_resistant_checkpoint.py`

---

## Architectural Overview

```
                      +---------------------------------------+
                      |       Streaming Input Stream          |
                      +---------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Unified Learning Controller (ULC-v5)                       |
|   - Divergence & Cosine Similarity Arbitration                                     |
|   - Multi-Tier Directive: No-Op / Filter Noise / Adjust / Adapt Learner           |
+-----------------------------------------------------------------------------------+
          |                                   |                              |
          v                                   v                              v
+--------------------+              +--------------------+         +--------------------+
|   ALA Architecture |              |    RLA Defense     |         | Minority Tracking  |
| - Drift Detection  |              | - GCE Robust Loss  |         | - Online Prior     |
| - Dynamic Ensembles|              | - Label Correction |         | - Adaptive Thresh  |
+--------------------+              +--------------------+         +--------------------+
          |                                   |                              |
          +-----------------------------------+------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                    Resource-Aware Optimization (RAO) & Security                   |
|   - 8-bit Block Quantizer (73% RAM Reduction)                                     |
|   - Dynamic Latency Budget Governor (SLA Protection)                              |
|   - Zero-Pickle SafeTensors + HMAC-SHA256 Checkpointing                           |
+-----------------------------------------------------------------------------------+
```

---

## Links & Reference

- **PyPI Package:** [https://pypi.org/project/robust-adapt/1.0.0/](https://pypi.org/project/robust-adapt/1.0.0/)
- **GitHub Repository:** [https://github.com/Livesh-L-28/robust-adapt](https://github.com/Livesh-L-28/robust-adapt)
- **Release v1.0.0:** [https://github.com/Livesh-L-28/robust-adapt/releases/tag/v1.0.0](https://github.com/Livesh-L-28/robust-adapt/releases/tag/v1.0.0)
- **License:** Apache 2.0

