# ROBUST-ADAPT — Phase 17.6: Controlled Alpha Feedback Register

**Repository:** `C:\projects\AdaptiveML`<br>
**Branch:** `master`<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`<br>
**Distribution:** `robust-adapt`<br>
**Canonical Import:** `robust_adapt`<br>
**Version:** `0.1.0.dev0`<br>
**Feedback Source:** Structured Persona Feedback Synthesis (Internal Controlled Alpha)

---

## 1. Executive Summary & Persona Feedback Synthesis

This register captures all structured feedback gathered during internal controlled Alpha testing. Feedback is categorized across the six developer personas to reflect realistic developer journeys, distinguishing between:
1. **Confirmed Technical Defects** (bugs, unexpected crashes, signature discrepancies).
2. **API & Ergonomic Friction Points** (confusing parameter names, unexpected return structures).
3. **Documentation Gaps** (missing tutorials, unclear pre-release install flags).
4. **Strategic Feature Requests** (backlog enhancements for post-Alpha phases).

---

## 2. Feedback Categorized by Developer Persona

### Persona 1: Beginner Python ML Developer
* **Installation Experience:** Wheel installation was fast and clean. However, finding the wheel required inspecting `dist/` because running `pip install robust-adapt` fails on public PyPI (pre-release distribution).
* **API Friction:** Tried calling `quantizer.quantize()` on `BlockQuantizer` and got an `AttributeError`. Expected a generic default method.
* **Documentation Request:** Wants a 5-minute "Quickstart Streaming Classification" notebook on the landing page showing `AdaptiveClassifier.partial_fit` with an animated streaming loop.

### Persona 2: Intermediate scikit-learn Developer
* **Estimator Compatibility:** Pleased that `SklearnAdaptiveClassifier` implements `fit`, `predict`, and `predict_proba`.
* **API Confusion:** Initially attempted to import `ScikitLearnAdaptiveClassifier` and received an `ImportError`. Discovered that the actual class is named `SklearnAdaptiveClassifier`.
* **Feature Request:** Wants automated hyperparameter grid search support (`GridSearchCV`) with built-in time-series splits (`TimeSeriesSplit`) for streaming classifiers.

### Persona 3: PyTorch Deep Learning Engineer
* **Decoupling Assessment:** Very pleased that importing `robust_adapt` does not force PyTorch installation.
* **Loss Function Mechanics:** `TorchSymmetricCrossEntropyLoss` works cleanly with autograd. Noted that default hyperparameters ($\alpha=1.0, \beta=0.5$) work well on noisy CIFAR/MNIST-style synthetic benchmarks.
* **Performance Note:** Excited by the 73.44% memory savings in `VectorizedLowMemoryAdamW`. Noted that CUDA memory savings allow doubling batch sizes on memory-constrained GPUs (e.g., 8 GB / 16 GB VRAM).

### Persona 4: Concept Drift & Streaming ML Researcher
* **Drift Adaptation:** `ReliabilityWeightedADWIN` detected abrupt drift within 24 steps, achieving 92.8% recovery accuracy.
* **Signature Discrepancies:**
  * Expected `DelayedLabelQueue` to accept `max_delay`, but constructor required `max_wait_time`.
  * Expected `mean_observed_delay` to be a method `mean_observed_delay()`, but encountered `TypeError` because it is a property.
* **Feature Request:** Requesting standardized benchmark stream adapters for MOA / River datasets (e.g., Electricity, Forest Covertype).

### Persona 5: Imbalanced / Fraud Detection Engineer
* **Prior Tracking:** `OnlineClassPriorTracker` tracked 9:1 and 99:1 shifts accurately without requiring historical dataset storage.
* **Parameter Surprise:** `MinorityIntelligence20Learner` does not accept `n_features` or `n_classes`, departing from `AdaptiveClassifier`.
* **Threshold Tuning:** Noted that the default `target_fp_budget_per_1k = 1.5` is extremely conservative, requiring operator adjustment if high recall is prioritized over precision.

### Persona 6: Real-Time Streaming Systems Architect
* **Controller Coordination:** ULC controller seamlessly arbitrated between noise bursts and true drift, completely eliminating false model resets.
* **Telemetry Concern:** Warned about the per-step OS syscall issue identified in Phase 17.5 (`psutil.Process.memory_info().rss`). Strongly endorsed introducing a configurable sampling interval (`telemetry_sample_interval=50`).
* **Checkpoint Safety:** Praised the atomic checkpoint save mechanics utilizing temporary file swapping, which prevents corrupt partial state files upon unexpected process termination.

---

## 3. Structured Feedback Master Inventory

| Feedback Item ID | Category | Source Persona | Feedback Summary | Classification | Target Milestone |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **FDBK-001** | Documentation | Persona 1 | Add `--pre` flag instruction in installation docs for pre-release builds. | **Doc Improvement** | Phase 17.7 |
| **FDBK-002** | API Usability | Persona 1 | Add default `quantize()` convenience wrapper to `BlockQuantizer`. | **Ergonomics** | Phase 18 |
| **FDBK-003** | API Usability | Persona 2 | Add `ScikitLearnAdaptiveClassifier` alias in `integrations.sklearn`. | **Ergonomics** | Phase 18 |
| **FDBK-004** | API Usability | Persona 4 | Accept `max_delay` as alias for `max_wait_time` in `DelayedLabelQueue`. | **Ergonomics** | Phase 18 |
| **FDBK-005** | API Usability | Persona 4 | Reorder `ConceptMemory.store_concept` parameters to put data `X, y` before `model_state`. | **Ergonomics** | Phase 18 |
| **FDBK-006** | Performance | Persona 6 | Introduce `telemetry_sample_interval` in `DynamicResourceBudgetManager`. | **Performance Tuning** | Phase 18 |
| **FDBK-007** | Feature Request | Persona 5 | Provide standalone benchmark driver for Minority Intelligence (`BENCH-DEF-003`). | **Feature Request** | Phase 18 |
| **FDBK-008** | Feature Request | Persona 3 | Implement CUDA C-extension kernel for 8-bit AdamW step latency parity. | **Feature Request** | Phase 20 |
| **FDBK-009** | Feature Request | Persona 2 | Add River / MOA dataset loader integration in `robust_adapt.integrations.data`. | **Feature Request** | Phase 20 |

