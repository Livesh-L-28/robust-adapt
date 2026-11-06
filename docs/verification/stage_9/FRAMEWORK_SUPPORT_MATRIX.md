# AdaptiveML Stage 9 — Framework Support Matrix

**Document Identifier**: `STAGE-9-MATRIX-001`<br>
**Distribution Name**: `aml-core`<br>
**Namespace**: `adaptive_ml`<br>
**Version**: `0.1.0.dev0`<br>
**Status**: ACTIVE STANDARD<br>
**Date**: November 6, 2026<br>
**Governance**: DEF-004 Remains Open (Phase 17 & Phase 18 locked)

---

## 1. Executive Summary

This matrix specifies the certified support levels, version constraints, optional extras, and verified capabilities of AdaptiveML across external machine learning frameworks.

---

## 2. Framework Support Matrix

| Framework | Target Version Range | Verified Version in Workspace | Optional Extra Group | Support Level | Primary Integration Scope |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NumPy** | `>=1.24.0` | `2.4.3` | *Core Mandatory* | **Native Core** | Array memory buffers, vectorized trees, math kernels |
| **scikit-learn** | `>=1.2.0` | `1.8.0` | `[sklearn]` | **Tier 1 (Full)** | `BaseEstimator`, `ClassifierMixin`, `partial_fit`, Pipelines, `clone()` |
| **SciPy** | `>=1.10.0` | `1.17.1` | `[sklearn]` | **Tier 1 (Full)** | Sparse structures, scientific distributions, k-NN utilities |
| **PyTorch** | `>=2.0.0` | `2.12.1+cpu` | `[torch]` | **Tier 1 (Full)** | `nn.Module` robust losses, `LowMemoryAdamW`, training hooks |
| **pandas** | `>=1.5.0` | `3.0.1` | `[dataframe]` | **Tier 1 (Full)** | Streaming DataFrame batch ingestion, Series target validation |
| **Polars** | `>=0.18.0` | `1.42.0` | `[dataframe]` | **Tier 1 (Full)** | Zero-copy arrow-to-numpy ingestion for micro-batches |
| **SafeTensors** | `>=0.4.0` | `0.8.0` | `[safetensors]` | **Tier 1 (Full)** | Zero-copy tensor serialization, safe checkpoint loading |
| **psutil** | `>=5.9.0` | `7.2.2` | `[benchmarks]` | **Tier 1 (Full)** | Process RAM (RSS), CPU time telemetry for RAO budgets |
| **TensorFlow / Keras** | `>=2.12.0` | *Not Installed* | *N/A (Assessed)* | **Deferred (Assessment)** | Detailed technical feasibility assessment documented; no Windows 3.14 wheel |

---

## 3. Tier Definitions

### Tier 1: Full Support (Certified & Tested in CI)
- Fully covered by unit tests, integration tests, and executable examples.
- Documented in getting-started and API reference guides.
- Automatic graceful degradation when the library is not installed.
- Continuous backward compatibility maintained across minor versions.

### Tier 2: Deferred Support (Technical Assessment Completed)
- Evaluated against technical interfaces, maintenance costs, and ecosystem support.
- Deferred when the framework lacks upstream support on target Python versions (e.g. TensorFlow on Python 3.14 for Windows) or introduces disproportionate binary bloat without unique algorithmic advantage.
- Clear interface boundary documented for potential future integration.

---

## 4. Hardware and Device Support

| Hardware Target | Execution Mode | Verification Status | Notes |
| :--- | :---: | :---: | :--- |
| **CPU (x86_64 / AMD64)** | Pure Vector NumPy / PyTorch | **Verified Native** | Default target; SIMD block quantization optimized for CPU caches |
| **CPU (ARM64 / Apple Silicon)** | Pure Vector NumPy / PyTorch | **Supported** | Compatible via standard Python wheels; endianness independent |
| **NVIDIA CUDA** | Host-Tensor Memory Bridge | **Supported** | PyTorch adapters accept CUDA tensors and safely move to CPU when required |
| **Apple Metal (MPS)** | Host-Tensor Memory Bridge | **Supported** | PyTorch MPS tensors ingested with automatic CPU device transfer |

---

## 5. Compatibility Verification Rules

1. **No Silent Upgrades**: Optional extras must never force unexpected upgrades of host frameworks that break host environments.
2. **Minimal Version Headroom**: Version constraints use conservative lower bounds (`>=`) to support modern Python releases without artificially restricting future minor versions.
3. **Pure Python Fallback**: Every adapter must provide a standard pure-Python or NumPy fallback if the host framework is missing.
