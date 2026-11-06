# Stage 2: Test Results Report
## Production Defect Remediation & Architecture Hardening

**Document Identifier:** `VERIF-STAGE-2-005`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Date:** November 2026<br>
**Test Suite:** `pytest 8.2.2`<br>
**Python Runtime:** `Python 3.14.3` on Windows 11 Enterprise AMD64<br>
**Pass Rate:** `63/63 passed (100.0%)`

---

## 1. Executive Summary

All 54 existing baseline tests across unit, integration, and remediation suites continue to pass without regression. In addition, 9 new comprehensive unit tests were authored in [`tests/unit/test_stage2_remediation.py`](file:///c:/projects/AdaptiveML/tests/unit/test_stage2_remediation.py) to validate DEF-006, DEF-007, and cross-pillar coordination. The complete test suite now totals **63 passed tests in 3.97 seconds**.

---

## 2. Itemized Test Results

### 2.1 Stage 2 Remediation Suite (`tests/unit/test_stage2_remediation.py`)

| Test Class | Test Name | Status | Duration | Coverage Target |
| :--- | :--- | :--- | :--- | :--- |
| `TestDEF006ReplayBufferContract` | `test_classifier_replay_buffer_property` | **PASSED** | 0.05s | Public `@property replay_buffer` access |
| `TestDEF006ReplayBufferContract` | `test_replay_buffer_purge_full` | **PASSED** | 0.04s | Complete memory flush via `policy="full"` |
| `TestDEF006ReplayBufferContract` | `test_replay_buffer_purge_selective_preserves_minority` | **PASSED** | 0.06s | Reliability filtering with minority retention |
| `TestDEF006ReplayBufferContract` | `test_replay_buffer_purge_partial` | **PASSED** | 0.04s | 50% majority pruning with minority retention |
| `TestDEF006ReplayBufferContract` | `test_classifier_purge_replay_method` | **PASSED** | 0.05s | Facade method on `AdaptiveClassifier` |
| `TestDEF006ReplayBufferContract` | `test_invalid_purge_policy_raises_validation_error` | **PASSED** | 0.03s | Validation on unrecognized purge policy |
| `TestDEF007OptimizerContract` | `test_low_memory_adamw_reset_momenta_numpy` | **PASSED** | 0.07s | Zeroing of quantized `q_m` and `scale_m` |
| `TestDEF007OptimizerContract` | `test_low_memory_adamw_scale_learning_rate` | **PASSED** | 0.03s | Multiplier applied to `param_groups[0]["lr"]` |
| `TestStage2CrossPillarCoordination` | `test_ulc_confirmed_drift_triggers_safe_purge_and_momentum_reset` | **PASSED** | 0.09s | End-to-end ULC drift triggering purge & reset |

---

## 3. Full Test Suite Execution Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-8.2.2, pluggy-1.6.0
rootdir: C:\projects\AdaptiveML
configfile: pyproject.toml
collected 63 items

tests/integration/test_end_to_end.py (2 items) ................ PASSED
tests/integration/test_sklearn_integration.py (3 items) ........ PASSED
tests/integration/test_torch_integration.py (2 items) .......... PASSED
tests/unit/test_ala.py (10 items) .............................. PASSED
tests/unit/test_backends.py (2 items) .......................... PASSED
tests/unit/test_defect_remediation.py (10 items) ............... PASSED
tests/unit/test_rao.py (8 items) ............................... PASSED
tests/unit/test_rla.py (7 items) ............................... PASSED
tests/unit/test_stage2_remediation.py (9 items) ................ PASSED
tests/unit/test_state.py (2 items) ............................. PASSED
tests/unit/test_ulc.py (8 items) ............................... PASSED

============================= 63 passed in 3.97s ==============================
```
