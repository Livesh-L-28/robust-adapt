# Migration Guide: AdaptiveML to ROBUST-ADAPT

> **Document ID:** `DOC-MIG-001`<br>
> **Status:** Ratified / Active<br>
> **Effective Version:** `0.1.0.dev0`<br>
> **Target Audience:** All developers, contributors, and platform teams migrating from AdaptiveML to ROBUST-ADAPT.

---

## 1. Executive Summary

This guide details the technical migration of the repository and codebase formerly known under the development codename **AdaptiveML** (`aml-core`, `adaptive_ml`) to its official, permanent open-source identity: **ROBUST-ADAPT** (`robust-adapt`, `robust_adapt`).

The migration preserves:
- 100% mathematical and algorithmic equivalence (ALA, RLA, RAO, ULC, Adaptive Minority Intelligence).
- Complete historical Git commit history and development artifacts (Phases 0 through 16).
- Full backwards-compatibility via an in-tree `adaptive_ml` compatibility layer.

---

## 2. Identity Mapping Reference

| Attribute | Legacy / Historical Identity | Official Permanent Identity |
| :--- | :--- | :--- |
| **Brand / Project Name** | AdaptiveML | **ROBUST-ADAPT** |
| **Full Meaning** | — | **Robust and Adaptive Learning with Resource-Efficient Optimization** |
| **Tagline** | *Adaptive, Robust, and Resource-Efficient Learning* | **Adaptive. Robust. Resource-Efficient.** |
| **PyPI Distribution** | `aml-core` | **`robust-adapt`** |
| **Python Import Namespace** | `adaptive_ml` | **`robust_adapt`** |
| **Repository URL** | `https://github.com/adaptiveml/adaptiveml` | **`https://github.com/robust-adapt/robust-adapt`** |
| **Documentation Name** | AdaptiveML Documentation | **ROBUST-ADAPT Documentation** |
| **Base Exception** | `AdaptiveMLError` | **`RobustAdaptError`** (`AdaptiveMLError` retained as alias) |
| **License** | Apache-2.0 | **Apache-2.0** |

---

## 3. Package & Distribution Changes

### 3.1 Installation Commands

Replace `aml-core` with `robust-adapt`:

```bash
# Core package (minimal dependencies: numpy only)
# Legacy:
pip install aml-core

# New canonical:
pip install robust-adapt
```

### 3.2 Optional Framework Extras

All optional dependency extras have transitioned identically to `robust-adapt`:

| Extra Name | Description | Legacy Command | New Canonical Command |
| :--- | :--- | :--- | :--- |
| `[torch]` | PyTorch 8-bit optimizer & robust losses | `pip install "aml-core[torch]"` | `pip install "robust-adapt[torch]"` |
| `[sklearn]` | Scikit-learn estimator adapters & pipelines | `pip install "aml-core[sklearn]"` | `pip install "robust-adapt[sklearn]"` |
| `[safetensors]` | Secure binary tensor serialization | `pip install "aml-core[safetensors]"` | `pip install "robust-adapt[safetensors]"` |
| `[dataframe]` | Pandas and Polars DataFrame support | `pip install "aml-core[dataframe]"` | `pip install "robust-adapt[dataframe]"` |
| `[docs]` | MkDocs documentation tooling | `pip install "aml-core[docs]"` | `pip install "robust-adapt[docs]"` |
| `[all]` | Full development & test environment | `pip install "aml-core[all]"` | `pip install "robust-adapt[all]"` |

> [!NOTE]
> For existing automated environments, installing `pip install aml-core` continues to function during the transitional grace period as a meta-package directing dependencies to `robust-adapt`.

---

## 4. Python Import Namespace Changes

### 4.1 Top-Level Import

Change your root import statement from `adaptive_ml` to `robust_adapt`:

```python
# Legacy import
import adaptive_ml as aml

# New canonical import
import robust_adapt as ra
```

### 4.2 Submodule Hierarchy

Every submodule in `adaptive_ml.*` has a direct, 1-to-1 counterpart in `robust_adapt.*`:

| Component Pillar | Legacy Import Path | New Canonical Import Path |
| :--- | :--- | :--- |
| **ALA** (Adaptive Learning) | `from adaptive_ml.ala import ...` | `from robust_adapt.ala import ...` |
| **RLA** (Robust Learning) | `from adaptive_ml.rla import ...` | `from robust_adapt.rla import ...` |
| **RAO** (Resource-Aware) | `from adaptive_ml.rao import ...` | `from robust_adapt.rao import ...` |
| **ULC** (Unified Controller) | `from adaptive_ml.ulc import ...` | `from robust_adapt.ulc import ...` |
| **Minority Intelligence** | `from adaptive_ml.minority import ...` | `from robust_adapt.minority import ...` |
| **Core Contracts** | `from adaptive_ml.core import ...` | `from robust_adapt.core import ...` |
| **State & Checkpoints** | `from adaptive_ml.state import ...` | `from robust_adapt.state import ...` |
| **Framework Integrations** | `from adaptive_ml.integrations import ...` | `from robust_adapt.integrations import ...` |

---

## 5. API Compatibility & Exception Hierarchy

### 5.1 100% Symbol Parity

All 65+ exported symbols from the public API exist in `robust_adapt` with identical function signatures, method parameters, return types, and docstrings.

### 5.2 Exception Hierarchy Parity

The root exception `AdaptiveMLError` has been replaced by `RobustAdaptError`, but `AdaptiveMLError` remains defined as an exact alias:

```python
from robust_adapt.core.exceptions import RobustAdaptError, AdaptiveMLError

assert issubclass(AdaptiveMLError, Exception)
assert AdaptiveMLError is RobustAdaptError
```

All specialized exception types inherit from both:
- `ConfigurationError(RobustAdaptError)`
- `ValidationError(RobustAdaptError)`
- `StateError(RobustAdaptError)`
- `ResourceBudgetExceededError(RobustAdaptError)`
- `IntegrationDependencyError(RobustAdaptError)`

Existing user code with `except AdaptiveMLError:` will continue to catch all library exceptions without modification.

---

## 6. Compatibility Layer & Deprecation Timeline

### 6.1 Compatibility Shim

The repository maintains an active `adaptive_ml` package directory that acts as a transparent compatibility shim. When user code imports `adaptive_ml`:

1. It imports symbols directly from `robust_adapt`.
2. It emits a Python `FutureWarning`:
   ```text
   FutureWarning: The 'adaptive_ml' package has been rebranded to 'robust_adapt'.
   Please update your imports from 'adaptive_ml' to 'robust_adapt'.
   The 'adaptive_ml' compatibility namespace will be deprecated in future releases.
   ```
3. Execution proceeds without error.

### 6.2 Deprecation Schedule

- **v0.1.x (Current Pre-release)**: `adaptive_ml` compatibility shim is active and emits `FutureWarning`.
- **v1.0.0 (General Availability)**: `adaptive_ml` compatibility shim remains included for at least one minor cycle.
- **v2.0.0 (Future Major Release)**: Legacy `adaptive_ml` namespace will be fully retired.

---

## 7. Migration Examples

### 7.1 Prequential Classifier & Drift Detector

#### Before (AdaptiveML):
```python
import numpy as np
from adaptive_ml.ala import AdaptiveClassifier, ReliabilityWeightedADWIN

clf = AdaptiveClassifier(n_features=4, n_classes=2)
detector = ReliabilityWeightedADWIN(delta=0.01)

X = np.random.randn(10, 4)
y = np.random.randint(0, 2, size=10)

probs = clf.predict_proba(X)
clf.partial_fit(X, y)
```

#### After (ROBUST-ADAPT):
```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier, ReliabilityWeightedADWIN

clf = AdaptiveClassifier(n_features=4, n_classes=2)
detector = ReliabilityWeightedADWIN(delta=0.01)

X = np.random.randn(10, 4)
y = np.random.randint(0, 2, size=10)

probs = clf.predict_proba(X)
clf.partial_fit(X, y)
```

---

### 7.2 Unified Learning Controller (ULC-v5)

#### Before (AdaptiveML):
```python
from adaptive_ml.ulc import UnifiedLearningControllerV5, ULCv5Config

config = ULCv5Config(grace_period=20, delta=0.002)
controller = UnifiedLearningControllerV5(n_features=8, n_classes=2, config=config)
directive, telemetry = controller.step(X_batch, y_batch)
```

#### After (ROBUST-ADAPT):
```python
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config

config = ULCv5Config(grace_period=20, delta=0.002)
controller = UnifiedLearningControllerV5(n_features=8, n_classes=2, config=config)
directive, telemetry = controller.step(X_batch, y_batch)
```

---

### 7.3 PyTorch Low-Memory Optimizer

#### Before (AdaptiveML):
```python
import torch
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw

model = torch.nn.Linear(10, 2)
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3)
```

#### After (ROBUST-ADAPT):
```python
import torch
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw

model = torch.nn.Linear(10, 2)
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3)
```

---

## 8. Historical Research & Governance Audit Notice

To maintain absolute scientific, academic, and legal integrity, historical audit artifacts and research documentation produced during Phases 0 through 16:
- Retain their original text, dates, citations, and working codename references (e.g. `AdaptiveML`, `aml-core`).
- Are indexed under `docs/foundation/`, `docs/research/`, `docs/design/`, `docs/implementation/`, `docs/verification/`, and `docs/release/`.
- Must **NOT** be rewritten retroactively.

All forward-facing operational guides, tutorials, public API references, build configurations, and test suites now reflect **ROBUST-ADAPT**.
