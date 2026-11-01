# Integration Compatibility Matrix

**Document ID:** `DOC-INT-P13-005`  
**Phase:** Phase 13 — Framework Integrations  
**Status:** READY FOR REVIEW  

---

## 1. Compatibility Matrix

| Framework | Minimum Version | Tested Version | Integration Modules | Compatibility Level |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `>= 3.10` | `3.14.3` | Full Core Package | **Tier 1 (Primary)** |
| **NumPy** | `>= 1.24.0` | `2.4.3` | `adaptive_ml.backends.numpy_backend` | **Tier 1 (Mandatory Core)** |
| **scikit-learn** | `>= 1.2.0` | `1.8.0` | `adaptive_ml.integrations.sklearn` | **Tier 1 (Verified)** |
| **PyTorch** | `>= 2.0.0` | `2.12.1` | `adaptive_ml.integrations.torch_optim`, `torch_module` | **Tier 1 (Verified)** |
| **Safetensors** | `>= 0.4.0` | `0.8.0` | `adaptive_ml.state.serializer` | **Tier 1 (Verified)** |
| **TensorFlow** | N/A | N/A | None (NumPy bridge only) | **Deferred** |

---

## 2. Optional Dependency Groups in `pyproject.toml`

```toml
[project.optional-dependencies]
torch = ["torch>=2.0.0"]
sklearn = ["scikit-learn>=1.2.0"]
all = ["torch>=2.0.0", "scikit-learn>=1.2.0", "safetensors>=0.4.0"]
```
Zero mandatory framework dependencies are imposed on core users.
