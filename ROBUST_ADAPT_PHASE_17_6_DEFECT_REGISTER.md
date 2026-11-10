# ROBUST-ADAPT — Phase 17.6: Alpha Defect Register

**Repository:** `C:\projects\AdaptiveML`<br>
**Branch:** `master`<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`<br>
**Distribution:** `robust-adapt`<br>
**Canonical Import:** `robust_adapt`<br>
**Version:** `0.1.0.dev0`<br>
**Audit Focus:** Formal Registration of Alpha Usability, Technical, and Governance Defects

---

## 1. Defect Master Table

| Defect ID | Category | Severity | Affected Component | Summary | Operational Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ALPHA-DEF-001** | Usability / API | **Medium** | `robust_adapt.ala.delayed_labels` | `DelayedLabelQueue` constructor parameter named `max_wait_time` instead of expected `max_delay`, causing `TypeError`. | **REGISTERED** |
| **ALPHA-DEF-002** | Usability / API | **Medium** | `robust_adapt.ala.concept_memory` | `ConceptMemory.store_concept()` places `model_state` ahead of training data `X, y`, causing argument transposition errors. | **REGISTERED** |
| **ALPHA-DEF-003** | Usability / API | **Medium** | `robust_adapt.rao.quantizer` | `BlockQuantizer` lacks a generic `quantize()` method, raising `AttributeError` when developers attempt standard calls. | **REGISTERED** |
| **ALPHA-DEF-004** | Usability / API | **Low** | `robust_adapt.integrations.sklearn` | Scikit-learn estimator adapter is named `SklearnAdaptiveClassifier`, lacking expected `ScikitLearnAdaptiveClassifier` alias. | **REGISTERED** |
| **ALPHA-DEF-005** | Usability / API | **Low** | `robust_adapt.rla.reliability` | `MultiSignalReliabilityEngine.compute_reliability` takes `probas`, whereas losses take `logits`, risking unnormalized score inputs. | **REGISTERED** |
| **ALPHA-DEF-006** | Usability / API | **Low** | `robust_adapt.minority.learner` | `MinorityIntelligence20Learner` does not accept `n_features` in `__init__`, departing from the standard `AdaptiveClassifier` signature. | **REGISTERED** |
| **DEF-004** | Legal / Governance | **High** | Global Package Identity | Trademark and naming clearance for "ROBUST-ADAPT" pending outside intellectual property counsel review. | **OPEN / RELEASE BLOCKER** |
| **BENCH-DEF-001** | Benchmark Integrity | **High** | Phase 17 Validation Report | Disparate scalar loss comparison between Standard Cross-Entropy and Symmetric Cross-Entropy. | **MITIGATED VIA AUDIT** |
| **BENCH-DEF-002** | Benchmark Integrity | **Medium** | Phase 17 Validation Report | Runtime asymmetry comparing bare NumPy addition ($2.22\text{ ms}$) vs per-step OS `psutil` process memory syscalls ($451.54\text{ ms}$). | **RECONCILED** |
| **BENCH-DEF-003** | Test Suite Parity | **Low** | `benchmarks/phase-12/` | Lack of a dedicated standalone benchmark driver for Adaptive Minority Intelligence. | **BACKLOGGED** |
| **BENCH-DEF-004** | Performance Limitation | **Medium** | `robust_adapt.rao` | Pure Python block quantization loop incurs $140\times$ CPU step latency overhead ($3.12\text{ ms}$ vs $0.022\text{ ms}$). | **DOCUMENTED LIMITATION** |

---

## 2. Detailed Alpha Defect Dossiers

### 2.1 ALPHA-DEF-001: DelayedLabelQueue Parameter Naming Mismatch
* **Defect ID:** `ALPHA-DEF-001`
* **Severity:** **Medium** (API Discoverability & Developer Experience)
* **Component:** `robust_adapt.ala.delayed_labels.DelayedLabelQueue`
* **Reproduction Steps:**
  ```python
  from robust_adapt.ala import DelayedLabelQueue

  queue = DelayedLabelQueue(max_delay=50.0)
```
* **Expected Behavior:** Instantiates queue with a maximum allowable label delay threshold of 50.0 seconds.
* **Actual Behavior:** Raises `TypeError: DelayedLabelQueue.__init__() got an unexpected keyword argument 'max_delay'`.
* **Root Cause:** The constructor parameter was named `max_wait_time: Optional[float] = None` during initial implementation.
* **Proposed Remediation:** Update `__init__` signature in Phase 18 to accept `max_delay: Optional[float] = None` as an alias for `max_wait_time`.
* **Status:** **REGISTERED**.

---

### 2.2 ALPHA-DEF-002: ConceptMemory Parameter Order Inversion
* **Defect ID:** `ALPHA-DEF-002`
* **Severity:** **Medium** (API Ergonomics)
* **Component:** `robust_adapt.ala.concept_memory.ConceptMemory.store_concept`
* **Reproduction Steps:**
  ```python
  mem = ConceptMemory()
  mem.store_concept("concept_1", X_batch, y_batch, model_state)
```
* **Expected Behavior:** Stores concept using standard `(id, data, target, state)` parameter order.
* **Actual Behavior:** Raises `TypeError` because the actual method signature is `store_concept(self, concept_id: str, model_state: Dict[str, Any], X: np.ndarray, y: Optional[np.ndarray] = None)`.
* **Root Cause:** Inverted parameter order placing metadata ahead of training data.
* **Proposed Remediation:** Update signature to `store_concept(concept_id, X, y=None, model_state=None)` or make `model_state` a keyword-only argument.
* **Status:** **REGISTERED**.

---

### 2.3 ALPHA-DEF-003: BlockQuantizer Missing Generic `quantize` Method
* **Defect ID:** `ALPHA-DEF-003`
* **Severity:** **Medium** (API Ergonomics)
* **Component:** `robust_adapt.rao.quantizer.BlockQuantizer`
* **Reproduction Steps:**
  ```python
  from robust_adapt.rao import BlockQuantizer

  quantizer = BlockQuantizer(block_size=64)
  q, s = quantizer.quantize(tensor_data)
```
* **Expected Behavior:** Quantizes array using default signed 8-bit quantization.
* **Actual Behavior:** Raises `AttributeError: 'BlockQuantizer' object has no attribute 'quantize'`.
* **Root Cause:** `BlockQuantizer` only defines `quantize_signed` and `quantize_unsigned`.
* **Proposed Remediation:** Add `quantize(self, vector: np.ndarray, signed: bool = True)` that delegates to `quantize_signed`.
* **Status:** **REGISTERED**.

---

### 2.4 ALPHA-DEF-004: Scikit-Learn Estimator Name Inconsistency
* **Defect ID:** `ALPHA-DEF-004`
* **Severity:** **Low** (Developer Ergonomics)
* **Component:** `robust_adapt.integrations.sklearn`
* **Reproduction Steps:**
  ```python
  from robust_adapt.integrations.sklearn import ScikitLearnAdaptiveClassifier
```
* **Expected Behavior:** Imports the scikit-learn compatible classifier adapter.
* **Actual Behavior:** Raises `ImportError: cannot import name 'ScikitLearnAdaptiveClassifier'`.
* **Root Cause:** The class is named `SklearnAdaptiveClassifier` (without `Scikit`).
* **Proposed Remediation:** Export `ScikitLearnAdaptiveClassifier = SklearnAdaptiveClassifier` alias in `integrations.sklearn`.
* **Status:** **REGISTERED**.

---

### 2.5 DEF-004: Trademark Clearance for "ROBUST-ADAPT" (Release Blocker)
* **Defect ID:** `DEF-004`
* **Severity:** **High** (Legal Compliance & Distribution Blocker)
* **Component:** Package Identity & Public Distribution
* **Title:** Trademark and naming clearance for "ROBUST-ADAPT" remains pending outside legal counsel review.
* **Impact:** Public PyPI upload, TestPyPI distribution, and external marketing remain strictly prohibited.
* **Status:** **OPEN / PENDING OUTSIDE COUNSEL REVIEW**.

