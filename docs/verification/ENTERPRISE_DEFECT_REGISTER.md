# AdaptiveML — Enterprise Defect Register
## Comprehensive Log of Audit Findings, Technical Observations, and Legal Risks

**Document Identifier:** `VERIF-REG-009`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Verification Baseline:** Baseline Commit `67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** November 2026<br>
**Auditor:** Independent Enterprise Verification Agent<br>
**Status:** `ACTIVE — LOGGED FOR PROJECT OWNER TRIAGE`

---

## 1. Executive Summary

This register consolidates all defects, technical observations, code-quality warnings, and legal risks identified during the independent enterprise verification of AdaptiveML. Each entry is assigned an enterprise tracking identifier, categorized by risk severity, provided with reproducible evidence, and paired with an actionable remediation path.

### Summary of Register Items

| Defect ID | Category | Severity | Item Summary | Remediation Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | Packaging / Dependency | **MEDIUM** | Unguarded top-level `safetensors` import in `adaptive_ml.state.serializer` | **RESOLVED & VERIFIED** |
| **DEF-002** | Code Quality / Static | **LOW** | Use of `assert` in `adaptive_ml/ala/tree.py` (Bandit B101) | **RESOLVED & VERIFIED** |
| **DEF-003** | Code Quality / Static | **LOW** | Broad `except Exception: pass` in `telemetry.py` (Bandit B110) | **RESOLVED & VERIFIED** |
| **DEF-004** | Legal / Trademark | **HIGH** | Active trademark collision with Datadog's *Adaptive ML, Inc.* | **REMAINS OPEN (OWNER DECISION)** |
| **DEF-005** | Performance / Architecture | **INFORMATIONAL** | Pure NumPy CPU quantization step latency for $>5\text{M}$ parameters | **RESOLVED & VERIFIED** |
| **DEF-006** | Architecture / Contract | **MEDIUM** | Private replay buffer attribute access and missing selective purge contract | **RESOLVED & VERIFIED** |
| **DEF-007** | Architecture / Interface | **MEDIUM** | Missing `reset_momenta` and `scale_learning_rate` methods on `LowMemoryAdamW` | **RESOLVED & VERIFIED** |

---

## 2. Itemized Defect & Observation Records

### DEF-001: Unguarded Top-Level `safetensors` Import in State Management

- **Severity:** **MEDIUM**
- **Category:** Packaging & Modular Dependencies
- **Affected File:** [`adaptive_ml/state/serializer.py#L15`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py#L15)
- **Component:** Safe State Serialization / Checkpointing
- **Discovered In:** Independent Clean Wheel Installation Audit (`VERIF-AUD-001`)

#### Description & Impact
In [`pyproject.toml`](file:///c:/projects/AdaptiveML/pyproject.toml#L44-L46), `safetensors` is declared under `[project.optional-dependencies]`. However, in `adaptive_ml/state/serializer.py`, the import is top-level and unguarded:
```python
import safetensors.numpy as sn
```
When an end-user installs only the core distribution (`pip install aml-core`) and subsequently attempts to import `adaptive_ml.state` (or use `CheckpointManager`), Python immediately crashes with:
```text
ModuleNotFoundError: No module named 'safetensors'
```
*Note:* The core algorithmic packages (`ala`, `rla`, `rao`, `ulc`) do not import `adaptive_ml.state`, so streaming models function properly if checkpointing is not called.

#### Recommended Remediation
Wrap the import in a conditional availability guard in `adaptive_ml/state/serializer.py`:
```python
try:
    import safetensors.numpy as sn
    _SAFETENSORS_AVAILABLE = True
except ImportError:
    _SAFETENSORS_AVAILABLE = False
```
If `_SAFETENSORS_AVAILABLE` is `False`, raise `SerializationError("Safe tensor persistence requires 'safetensors'. Install with: pip install 'aml-core[safetensors]'")` when `save_state` or `load_state` is invoked.

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Wrapped `safetensors.numpy` import with conditional guard in `adaptive_ml/state/serializer.py`. Exported `is_safetensors_available()`. Ensured `SerializationError` with explicit installation guidance is raised whenever serialization or deserialization is requested without the optional extra.
- **Verification:** Verified in Python 3.11 environment with only NumPy installed: `import adaptive_ml` and `import adaptive_ml.state` succeed without error. Regression tests in `tests/unit/test_defect_remediation.py::TestDEF001SafetensorsIsolation` passed. Full details in [`docs/verification/remediation/DEF-001_OPTIONAL_DEPENDENCY_FIX.md`](file:///c:/projects/AdaptiveML/docs/verification/remediation/DEF-001_OPTIONAL_DEPENDENCY_FIX.md).

---

### DEF-002: Type-Narrowing Assertions in Tree Traversal (Bandit B101)

- **Severity:** **LOW**
- **Category:** Code Quality & Static Analysis
- **Affected File:** [`adaptive_ml/ala/tree.py#L177`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py#L177), [`L211`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py#L211), [`L230`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py#L230)
- **Component:** Vectorized Hoeffding Tree
- **Discovered In:** Security & Vulnerability Audit (`VERIF-SEC-006`)

#### Description & Impact
Bandit flagged three instances of `assert` statements used for type narrowing (e.g., `assert self.bin_edges is not None`). When Python is executed in optimized bytecode mode (`python -O` or `python -OO`), all `assert` statements are stripped by the compiler. While inputs are validated at ingestion by `check_array_2d`, reliance on `assert` for internal branch guarantees is discouraged in production libraries.

#### Recommended Remediation
Replace `assert` statements with explicit conditional checks:
```python
if self.bin_edges is None:
    raise ValidationError("Tree bin edges have not been initialized.")
```

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Replaced all three assertions in `adaptive_ml/ala/tree.py` (lines 177, 211, 230, and added guard in `_split_leaf`) with explicit checks raising `ValidationError`.
- **Verification:** Bandit scan reports **0 B101 issues**. Validated under `python -O` in `tests/unit/test_defect_remediation.py::TestDEF002RuntimeValidation::test_validation_works_under_optimized_python`. Full details in [`docs/verification/remediation/DEF-002_RUNTIME_VALIDATION_FIX.md`](file:///c:/projects/AdaptiveML/docs/verification/remediation/DEF-002_RUNTIME_VALIDATION_FIX.md).

---

### DEF-003: Broad Exception Handling in Telemetry Helpers (Bandit B110)

- **Severity:** **LOW**
- **Category:** Code Quality & Exception Handling
- **Affected File:** [`adaptive_ml/core/telemetry.py#L15`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py#L15), [`L43`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py#L43), [`L52`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py#L52)
- **Component:** Core Memory Budget Tracking
- **Discovered In:** Security & Vulnerability Audit (`VERIF-SEC-006`)

#### Description & Impact
The cross-platform RSS memory detection function [`get_process_memory_bytes()`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py#L9) attempts to query memory usage via `psutil`, Win32 API, and Linux `/proc/self/statm` sequentially. Each stage uses a catch-all `except Exception: pass`. Bandit flags this under rule `B110: try_except_pass`.

#### Recommended Remediation
Narrow the exception clauses to specific anticipated system errors:
```python
except (ImportError, AttributeError, OSError, PermissionError):
    pass
```

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Narrowed exception handlers in `adaptive_ml/core/telemetry.py` to `(ImportError, AttributeError, OSError)`, `(ImportError, AttributeError, OSError, ValueError)`, and `(FileNotFoundError, PermissionError, IsADirectoryError, OSError, ValueError, IndexError)`. Also fixed 64-bit Windows ctypes `GetCurrentProcess.restype = wintypes.HANDLE` to ensure the native Win32 API memory fallback works properly without psutil.
- **Verification:** Bandit scan reports **0 B110 issues**. Verified in `tests/unit/test_defect_remediation.py::TestDEF003TelemetryExceptionHandling` that unexpected programming bugs are not swallowed and legitimate platform fallbacks succeed. Full details in [`docs/verification/remediation/DEF-003_EXCEPTION_HANDLING_FIX.md`](file:///c:/projects/AdaptiveML/docs/verification/remediation/DEF-003_EXCEPTION_HANDLING_FIX.md).

---

### DEF-004: Active Trademark Collision with Datadog's "Adaptive ML, Inc."

- **Severity:** **HIGH (LEGAL & COMMERCIAL)**
- **Category:** Intellectual Property & Brand Governance
- **Affected Entity:** Project Brand Identity & PyPI Namespace
- **Discovered In:** Phase 3 Legal Review (`DOC-RES-P3-007`) & Current Status Inspection

#### Description & Impact
The commercial artificial intelligence enterprise **Adaptive ML, Inc.** (founded in 2023 by former researchers from Mistral and Meta, and acquired by **Datadog** in 2024) holds registered trademarks in the United States and European Union in Nice Class 42 (machine learning software services). They also hold the registered GitHub organization and PyPI namespace for `adaptive-ml` / `adaptiveml`.

Distributing or promoting this open-source project publicly under the primary name **"AdaptiveML"** presents significant legal risk of trademark infringement claims, cease-and-desist notices, or confusion in the developer community.

#### Existing Engineering Mitigation
1. The project has strictly designated "AdaptiveML" as an **internal provisional engineering codename** across all architectural specifications.
2. The PyPI distribution identifier in [`pyproject.toml`](file:///c:/projects/AdaptiveML/pyproject.toml#L6) has been set to **`aml-core`**.
3. Distribution wheels and tarballs are built exclusively under the `aml_core` namespace.

#### Required Project Owner Action
The Project Owner must formally resolve the permanent public brand identity prior to public PyPI distribution. Options include:
1. **Approve `aml-core` as permanent public name:** Formalize `aml-core` (or `libadaptive`) as the public package name, keeping AdaptiveML solely as an internal historical codename.
2. **Execute Full Rebrand:** Rename the repository, documentation headers, and import package to an uncontested namespace (e.g., `libadaptive`, `streamml`, `flexlearn`).
3. **Seek Outside IP Counsel Review:** Obtain formal legal clearance regarding the defensibility of descriptive use of "adaptive machine learning".

#### Current Status
- **Status:** **REMAINS OPEN (PENDING PROJECT OWNER & QUALIFIED LEGAL COUNSEL DECISION)**
- **Note:** Engineering cannot unilaterally resolve trademark and corporate brand collisions. The PyPI distribution namespace remains shielded under `aml-core`. Full analysis documented in [`docs/verification/remediation/DEF-004_OWNER_DECISION_REQUIRED.md`](file:///c:/projects/AdaptiveML/docs/verification/remediation/DEF-004_OWNER_DECISION_REQUIRED.md).

---

### DEF-005: Pure CPU NumPy Block Quantization Scaling for Very Large Models

- **Severity:** **INFORMATIONAL**
- **Category:** Performance & Hardware Architecture
- **Affected File:** [`adaptive_ml/rao/quantizer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/quantizer.py)
- **Component:** Resource-Aware Optimization
- **Discovered In:** Performance & Profiling Audit (`VERIF-PRF-007`)

#### Description & Guidance
[`BlockQuantizer`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/quantizer.py) achieves a consistent throughput of $\approx 9.8\text{ MParams/second}$ using pure vectorized NumPy on standard CPU architectures. For target embedded, edge, and streaming models ($P < 1\text{M}$ parameters), quantization step latency is negligible ($<10\text{ ms}$).

However, for large neural networks exceeding $5\text{M}$ to $10\text{M}$ parameters, quantizing and dequantizing the optimizer state in pure Python introduces $\approx 500\text{ ms}$ to $1,000\text{ ms}$ overhead per optimizer step.

#### Guidance
This is an expected architectural characteristic of pure-CPU zero-dependency Python code. The documentation should explicitly guide users training large deep models on GPU to utilize PyTorch's native CUDA-accelerated 8-bit optimizers (e.g., `bitsandbytes`) via AdaptiveML's PyTorch adapter.

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Updated user documentation in [`docs/guides/rao.md`](file:///c:/projects/AdaptiveML/docs/guides/rao.md#L36) and architectural concepts in [`docs/concepts/resource-aware-optimization.md`](file:///c:/projects/AdaptiveML/docs/concepts/resource-aware-optimization.md#L38) with explicit hardware requirements, CPU vs GPU boundaries, throughput measurements ($9.7 - 9.9\text{ MParams/s}$), and large-model latency scaling.
- **Verification:** Documentation reviewed for clarity and factual accuracy. Full details in [`docs/verification/remediation/DEF-005_PERFORMANCE_DOCUMENTATION_UPDATE.md`](file:///c:/projects/AdaptiveML/docs/verification/remediation/DEF-005_PERFORMANCE_DOCUMENTATION_UPDATE.md).

---

### DEF-006: Replay Buffer Contract Mismatch and Unsafe Buffer Purging

- **Severity:** **MEDIUM**
- **Category:** Architecture & Pillar Contracts
- **Affected Files:** [`adaptive_ml/ala/replay.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py), [`adaptive_ml/ala/classifier.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py), [`adaptive_ml/ulc/controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py)
- **Component:** ALA / ULC Interoperability
- **Discovered In:** Enterprise Defect Audit & Stage 2 Execution

#### Description & Impact
In `adaptive_ml/ala/classifier.py`, the replay buffer was held privately as `self._replay_buffer` without a public property, causing `hasattr(self.classifier, "replay_buffer")` checks in ULC to fail or bypass replay purging. Furthermore, when `clear()` was called upon concept drift, all experience replay was unconditionally wiped, causing catastrophic forgetting of rare minority class patterns.

#### Recommended Remediation
1. Expose public `@property def replay_buffer(self) -> Optional[ClassBalancedReservoirReplay]` on `AdaptiveClassifier`.
2. Implement `purge(policy="selective"|"partial"|"full", min_reliability=0.0, keep_minority=True)` on `ClassBalancedReservoirReplay`.
3. Add `purge_replay(policy="selective", ...)` facade on `AdaptiveClassifier`.
4. Update ULC `AdaptiveLearningController.step` to invoke safe selective purge protecting minority classes.

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Implemented public property and `purge(policy=...)` with sample-weight tracking in `adaptive_ml/ala/replay.py` and `adaptive_ml/ala/classifier.py`. Updated `adaptive_ml/ulc/controller.py` with multi-tier capability detection.
- **Verification:** Verified via unit tests in [`tests/unit/test_stage2_remediation.py`](file:///c:/projects/AdaptiveML/tests/unit/test_stage2_remediation.py) and empirical benchmark in [`experiments/stage_2_production_remediation/`](file:///c:/projects/AdaptiveML/experiments/stage_2_production_remediation/). Minority class retention ratio = $1.0000$ ($100\%$). Full report in [`docs/verification/stage_2/`](file:///c:/projects/AdaptiveML/docs/verification/stage_2/).

---

### DEF-007: Optimizer Interface Mismatch for Momentum Reset and LR Scaling

- **Severity:** **MEDIUM**
- **Category:** Architecture & Optimization Interface
- **Affected Files:** [`adaptive_ml/rao/adamw.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py), [`adaptive_ml/ulc/controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py)
- **Component:** RAO / ULC Interoperability
- **Discovered In:** Enterprise Defect Audit & Stage 2 Execution

#### Description & Impact
In `adaptive_ml/ulc/controller.py`, the controller issued `self.optimizer.reset_momenta()` and `self.optimizer.scale_learning_rate(directive.learning_rate_scale)`. However, `LowMemoryAdamW` did not implement either method, rendering dynamic momentum flushes and learning rate annealing completely inoperative during drift recovery.

#### Recommended Remediation
Implement `reset_momenta(param_indices=None)` and `scale_learning_rate(factor)` on `LowMemoryAdamW` supporting both NumPy arrays and PyTorch tensors.

#### Remediation Status & Verification Evidence
- **Status:** **RESOLVED & VERIFIED**
- **Action Taken:** Implemented `reset_momenta` and `scale_learning_rate` on `LowMemoryAdamW` in `adaptive_ml/rao/adamw.py`. Zeroes out quantized first-order momenta (`q_m`, `scale_m`) and resets step count to 0. Added safe fallback in `AdaptiveLearningController`.
- **Verification:** Verified via unit tests in [`tests/unit/test_stage2_remediation.py`](file:///c:/projects/AdaptiveML/tests/unit/test_stage2_remediation.py) and empirical benchmark in [`experiments/stage_2_production_remediation/`](file:///c:/projects/AdaptiveML/experiments/stage_2_production_remediation/). First-order momentum norm reduced from 860.8194 to 0.0000 in $0.0056$ ms. Full report in [`docs/verification/stage_2/`](file:///c:/projects/AdaptiveML/docs/verification/stage_2/).
