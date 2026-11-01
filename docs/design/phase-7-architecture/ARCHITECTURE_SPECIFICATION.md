# AdaptiveML — Master Technical Architecture Specification

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-001`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: System Architects, Senior Software Engineers, Core Maintainers  
> **Target Downstream Phase**: Phase 8 (Core Algorithm Implementation)  
> **Upstream Foundation**: Phase 6 Algorithm Design (`DOC-DES-P6-001` through `DOC-DES-P6-011`)

---

## 1. Executive Architecture Summary

The **AdaptiveML Technical Architecture** translates the mathematical foundations, closed-form equations, and complexity proofs established in Phase 6 into an enterprise-grade, modular, and extensible Python library architecture.

AdaptiveML is designed from the ground up under six foundational engineering tenets:
1. **Local-First & CPU-First**: Optimized for execution on standard multi-core CPUs (x86_64, ARM64/Apple Silicon) without mandatory GPUs or cloud infrastructure.
2. **Minimal Mandatory Dependencies**: The core library requires strictly `numpy >= 1.24.0` and Python standard library modules. PyTorch and scikit-learn are optional, lazily-loaded integration extras.
3. **Zero Mandatory C++ Compilation**: Core performance is achieved through vectorized contiguous array manipulation (NumPy SIMD broadcasting), eliminating complex C++ or CUDA compilation steps that fail across heterogeneous user environments.
4. **Pillar Modularity & Independence**: The three operational pillars (**ALA**, **RLA**, **RAO**) are completely decoupled. The **ULC** acts as an optional high-level coordinator.
5. **Ecosystem Native Interfaces**: Direct compliance with established idioms:
   - Streaming classifiers adhere to the `scikit-learn` BaseEstimator and `partial_fit` protocol.
   - Optimizers inherit from `torch.optim.Optimizer` (when PyTorch is installed) or provide a standalone NumPy state interface.
6. **Zero Telemetry & Safe Serialization**: Complete user privacy with zero network calls, paired with safe, tamper-resistant serialization formats (JSON metadata + Safetensors/raw binary arrays), strictly rejecting unvalidated Python pickle.

---

## 2. Layered System Architecture Overview

The system architecture is structured into six strictly demarcated layers:

```
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 1: PUBLIC API & ESTIMATOR FACADES                       |
|   aml.ala (AdaptiveClassifier)       aml.rla (RobustLoss, MarginScorer)     |
|   aml.rao (LowMemoryAdamW)           aml.ulc (AdaptiveLearningController)   |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 2: CORE ALGORITHMIC ENGINES                             |
|   - VectorizedHoeffdingTree          - DensityAwareMarginScorer             |
|   - ReliabilityWeightedADWIN         - SymmetricCrossEntropyLoss            |
|   - ClassBalancedReservoir           - CPU Block-Quantized AdamW Core       |
|   - ULC Dual-Evidence State Automaton                                       |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 3: SHARED CORE & DATA STRUCTURES                        |
|   - SlidingWindow & BucketList       - Quantile Sketch & DigitizeEngine     |
|   - ReservoirBuffer & ClassBuckets   - Metric Accumulator & HysteresisState  |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 4: EXECUTION BACKENDS                                   |
|   - Pure NumPy SIMD Engine (Primary) - PyTorch Bridge Engine (Optional)     |
|   - Zero-Copy Tensor Views           - Vectorized Quantization Kernel       |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 5: ECOSYSTEM INTEGRATION ADAPTERS                       |
|   - Scikit-Learn Estimator Wrapper   - PyTorch Optimizer Adapter            |
|   - Pandas / Polars Dataframe Mapper - Array-API Compatibility Stubs        |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+─────────────────────────────────────────────────────────────────────────────+
|               LAYER 6: STATE, VALIDATION & DIAGNOSTICS                      |
|   - Safe Safetensors / JSON Serde    - Invariant & Boundary Validator       |
|   - Memory Budget & RAM Telemetry    - Exception Hierarchy & Error Context  |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 3. High-Level Pillar Decomposition

### 3.1 ALA: Adaptive Learning Architecture (`adaptive_ml.ala`)
- Implements `StreamingDecisionTree` and `StreamingEnsemble` using contiguous 3D NumPy array suff-stats.
- Implements `ReliabilityWeightedADWIN` managing exponential sub-window buckets.
- Implements `ClassBalancedReservoirReplay` guaranteeing proportional representation for rare modes.
- Implements scikit-learn standard methods: `fit()`, `partial_fit()`, `predict()`, `predict_proba()`.

### 3.2 RLA: Robust Learning Architecture (`adaptive_ml.rla`)
- Implements `DensityAwareMarginScorer` providing standalone $k$-NN density and logit margin evaluations.
- Implements `SymmetricCrossEntropyLoss` and `GeneralizedCrossEntropyLoss` with NumPy forward/backward methods and optional `torch.nn.Module` subclasses.
- Implements `ClassBalancedWeights` dynamically computing effective sample weights from class occurrence vectors.

### 3.3 RAO: Resource-Aware Architecture (`adaptive_ml.rao`)
- Implements `LowMemoryAdamW` utilizing pure vector block quantization ($B_q = 256$, signed `int8` momentum, unsigned `uint8` variance).
- Operates either as a PyTorch `torch.optim.Optimizer` subclass or as a standalone NumPy parameter updater.
- Implements `AdaptiveGradientAccumulator` providing dynamic micro-batch scheduling under host memory ceilings.

### 3.4 ULC: Unified Controller Architecture (`adaptive_ml.ulc`)
- Implements `AdaptiveLearningController` coordinating ALA drift detection and RLA reliability scoring.
- Encapsulates the 5-state arbitration finite automaton, enforcing hysteresis deadbands and issuing typed control directives.

---

## 4. Architectural Invariants & Quality Standards

Every component implementation must satisfy the following technical requirements:
1. **Contiguous Memory Alignment**: All internal multi-dimensional arrays must be allocated C-contiguous (`order='C'`) to maximize CPU L1/L2 cache line hits during SIMD loops.
2. **Zero-Copy In-Place Updates**: Internal buffer management must prioritize views (`np.ndarray.view()`) and in-place updates (`+=`, `out=`) over allocations.
3. **Explicit Typing & Protocols**: All public functions and classes must provide comprehensive Python type annotations conforming to `mypy --strict` and `numpy.typing`.
4. **Deterministic Reproducibility**: All stochastic components (reservoir sampling, tie breaking) must accept an explicit `random_state` parameter ensuring bit-level reproducibility across repeated runs.
5. **Fail-Fast Parameter Validation**: Invalid hyperparameters (e.g. learning rate $\le 0$, block size not a power of 2, reliability weight $< 0$) must be rejected at initialization with informative custom exceptions.

---

## 5. Phase 7 Deliverables Matrix

The complete architecture specification is organized into 14 comprehensive deliverables:

| Document ID | Deliverable File Name | Architectural Domain |
| :--- | :--- | :--- |
| `DOC-DES-P7-001` | `ARCHITECTURE_SPECIFICATION.md` | Master technical architecture overview |
| `DOC-DES-P7-002` | `SYSTEM_CONTEXT_AND_COMPONENT_ARCHITECTURE.md` | Detailed breakdown of Layers 1 through 6 |
| `DOC-DES-P7-003` | `PACKAGE_STRUCTURE_AND_MODULE_BOUNDARIES.md` | Package file tree, import rules, symbol exports |
| `DOC-DES-P7-004` | `PUBLIC_API_SPECIFICATION.md` | Exact method signatures, types, docstrings |
| `DOC-DES-P7-005` | `BACKEND_AND_INTEGRATION_ARCHITECTURE.md` | Backend dispatch, PyTorch/scikit-learn bridges |
| `DOC-DES-P7-006` | `STATE_AND_SERIALIZATION_ARCHITECTURE.md` | Checkpointing, Safetensors serde, lifecycle |
| `DOC-DES-P7-007` | `CONFIGURATION_AND_ERROR_HANDLING.md` | Configuration schemas, custom exceptions |
| `DOC-DES-P7-008` | `PERFORMANCE_AND_RESOURCE_ARCHITECTURE.md` | SIMD vectorization, memory budgeting |
| `DOC-DES-P7-009` | `TESTING_AND_VALIDATION_ARCHITECTURE.md` | Layered test strategy, 5-seed harness |
| `DOC-DES-P7-010` | `SECURITY_AND_SUPPLY_CHAIN_ARCHITECTURE.md` | Local-first security, zero telemetry, SBOM |
| `DOC-DES-P7-011` | `PACKAGING_AND_RELEASE_ARCHITECTURE.md` | `pyproject.toml`, extras, wheel matrix |
| `DOC-DES-P7-012` | `ARCHITECTURE_DIAGRAMS.md` | 12 complete Mermaid architectural diagrams |
| `DOC-DES-P7-013` | `ARCHITECTURE_DECISION_RECORDS.md` | ADR-001 to ADR-012 formal decision records |
| `DOC-DES-P7-014` | `PHASE_7_DECISIONS.md` | Architecture sign-off & Phase 8 hand-off |
