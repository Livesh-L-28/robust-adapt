# Developer Experience Review

**Document ID:** `DOC-ENG-P15-005`  
**Phase:** Phase 15 — Documentation & Developer Experience  
**Status:** READY FOR REVIEW  

---

## 1. Friction Point Analysis

To ensure smooth adoption, common friction points were evaluated and resolved:

### 1.1 Friction Point 1: Installation Dependencies
- **Issue**: Heavy dependencies like PyTorch or CUDA can stall installation on simple environments.
- **Resolution**: Core package depends strictly on NumPy. Installing `aml-core` takes $< 5$ seconds in clean virtual environments.

### 1.2 Friction Point 2: API Familiarity
- **Issue**: Novel continual learning frameworks often invent non-standard method names (e.g. `learn_one()`, `step_stream()`).
- **Resolution**: Follows scikit-learn standard nomenclature (`fit()`, `partial_fit()`, `predict()`, `predict_proba()`) and PyTorch standards (`torch.optim.Optimizer`, `forward()`, `backward()`).

### 1.3 Friction Point 3: Actionable Error Messages
- **Issue**: Silent dimension mismatches or obscure NaN exceptions in low-level linear algebra.
- **Resolution**: `adaptive_ml.core.validation` provides explicit messages (e.g. `"X feature dimension mismatch: expected 4 columns, but received 3"`, `"y must be a 1D array of integers"`).
