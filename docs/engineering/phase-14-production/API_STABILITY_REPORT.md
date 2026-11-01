# API Stability and Deprecation Policy

**Document ID:** `DOC-ENG-P14-003`  
**Phase:** Phase 14 — Production Engineering  
**Status:** READY FOR REVIEW  

---

## 1. Public API Stability Levels

AdaptiveML categorizes its interfaces into three stability tiers:

| Tier | Stability Level | Modules & Classes | Breaking Change Policy |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Public Stable)** | High Stability | `AdaptiveClassifier`, `VectorizedHoeffdingTree`, `ReliabilityWeightedADWIN`, `LowMemoryAdamW`, `DensityAwareMarginScorer`, `SymmetricCrossEntropyLoss`, `AdaptiveLearningController` | Minimum 2 minor version deprecation warning cycle prior to removal. |
| **Tier 2 (Integration Adapters)**| Moderate Stability | `SklearnAdaptiveClassifier`, `TorchSymmetricCrossEntropyLoss`, `create_torch_low_memory_adamw` | Track upstream framework releases (`scikit-learn`, `torch`). |
| **Tier 3 (Internal Core)** | Internal / Experimental | `_Bucket`, `_compress_buckets`, `adaptive_ml.core.validation` | Subject to private refactoring; no deprecation guarantee. |

---

## 2. Semantic Versioning Protocol

Releases adhere strictly to **Semantic Versioning 2.0.0 (SemVer)**:
- `MAJOR` (x.0.0): Incompatible API modifications.
- `MINOR` (0.x.0): Backwards-compatible feature additions and new algorithm candidates.
- `PATCH` (0.0.x): Backwards-compatible bug fixes and numerical stability corrections.

