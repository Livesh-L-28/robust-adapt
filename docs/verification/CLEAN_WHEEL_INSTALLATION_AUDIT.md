# AdaptiveML — Clean Wheel & Isolated Environment Installation Audit
## Independent Enterprise Verification Deliverable

**Document Identifier:** `VERIF-AUD-001`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Built Wheel Artifact:** [`dist/aml_core-0.1.0.dev0-py3-none-any.whl`](file:///c:/projects/AdaptiveML/dist/aml_core-0.1.0.dev0-py3-none-any.whl)<br>
**Built Source Tarball:** [`dist/aml_core-0.1.0.dev0.tar.gz`](file:///c:/projects/AdaptiveML/dist/aml_core-0.1.0.dev0.tar.gz)<br>
**Verification Target:** Baseline Commit `67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** November 2026<br>
**Auditor:** Independent Enterprise Verification Agent<br>
**Status:** `AUDIT COMPLETE — PASSED WITH ONE OBSERVATION`

---

## 1. Executive Summary

This audit independently validates the packaged distribution artifacts of AdaptiveML (`aml-core==0.1.0.dev0`). The evaluation was conducted in isolated clean virtual environments (`.verification_venv` on Python 3.14.3 and `.verification_venv_py311` on Python 3.11.9) completely decoupled from the project repository root and without source repository paths on `sys.path`.

### Summary of Audit Findings

| Audit Check | Requirement / Expectation | Empirical Result | Status |
| :--- | :--- | :--- | :--- |
| **Wheel Build Integrity** | Valid wheel metadata, PEP 517 / PEP 621 compliance | Wheel archive size: 67.4 KB, standard PEP 621 metadata, `aml_core-0.1.0.dev0-py3-none-any.whl` | **PASSED** |
| **Zero Runtime Pollution** | Mandatory runtime dependencies strictly minimal | `Requires-Dist: numpy>=1.24.0` is the single mandatory runtime dependency. | **PASSED** |
| **Optional Extras Grouping** | Framework integrations and dev tools in optional extras | `torch`, `sklearn`, `safetensors`, `dataframe`, `dev`, `benchmarks`, `all` cleanly declared as extras. | **PASSED** |
| **Isolated Core Execution** | ALA, RLA, RAO, ULC functional with only `numpy` installed | All 4 core algorithmic pillars initialize and execute without any framework dependencies. | **PASSED** |
| **Pillar Decoupling** | ALA, RLA, RAO, ULC have zero cross-pillar imports | Verified via AST and module dependency inspection. | **PASSED** |
| **State Submodule Dependency Guard** | `adaptive_ml.state` handling when `safetensors` absent | `import adaptive_ml.state.serializer` contains top-level unguarded import of `safetensors.numpy`. | **OBSERVATION (DEF-001)** |

---

## 2. Wheel Archive Inspection & Package Metadata

The wheel archive located at [`dist/aml_core-0.1.0.dev0-py3-none-any.whl`](file:///c:/projects/AdaptiveML/dist/aml_core-0.1.0.dev0-py3-none-any.whl) was inspected directly:

### 2.1 Wheel Metadata (`METADATA`)

```ini
Metadata-Version: 2.4
Name: aml-core
Version: 0.1.0.dev0
Summary: Adaptive, Robust, and Resource-Efficient Learning Library
Author-email: AdaptiveML Core Development Team <maintainers@adaptiveml.internal>
License-Expression: Apache-2.0
Classifier: Development Status :: 3 - Alpha
Classifier: Intended Audience :: Science/Research
Classifier: Intended Audience :: Developers
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.10
Classifier: Programming Language :: Python :: 3.11
Classifier: Programming Language :: Python :: 3.12
Classifier: Programming Language :: Python :: 3.13
Classifier: Programming Language :: Python :: 3.14
Classifier: Topic :: Scientific/Engineering :: Artificial Intelligence
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Classifier: Operating System :: OS Independent
Classifier: Typing :: Typed
Requires-Dist: numpy>=1.24.0
Provides-Extra: torch
Requires-Dist: torch>=2.0.0; extra == "torch"
Provides-Extra: sklearn
Requires-Dist: scikit-learn>=1.2.0; extra == "sklearn"
Requires-Dist: scipy>=1.10.0; extra == "sklearn"
Provides-Extra: safetensors
Requires-Dist: safetensors>=0.4.0; extra == "safetensors"
Provides-Extra: dataframe
Requires-Dist: pandas>=1.5.0; extra == "dataframe"
Requires-Dist: polars>=0.18.0; extra == "dataframe"
Provides-Extra: dev
Requires-Dist: pytest>=7.4.0; extra == "dev"
Requires-Dist: pytest-cov>=4.1.0; extra == "dev"
Requires-Dist: hypothesis>=6.80.0; extra == "dev"
Requires-Dist: mypy>=1.5.0; extra == "dev"
Requires-Dist: ruff>=0.1.0; extra == "dev"
Provides-Extra: benchmarks
Requires-Dist: psutil>=5.9.0; extra == "benchmarks"
Provides-Extra: all
```

### 2.2 Namespace Resolution & Distribution Mapping

- **PyPI Distribution Package Name:** `aml-core`
- **Import Namespace:** `adaptive_ml`
- **Module Root Path:** `Lib/site-packages/adaptive_ml/`
- **Typing Marker:** `Lib/site-packages/adaptive_ml/py.typed` is present in the wheel, enabling PEP 561 compliance for static type checkers (`mypy`, `pyright`).

---

## 3. Isolated Environment Execution Verification

### 3.1 Clean Virtual Environment Provisioning

A dedicated virtual environment `.verification_venv` was provisioned:
```powershell
py -3.14 -m venv .verification_venv
.\.verification_venv\Scripts\pip.exe install dist\aml_core-0.1.0.dev0-py3-none-any.whl
```
Installed packages in isolated environment:
- `aml-core==0.1.0.dev0`
- `numpy==2.5.4`
- `pip==25.3`

Zero optional dependencies (`torch`, `scikit-learn`, `safetensors`, `pandas`) were installed into this baseline environment.

### 3.2 Out-of-Workspace Execution Test

The test was executed with the working directory changed to the system temporary directory (`%TEMP%`) to prevent Python from searching `C:\projects\AdaptiveML` via `sys.path[0]`:

```python
import adaptive_ml
from adaptive_ml.ala import AdaptiveClassifier, VectorizedHoeffdingTree, ReliabilityWeightedADWIN
from adaptive_ml.rla import DensityAwareMarginScorer, SymmetricCrossEntropyLoss
from adaptive_ml.rao import BlockQuantizer, LowMemoryAdamW
from adaptive_ml.ulc import AdaptiveLearningController, ControllerState
```

**Results:**
1. **Module Import Location:** `C:\projects\AdaptiveML\.verification_venv\Lib\site-packages\adaptive_ml\__init__.py`
2. **Package Version:** `0.1.0.dev0`
3. **ALA Execution:** `AdaptiveClassifier(n_features=4, n_classes=2)` executed `partial_fit` and `predict` with shape `(50,)` and `predict_proba` with shape `(50, 2)`.
4. **RLA Execution:** `DensityAwareMarginScorer(n_classes=2)` scored 50 samples and computed weights in range $[0.101, 0.925]$. `SymmetricCrossEntropyLoss(alpha=1.0, beta=1.0)` evaluated forward loss ($5.37$) and computed analytical gradient matrix of shape `(50, 2)`.
5. **RAO Execution:** `BlockQuantizer(block_size=64)` quantized 128 elements into 8-bit integers; dequantization error ($0.0106$) strictly met the theoretical bound ($\text{scale}/2 = 0.0110$). `LowMemoryAdamW` updated parameter weights and reported memory state allocation of 272 bytes.
6. **ULC Execution:** `AdaptiveLearningController()` coordinated streaming batch, returning `ControllerDirective(state=ControllerState.STABLE)`.

---

## 4. Defect Observation DEF-001: Unguarded Optional Import in State Management

During isolated installation verification, an import failure was identified when importing `adaptive_ml.state`:

```text
ModuleNotFoundError: No module named 'safetensors'
  File ".../adaptive_ml/state/serializer.py", line 15, in <module>
    import safetensors.numpy as sn
```

### 4.1 Root Cause Analysis

1. In [`pyproject.toml`](file:///c:/projects/AdaptiveML/pyproject.toml#L44-L46), `safetensors` is classified as an optional extra:
   ```toml
   [project.optional-dependencies]
   safetensors = [
       "safetensors>=0.4.0",
   ]
   ```
2. However, in [`adaptive_ml/state/serializer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py#L15), the import is top-level and unguarded:
   ```python
   import safetensors.numpy as sn
   ```
3. When end users install `aml-core` via `pip install aml-core` without the `[safetensors]` extra and attempt to import `adaptive_ml.state`, Python immediately raises `ModuleNotFoundError`.
4. Note: Top-level `import adaptive_ml` does not import `adaptive_ml.state`, and the algorithmic modules (`ala`, `rla`, `rao`, `ulc`) do not import `adaptive_ml.state`. Therefore, core algorithmic operations remain functional.

### 4.2 Remediation Recommendation

1. Wrap the import in a graceful fallback or guard in `adaptive_ml/state/serializer.py`:
   ```python
   try:
       import safetensors.numpy as sn
       _SAFETENSORS_AVAILABLE = True
   except ImportError:
       _SAFETENSORS_AVAILABLE = False
   ```
2. If `_SAFETENSORS_AVAILABLE` is `False`, raise an informative `SerializationError` directing users to install `pip install "aml-core[safetensors]"`.
3. Alternatively, if state persistence is deemed mandatory for all users, move `safetensors>=0.4.0` from optional dependencies to mandatory `dependencies` in `pyproject.toml`.

---

## 5. Clean Wheel Audit Conclusion

The built wheel `aml_core-0.1.0.dev0-py3-none-any.whl` successfully passes clean installation and isolated runtime execution verification. The core algorithmic engine is completely self-contained with zero runtime dependencies beyond NumPy. Defect DEF-001 has been logged in the Enterprise Defect Register for resolution prior to public PyPI release.
