# AdaptiveML Stage 10 — Dependency & Supply Chain Security Report

**Distribution Package:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Version:** `0.1.0.dev0`<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Status:** Complete & Reconciled<br>

---

## 1. Executive Summary

A secure software supply chain requires that libraries minimize attack surfaces, avoid unpinned or unnecessary third-party dependencies, eliminate copyleft license liabilities, and guarantee that missing optional packages fail cleanly without executing unauthorized network calls or dynamic package downloads.

This audit evaluates the complete dependency graph of `aml-core` across mandatory, optional, build, and development tiers:
- **Mandatory Dependencies:** Strictly bounded to `numpy>=1.24.0`.
- **License Posture:** 100% permissive open source (Apache-2.0, BSD-3-Clause, MIT). Zero viral GPL/copyleft obligations.
- **Dependency Integrity:** `pip check` confirmed zero broken requirements.
- **Provenance & Portability:** Zero unpinned C/C++ compiled binaries distributed by `aml-core`. Completely reproducible pure Python package.

---

## 2. Dependency Graph Specification & License Matrix

```
aml-core v0.1.0.dev0 (Apache-2.0)
  ├── Mandatory:
  │   └── numpy>=1.24.0 (BSD-3-Clause)
  │
  └── Optional Extras (Opt-In):
      ├── [torch]       -> torch>=2.0.0 (BSD-3-Clause)
      ├── [sklearn]     -> scikit-learn>=1.2.0 (BSD-3-Clause), scipy>=1.10.0 (BSD-3-Clause)
      ├── [safetensors] -> safetensors>=0.4.0 (Apache-2.0)
      ├── [dataframe]   -> pandas>=1.5.0 (BSD-3-Clause), polars>=0.18.0 (MIT)
      ├── [benchmarks]  -> psutil>=5.9.0 (BSD-3-Clause)
      └── [dev]         -> pytest>=7.4.0 (MIT), pytest-cov>=4.1.0, hypothesis>=6.80.0, mypy>=1.5.0, ruff>=0.1.0
```

### Complete Software Bill of Materials (SBOM)

| Package | Minimum Constraint | Verified Runtime Version | License | Security & Supply Chain Role |
|:---|:---|:---|:---|:---|
| **`aml-core`** | N/A (Root) | `0.1.0.dev0` | **Apache-2.0** | Core AdaptiveML library. |
| **`numpy`** | `>=1.24.0` | `2.4.3` | **BSD-3-Clause** | Core vectorization, array algebra, probability math. |
| **`torch`** | `>=2.0.0` | `2.12.1+cpu` | **BSD-3-Clause** | Optional neural network training and autograd loss modules. |
| **`scikit-learn`** | `>=1.2.0` | `1.8.0` | **BSD-3-Clause** | Optional estimator, pipeline, and transformer interfaces. |
| **`scipy`** | `>=1.10.0` | `1.17.1` | **BSD-3-Clause** | Optional numerical routines supporting scikit-learn. |
| **`pandas`** | `>=1.5.0` | `3.0.1` | **BSD-3-Clause** | Optional tabular DataFrame array extraction. |
| **`polars`** | `>=0.18.0` | `1.42.0` | **MIT** | Optional high-speed Arrow DataFrame array extraction. |
| **`safetensors`** | `>=0.4.0` | `0.8.0` | **Apache-2.0** | Optional cryptographically safe tensor serialization. |
| **`psutil`** | `>=5.9.0` | `7.2.2` | **BSD-3-Clause** | Optional process physical RSS memory telemetry. |
| **`pytest`** | `>=7.4.0` | `8.2.2` | **MIT** | Development test automation runner. |

---

## 3. Supply Chain Security Invariants

1. **Zero Hidden Runtime Installation:**
   The library never executes `pip install`, `subprocess.Popen("curl ...")`, or dynamic module bootstrapping at runtime. If an optional package is absent, it raises a typed `ImportError` detailing the exact pip command for the user to execute manually.

2. **Zero Network Activity:**
   The library does not establish outbound HTTP, HTTPS, gRPC, or socket connections. All execution is strictly local and CPU-first.

3. **No Unpinned Native Extensions:**
   `aml-core` does not distribute custom compiled C/C++ binaries, shared libraries (`.so`, `.dll`), or unverified wheels that could bypass OS security controls or trigger ABI collisions.

4. **Transitive Dependency Isolation:**
   Importing `adaptive_ml` does not import `torch`, `pandas`, or `sklearn` unless the corresponding integration submodule in `adaptive_ml.integrations` is explicitly imported by user code.

---

## 4. Verification

- **Requirement Verification:** `pip check` executed with 0 errors.
- **License Review:** 100% compliance with Apache-2.0 commercial licensing.
- **Isolation Verification:** Verified via automated import tests in `tests/unit/test_api_stability.py` and `examples/integrations/08_core_only_workflow.py`.
