# Installation Guide

AdaptiveML (`aml-core`) is engineered to be lightweight, modular, and local-first.

---

## System Requirements

- **Python**: `>= 3.10` (tested on Python 3.10, 3.11, 3.12, 3.13, 3.14).
- **Operating Systems**: Linux (Ubuntu, Debian, Fedora, RHEL), macOS (Apple Silicon & Intel), Windows 10/11 (x64).
- **Mandatory Runtime Dependencies**: `numpy >= 1.24.0` only.
- **Hardware**: Standard x86_64 or ARM64 CPU. No GPU accelerator or C++ compiler required.

---

## Installation Methods

### 1. Pre-Release / Wheel Installation
Until public release on PyPI (scheduled for Phase 18), install from the built distribution artifacts in the repository:

```bash
# Install from pre-built wheel
pip install dist/aml_core-0.1.0.dev0-py3-none-any.whl

# Or install from source distribution
pip install dist/aml_core-0.1.0.dev0.tar.gz
```

### 2. Local Editable Installation (Development)
For local development and testing:

```bash
# Clone the repository
git clone https://github.com/adaptiveml/adaptiveml.git
cd adaptiveml

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development extras
pip install -e ".[dev]"
```

---

## Optional Framework Extras

AdaptiveML isolates third-party framework dependencies into optional extras:

| Extra | Command | Key Capabilities |
| :--- | :--- | :--- |
| **PyTorch** | `pip install ".[torch]"` | `create_torch_low_memory_adamw`, `TorchSymmetricCrossEntropyLoss` |
| **Scikit-learn** | `pip install ".[sklearn]"` | `SklearnAdaptiveClassifier`, `Pipeline`, `clone()` compliance |
| **SafeTensors** | `pip install ".[safetensors]"` | Zero-pickle binary tensor checkpointing |
| **DataFrame** | `pip install ".[dataframe]"` | Pandas and Polars streaming data loaders |
| **All Extras** | `pip install ".[all]"` | Complete ecosystem dependencies |

---

## Verifying the Installation

Verify that the package imports correctly and reports its version:

```python
import adaptive_ml
print("AdaptiveML Version:", adaptive_ml.__version__)
```
