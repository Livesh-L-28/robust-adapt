# Core API Reference (`adaptive_ml.core`)

The `adaptive_ml.core` subpackage defines the foundational exception hierarchy, input validation contracts, memory telemetry probes, and structured diagnostics.

---

## 1. Exception Hierarchy

All custom exceptions inherit from the base class `AdaptiveMLError`:

```python
from robust_adapt.core.exceptions import (
    AdaptiveMLError,
    ValidationError,
    ConfigurationError,
    SerializationError,
    DriftStateError,
    NumericalInstabilityError,
    QuantizationError,
    ResourceBudgetExceededError,
)
```

### `AdaptiveMLError`
```python
class AdaptiveMLError(Exception):
    """Base exception for all errors raised by the AdaptiveML library."""
```

### `ValidationError(AdaptiveMLError)`
Raised when input data, feature dimensions, batch shapes, or label types violate API contracts:
- Non-2D feature arrays ($X \notin \mathbb{R}^{N \times d}$).
- Empty batches ($N = 0$).
- Out-of-bounds class labels ($y_i \ge K$ or $y_i < 0$).
- Non-finite numbers (`NaN` / `Inf`) in feature arrays.

### `ConfigurationError(AdaptiveMLError)`
Raised when hyperparameter values violate mathematical domain boundaries or required optional dependencies are missing:
- Learning rate $\le 0.0$.
- Quantization block size not a power of 2.
- Accessing `[torch]` or `[safetensors]` functionality when the extra is not installed.

### `SerializationError(AdaptiveMLError)`
Raised when state persistence or restoration fails:
- Checkpoint payload tampering or SHA-256 integrity mismatch.
- Missing or invalid HMAC-SHA256 signature when `auth_key` is provided.
- File size exceeding `max_file_size_bytes` (DoS ceiling).

### `DriftStateError(AdaptiveMLError)`
Raised when drift detector internal state transitions fail or invalid observations are passed.

### `NumericalInstabilityError(AdaptiveMLError)`
Raised when mathematical operations produce non-finite values or division by zero.

### `QuantizationError(AdaptiveMLError)`
Raised when block quantization inputs cannot be mapped to the requested integer bit-width.

### `ResourceBudgetExceededError(AdaptiveMLError)`
Raised when memory allocation or execution runtime breaches configured budget ceilings.

---

## 2. Telemetry & Diagnostics API

```python
from robust_adapt.core.telemetry import get_process_memory_bytes, MemoryBudgetTracker
from robust_adapt.core.diagnostics import DiagnosticRegistry, DiagnosticEvent
```

### `get_process_memory_bytes() -> int`
Returns the current resident set size (RSS) memory in bytes without mandatory external dependencies. Automatically falls back through:
1. `psutil.Process().memory_info().rss` (if installed)
2. Win32 `psapi.dll!GetProcessMemoryInfo` (on Windows)
3. `/proc/self/statm` (on Linux)
4. Returns 0 safely if introspection fails.

### `DiagnosticRegistry`
Thread-safe, bounded in-memory diagnostic event registry:
```python
registry = DiagnosticRegistry(max_events=1000)
event = registry.record(
    component="ULCv5",
    event_type="DRIFT_DETECTED",
    details={"mean_error": 0.42},
    level="INFO",
    step=150,
)
```
- `max_events`: Maximum historical events retained in memory (`deque(maxlen=max_events)`).
- `record(...)`: Records event and emits to standard Python `logging`.
- `events`: Returns read-only snapshot list of recorded events.
- `clear()`: Purges in-memory event queue.
