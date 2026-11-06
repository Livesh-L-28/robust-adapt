# Installation Guide

ROBUST-ADAPT is distributed under the official package name **`robust-adapt`**.
*(For existing deployments, installation under legacy name `aml-core` remains functional via backward-compatibility dependencies).*

---

## Supported Environment Matrix

| Dimension | Supported Range | Notes |
| :--- | :--- | :--- |
| **Python Version** | `>=3.10`, including `3.11`, `3.12`, `3.13`, `3.14` | Verified on Python 3.14.3 AMD64 |
| **Operating Systems** | Microsoft Windows (x86_64, ARM64)<br/>Linux (Ubuntu, Debian, RHEL, Alpine)<br/>macOS (Intel & Apple Silicon M-series) | Pure-Python universal wheel (`py3-none-any.whl`) |
| **Hardware** | Standard CPU cores (x86_64 / ARM64) | Optional GPU acceleration via PyTorch |

---

## 1. Core Installation (Minimal Dependencies)

To install ROBUST-ADAPT with strictly minimal dependencies (only `numpy>=1.24.0`):

```bash
pip install robust-adapt
```

This installation provides all core streaming algorithms:
- `AdaptiveClassifier` & `ReliabilityWeightedADWIN` (ALA)
- `MultiSignalReliabilityEngine` & `EvidenceBasedLabelCorrector` (RLA)
- `MinorityIntelligence20Learner` & `DynamicFPBudgetThresholdManager`
- `LowMemoryAdamW` (NumPy mode) & `ResilientCheckpointManager` (RAO)
- `UnifiedLearningControllerV5` (ULC)

---

## 2. Optional Framework Extras

ROBUST-ADAPT uses dependency extras to avoid installing heavy external frameworks unless you need them:

```bash
# PyTorch Integration & VectorizedLowMemoryAdamW
pip install "robust-adapt[torch]"

# Scikit-Learn Estimator Protocols & Pipeline Utilities
pip install "robust-adapt[sklearn]"

# Secure Zero-Pickle SafeTensors Serialization
pip install "robust-adapt[safetensors]"

# Tabular DataFrames (Pandas & Polars support)
pip install "robust-adapt[dataframe]"

# Documentation Tools (MkDocs & Material theme)
pip install "robust-adapt[docs]"

# Full Developer Environment (all extras combined)
pip install "robust-adapt[all]"
```

---

## 3. Local Editable Installation (Development)

To contribute to or modify the ROBUST-ADAPT codebase:

```bash
# Clone the repository
git clone https://github.com/robust-adapt/robust-adapt.git
cd robust-adapt

# Create and activate a clean virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install in editable mode with development & test tools
pip install -e ".[dev]"
```
