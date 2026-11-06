# AdaptiveML Stage 10 — Public API Stability Policy

**Distribution Package:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Version:** `0.1.0.dev0`<br>
**Status:** Canonical & Enforced<br>

---

## 1. Scope & Objective

This policy defines the public API contracts, versioning commitments, deprecation protocols, and stability guarantees for `aml-core` (`adaptive_ml`). It governs how public interfaces evolve, prevents silent semantic breaking changes, and guarantees long-term backward compatibility for production systems integrating AdaptiveML.

---

## 2. API Classification Hierarchy

Every exported module, class, function, and attribute in AdaptiveML is categorized under one of five stability tiers:

```
[STABLE]        -> High guarantee: Zero breaking changes without a major version bump & 2-minor deprecation cycle.
[PROVISIONAL]   -> Medium guarantee: Complete functional API; signatures may undergo non-breaking refinement.
[EXPERIMENTAL]  -> Research preview: Subject to rapid tuning based on empirical validation. Explicit opt-in.
[INTERNAL]      -> Private runtime: Prefix with underscore (_). Subject to modification without notice.
[DEPRECATED]    -> Scheduled for retirement: Issues a DeprecationWarning; maintained for compatibility window.
```

### Classification Breakdown

| Component | Stability Tier | Evolution & Guarantee Invariants |
|:---|:---|:---|
| **Root Public Exceptions** (`adaptive_ml.core.exceptions.*`) | **STABLE** | Exception hierarchy is immutable. Subclassing is preserved. |
| **Pillar 1 Core** (`AdaptiveClassifier`, `VectorizedHoeffdingTree`, `ReliabilityWeightedADWIN`) | **STABLE** | Method signatures (`fit`, `partial_fit`, `predict`, `predict_proba`, `score`) adhere strictly to scikit-learn protocol. |
| **Pillar 2 Core** (`MultiSignalReliabilityEngine`, `SymmetricCrossEntropyLoss`, `GeneralizedCrossEntropyLoss`) | **STABLE** | Loss mathematical formulas and scoring signatures are frozen. |
| **Pillar 3 Core** (`LowMemoryAdamW`, `DynamicResourceBudgetManager`) | **STABLE** | 8-bit dynamic block quantization parameters and budget state enums are backward-compatible. |
| **Pillar 4 ULC Facade** (`AdaptiveLearningController`, `ControllerDirective`, `ControllerState`) | **STABLE** | Facade step signature and action directive attributes are guaranteed stable. |
| **ULC-v4.1 Hybrid Controller** (`UnifiedLearningControllerV4_1`, `ULCv41Config`) | **PROVISIONAL** | Validated candidate promoted in Stage 7.3. Hyperparameters may undergo minor calibrated threshold tuning. |
| **Minority Intelligence** (`OnlineClassPriorTracker`, `AdaptiveThresholdManager`) | **PROVISIONAL** | G-mean threshold adaptation and prior tracking interfaces. |
| **Framework Integrations** (`adaptive_ml.integrations.*`) | **STABLE** | External adapters adhere strictly to third-party protocols (PyTorch `nn.Module`, scikit-learn `BaseEstimator`). |
| **Internal Engines** (`_Bucket`, `_Node`, `_history_*`, private helpers) | **INTERNAL** | Prefixed with leading underscore. No public stability guarantee. |

---

## 3. Compatibility Rules & Invariants

1. **Strict Parameter Invariants:**
   - Public function and method signatures must never change parameter ordering.
   - New parameters must always provide backward-compatible default values.
   - Positional parameters must not be removed or renamed without a deprecation window.

2. **Return Type Invariants:**
   - Return types of stable methods (`predict() -> np.ndarray`, `predict_proba() -> np.ndarray`, `score() -> float`) are invariant.
   - New dictionary fields in diagnostic returns are strictly additive.

3. **Exception Behavior Invariants:**
   - Public APIs raise only typed subclasses of [`AdaptiveMLError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py).
   - Raw untyped `Exception`, `IndexError`, or `KeyError` must never escape public boundary facades.

4. **Deprecation Protocol:**
   - Any API intended for removal must emit a standard `FutureWarning` or `DeprecationWarning` stating:
     1. The deprecated symbol name.
     2. The recommended replacement API.
     3. The scheduled removal version (minimum 2 minor release cycles).

---

## 4. Semantic Versioning Protocol

AdaptiveML adopts Semantic Versioning (`MAJOR.MINOR.PATCH`):
- `MAJOR`: Incompatible API changes, removals of deprecated symbols, or breaking architectural redesigns.
- `MINOR`: New backwards-compatible features, new framework adapters, or provisional controller enhancements.
- `PATCH`: Backwards-compatible bug fixes, reliability hardening, and security patches.

*Current Development Version:* `0.1.0.dev0`
