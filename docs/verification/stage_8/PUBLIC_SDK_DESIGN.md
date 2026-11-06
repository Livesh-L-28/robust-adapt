# Public SDK Architecture & Top-Level Import Design

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Report Date:** 2026-11-06<br>
**Auditor:** Principal Python SDK Architect & Systems Architecture Team<br>
**Artifact Path:** [PUBLIC_SDK_DESIGN.md](file:///c:/projects/AdaptiveML/docs/verification/stage_8/PUBLIC_SDK_DESIGN.md)<br>

---

## 1. Executive Summary & Architecture Goals

The AdaptiveML Public SDK provides a unified, ergonomic developer interface while strictly respecting the core architectural principles:
- **Local-First & CPU-First**: Default execution requires zero GPUs, cloud accounts, or remote services.
- **Minimal Core Dependencies**: Only `numpy>=1.24.0` is required at runtime.
- **Lazy Optional Framework Bindings**: PyTorch, Scikit-learn, and Safetensors are loaded as optional extensions without polluting pure CPU workflows.
- **Pillar Autonomy**: ALA, RLA, RAO, and Minority Intelligence remain fully usable in isolation.
- **Top-Level Discovery**: All primary components are exported directly from `adaptive_ml`.

---

## 2. Public SDK Namespace Organization

The root module [`adaptive_ml/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/__init__.py) now provides an intuitive developer interface:

```
adaptive_ml
├── __version__                 # "0.1.0.dev0"
├── AdaptiveClassifier          # ALA primary streaming classifier
├── VectorizedHoeffdingTree     # ALA fast incremental tree
├── ReliabilityWeightedADWIN    # ALA reliability-weighted drift detector
├── RobustLearningPipeline      # RLA master robust pipeline
├── SymmetricCrossEntropyLoss   # RLA robust loss function
├── LowMemoryAdamW              # RAO 8-bit quantized optimizer
├── DynamicResourceBudgetManager# RAO compute & memory ceiling manager
├── OnlineClassPriorTracker     # Minority class prior tracker
├── AdaptiveThresholdManager    # Minority cost-sensitive threshold manager
├── AdaptiveLearningController  # ULC baseline (v1-v3) controller
├── UnifiedLearningControllerV4 # ULC v4 default controller
├── UnifiedLearningControllerV4_1# ULC v4.1 promoted hybrid controller
├── ULCv41Config                # ULC v4.1 configuration dataclass
├── compute_spatial_discordance # ULC spatial discordance function
├── save_state / load_state     # Safe state serialization without pickle
└── AdaptiveMLError             # Root exception class
```

---

## 3. Submodule Import Compatibility

All existing submodule paths are preserved with zero deprecation warnings:
- `from adaptive_ml.ala import ...`
- `from adaptive_ml.rla import ...`
- `from adaptive_ml.rao import ...`
- `from adaptive_ml.ulc import ...`
- `from adaptive_ml.minority import ...`
- `from adaptive_ml.state import ...`
- `from adaptive_ml.core import ...`

---

## 4. Optional Framework Integration Design

| Framework | Optional Extra | Integration Point | Fallback Behavior When Absent |
|---|---|---|---|
| **PyTorch** | `pip install aml-core[torch]` | `SymmetricCrossEntropyLoss`, `LowMemoryAdamW` | Falls back to NumPy CPU implementation or custom parameter loop. |
| **Scikit-Learn** | `pip install aml-core[sklearn]` | `AdaptiveClassifier` cloning, `Pipeline` compatibility | Operates as pure standalone Python estimator with `.fit()` and `.predict()`. |
| **Safetensors** | `pip install aml-core[safetensors]` | `save_state()`, `load_state()` | Raises actionable `SerializationError` with installation instructions; zero pickle fallback. |
| **Pandas / Polars** | `pip install aml-core[dataframe]` | Ingesting streaming DataFrames | Features must be converted via `.to_numpy()` before passing to estimators. |

---

## 5. Verification Checklist

- [x] Top-level imports verified via `import adaptive_ml as aml`.
- [x] All 70 primary symbols exported cleanly in `__all__`.
- [x] Zero circular dependencies across package modules.
- [x] Backward compatibility preserved across all 147 existing unit/integration tests.
