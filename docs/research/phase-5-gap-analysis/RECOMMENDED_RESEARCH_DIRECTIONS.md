# AdaptiveML — Phase 5: Recommended Research Directions

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-009`  
> **Last Updated**: 2026-11-01  
> **Target Downstream Phase**: Phase 6 (Mathematical & Algorithm Design)

---

## 1. Executive Direction Matrix

To ensure that Phase 6 mathematical derivations focus strictly on high-impact, scientifically validated opportunities, research directions are structured into six distinct operational categories:

```
+-------------------------------------------------------------------------------------------------------+
|                                    STRATEGIC RESEARCH DIRECTION TAXONOMY                              |
+--------------------------+------------------------------------+---------------------------------------+
| Category                 | Features / Methodologies Assigned  | Strategic Action in Phase 6           |
+--------------------------+------------------------------------+---------------------------------------+
| **1. Scientifically**    | - Bounded Symmetric Cross Entropy  | Formalize closed-form loss equations  |
|    **Supported Primitives**| - ADWIN statistical window cutting | and parameter gradients for pure NumPy|
|                          | - Standard AdamW update equations  | and PyTorch integration.              |
+--------------------------+------------------------------------+---------------------------------------+
| **2. Original Algorithm**| - Density-Aware Margin Reliability | Formulate mathematical equations      |
|    **Development**       |   Scorer (RLA)                     | linking local k-NN density to margin. |
|                          | - Dual-Evidence Drift-Noise        | Derive state automaton transition     |
|                          |   Arbitration Automaton (ULC)      | matrix and stability bounds.          |
+--------------------------+------------------------------------+---------------------------------------+
| **3. Existing Art to**   | - Vitter's Reservoir Sampling      | Adopt verbatim from academic literature|
|    **Reuse Directly**    | - Hoeffding tree split criteria    | with full bibliographic attribution.  |
|                          | - Class-Balanced Effective Number  |                                       |
+--------------------------+------------------------------------+---------------------------------------+
| **4. High-Value**        | - Vectorized 2D NumPy array chunks | Design scikit-learn partial_fit()     |
|    **Integration / DX**  | - Drop-in torch.optim.Optimizer    | and PyTorch optimizer state contracts |
|                          | - Zero-compilation CPU execution   | ensuring zero C++ compiler hurdles.   |
+--------------------------+------------------------------------+---------------------------------------+
| **5. Permanently**       | - Autonomous AutoML search engines | Excluded from scope; maintain focus on|
|    **Rejected Vectors**  | - Multi-node cluster schedulers    | core algorithmic modularity.          |
|                          | - Custom tensor autograd runtimes  |                                       |
+--------------------------+------------------------------------+---------------------------------------+
```

---

## 2. Research Questions Advancing to Phase 6

The following three core research questions are formally approved to advance to **Phase 6: Mathematical & Algorithm Design**:

### Priority Research Question 1 (RLA Focus — RQ-1):
> *"Can a closed-form density-aware margin score distinguish between corrupt common labels and legitimate rare-class instances, provably bounding minority pruning errors on long-tailed distributions?"*
- **Phase 6 Task**: Derive the mathematical formulations for $\text{Reliability}(x, y) = \mathcal{F}(\mathcal{M}(x, y), \rho_k(x))$ and prove its asymptotic behavior in low-density feature regimes.

### Priority Research Question 2 (ULC Focus — RQ-2):
> *"Can an in-loop arbitration automaton dynamically modulate drift detection thresholds using sample reliability distributions, provably suppressing false-positive drift alarms under bursty label noise?"*
- **Phase 6 Task**: Formalize the finite state automaton $\mathcal{S} \times \mathcal{E} \to \mathcal{S}'$ and derive mathematical conditions under which drift resets are suppressed without increasing detection lag on true structural shifts.

### Priority Research Question 3 (RAO Focus — RQ-3):
> *"What is the minimal block size and integer precision required to quantize first- and second-order optimizer states in pure NumPy/PyTorch on CPU while preserving the spectral convergence properties of AdamW?"*
- **Phase 6 Task**: Derive the error bounds of block-wise symmetric integer scaling and prove convergence on L-smooth non-convex objective functions.

---

## 3. Preservation of Modular Independence

The architectural mandate is reaffirmed:
- **ALA, RLA, and RAO must remain completely independent.**
- A developer must be able to use:
  - `aml.ala.AdaptiveClassifier` without importing `rla` or `rao`.
  - `aml.rla.RobustLoss` without importing `ala` or `rao`.
  - `aml.rao.LowMemoryAdamW` without importing `ala` or `rla`.
- **The ULC is strictly an optional coordinator** that imports the three pillars through abstract protocols when holistic orchestration is explicitly requested.
