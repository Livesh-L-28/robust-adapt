# ROBUST-ADAPT Compatibility Layer & Transition Report

> **Document ID:** `DOC-COMPAT-001`<br>
> **Status:** RATIFIED<br>
> **Effective Version:** `0.1.0.dev0`<br>
> **Date:** November 2026<br>
> **Canonical Namespace:** `robust_adapt`<br>
> **Compatibility Namespace:** `adaptive_ml`

---

## 1. Executive Summary

This report specifies the architecture, implementation, and verification of the backwards-compatibility layer bridging the legacy **AdaptiveML** namespace (`adaptive_ml`, `aml-core`) to **ROBUST-ADAPT** (`robust_adapt`, `robust-adapt`).

The compatibility layer guarantees:
1. **Zero Disruption for Existing Users:** Existing applications importing `adaptive_ml` continue to execute without code modification.
2. **Informed Transition:** Every import of `adaptive_ml` emits a standard Python `FutureWarning` alerting developers to update their import paths.
3. **100% Symbol Parity:** Every class, function, constant, and exception in `adaptive_ml` maps directly to its identical implementation in `robust_adapt`.
4. **Exception Handling Resilience:** Existing `try ... except AdaptiveMLError:` exception blocks catch all exceptions raised by `robust_adapt`.

---

## 2. Compatibility Architecture

### 2.1 Dual-Package Distribution Model

Rather than creating a disjoint stub package, `robust-adapt` ships with both the canonical `robust_adapt` package tree and the `adaptive_ml` compatibility tree bundled into the same distribution wheel (`robust_adapt-0.1.0.dev0-py3-none-any.whl`).

```
Wheel Package Root
├── robust_adapt/            [CANONICAL SOURCE OF TRUTH]
│   ├── __init__.py          [Canonical imports, exports, __version__]
│   ├── py.typed             [PEP 561 compliance]
│   └── [submodules]         [Full algorithmic implementations]
└── adaptive_ml/             [COMPATIBILITY SHIM LAYER]
    ├── __init__.py          [FutureWarning emitter + re-exports]
    ├── py.typed             [PEP 561 compliance]
    └── [submodules]         [Direct re-exports from robust_adapt]
```

### 2.2 Deprecation Mechanism & Telemetry

When `adaptive_ml` is loaded, the top-level `__init__.py` executes:

```python
import warnings

warnings.warn(
    "The 'adaptive_ml' package has been rebranded to 'robust_adapt'. "
    "Please update your imports from 'adaptive_ml' to 'robust_adapt'. "
    "The 'adaptive_ml' compatibility namespace will be deprecated in future releases.",
    category=FutureWarning,
    stacklevel=2,
)
```

**Technical Specifications:**
- **Warning Category:** `FutureWarning` (intended for end users and developers; not hidden by default Python warning filters).
- **Stacklevel:** `stacklevel=2` correctly attributes the warning to the user's import statement rather than the internal `__init__.py` file.
- **Single-Emission per Runtime:** Python's default warning filter deduplicates module-level warnings, ensuring the notice is printed once per process execution.

---

## 3. Deprecation Lifecycle & Phasing

| Lifecycle Stage | Release Version | Timeline | Compatibility Layer Status |
| :--- | :--- | :--- | :--- |
| **Phase 1: Pre-Release (Current)** | `v0.1.0.dev0` | Present | Active `adaptive_ml` shim emitting `FutureWarning`. Full test suite pass. |
| **Phase 2: General Availability** | `v1.0.0` | Target Release | Active `adaptive_ml` shim bundled in `robust-adapt` wheel. Clear deprecation notice in documentation. |
| **Phase 3: Extended Transition** | `v1.x.y` | Maintenance | Ongoing shim availability; monitoring community migration telemetry. |
| **Phase 4: Sunsetting** | `v2.0.0` | Major Milestone | Permanent removal of `adaptive_ml` namespace. Strict requirement for `robust_adapt`. |

---

## 4. API Parity Matrix

The compatibility layer was verified against all 65+ public exports. The following table highlights core symbols:

| Pillar | Symbol Name | `robust_adapt` Path | `adaptive_ml` Alias Path | Parity Status |
| :--- | :--- | :--- | :--- | :---: |
| **ALA** | `AdaptiveClassifier` | `robust_adapt.ala.AdaptiveClassifier` | `adaptive_ml.ala.AdaptiveClassifier` | 100% IDENTICAL |
| **ALA** | `HoeffdingTree` | `robust_adapt.ala.HoeffdingTree` | `adaptive_ml.ala.HoeffdingTree` | 100% IDENTICAL |
| **ALA** | `ReliabilityWeightedADWIN` | `robust_adapt.ala.ReliabilityWeightedADWIN` | `adaptive_ml.ala.ReliabilityWeightedADWIN` | 100% IDENTICAL |
| **ALA** | `RecurringConceptMemory` | `robust_adapt.ala.RecurringConceptMemory` | `adaptive_ml.ala.RecurringConceptMemory` | 100% IDENTICAL |
| **RLA** | `MultiSignalReliabilityEngine` | `robust_adapt.rla.MultiSignalReliabilityEngine` | `adaptive_ml.rla.MultiSignalReliabilityEngine` | 100% IDENTICAL |
| **RLA** | `DensityAwareMarginScorer` | `robust_adapt.rla.DensityAwareMarginScorer` | `adaptive_ml.rla.DensityAwareMarginScorer` | 100% IDENTICAL |
| **RLA** | `SymmetricCrossEntropyLoss` | `robust_adapt.rla.SymmetricCrossEntropyLoss` | `adaptive_ml.rla.SymmetricCrossEntropyLoss` | 100% IDENTICAL |
| **Minority** | `OnlineClassPriorTracker` | `robust_adapt.minority.OnlineClassPriorTracker` | `adaptive_ml.minority.OnlineClassPriorTracker` | 100% IDENTICAL |
| **Minority** | `AdaptiveThresholdManager` | `robust_adapt.minority.AdaptiveThresholdManager` | `adaptive_ml.minority.AdaptiveThresholdManager` | 100% IDENTICAL |
| **RAO** | `LowMemoryAdamW` | `robust_adapt.rao.LowMemoryAdamW` | `adaptive_ml.rao.LowMemoryAdamW` | 100% IDENTICAL |
| **RAO** | `VectorizedLowMemoryAdamW` | `robust_adapt.rao.VectorizedLowMemoryAdamW` | `adaptive_ml.rao.VectorizedLowMemoryAdamW` | 100% IDENTICAL |
| **RAO** | `BlockQuantizer` | `robust_adapt.rao.BlockQuantizer` | `adaptive_ml.rao.BlockQuantizer` | 100% IDENTICAL |
| **ULC** | `UnifiedLearningControllerV5` | `robust_adapt.ulc.UnifiedLearningControllerV5` | `adaptive_ml.ulc.UnifiedLearningControllerV5` | 100% IDENTICAL |
| **ULC** | `ArbitrationAutomaton` | `robust_adapt.ulc.ArbitrationAutomaton` | `adaptive_ml.ulc.ArbitrationAutomaton` | 100% IDENTICAL |
| **State** | `ResilientCheckpointManager` | `robust_adapt.state.ResilientCheckpointManager` | `adaptive_ml.state.ResilientCheckpointManager` | 100% IDENTICAL |
| **Integrations**| `SklearnAdaptiveClassifier` | `robust_adapt.integrations.SklearnAdaptiveClassifier` | `adaptive_ml.integrations.SklearnAdaptiveClassifier` | 100% IDENTICAL |
| **Integrations**| `TorchLowMemoryAdamW` | `robust_adapt.integrations.TorchLowMemoryAdamW` | `adaptive_ml.integrations.TorchLowMemoryAdamW` | 100% IDENTICAL |

---

## 5. Exception Catchability & Inheritance Verification

The base exception architecture guarantees cross-namespace interoperability:

```python
from robust_adapt.core.exceptions import RobustAdaptError, AdaptiveMLError
import adaptive_ml.core.exceptions as legacy_exc

# 1. Identity assertion
assert RobustAdaptError is AdaptiveMLError
assert legacy_exc.AdaptiveMLError is RobustAdaptError

# 2. Polymorphic catching
try:
    raise robust_adapt.core.exceptions.ConfigurationError("Invalid hyperparameter")
except legacy_exc.AdaptiveMLError as e:
    # Successfully caught!
    pass
```

All 6 concrete exception types (`ConfigurationError`, `ValidationError`, `StateError`, `ResourceBudgetExceededError`, `IntegrationDependencyError`, `DriftDetectionError`) inherit from `RobustAdaptError`, ensuring zero catch escapes in existing production code.

---

## 6. Compatibility Layer Test Automation

The compatibility layer is actively tested in every CI run via `tests/unit/test_compatibility_shim.py`:
- `test_robust_adapt_primary_import`: Asserts direct import does not emit warnings.
- `test_adaptive_ml_compatibility_shim_warning`: Asserts legacy import emits `FutureWarning` containing migration instructions.
- `test_exception_hierarchy_compatibility`: Validates `AdaptiveMLError is RobustAdaptError` and sub-exception inheritance.
- `test_submodule_parity`: Iterates over all 8 submodules to verify symbol identity.

---

## 7. Conclusion

The ROBUST-ADAPT compatibility layer delivers seamless transition guarantees. It eliminates risks of sudden breaking changes, guides developers proactively toward the new canonical identity, and maintains full operational continuity across downstream deployments.
