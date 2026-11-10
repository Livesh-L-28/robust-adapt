# ROBUST-ADAPT — Phase 17.7: Alpha Defect Triage & Remediation Decisions

**Repository:** `C:\projects\AdaptiveML`<br>
**Branch:** `master`<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`<br>
**Distribution:** `robust-adapt`<br>
**Canonical Package:** `robust_adapt`<br>
**Version:** `0.1.0.dev0`<br>
**Audit Focus:** Triage of Six Alpha Usability Defects and Remediation Boundary Assessment

---

## 1. Executive Summary

Gate 17.7.1 conducts a rigorous engineering review of all six usability and API defects discovered during Phase 17.6 Alpha testing (`ALPHA-DEF-001` through `ALPHA-DEF-006`). Each defect was triaged against three strict criteria:
1. **Mathematical & Algorithmic Invariance:** Core mathematical models, loss formulas, and split criteria must remain 100% unaltered.
2. **Backward Compatibility:** All existing positional and keyword calling patterns must continue to function without regression.
3. **Ergonomic Improvement:** The change must measurably reduce cognitive load, eliminate surprising exceptions, and align with standard Python/scikit-learn conventions.

---

## 2. Six-Defect Triage & Decision Matrix

| Defect ID | Affected Component | Usability Issue Reported | Triage Decision | Remediation Approach | Breaking Change Risk |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **ALPHA-DEF-001** | `ala.delayed_labels` | `DelayedLabelQueue` parameter `max_wait_time` conflicts with intuitive name `max_delay`. | **APPROVE** | Accept `max_delay` as an explicit keyword alias; validate conflicting values; provide property alias. | **Zero** (100% backward compatible) |
| **ALPHA-DEF-002** | `ala.concept_memory` | `store_concept()` places `model_state` ahead of training data `X, y`. | **APPROVE** | Implement signature polymorphism supporting both legacy `(concept_id, model_state, X, y)` and ergonomic `(concept_id, X, y, model_state)`. | **Zero** (Legacy callers preserved) |
| **ALPHA-DEF-003** | `rao.quantizer` | `BlockQuantizer` lacks generic `quantize()` and `dequantize()` methods. | **APPROVE** | Add `quantize()` and `dequantize()` convenience methods delegating to signed 8-bit routines by default. | **Zero** (Purely additive) |
| **ALPHA-DEF-004** | `integrations.sklearn` | Scikit-learn adapter is named `SklearnAdaptiveClassifier`, lacking expected `ScikitLearnAdaptiveClassifier` alias. | **APPROVE** | Export `ScikitLearnAdaptiveClassifier` and transformer aliases in `integrations.sklearn` and `__all__`. | **Zero** (Purely additive) |
| **ALPHA-DEF-005** | `rla.reliability` | `compute_reliability` requires normalized `probas`, whereas other APIs use `logits`. | **APPROVE** | Add explicit `compute_reliability_from_logits()` method and `input_type` parameter; no heuristic autodetection. | **Zero** (Explicit modes, backward compatible) |
| **ALPHA-DEF-006** | `minority.learner` | `MinorityIntelligence20Learner` does not accept `n_features` in `__init__`. | **APPROVE** | Support optional `n_features: Optional[int] = None` and `n_classes: int = 2` while preserving dynamic inference default. | **Zero** (Optional parameter addition) |

---

## 3. Detailed Defect Analysis & Remediation Strategy

### 3.1 ALPHA-DEF-001 — DelayedLabelQueue Parameter Naming
* **Problem:** In streaming asynchronous queues, developers expect `DelayedLabelQueue(max_delay=50.0)`. Passing `max_delay` raised `TypeError: unexpected keyword argument 'max_delay'`.
* **Remediation Strategy:**
  1. Add `max_delay: Optional[float] = None` as keyword-only parameter to `__init__`.
  2. If both `max_wait_time` and `max_delay` are provided with conflicting values, raise `ValidationError`.
  3. If only `max_delay` is provided, assign to internal `self.max_wait_time`.
  4. Expose `@property def max_delay(self) -> Optional[float]` returning `self.max_wait_time`.
  5. Retain existing positional signature `(max_queue_size=10000, max_wait_time=None)` unchanged.

### 3.2 ALPHA-DEF-002 — ConceptMemory.store_concept Argument Order
* **Problem:** The legacy signature `store_concept(self, concept_id: str, model_state: Dict[str, Any], X: np.ndarray, y: Optional[np.ndarray] = None)` placed `model_state` ahead of `X, y`, violating the standard `(data, target, metadata)` pattern.
* **Remediation Strategy:**
  1. Inspect the second positional argument dynamically at runtime:
     * If `isinstance(arg2, np.ndarray)`: Caller passed `X` as second argument. Map `X = arg2`, `y = arg3`, and resolve `model_state` from `kwargs` or 4th argument.
     * If `isinstance(arg2, dict)`: Caller used legacy positional signature `(concept_id, model_state, X, y)`. Execute legacy mapping.
  2. Support full keyword invocation: `store_concept(concept_id=..., X=..., y=..., model_state=...)`.
  3. Retain complete compatibility for all existing unit tests and integration scripts.

### 3.3 ALPHA-DEF-003 — BlockQuantizer Generic Methods
* **Problem:** Developers calling `quantizer.quantize(vector)` or `quantizer.dequantize(q, scales)` received `AttributeError`.
* **Remediation Strategy:**
  1. Add `def quantize(self, vector: np.ndarray, signed: bool = True) -> Tuple[np.ndarray, np.ndarray]`.
     Delegates directly to `quantize_signed` (if signed=True) or `quantize_unsigned` (if signed=False).
  2. Add `def dequantize(self, q_vector: np.ndarray, scales: np.ndarray, signed: bool = True) -> np.ndarray`.
     Delegates directly to `dequantize_signed` or `dequantize_unsigned`.
  3. Existing specific methods (`quantize_signed`, etc.) remain fully functional and documented.

### 3.4 ALPHA-DEF-004 — Scikit-Learn Class Naming Alias
* **Problem:** Developers importing from `robust_adapt.integrations.sklearn` naturally tried `ScikitLearnAdaptiveClassifier` and received `ImportError`.
* **Remediation Strategy:**
  1. In `robust_adapt.integrations.sklearn`, declare:
     ```python
     ScikitLearnAdaptiveClassifier = SklearnAdaptiveClassifier
     ScikitLearnDriftDetectorTransformer = SklearnDriftDetectorTransformer
     ScikitLearnReliabilityFilter = SklearnReliabilityFilter
```
  2. Add all aliases to `__all__` in `sklearn.py` and top-level `robust_adapt/__init__.py`.
  3. Maintain `SklearnAdaptiveClassifier` as the canonical reference class to adhere to PEP 8 brevity conventions.

### 3.5 ALPHA-DEF-005 — Reliability Engine Input Semantics
* **Problem:** `MultiSignalReliabilityEngine.compute_reliability(X, y, probas)` expects normalized posterior probabilities in $[0, 1]$, whereas `SymmetricCrossEntropyLoss` expects unnormalized `logits`. Passing logits to reliability scoring distorted distances.
* **Remediation Strategy:**
  1. **Strict No-Autodetection Policy:** In accordance with Gate 17.7.1 guidelines, do NOT implement heuristic threshold guessing (which can fail silently on bounded logit distributions).
  2. Add a dedicated explicit method:
     `def compute_reliability_from_logits(self, X: np.ndarray, y: np.ndarray, logits: np.ndarray) -> np.ndarray`.
     Converts logits via numerically stable softmax ($z - \max(z)$) before delegating to `compute_reliability`.
  3. Add `logits: Optional[np.ndarray] = None` and `input_type: str = "probabilities"` to `compute_reliability()`.
     If `input_type == "logits"` or `logits` keyword is provided, numerically stable softmax is applied explicitly.

### 3.6 ALPHA-DEF-006 — MinorityIntelligence20Learner Constructor Ergonomics
* **Problem:** `AdaptiveClassifier` requires `n_features`, whereas `MinorityIntelligence20Learner` inferred feature dimensions dynamically from the first batch, surprising developers expecting constructor parameter symmetry.
* **Remediation Strategy:**
  1. Document that dynamic feature dimension inference on the first batch is standard linear estimator behavior (matching scikit-learn `SGDClassifier`).
  2. Add optional keyword-only parameters `n_features: Optional[int] = None` and `n_classes: int = 2` to `__init__`.
  3. If `n_features` is explicitly provided, pre-initialize weight vector `self.weights = rng.normal(0.0, 0.01, size=n_features)`.
  4. If `n_features` is omitted (None), maintain current dynamic inference behavior without modification.

---

## 4. Defect Closure Roadmap

All six remediations are approved for immediate implementation under Gate 17.7.3. Every change is strictly additive, preserves 100% of existing behavior, and introduces zero risk of test regression.

