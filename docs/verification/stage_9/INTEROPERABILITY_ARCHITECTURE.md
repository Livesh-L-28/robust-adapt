# AdaptiveML Stage 9 — Framework Interoperability Architecture

**Document Identifier**: `STAGE-9-ARCH-001`<br>
**Distribution Name**: `aml-core`<br>
**Namespace**: `adaptive_ml`<br>
**Version**: `0.1.0.dev0`<br>
**Status**: APPROVED ARCHITECTURE<br>
**Date**: November 6, 2026<br>
**Governance**: DEF-004 Remains Open (Phase 17 & Phase 18 locked)

---

## 1. Architectural Philosophy & Design Principles

AdaptiveML is an algorithmically specialized library designed for online streaming adaptation, label noise robustness, 8-bit optimizer state compression, and multi-objective controller arbitration.

It is **not** a monolithic general-purpose machine learning framework, and it must **never replace** existing industry-standard frameworks:
- **NumPy**: The universal array foundation.
- **scikit-learn**: The standard for static tabular pipelines, model selection, and classic estimators.
- **PyTorch**: The standard for deep learning, differentiable computation, and dynamic neural computation graphs.
- **TensorFlow / Keras**: Large-scale distributed neural pipelines.

### 1.1 Core Principles of Interoperability
1. **Zero Core Coupling**: The core library (`adaptive_ml.ala`, `adaptive_ml.rla`, `adaptive_ml.rao`, `adaptive_ml.ulc`, `adaptive_ml.minority`) depends exclusively on `numpy>=1.24.0`. No framework dependencies may be introduced into the core runtime.
2. **Adapter & Protocol Pattern**: Framework-specific integration layers reside strictly in `adaptive_ml.integrations` and interface with core algorithms via explicit composition rather than invasive multiple inheritance.
3. **Explicit Opt-in Execution**: AdaptiveML components never hijack framework control flow, global dispatchers, or background threads without explicit user code invocation.
4. **Copy-Conscious Data Conversions**: Data conversions between frameworks must be explicit, memory-layout aware, and zero-copy wherever memory alignment and hardware topology permit.
5. **Decoupled Checkpoint Boundaries**: Framework-specific state (e.g. PyTorch `model.state_dict()`) and AdaptiveML state (e.g. `AdaptiveClassifier.state_dict()`, `ULCv41Config`) must remain cleanly separated in checkpoint artifacts.

---

## 2. High-Level System Architecture

```mermaid
graph TD
    subgraph Host Frameworks ["Host ML Frameworks (External)"]
        SKL["scikit-learn (Pipelines, Estimators, CV)"]
        TORCH["PyTorch (nn.Module, Optimizers, Tensors)"]
        DF["DataFrames (pandas, Polars)"]
    end

    subgraph Integration Layer ["adaptive_ml.integrations (Adapter Layer)"]
        SKL_ADAPT["SklearnAdaptiveClassifier<br/>SklearnDriftDetector<br/>SklearnNoiseFilter"]
        TORCH_ADAPT["TorchSymmetricCrossEntropyLoss<br/>TorchGeneralizedCrossEntropyLoss<br/>TorchTrainingCallback<br/>create_torch_low_memory_adamw"]
        DATA_ADAPT["to_numpy()<br/>to_tensor()<br/>DatasetContract"]
    end

    subgraph Core Engine ["adaptive_ml Core Pillars (Pure Python + NumPy)"]
        ALA["ALA 2.0 (Adaptive Trees, ADWIN, Replay)"]
        RLA["RLA 2.0 (Reliability Engine, Losses, Noise Taxonomy)"]
        RAO["RAO 2.0 (8-Bit AdamW, Dynamic Budget Manager)"]
        ULC["ULC-v4.1 (Spatial Gated Arbitration)"]
        MIN["Minority Intelligence (Prior Tracker, Thresholds)"]
    end

    SKL <==> SKL_ADAPT
    TORCH <==> TORCH_ADAPT
    DF <==> DATA_ADAPT

    SKL_ADAPT --> ALA
    SKL_ADAPT --> MIN
    TORCH_ADAPT --> RAO
    TORCH_ADAPT --> RLA
    DATA_ADAPT --> Core Engine
    ULC -.->|"Arbitrates Directives"| Core Engine
```

---

## 3. Structural Representation Across Frameworks

To establish clean interoperability, AdaptiveML maps host framework representations to its core primitives:

| Dimension | scikit-learn Representation | PyTorch Representation | AdaptiveML Representation | Adapter Mapping Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Estimator / Model** | `BaseEstimator`, `ClassifierMixin` | `torch.nn.Module` | Vectorized trees, loss functions | Composition inside wrapper classes |
| **Dataset / Inputs** | 2D `np.ndarray`, pandas DataFrame | `torch.Tensor`, `DataLoader` | 2D contiguous `float64` / `float32` | `to_numpy()` / `to_tensor()` converters |
| **Labels / Targets** | 1D `np.ndarray`, pandas Series | 1D `torch.LongTensor` | 1D contiguous `int64` | `to_numpy(dtype=np.int64)` |
| **Training Steps** | `fit()`, `partial_fit()` | Manual training loop (`optimizer.step()`) | `partial_fit()`, `step()` | Interleaved test-then-train wrappers |
| **Optimizer** | Solvers inside estimators | `torch.optim.Optimizer` | `LowMemoryAdamW` | Inherits `torch.optim.Optimizer` (if torch installed) |
| **State / Weights** | Fitted attributes (`classes_`, etc.) | `module.state_dict()` | `state_dict()` / `load_state_dict()` | Key-value dictionary / SafeTensors |
| **Checkpoints** | `joblib.dump()`, `pickle` | `torch.save()`, SafeTensors | `save_state()`, `load_state()` | Isolated format-tagged archives |
| **Device Placement** | CPU only (RAM) | `cpu`, `cuda`, `mps` | CPU-first (block quantization) | CPU execution with safe GPU tensor ingestion |

---

## 4. Integration Module Structure

The integration subsystem is structured as follows:

```
adaptive_ml/integrations/
├── __init__.py               # Top-level integration exports
├── data.py                   # Data interoperability (to_numpy, to_tensor, DatasetContract)
├── sklearn.py                # Scikit-learn estimator adapters, pipelines & transformers
├── torch_module.py           # PyTorch nn.Module loss functions & models
├── torch_optim.py            # PyTorch optimizer factory & wrappers
└── torch_callback.py         # PyTorch training loop callbacks & budget hooks
```

Every module in `adaptive_ml/integrations/` is protected by try/except guards:
- If `scikit-learn` is not installed, importing `adaptive_ml.integrations.sklearn` raises an informative, actionable `ImportError` without affecting the rest of AdaptiveML.
- If `torch` is not installed, importing `adaptive_ml.integrations.torch_*` raises an informative `ImportError`.
- Core imports (`import adaptive_ml as aml`) never trigger framework imports automatically.

---

## 5. Security and Serialization Boundaries

1. **Untrusted Data Warning**: While scikit-learn standard practice frequently relies on Python `pickle` or `joblib`, AdaptiveML documents that pickle is unsafe for untrusted models.
2. **SafeTensors Standard**: For deep neural network weights and numerical optimizer moment state, AdaptiveML provides zero-copy SafeTensors serialization via [`SafeTensorsSerializer`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py), avoiding arbitrary code execution vulnerabilities.
3. **State Segregation**: When persisting hybrid pipelines (e.g. PyTorch model + AdaptiveML controller), the adapter writes separate metadata blocks ensuring model tensors and controller states are inspected and validated independently.
