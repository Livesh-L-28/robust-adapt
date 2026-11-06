# Getting Started — Installation

This guide covers installing and configuring **AdaptiveML** (`aml-core`) in Python environments.

---

## 1. Prerequisites

- **Python**: `>= 3.10` (tested on 3.10, 3.11, 3.12, 3.13, 3.14).
- **Architecture**: AMD64 / ARM64 (Linux, Windows, macOS).
- **Core Dependencies**: Only `numpy >= 1.24.0` is required for core streaming operations.

---

## 2. Standard Installation

Install the core package using `pip`:

```bash
pip install robust-adapt
```

> [!NOTE]
> The distribution package is named `aml-core` on PyPI/wheelhouse, but the Python import namespace is `adaptive_ml`:
> ```python
> import robust_adapt as aml
> ```

---

## 3. Optional Framework Extras

AdaptiveML uses PEP 508 optional extras so that you only pull in the frameworks you need:

### PyTorch Support
For custom differentiable losses ([`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py)), 8-bit quantized PyTorch optimizer ([`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py)), and neural adapters:
```bash
pip install "robust-adapt[torch]"
```

### Scikit-Learn Interoperability
For pipeline composition, grid search, and standard metrics:
```bash
pip install "robust-adapt[sklearn]"
```

### SafeTensors Zero-Copy Checkpoints
For high-speed, zero-copy checkpoint serialization:
```bash
pip install "robust-adapt[safetensors]"
```

### DataFrame Streaming Ingestion
For streaming directly from Pandas or Polars DataFrames:
```bash
pip install "robust-adapt[dataframe]"
```

### All Production Extras
Installs all optional dependencies for full capabilities:
```bash
pip install "robust-adapt[all]"
```

### Development & Benchmarking Tools
For running tests, benchmarks, linters, and type-checking:
```bash
pip install "robust-adapt[dev,benchmarks]"
```

---

## 4. Local Editable Installation (Development)

To contribute to or inspect the source code directly:

```bash
git clone https://github.com/adaptive-ml/AdaptiveML.git
cd AdaptiveML
pip install -e ".[dev]"
```

Verify your installation:

```python
import robust_adapt as aml
print(aml.__version__)  # Output: 0.1.0.dev0
```

---

## 5. Offline / Air-Gapped Environments

AdaptiveML is fully local-first with zero telemetry, zero tracking, and zero mandatory cloud services. You can deploy pre-built wheels directly:

```bash
pip install dist/aml_core-0.1.0.dev0-py3-none-any.whl --no-index
```
