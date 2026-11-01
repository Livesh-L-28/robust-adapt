# AdaptiveML — Package Structure & Module Boundaries

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-003`  
> **Last Updated**: 2026-11-01  
> **Scope**: Concrete file tree, public symbol exports, import hierarchy, and circular dependency rules  
> **Target Package Root**: `adaptive_ml/`

---

## 1. Concrete Package File Tree

The source package structure for AdaptiveML is defined as follows:

```
adaptive_ml/
│
├── __init__.py                           # Root package export, version metadata, __all__
├── py.typed                              # PEP 561 inline typing marker
│
├── core/                                 # Layer 3/6: Shared Core, Types, Exceptions
│   ├── __init__.py
│   ├── types.py                          # Type definitions, Protocols, TypeVars
│   ├── exceptions.py                     # Custom exception hierarchy (AdaptiveMLError)
│   ├── config.py                         # Frozen configuration dataclasses
│   ├── validation.py                     # Input validation and boundary checks
│   ├── telemetry.py                      # Local memory and performance metrics
│   └── constants.py                      # Mathematical epsilon guards, bounds
│
├── ala/                                  # Layer 2: Adaptive Learning Algorithms
│   ├── __init__.py
│   ├── tree.py                           # VectorizedHoeffdingTree implementation
│   ├── adwin.py                          # ReliabilityWeightedADWIN implementation
│   ├── replay.py                         # ClassBalancedReservoirReplay
│   ├── ensemble.py                       # StreamingDecisionForestEnsemble
│   └── classifier.py                     # High-level AdaptiveClassifier facade
│
├── rla/                                  # Layer 2: Robust Learning Algorithms
│   ├── __init__.py
│   ├── scorer.py                         # DensityAwareMarginScorer implementation
│   ├── losses.py                         # SymmetricCrossEntropy & GeneralizedCrossEntropy
│   ├── weighting.py                      # ClassBalancedReweighting engine
│   └── pipeline.py                       # Denoising and filtering pipeline wrapper
│
├── rao/                                  # Layer 2: Resource-Aware Optimization
│   ├── __init__.py
│   ├── adamw.py                          # LowMemoryAdamW (NumPy/PyTorch compatible)
│   ├── quantizer.py                      # Block-quantization kernels (int8 / uint8)
│   ├── accumulator.py                    # AdaptiveGradientAccumulator
│   └── memory.py                         # Host RAM monitoring and micro-batch sizing
│
├── ulc/                                  # Layer 2: Unified Learning Controller
│   ├── __init__.py
│   ├── controller.py                     # AdaptiveLearningController facade
│   ├── automaton.py                      # Dual-evidence finite state machine
│   └── directives.py                     # Typed cross-pillar control directives
│
├── backends/                             # Layer 4: Execution Backends
│   ├── __init__.py
│   ├── base.py                           # Abstract Backend protocol
│   ├── numpy_backend.py                  # Primary pure NumPy SIMD implementation
│   └── torch_backend.py                  # Optional lazy PyTorch execution bridge
│
├── integrations/                         # Layer 5: Ecosystem Framework Bridges
│   ├── __init__.py
│   ├── sklearn.py                        # Scikit-learn BaseEstimator integration
│   ├── torch_optim.py                    # torch.optim.Optimizer subclass bridge
│   └── dataframe.py                      # Pandas/Polars input converters
│
└── state/                                # Layer 6: Persistence & Checkpointing
    ├── __init__.py
    ├── serializer.py                     # Safe Safetensors + JSON metadata serde
    └── checkpoint.py                     # State snapshotting, rollback, and recovery
```

---

## 2. Public vs Private Symbol Exports (`__all__`)

### 2.1 Root Package Export (`adaptive_ml/__init__.py`)
```python
__version__ = "0.1.0.dev0"

__all__ = [
    # Top-Level Facades
    "AdaptiveClassifier",
    "DensityAwareMarginScorer",
    "SymmetricCrossEntropyLoss",
    "GeneralizedCrossEntropyLoss",
    "LowMemoryAdamW",
    "AdaptiveLearningController",
    # Core Exceptions
    "AdaptiveMLError",
    "DriftDetectedException",
    "ResourceBudgetExceededError",
    "NumericalInstabilityError",
]
```

### 2.2 Pillar Symbol Exports
- `adaptive_ml.ala`: Exposes `AdaptiveClassifier`, `VectorizedHoeffdingTree`, `ReliabilityWeightedADWIN`, `ClassBalancedReservoirReplay`. All node internals (`_LeafNode`, `_attempt_split`) are private (`_`).
- `adaptive_ml.rla`: Exposes `DensityAwareMarginScorer`, `SymmetricCrossEntropyLoss`, `GeneralizedCrossEntropyLoss`, `ClassBalancedWeights`.
- `adaptive_ml.rao`: Exposes `LowMemoryAdamW`, `AdaptiveGradientAccumulator`, `BlockQuantizer`.
- `adaptive_ml.ulc`: Exposes `AdaptiveLearningController`, `ControllerDirective`, `AutomatonState`.

---

## 3. Strict Import Direction Hierarchy

To maintain complete architectural integrity and guarantee zero circular imports, module imports must strictly follow this directed acyclic graph (DAG):

```
+─────────────────────────────────────────────────────────────────────────────+
|                         ALLOWED IMPORT DEPENDENCY DAG                       |
+─────────────────────────────────────────────────────────────────────────────+

                           core/ (Leaf - Imports Nothing)
                             ▲
              ┌──────────────┴──────────────┐
              │                             │
          backends/                       state/
              ▲                             ▲
      ┌───────┴───────┐                     │
      │               │                     │
     ala/            rla/            rao/ ──┘
      ▲               ▲               ▲
      └───────┬───────┴───────┬───────┘
              │               │
             ulc/        integrations/
```

### 3.1 Strict Import Prohibitions

1. **`core` MUST NOT import anything outside `core`**. It only imports Python standard library modules (`dataclasses`, `typing`, `math`, `enum`) and `numpy`.
2. **`ala`, `rla`, and `rao` MUST NOT import each other**.
   - `ala` importing `rla` is a **FATAL ARCHITECTURAL VIOLATION**.
   - `rla` importing `rao` is a **FATAL ARCHITECTURAL VIOLATION**.
   - `rao` importing `ala` is a **FATAL ARCHITECTURAL VIOLATION**.
3. **`ulc` MAY import protocols from `ala`, `rla`, and `rao`**, but only for type annotations or facade orchestration.
4. **`integrations` MUST use lazy dynamic imports for external libraries**:
   ```python
   # Correct lazy import pattern in integrations/torch_optim.py:
   def get_torch_optimizer_base():
       try:
           import torch
           return torch.optim.Optimizer
       except ImportError:
           raise ImportError("PyTorch is required for this integration. Install via: pip install adaptive-ml[torch]")
   ```
5. **No `from module import *`**: All imports must be explicit.

---

## 4. Circular Dependency Elimination Architecture

Circular imports are structurally impossible in this design because:
- Cross-pillar communications occur exclusively via primitives and standard Python dataclasses defined in `core.types` and `ulc.directives`.
- Pillar engines never reference high-level facades or integration bridges.
- Execution backends are injected via dependency injection or protocol interfaces rather than hard-coded concrete imports.
