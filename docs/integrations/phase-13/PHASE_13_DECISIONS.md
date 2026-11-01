# Phase 13 Decisions & Architecture Records

**Document ID:** `DOC-INT-P13-007`  
**Phase:** Phase 13 — Framework Integrations  
**Status:** READY FOR REVIEW  

---

## 1. Ratified Decisions

### DEC-P13-001: Lazy Dependency Import Boundaries
- **Context**: Users importing `adaptive_ml.ala` or `adaptive_ml.core` should not experience import failures if `torch` or `scikit-learn` are not installed.
- **Decision**: All framework integrations are isolated inside `adaptive_ml.integrations` and guarded with runtime availability flags (`_SKLEARN_AVAILABLE`, `_TORCH_AVAILABLE`).

### DEC-P13-002: Formal Deferral of Native TensorFlow Package
- **Context**: Evaluated cost/benefit of supporting TensorFlow/Keras adapters.
- **Decision**: TensorFlow integration is deferred to preserve local-first CPU agility. Core NumPy backends provide standard interoperability.

### DEC-P13-003: PyTorch Loss Module Standardization
- **Context**: Practitioners building deep neural networks with PyTorch require native `nn.Module` loss functions that work with PyTorch autograd.
- **Decision**: Implemented `TorchSymmetricCrossEntropyLoss` directly under `adaptive_ml.integrations.torch_module`.
