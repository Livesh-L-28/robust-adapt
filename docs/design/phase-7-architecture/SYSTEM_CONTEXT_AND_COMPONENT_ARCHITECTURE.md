# AdaptiveML — System Context & Component Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-002`  
> **Last Updated**: 2026-11-01  
> **Scope**: Detailed component responsibilities, layer interactions, and interface protocols across Layers 1–6  
> **Cross-Reference**: `DOC-DES-P7-001` (Master Architecture), `DOC-DES-P7-012` (Diagrams)

---

## 1. System Context & External Environment

AdaptiveML operates as an embedded algorithm library within the user's local Python environment. It maintains zero persistent daemon processes, connects to zero remote network endpoints, and executes strictly within the calling process's memory space.

```
                           SYSTEM CONTEXT BOUNDARY
                                      │
  ┌───────────────────────────────────▼───────────────────────────────────┐
  │                           USER APPLICATION                            │
  │   - Training Scripts / Jupyter Notebooks                              │
  │   - Online Streaming Pipelines / Real-Time Inference Services         │
  └───────────────────┬───────────────────────────────┬───────────────────┘
                      │ Calls API                     │ Provides Data
                      ▼                               ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │                         ADAPTIVEML RUNTIME                            │
  │                                                                       │
  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐   │
  │   │  ALA Pillar  │ │  RLA Pillar  │ │  RAO Pillar  │ │ ULC Pillar │   │
  │   └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘   │
  │                                                                       │
  │   ┌───────────────────────────────────────────────────────────────┐   │
  │   │           Shared Core Data Structures & Backend Engine        │   │
  │   └───────────────────────────────────────────────────────────────┘   │
  └───────────────────┬───────────────────────────────┬───────────────────┘
                      │ (Optional Imports)            │ CPU Math Ops
                      ▼                               ▼
  ┌──────────────────────────────────────┐  ┌─────────────────────────────┐
  │   OPTIONAL ECOSYSTEM DEPENDENCIES    │  │      HOST PLATFORM / OS     │
  │   - PyTorch (torch.optim, Tensor)    │  │   - Standard CPU RAM / SIMD │
  │   - scikit-learn (BaseEstimator)     │  │   - Pure NumPy (BLAS/LAPACK)│
  │   - Pandas / Polars DataFrames       │  │   - Local POSIX/Win32 FileIO│
  └──────────────────────────────────────┘  └─────────────────────────────┘
```

---

## 2. Detailed Six-Layer Architecture

### 2.1 Layer 1: Public Surface & Estimator Facade
The public layer provides clean, idiomatic Python classes exposing the library's capabilities.
- **`adaptive_ml.ala.AdaptiveClassifier`**: scikit-learn compliant estimator providing `fit()`, `partial_fit()`, and `predict()`.
- **`adaptive_ml.rla.DensityAwareMarginScorer`**: Standalone evaluator generating instance reliability arrays.
- **`adaptive_ml.rla.SymmetricCrossEntropyLoss`**: Robust loss module supporting both NumPy arrays and `torch.Tensor`.
- **`adaptive_ml.rao.LowMemoryAdamW`**: Memory-bounded optimizer compatible with standard PyTorch training loops or standalone NumPy weight updates.
- **`adaptive_ml.ulc.AdaptiveLearningController`**: High-level coordinator managing holistic drift-noise arbitration.

---

### 2.2 Layer 2: Core Algorithmic Engines
Encapsulates pure mathematical logic derived in Phase 6:
1. **`VectorizedHoeffdingTreeEngine`**: Manages recursive node splitting, Hoeffding bound computation, and candidate split heuristic comparisons.
2. **`ReliabilityWeightedADWINEngine`**: Manages variable-length statistical sliding windows, variance tracking, and harmonic effective sample cut bounds.
3. **`ClassBalancedReservoirEngine`**: Manages class-stratified reservoir retention pools and stratified replay sampling.
4. **`MarginScoringEngine`**: Computes signed logit margins and vector $k$-NN feature space density ratios.
5. **`BlockQuantizationEngine`**: Executes vector-sliced symmetric dynamic integer quantization and dequantization.
6. **`ArbitrationAutomatonEngine`**: Executes the 5-state hysteresis transition kernel and directive dispatch.

---

### 2.3 Layer 3: Shared Core & Data Structures
Underpinning algorithms with cache-efficient, memory-safe data structures:
- **`SlidingWindowBuffer`**: Contiguous circular buffer storing sliding time-series metrics without dynamic reallocation.
- **`QuantileHistogramBins`**: Pre-calculated or dynamically estimated quantile split threshold matrices.
- **`ClassSampleBucket`**: Compact fixed-capacity reservoir buffer storing feature arrays for specific classes.
- **`StateVector`**: Lightweight, typed dataclass encapsulating controller metrics.

---

### 2.4 Layer 4: Execution Backends
Directs mathematical operations to available hardware acceleration:
- **`NumPySIMDBackend` (Primary)**: Uses contiguous C-order NumPy arrays, in-place accumulation (`np.add.at`), and vector broadcasting. Guarantees 100% CPU compatibility.
- **`PyTorchBridgeBackend` (Optional)**: Automatically detected when `torch` is imported. Wraps PyTorch tensors directly, enabling autograd integration and GPU/MPS pass-through without unnecessary memory copies.

---

### 2.5 Layer 5: Ecosystem Integration Adapters
Bridges AdaptiveML to broader industry frameworks:
- **`ScikitLearnAdapter`**: Implements `sklearn.base.BaseEstimator` and `ClassifierMixin`, enabling `GridSearchCV`, `Pipeline`, and cross-validation integration.
- **`PyTorchOptimizerAdapter`**: Inherits from `torch.optim.Optimizer`, exposing standard `.step()` and `.zero_grad()` semantics.
- **`ArrayAPIMapper`**: Converts incoming inputs (lists, Pandas Series, Polars DataFrames) into standardized C-contiguous NumPy ndarrays.

---

### 2.6 Layer 6: State, Validation & Diagnostics
Guarantees operational reliability, persistence, and debuggability:
- **`SafetensorsStateSerializer`**: Serializes internal arrays into safe binary `.safetensors` files paired with JSON schema metadata.
- **`BoundaryValidator`**: Verifies input dimensions, non-negativity, probability simplices, and finite float values.
- **`MemoryBudgetTracker`**: Monitors host RAM usage and triggers dynamic micro-batch resizing when approaching memory ceilings.
- **`DiagnosticTelemetry`**: Local-only logging system tracking drift events, reliability histograms, and quantization errors.

---

## 3. Component Interaction & Data Flow Protocol

```
+─────────────────────────────────────────────────────────────────────────────+
|                         END-TO-END DATA FLOW PIPELINE                       |
+─────────────────────────────────────────────────────────────────────────────+

  1. User calls: model.partial_fit(X, y)
       │
  2. Layer 5 (Adapter): Validates input, converts to C-contiguous float32 / int64
       │
  3. Layer 1 (ULC / Facade): Passes batch to RLA Margin Scorer
       │
  4. Layer 2 (RLA Engine): Computes sample reliability vector r in [eps_r, 1.0]
       │
  5. Layer 1 (ULC / Facade): Evaluates error against ALA RW-ADWIN
       │
  6. Layer 2 (ULC Automaton): Checks (Delta_drift, r_bar_W) -> updates state directive
       │
  7. Layer 2 (ALA Engine): Updates tree sufficient statistics and evaluates split
       │
  8. Layer 2 (RAO Engine): In deep models, computes gradients and executes LowMemoryAdamW step
       │
  9. Layer 6 (Diagnostics): Records step metrics; checks RAM ceiling
```

---

## 4. Architectural Boundary Invariants

1. **Unidirectional Dependency**: Higher layers may import lower layers; lower layers MUST NEVER import higher layers.
   $$\text{Layer } 1 \to \text{Layer } 2 \to \text{Layer } 3 \to \text{Layer } 4$$
2. **Zero Heavy Imports in Core**: Importing `adaptive_ml.ala` or `adaptive_ml.rao` must never trigger imports of PyTorch or scikit-learn unless explicitly invoked.
3. **Pure Function Contracts**: Core mathematical engines in Layer 2 operate on explicit parameters and arrays, avoiding hidden global state or environment variables.
