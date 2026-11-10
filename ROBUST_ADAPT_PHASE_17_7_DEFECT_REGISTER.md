# ROBUST-ADAPT — Phase 17.7: Defect Register

**Repository:** `C:\projects\AdaptiveML`<br>
**Branch:** `master`<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`<br>
**Phase:** 17.7 — Alpha Defect Closure & Release Gate Reconciliation<br>
**Status:** ACTIVE AUDIT REGISTER

---

## 1. Master Defect Status Summary

| Defect ID | Category | Severity | Lifecycle Status | Phase Resolved / Verified | Blocker for Alpha Exit? |
|:---|:---|:---:|:---:|:---:|:---:|
| **DEF-ALPHA-001** | Implementation | High | **CLOSED (COMMITTED)** | Phase 17.3 (`4103b87`) | No |
| **ALPHA-DEF-001** | Ergonomics | Low | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **ALPHA-DEF-002** | Ergonomics | Moderate | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **ALPHA-DEF-003** | Ergonomics | Low | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **ALPHA-DEF-004** | Ergonomics | Low | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **ALPHA-DEF-005** | Robustness | Moderate | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **ALPHA-DEF-006** | Usability | Low | **RESOLVED & VERIFIED** | Phase 17.7 (Working Tree) | No |
| **DEF-004** | Legal / Trademark | Critical | **OPEN / PENDING LEGAL** | Outside Counsel Review | **YES (for Public GA)** |

---

## 2. Detailed Defect Dossiers

### 2.1 DEF-ALPHA-001 — `typing.Any` Import Regression in RLA Losses
- **Component:** `robust_adapt.rla.losses`
- **Description:** Unresolved `Any` type annotation caused `NameError` during import on Python 3.10 and 3.11 runtimes.
- **Remediation:** Added `Any` to `from typing import ...` in `losses.py`.
- **Status:** **CLOSED**. Committed in Git baseline `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`.

### 2.2 ALPHA-DEF-001 — `DelayedLabelQueue` Parameter Inconsistency
- **Component:** `robust_adapt.ala.delayed_labels`
- **Description:** Initializer required `max_wait_time`, whereas developer tutorials and intuitions used `max_delay`.
- **Remediation:** Added `max_delay` parameter, conflict validation against `max_wait_time`, and `@property def max_delay`.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

### 2.3 ALPHA-DEF-002 — `ConceptMemory.store_concept` Argument Ordering Rigidity
- **Component:** `robust_adapt.ala.concept_memory`
- **Description:** Required `(concept_id, model_state, X, y)`, leading to runtime errors when developers passed feature data first.
- **Remediation:** Implemented dynamic argument type sniffing supporting both `(concept_id, X, y, model_state)` and legacy ordering, plus keyword arguments and model getter methods.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

### 2.4 ALPHA-DEF-003 — `BlockQuantizer` Missing Unified Methods
- **Component:** `robust_adapt.rao.quantizer`
- **Description:** Developers were forced to distinguish between `quantize_signed` and `quantize_unsigned` manually.
- **Remediation:** Introduced unified `quantize(vector, signed=True)` and `dequantize(q_vector, scales, signed=True)`.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

### 2.5 ALPHA-DEF-004 — Scikit-learn Adapter Naming & Import Friction
- **Component:** `robust_adapt.integrations.sklearn` / `robust_adapt`
- **Description:** Adapters named `Sklearn*` were difficult to locate and could not be imported from root package.
- **Remediation:** Defined `ScikitLearn*` aliases in `sklearn.py` and exported them in root `robust_adapt` via lazy `__getattr__`.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

### 2.6 ALPHA-DEF-005 — `MultiSignalReliabilityEngine` Unnormalized Logits Distortion
- **Component:** `robust_adapt.rla.reliability`
- **Description:** Passing neural network logits without probabilities produced distorted margin metrics.
- **Remediation:** Added numerically stable softmax transformation, `compute_reliability_from_logits()`, and `input_type="probabilities"|"logits"` parameter.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

### 2.7 ALPHA-DEF-006 — `MinorityIntelligence20Learner` Missing Upfront Dimensions
- **Component:** `robust_adapt.minority.learner`
- **Description:** Inability to specify `n_features` or `n_classes` during `__init__`, preventing upfront model architecture introspection.
- **Remediation:** Added optional `n_features` and `n_classes=2` parameters to `__init__`, enabling immediate weight allocation and subsequent batch shape validation.
- **Status:** **RESOLVED & VERIFIED** in `tests/unit/test_phase17_7_remediation.py`.

---

## 3. Persistent Legal Blocker Dossier: DEF-004

### DEF-004 — Trademark & Project Brand Clearance
- **Severity:** Critical (Legal & Distribution Boundary)
- **Status:** **OPEN / PENDING OUTSIDE COUNSEL REVIEW**
- **Description:** A third-party commercial machine learning enterprise operates under the name "Adaptive ML" / "AdaptiveML". Distributing software publicly under the distribution name `adaptive-ml` or primary import namespace `adaptive_ml` carries severe trademark infringement and commercial dispute liability.
- **Technical Mitigations Executed:**
  - Complete elimination of the legacy `adaptive_ml` package namespace across the codebase and packaging files.
  - Canonical consolidation to `robust-adapt` (distribution) and `robust_adapt` (import).
  - All CI workflows verify complete absence of `adaptive_ml` in built wheels.
- **Remaining Requirement:** Formal written trademark clearance and legal entity brand approval by intellectual property legal counsel prior to:
  1. Registering names on public PyPI / TestPyPI.
  2. Public domain registration or announcement.
  3. Commercial deployment or General Availability release.
- **Impact on Alpha Exit:** Does NOT block local Alpha evaluation; strictly blocks public release and package index registration.

