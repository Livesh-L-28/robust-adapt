# AdaptiveML: Phase 1 Strategic Decisions and Research Handoff

> **Document Status**: Authoritative Baseline (Phase 1 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-RES-006`  
> **Last Updated**: 2026-11-01  
> **Governing Phase**: Phase 1 (Product & Market Research) -> Phase 2 (Novelty & Prior-Art Research)

---

## 1. Executive Summary of Phase 1 Decisions

Phase 1 established the empirical evidence base regarding the Python machine learning ecosystem. Based on competitive benchmarking, developer issue tracking, and market white-space identification, the following strategic decisions are codified:

```
+-------------------------------------------------------------------------------------------------------+
|                                  PHASE 1 STRATEGIC DECISION SUMMARY                                   |
+--------------------------+------------------------------------+---------------------------------------+
| Strategic Area           | Ratified Decision                  | Key Justification                     |
+--------------------------+------------------------------------+---------------------------------------+
| **Product Positioning**  | Algorithmic Companion to NumPy,    | Maximizes adoption; complements       |
|                          | scikit-learn, and PyTorch          | existing runtimes rather than compete |
+--------------------------+------------------------------------+---------------------------------------+
| **Core API Contract**    | Vectorized 2D NumPy partial_fit()  | Solves River's dict loop bottleneck;  |
|                          | and torch.optim.Optimizer step()   | aligns with standard industry tools   |
+--------------------------+------------------------------------+---------------------------------------+
| **MVP Scope (v0.1.0)**   | 6 Priority A Opportunities across  | Eliminates scope creep; delivers      |
|                          | ALA, RLA, RAO, and ULC             | immediate tangible value on CPU       |
+--------------------------+------------------------------------+---------------------------------------+
| **Dependency Model**     | Zero mandatory compiled core;      | Guarantees 100% reliable installation  |
|                          | strictly numpy >= 1.24.0           | across Windows, macOS, and Linux      |
+--------------------------+------------------------------------+---------------------------------------+
| **Rejected Directions**  | No AutoML, No Distributed Sched,   | Preserves bandwidth and sharp focus   |
|                          | No Custom Autograd, No Cloud SaaS  | on core mathematical primitives       |
+--------------------------+------------------------------------+---------------------------------------+
```

---

## 2. Detailed Ratified Recommendations

### REC-P1-001: Product Identity as an Algorithmic Companion
- **Decision**: AdaptiveML will position itself strictly as a **modular algorithmic companion library** for Python machine learning practitioners.
- **Implementation**: The library will never demand that users abandon their existing models, datasets, or pipelines. Users will import targeted mathematical primitives:
  - An ALA estimator for online stream drift adaptation.
  - An RLA loss module for training under noisy or corrupted labels.
  - An RAO optimizer for slashing optimizer memory footprint during CPU fine-tuning.
  - An optional ULC controller when multi-objective arbitration is necessary.

### REC-P1-002: Rejection of Single-Instance Dictionary Streaming as Default
- **Decision**: AdaptiveML will not adopt River's `learn_one(dict)` as its primary API contract.
- **Implementation**: All streaming estimators in ALA must accept standard **2D NumPy arrays (`numpy.ndarray`) via `partial_fit(X, y)`**. A lightweight dictionary adapter will be provided as an optional helper for event streams, but core math loops must operate on contiguous vectorized arrays to ensure maximal CPU BLAS performance.

### REC-P1-003: Rare-Sample Preservation Policy in RLA
- **Decision**: RLA will reject the naive "small-loss" sample filtering heuristic utilized by existing data-cleaning tools (Cleanlab / Confident Learning).
- **Implementation**: All sample reliability scorers must incorporate a feature-space density or margin-ratio penalty to guarantee that difficult-to-learn minority-class samples are not discarded as "label noise".

### REC-P1-004: CPU-First Zero-C-Extension Optimizer Architecture
- **Decision**: RAO optimizers must run natively on commodity x86_64 and ARM64 CPUs without requiring C/C++ compilation, CUDA toolchains, or AVX-512 vector extensions.
- **Implementation**: Initial optimizer state compression in Phase 10 will utilize block-wise scaling and bit-packing implemented in pure NumPy / PyTorch tensor operations, guaranteeing zero installation failures on consumer laptops and edge appliances.

---

## 3. Formally Rejected & Deferred Product Directions

### 3.1 Rejected Directions (Permanently Out of Scope)
1. **Autonomous Hyperparameter Search / AutoML Engine**:
   - *Reason*: Mature tools (Optuna, Ray Tune, Hyperopt) already dominate this space. Building an internal search engine would distract from core algorithmic research.
2. **Custom Neural Network Runtime / Autograd Engine**:
   - *Reason*: PyTorch and JAX are industry standards. Re-implementing tensor execution is commercially and technically unviable.
3. **Distributed Multi-Node Cluster Orchestrator**:
   - *Reason*: Ray Train, Torchrun, and Slurm solve multi-machine scheduling. AdaptiveML's focus is local-first and CPU-first.
4. **Cloud Telemetry & Managed SaaS Platform**:
   - *Reason*: Directly violates Project Charter and Research Governance Rule 9.

### 3.2 Deferred Directions (Scheduled for Post-v1.0 / Phases 20–21)
1. **SVD Low-Rank Optimizer State Compression (GaLore-style)**:
   - *Reason*: Periodic SVD introduces substantial CPU latency spikes; deferred until efficient CFFI/Rust micro-kernels can be validated without compromising pure Python fallbacks.
2. **Deep Continual Learning for Vision-Language Models (VLMs)**:
   - *Reason*: High computational cost; initial releases will focus on tabular, time-series, text embeddings, and compact vision backbones.

---

## 4. Formal Research Handoff to Subsequent Phases

Phase 1 findings generate specific, bounded research assignments for upcoming roadmap phases:

```
Phase 1 Handoff Architecture:
├── To Phase 2 (Novelty & Prior-Art):
│   ├── Investigate patent landscape for low-memory optimizer state compression (RAO).
│   └── Search patent databases for real-time drift-gated noise filtering architectures (ULC).
├── To Phase 3 (Legal & IP Assessment):
│   ├── Conduct formal clearance on provisional codename "AdaptiveML" (resolve potential conflict with Adaptive ML SAS).
│   └── Confirm Cleanlab AGPL-3.0 clean-room non-infringement for RLA algorithms.
├── To Phase 4 (Comprehensive Literature Review):
│   ├── Collate foundational papers on Symmetric Cross Entropy (Wang et al., 2019) and Generalized Cross Entropy (Zhang & Sabuncu, 2018).
│   ├── Review mathematical convergence bounds for Adafactor and block-wise 8-bit momentum.
│   └── Survey multi-variate streaming drift detection algorithms (ADWIN, DDM, Page-Hinkley).
├── To Phase 5 (Research Gap Identification):
│   ├── Formalize the "Small-Loss Failure in Imbalanced Regimes" gap.
│   ├── Formalize the "Drift-Noise Collision in Streaming Pipelines" gap.
│   └── Formalize the "CPU Optimizer State Memory Overhead" gap.
└── To Phase 6 (Mathematical & Algorithm Design):
    ├── Derive closed-form equations for Density-Aware Margin Reliability Scoring (RLA).
    └── Formulate the ULC Drift-Noise Arbitration state-transition automaton.
```
