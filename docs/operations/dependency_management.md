# AdaptiveML Production Operations — Dependency Management Guide

## 1. Minimal-Core Philosophy

AdaptiveML adheres to a strict minimal-core architecture:
- **Core Runtime Dependency:** Only `numpy>=1.24.0` is required.
- **Optional Extras:** Deep learning, traditional machine learning, DataFrame adapters, and serialization formats are strictly isolated into optional extras.
- **CPU-First Architecture:** The entire core runs seamlessly on standard x86_64 and ARM64 CPUs without CUDA or GPU dependencies.

---

## 2. Dependency Stratification and Installation

| Target Environment | Installation Command | Key Packages Brought In |
| :--- | :--- | :--- |
| **Core Only (Minimal)** | `pip install robust-adapt` | `numpy` |
| **PyTorch Deep Learning** | `pip install 'robust-adapt[torch]'` | `torch>=2.0.0` |
| **scikit-learn Ecosystem**| `pip install 'robust-adapt[sklearn]'` | `scikit-learn>=1.2.0`, `scipy>=1.10.0` |
| **Enterprise Checkpointing**| `pip install 'robust-adapt[safetensors]'` | `safetensors>=0.4.0` |
| **DataFrame Interop** | `pip install 'robust-adapt[dataframe]'` | `pandas>=1.5.0`, `polars>=0.18.0` |
| **Complete Enterprise** | `pip install 'robust-adapt[all]'` | All integrations & telemetry extras |
| **Developer / Testing** | `pip install 'robust-adapt[dev]'` | `pytest`, `pytest-cov`, `mypy`, `ruff` |

---

## 3. License Compliance Audit

All dependencies used across core and optional extras are audited for open-source license compatibility:

| Package | License | Commercial Use Allowed | Viral Copyleft Risk |
| :--- | :--- | :--- | :--- |
| **`numpy`** | BSD-3-Clause | YES | NONE |
| **`torch`** | Modified BSD-3-Clause | YES | NONE |
| **`scikit-learn`** | BSD-3-Clause | YES | NONE |
| **`scipy`** | BSD-3-Clause | YES | NONE |
| **`safetensors`** | Apache-2.0 | YES | NONE |
| **`pandas`** | BSD-3-Clause | YES | NONE |
| **`polars`** | MIT | YES | NONE |
| **`psutil`** | BSD-3-Clause | YES | NONE |

> [!NOTE]
> AdaptiveML contains **zero GPL, AGPL, or viral copyleft dependencies**, ensuring complete freedom for proprietary enterprise integration.

---

## 4. Supply Chain Security Invariants

1. **Automated Conflict Verification:** Run `pip check` periodically in production build pipelines to detect broken requirement trees.
2. **Deterministic Build Pins:** In mission-critical environments, generate frozen lockfiles using `pip-tools` or `uv` to ensure byte-for-byte reproducible runtime environments.
3. **Trademark Defense Notice (DEF-004):** To avoid namespace conflicts with third-party trademarks (*Adaptive ML, Inc.*), the package is distributed strictly as `aml-core`.
