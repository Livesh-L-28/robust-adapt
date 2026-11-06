# ROBUST-ADAPT Technical Package Migration Report

> **Document ID:** `DOC-MIG-TECH-001`<br>
> **Status:** RATIFIED<br>
> **Distribution:** `robust-adapt`<br>
> **Namespace:** `robust_adapt`<br>
> **Date:** November 2026<br>
> **Baseline Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`

---

## 1. Executive Summary

This report documents the end-to-end technical package migration from `AdaptiveML` (`adaptive_ml`, `aml-core`) to **`ROBUST-ADAPT`** (`robust_adapt`, `robust-adapt`).

The migration achieved:
1. Creation of a full, independent canonical package tree at `robust_adapt/` (70 Python source files across 8 submodules + PEP 561 marker).
2. Complete internal AST import refactoring replacing all intra-package references to `adaptive_ml` with `robust_adapt`.
3. Seamless backwards-compatibility via an in-tree `adaptive_ml/` compatibility shim emitting a `FutureWarning`.
4. Modernized PEP 517 / PEP 621 packaging via `pyproject.toml` bundling both namespaces into the universal wheel distribution.
5. Successful build and verification of `robust_adapt-0.1.0.dev0-py3-none-any.whl` (308 KB) and `robust_adapt-0.1.0.dev0.tar.gz`.

---

## 2. Directory Structure & Inventory

The repository now houses both the primary canonical package and the backwards-compatibility shim:

```
C:\projects\AdaptiveML\
├── robust_adapt/               # PRIMARY CANONICAL PACKAGE
│   ├── __init__.py             # Public API exports (65+ symbols), __version__
│   ├── py.typed                # PEP 561 type marker
│   ├── ala/                    # Adaptive Learning Algorithms (10 modules)
│   ├── rla/                    # Robust Learning Algorithms (8 modules)
│   ├── minority/               # Adaptive Minority Intelligence (6 modules)
│   ├── rao/                    # Resource-Aware Optimization (9 modules)
│   ├── ulc/                    # Unified Learning Controller (14 modules)
│   ├── core/                   # Core contracts, exceptions, telemetry (8 modules)
│   ├── state/                  # Resilient checkpointing & SafeTensors serde (3 modules)
│   ├── backends/               # NumPy & PyTorch execution backends (4 modules)
│   └── integrations/           # Scikit-learn, PyTorch, and Data adapters (6 modules)
├── adaptive_ml/                # BACKWARDS-COMPATIBILITY SHIM
│   ├── __init__.py             # Emits FutureWarning, re-exports from robust_adapt
│   ├── py.typed                # PEP 561 type marker
│   └── [submodules]            # Re-exporting modules routing to robust_adapt.*
├── pyproject.toml              # Build metadata: robust-adapt v0.1.0.dev0
├── dist/                       # Built distribution packages
│   ├── robust_adapt-0.1.0.dev0-py3-none-any.whl
│   └── robust_adapt-0.1.0.dev0.tar.gz
```

### Submodule File Inventory (`robust_adapt/`)

| Submodule | Module Count | Key Components |
| :--- | :---: | :--- |
| `robust_adapt.ala` | 10 | `AdaptiveClassifier`, `HoeffdingTree`, `ReliabilityWeightedADWIN`, `ConceptMemory`, `ClassBalancedReservoirReplay`, `StreamingEnsemble` |
| `robust_adapt.rla` | 8 | `MultiSignalReliabilityEngine`, `DensityAwareMarginScorer`, `SymmetricCrossEntropyLoss`, `GeneralizedCrossEntropyLoss`, `ClassBalancedWeights` |
| `robust_adapt.minority` | 6 | `MinorityIntelligence20Learner`, `OnlineClassPriorTracker`, `AdaptiveThresholdManager`, `BetaBinomialConjugatePrior` |
| `robust_adapt.rao` | 9 | `LowMemoryAdamW`, `VectorizedLowMemoryAdamW`, `BlockQuantizer`, `AdaptiveGradientAccumulator`, `DynamicResourceBudgetManager` |
| `robust_adapt.ulc` | 14 | `UnifiedLearningControllerV5`, `ArbitrationAutomaton`, `SpatialDiscordanceGater`, `ExpectedUtilityEvaluator`, `DirectiveV4` |
| `robust_adapt.core` | 8 | `RobustAdaptError`, `AdaptiveMLError`, `DatasetContract`, `ModelContract`, `TelemetryManager`, `ValidationHelper` |
| `robust_adapt.state` | 3 | `ResilientCheckpointManager`, `SafeTensorsSerializer`, `HMACSHA256IntegrityValidator` |
| `robust_adapt.backends` | 4 | `NumPyBackend`, `PyTorchBackend`, `DeviceManager`, `ExecutionBackend` |
| `robust_adapt.integrations` | 6 | `SklearnAdaptiveClassifier`, `TorchLowMemoryAdamW`, `TorchSymmetricCrossEntropyLoss`, `DataFrameAdapter` |

---

## 3. AST & Codebase Refactoring Details

### 3.1 Exception Hierarchy Refactoring (`robust_adapt/core/exceptions.py`)
The base exception class was refactored as follows:

```python
class RobustAdaptError(Exception):
    """Base exception for all ROBUST-ADAPT library errors."""
    pass

# Backwards-compatibility alias for legacy exception handlers
AdaptiveMLError = RobustAdaptError
```

All derived exception types inherit from `RobustAdaptError`:
- `ConfigurationError(RobustAdaptError)`
- `ValidationError(RobustAdaptError)`
- `StateError(RobustAdaptError)`
- `ResourceBudgetExceededError(RobustAdaptError)`
- `IntegrationDependencyError(RobustAdaptError)`

### 3.2 Top-Level Public Interface (`robust_adapt/__init__.py`)
- Defines `__version__ = "0.1.0.dev0"`.
- Exports 65+ primary public classes, functions, and exception types in `__all__`.
- Imports cleanly without external framework dependencies (NumPy only).

### 3.3 Backwards-Compatibility Shim (`adaptive_ml/__init__.py`)
To prevent breaking existing downstream consumer code during the transition, `adaptive_ml/__init__.py` implements:

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

And re-exports all submodules and public symbols directly from `robust_adapt`.

---

## 4. Build Configuration (`pyproject.toml`)

The build specification was updated to PEP 621 compliance:

```toml
[project]
name = "robust-adapt"
version = "0.1.0.dev0"
description = "Robust and Adaptive Learning with Resource-Efficient Optimization"
readme = "README.md"
requires-python = ">=3.10"
license = "Apache-2.0"
authors = [
    { name = "ROBUST-ADAPT Core Development Team", email = "maintainers@robust-adapt.internal" }
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "numpy>=1.24.0",
]

[project.optional-dependencies]
torch = ["torch>=2.0.0"]
sklearn = ["scikit-learn>=1.2.0"]
safetensors = ["safetensors>=0.4.0"]
dataframe = ["pandas>=2.0.0", "polars>=0.18.0"]
docs = ["mkdocs-material>=9.5.0"]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
]
all = [
    "robust-adapt[torch,sklearn,safetensors,dataframe,docs,dev]",
]

[tool.setuptools.packages.find]
include = ["robust_adapt*", "adaptive_ml*"]

[tool.setuptools.package-data]
robust_adapt = ["py.typed"]
adaptive_ml = ["py.typed"]
```

---

## 5. Build Artifact Verification

Execution of `py -3.14 -m build --no-isolation` produced:

| Distribution Artifact | Size | Integrity / Hash Summary | Status |
| :--- | :---: | :--- | :---: |
| `robust_adapt-0.1.0.dev0-py3-none-any.whl` | 308 KB | Contains `robust_adapt/` (70 files) + `adaptive_ml/` shim + `METADATA` | VERIFIED |
| `robust_adapt-0.1.0.dev0.tar.gz` | 275 KB | Source distribution with `pyproject.toml`, `LICENSE`, `NOTICE` | VERIFIED |

Wheel package inspection confirmed:
- `METADATA` specifies `Name: robust-adapt`.
- `METADATA` specifies `Version: 0.1.0.dev0`.
- Both `robust_adapt` and `adaptive_ml` top-level packages are included with their `py.typed` markers.
- Zero stray build debris, temporary test files, or credentials included.
