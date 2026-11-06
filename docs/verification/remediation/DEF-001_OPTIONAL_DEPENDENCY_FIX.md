# AdaptiveML — DEF-001 Remediation Report
## Optional Safetensors Dependency Isolation and Safe Serialization Fallback

**Defect Identifier:** `DEF-001`<br>
**Severity:** `MEDIUM`<br>
**Category:** Packaging & Modular Dependencies<br>
**Affected Files:**
- [`adaptive_ml/state/serializer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py)
- [`adaptive_ml/state/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/__init__.py)

**Status:** `RESOLVED & VERIFIED`

---

## 1. Problem Description & Root Cause Analysis

In the Phase 14 packaging specification ([`pyproject.toml`](file:///c:/projects/AdaptiveML/pyproject.toml#L44-L46)), `safetensors` was designated as an optional dependency:
```toml
[project.optional-dependencies]
safetensors = [
    "safetensors>=0.4.0",
]
```
However, in [`adaptive_ml/state/serializer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py#L15), the import of `safetensors.numpy` was top-level and unguarded:
```python
import safetensors.numpy as sn
```

When an end-user installed `aml-core` in an environment without the `[safetensors]` extra (`pip install aml-core`), executing `import adaptive_ml.state` immediately crashed with:
```text
ModuleNotFoundError: No module named 'safetensors'
```

This violated the core architectural requirement that AdaptiveML must function cleanly with **NumPy as its only mandatory runtime dependency**.

---

## 2. Technical Remediation Implementation

### 2.1 Conditional Import & Availability Check
In [`adaptive_ml/state/serializer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py), the top-level import was wrapped with a conditional guard:

```python
from adaptive_ml.core.exceptions import SerializationError

try:
    import safetensors.numpy as sn
    _SAFETENSORS_AVAILABLE = True
except ImportError:
    sn = None
    _SAFETENSORS_AVAILABLE = False


def is_safetensors_available() -> bool:
    """Check whether the optional Safetensors dependency is installed."""
    return _SAFETENSORS_AVAILABLE
```

### 2.2 Actionable Error Handling in Public APIs
When a user explicitly invokes serialization (`save_state`) or deserialization (`load_state`) in an environment where `safetensors` is missing, the functions raise a descriptive [`SerializationError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py) with installation instructions:

```python
def save_state(filepath: Union[str, Path], tensors: Dict[str, np.ndarray], metadata: Optional[Dict[str, Any]] = None) -> None:
    if not _SAFETENSORS_AVAILABLE or sn is None:
        raise SerializationError(
            "State serialization requires the optional 'safetensors' dependency. "
            "Install it via: pip install 'aml-core[safetensors]'"
        )
    ...
```

```python
def load_state(filepath: Union[str, Path]) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    if not _SAFETENSORS_AVAILABLE or sn is None:
        raise SerializationError(
            "State deserialization requires the optional 'safetensors' dependency. "
            "Install it via: pip install 'aml-core[safetensors]'"
        )
    ...
```

### 2.3 Exception Encapsulation
In addition, runtime serialization exceptions (such as file I/O errors or corrupted file headers) are caught and re-raised as `SerializationError` to maintain consistent project-level exception semantics:
```python
    try:
        tensors = sn.load_file(str(tensor_path))
    except Exception as exc:
        raise SerializationError(f"Failed to load safetensors file at {tensor_path}: {exc}") from exc
```

### 2.4 State Module Export
[`adaptive_ml/state/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/state/__init__.py) was updated to export `is_safetensors_available`:
```python
from adaptive_ml.state.checkpoint import CheckpointManager
from adaptive_ml.state.serializer import is_safetensors_available, load_state, save_state

__all__ = ["save_state", "load_state", "CheckpointManager", "is_safetensors_available"]
```

---

## 3. Verification Test Evidence

Three distinct test regimes were executed to confirm the fix:

### Test A: Clean Environment with Only Mandatory Dependencies (NumPy Only)
Executed in a fresh isolated virtual environment with only `aml-core` and `numpy` installed:
```powershell
py -3.14 -m venv .clean_core_venv
.\.clean_core_venv\Scripts\pip.exe install dist\aml_core-0.1.0.dev0-py3-none-any.whl
```
- `import adaptive_ml` $\to$ **SUCCESS** (Version: `0.1.0.dev0`)
- `import adaptive_ml.state` $\to$ **SUCCESS**
- `adaptive_ml.state.is_safetensors_available()` $\to$ **`False`**
- Core algorithmic modules (`ala`, `rla`, `rao`, `ulc`) executed streaming classification and optimization without errors.

### Test B: Environment with Safetensors Installed
Executed in a fresh virtual environment with `aml-core[safetensors]`:
```powershell
py -3.14 -m venv .safetensors_venv
.\.safetensors_venv\Scripts\pip.exe install "dist\aml_core-0.1.0.dev0-py3-none-any.whl[safetensors]"
```
- `adaptive_ml.state.is_safetensors_available()` $\to$ **`True`**
- Saved state checkpoint with weights array and metadata.
- Loaded state checkpoint and verified exact array equality via `np.allclose`.
- Injected corrupt metadata JSON $\to$ raised `SerializationError: Failed to parse metadata JSON`.
- Injected corrupt safetensors binary $\to$ raised `SerializationError: Failed to load safetensors file: Error while deserializing header`.

### Test C: Missing Dependency Error Trapping
Verified via automated unit tests in [`tests/unit/test_defect_remediation.py::TestDEF001SafetensorsIsolation`](file:///c:/projects/AdaptiveML/tests/unit/test_defect_remediation.py):
- Calling `save_state` when `_SAFETENSORS_AVAILABLE = False` raised `SerializationError` matching `"pip install 'aml-core[safetensors]'"`: **PASSED**
- Calling `load_state` when `_SAFETENSORS_AVAILABLE = False` raised `SerializationError` matching `"pip install 'aml-core[safetensors]'"`: **PASSED**

---

## 4. Conclusion & Acceptance Status

**Acceptance Criterion:** *PASS only if core-only installation and state imports work without Safetensors, and requesting Safetensors functionality without the extra raises a clear, actionable error.*

**Verdict:** **`PASS`**
