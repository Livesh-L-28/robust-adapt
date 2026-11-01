# AdaptiveML — Packaging & Release Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-011`  
> **Last Updated**: 2026-11-01  
> **Scope**: PEP 517/621 packaging specifications, build backend, dependency extras, and wheel distribution matrix  
> **Target Audience**: Packaging Engineers, DevOps/CI Specialists, Release Managers

---

## 1. Packaging Philosophy & Build System Selection

AdaptiveML adopts modern standard Python packaging standards:
- **Standards Compliance**: Full adherence to PEP 517 (Build Backends), PEP 518 (Build Requirements), PEP 621 (Project Metadata), and PEP 561 (Inline Typing).
- **Build Backend**: Selected **`hatchling`** (`hatch`) for lightweight, reproducible, zero-C-extension packaging with robust license and file exclusion management.
- **Distribution Format**: Distributed as a universal pure-Python wheel (`py3-none-any.whl`) and Source Distribution (`.tar.gz`).
- **Immediate Portability**: Because there are no compiled C/C++ extensions, a single universal wheel installs instantly across all operating systems and architectures without pre-compiling platform wheels.

---

## 2. Complete `pyproject.toml` Specification

```toml
[build-system]
requires = ["hatchling>=1.18.0"]
build-backend = "hatchling.build"

[project]
name = "aml-core"  # Provisional public distribution name; internal: AdaptiveML
version = "0.1.0.dev0"
description = "Adaptive, Robust, Resource-Efficient Learning Library"
readme = "README.md"
requires-python = ">=3.9"
license = { text = "Apache-2.0" }
authors = [
    { name = "AdaptiveML Core Development Team", email = "maintainers@adaptiveml.internal" }
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Operating System :: OS Independent",
    "Typing :: Typed",
]

# Core mandatory runtime dependencies: STRICTLY MINIMAL
dependencies = [
    "numpy>=1.24.0",
]

[project.optional-dependencies]
# PyTorch Deep Learning Bridge
torch = [
    "torch>=2.0.0",
]

# Scikit-Learn Estimator and Pipeline Bridge
sklearn = [
    "scikit-learn>=1.2.0",
    "scipy>=1.10.0",
]

# Tabular Dataframe Converters
dataframe = [
    "pandas>=1.5.0",
    "polars>=0.18.0",
]

# Developer, Testing & Verification Suite
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "hypothesis>=6.80.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "pip-audit>=2.6.0",
]

# Ecosystem Benchmarking Suite
benchmarks = [
    "river>=0.19.0",
    "torch>=2.0.0",
    "scikit-learn>=1.2.0",
    "psutil>=5.9.0",
]

# All extras combined
all = [
    "aml-core[torch,sklearn,dataframe,dev,benchmarks]",
]

[project.urls]
Homepage = "https://github.com/adaptiveml-project/adaptiveml"
Documentation = "https://adaptiveml.readthedocs.io"
Repository = "https://github.com/adaptiveml-project/adaptiveml"
"Bug Tracker" = "https://github.com/adaptiveml-project/adaptiveml/issues"

[tool.hatch.build.targets.wheel]
packages = ["adaptive_ml"]

[tool.hatch.build.targets.sdist]
include = [
    "/adaptive_ml",
    "/tests",
    "/README.md",
    "/LICENSE",
]
exclude = [
    "/.git",
    "/.github",
    "/docs",
]

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.mypy]
python_version = "3.9"
strict = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 3. Wheel Matrix & Target Environments

| Distribution Channel | Target OS | Python Versions | Target Wheel Artifact |
| :--- | :--- | :--- | :--- |
| **PyPI Primary** | Any (OS Independent) | 3.9, 3.10, 3.11, 3.12 | `aml_core-0.1.0.dev0-py3-none-any.whl` |
| **Source Archive** | Any | All compatible | `aml_core-0.1.0.dev0.tar.gz` |
| **Edge / Embedded** | Linux ARM64, Raspberry Pi | 3.9+ | Universal wheel installs with zero compiling |
| **Windows / macOS** | Win32 x86_64, macOS Apple Silicon | 3.9+ | Universal wheel installs with zero compiling |

---

## 4. Release Validation Pipeline

Before any release wheel is published:
1. **Source & Wheel Build**: `python -m build` generates `.whl` and `.tar.gz`.
2. **Metadata Linter**: `twine check dist/*` verifies package metadata and README rendering.
3. **Clean Environment Install**: Wheel is installed into a blank virtual environment (`pip install dist/*.whl`) and executes `tests/unit/` to verify zero missing dependencies.
4. **Typing Verification**: `mypy --package adaptive_ml` verifies PEP 561 typing completeness.
