# AdaptiveML — Configuration & Error Handling Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-007`  
> **Last Updated**: 2026-11-01  
> **Scope**: Configuration schemas, custom exception hierarchies, and runtime validation rules  
> **Target Audience**: Core Engineers, API Designers, QA Engineers

---

## 1. Configuration Architecture

AdaptiveML eliminates heavy runtime configuration frameworks (e.g. Pydantic, OmegaConf) to preserve zero runtime overhead and minimal dependency overhead.  
All configuration schemas are implemented using standard Python `@dataclass(frozen=True)` classes.

```python
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass(frozen=True)
class TreeConfig:
    n_features: int
    n_classes: int
    grace_period: int = 200
    delta: float = 1e-5
    tau_tie: float = 0.05
    n_bins: int = 32
    min_leaf_samples: int = 10

@dataclass(frozen=True)
class AdamWConfig:
    lr: float = 1e-3
    betas: Tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 1e-2
    block_size: int = 256
```

---

## 2. Exception Hierarchy

All custom exceptions in AdaptiveML inherit from a unified base exception `AdaptiveMLError`, enabling users to catch library-specific errors cleanly.

```
                                  AdaptiveMLError (Base)
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
      ▼                  ▼                   ▼                   ▼                  ▼
ConfigurationError ValidationError  DriftStateError  QuantizationError  ResourceBudgetError
                                                                                │
                                                                   NumericalInstabilityError
```

### 2.1 Exception Definitions (`adaptive_ml.core.exceptions`)

```python
class AdaptiveMLError(Exception):
    """Base exception for all errors raised by AdaptiveML."""
    pass

class ConfigurationError(AdaptiveMLError):
    """Raised when an invalid hyperparameter configuration is provided."""
    pass

class ValidationError(AdaptiveMLError):
    """Raised when input tensors violate shape, dtype, or value constraints."""
    pass

class DriftStateError(AdaptiveMLError):
    """Raised when an invalid drift detector state transition or window partition occurs."""
    pass

class QuantizationError(AdaptiveMLError):
    """Raised when tensor dimensions or block alignments violate quantization rules."""
    pass

class ResourceBudgetExceededError(AdaptiveMLError):
    """Raised when allocated memory or compute exceeds the user-configured ceiling."""
    pass

class NumericalInstabilityError(AdaptiveMLError):
    """Raised when NaN, Inf, or unrecoverable numerical degeneracy is encountered."""
    pass
```

---

## 3. Fail-Fast Parameter Validation Matrix

| Parameter | Type / Domain | Valid Range | Exception Raised on Violation |
| :--- | :--- | :--- | :--- |
| `n_features` | Integer | $\ge 1$ | `ConfigurationError("n_features must be >= 1")` |
| `n_classes` | Integer | $\ge 2$ | `ConfigurationError("n_classes must be >= 2")` |
| `grace_period` | Integer | $\ge 1$ | `ConfigurationError("grace_period must be >= 1")` |
| `delta` | Float | $(0.0, 1.0)$ | `ConfigurationError("delta must be in (0, 1)")` |
| `tau_tie` | Float | $[0.0, 1.0)$ | `ConfigurationError("tau_tie must be in [0, 1)")` |
| `block_size` | Integer | Must be power of 2 ($32, 64, 128, 256, 512$) | `ConfigurationError("block_size must be power of 2")` |
| `lr` | Float | $> 0.0$ | `ConfigurationError("lr must be > 0.0")` |
| `eps` | Float | $> 0.0$ | `ConfigurationError("eps must be > 0.0")` |
| `reliability` | Float | $[\epsilon_r, 1.0]$ | `ValidationError("reliability must be in [eps_r, 1.0]")` |

---

## 4. Error Context & Diagnostic Reporting

When an exception is raised, AdaptiveML attaches rich diagnostic context:
```python
raise ValidationError(
    f"Input feature dimension mismatch: expected X.shape[1] == {self.n_features}, "
    f"but received X.shape == {X.shape}. "
    f"Ensure your streaming feature pipeline maintains consistent column count."
)
```
This guarantees immediate clarity for developer debugging without inspecting library internals.
