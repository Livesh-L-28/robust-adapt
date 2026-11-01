# AdaptiveML: Scope and Requirements

> **Document Status**: Approved Baseline (Phase 0 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-FDN-004`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Product managers, software architects, core engineers, test leads

---

## 1. Scope Definition & Boundary Matrix

AdaptiveML establishes explicit boundaries across releases to maintain technical excellence and prevent scope creep.

```
+--------------------------------------------------------------------------------------------------+
|                                    SCOPE BOUNDARY TAXONOMY                                       |
+------------------------------------+-------------------------------------+-----------------------+
| IN SCOPE (Must-Have for v0.1-v1.0) | SECONDARY (Post-v1.0 Considerations)| OUT OF SCOPE (Strict) |
+------------------------------------+-------------------------------------+-----------------------+
| - Pure Python/NumPy core routines  | - Distributed multi-node training   | - Cloud-hosted SaaS   |
| - Standard CPU-first execution     | - Automatic neural architecture     | - Proprietary cloud   |
| - Standalone ALA, RLA, RAO pillars |   search (NAS)                      |   SDK requirements    |
| - Optional ULC orchestration       | - Complex multimodal cross-attention| - Re-implementing     |
| - scikit-learn API compatibility   |   adaptation                        |   autograd / PyTorch  |
| - PyTorch optimizer wrappers       | - Specialized neuromorphic hardware | - GUI dashboards      |
| - Tabular, stream, vision, NLP     |   compilation                       | - Telemetry tracking  |
+------------------------------------+-------------------------------------+-----------------------+
```

---

## 2. Functional Requirements (FRs)

### 2.1 Pillar 1: Adaptive Learning Algorithms (ALA)
- **FR-ALA-001 (Streaming Update Interface)**: The system must provide estimators that accept non-stationary data streams sequentially via a standard `partial_fit(X, y)` method.
- **FR-ALA-002 (Drift Detection Engine)**: The library must implement statistical drift detection primitives (monitoring error rate distributions and input covariate shifts) outputting calibrated p-values or divergence statistics.
- **FR-ALA-003 (Regulated Forgetting & Retention)**: The system must provide configurable retention policies (e.g., parameter elasticity, reservoir memory buffers) that constrain catastrophic forgetting while enabling adaptation to new regimes.
- **FR-ALA-004 (Decoupled Execution)**: All ALA components must function independently without importing or invoking RLA, RAO, or ULC modules.

### 2.2 Pillar 2: Robust Learning Algorithms (RLA)
- **FR-RLA-001 (Loss Functions for Noisy Labels)**: The system must provide robust loss functions bounded or symmetric under label noise regimes, compatible with both PyTorch (`torch.nn.Module`) and NumPy vectorized computations.
- **FR-RLA-002 (Sample Reliability Scoring)**: The system must support sample weighting mechanisms that estimate label confidence $w_i \in [0, 1]$ based on historical prediction dynamics without user-specified clean validation sets.
- **FR-RLA-003 (Rare-Sample Preservation)**: The system must distinguish between true noise and rare tail samples, preventing the systematic deletion or suppression of legitimate minority-class data.
- **FR-RLA-004 (Outlier-Resilient Estimators)**: The system must provide robust estimators resistant to extreme non-Gaussian covariate outliers.
- **FR-RLA-005 (Decoupled Execution)**: All RLA components must function independently without importing or invoking ALA, RAO, or ULC modules.

### 2.3 Pillar 3: Resource-Aware Optimization (RAO)
- **FR-RAO-001 (Memory-Reduced Optimizer States)**: The system must implement optimization routines that compress, factor, or quantize first- and second-moment state accumulators to achieve lower memory overhead than standard 32-bit Adam.
- **FR-RAO-002 (Pure CPU Optimization Execution)**: RAO optimizers must run natively on commodity x86_64 and ARM64 CPUs without requiring CUDA compilation, external C/C++ build steps, or GPU hardware.
- **FR-RAO-003 (Dual API Compatibility)**: RAO optimizers must provide:
  1. A PyTorch-compatible `torch.optim.Optimizer` interface (`step()`, `zero_grad()`, `state_dict()`).
  2. A standalone NumPy-native functional step method `step(params, grads, state)` for non-PyTorch environments.
- **FR-RAO-004 (Decoupled Execution)**: All RAO components must function independently without importing or invoking ALA, RLA, or ULC modules.

### 2.4 Pillar 4: Unified Learning Controller (ULC)
- **FR-ULC-001 (Optional Orchestration)**: The system must provide an optional controller that unifies ALA, RLA, and RAO, dynamically arbitrating adaptation speed, noise filtering, and memory allocation.
- **FR-ULC-002 (Non-Invasive Architecture)**: The ULC must treat ALA, RLA, and RAO as pluggable, interchangeable components via standard abstract interfaces (`Protocol` / `ABC`).
- **FR-ULC-003 (Telemetry & Status Reporting)**: The ULC must provide an inspectable diagnostic state object containing current drift statistics, noise estimates, memory consumption, and controller action logs.

---

## 3. Non-Functional Requirements (NFRs)

### 3.1 Hardware, Platform & Execution NFRs
- **NFR-PLAT-001 (CPU-First Execution)**: Every algorithmic routine must run efficiently on commodity CPUs (minimum dual-core, 4 GB RAM). No algorithm may mandate GPU access for basic functionality.
- **NFR-PLAT-002 (Cross-Platform Support)**: Support Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), macOS (macOS 12+ on Apple Silicon and Intel), and Windows (Windows 10, 11).
- **NFR-PLAT-003 (Python Version Compatibility)**: Strict support for Python 3.10, 3.11, 3.12, and 3.13.

### 3.2 Dependency & Packaging NFRs
- **NFR-DEP-001 (Minimal Mandatory Core)**: The core package runtime dependencies must be restricted strictly to:
  - Python standard library.
  - `numpy >= 1.24.0`.
- **NFR-DEP-002 (Optional Ecosystem Integration)**: All external framework dependencies must be packaged as optional extras:
  - `adaptiveml[torch]`: PyTorch integrations.
  - `adaptiveml[sklearn]`: scikit-learn estimators and pipeline compatibility tests.
  - `adaptiveml[scipy]`: Advanced scientific / statistical distribution functions.
  - `adaptiveml[all]`: Complete development and integration test suite.
- **NFR-DEP-003 (Lazy Framework Imports)**: Core modules must never import `torch` or `sklearn` at module top-level. Optional adapters must import lazily and provide informative `ImportError` messages when the optional dependency is missing.

### 3.3 Security, Privacy & Compliance NFRs
- **NFR-SEC-001 (Zero Telemetry)**: The library must not include any network calls, usage tracking, telemetry, or remote telemetry logging.
- **NFR-SEC-002 (Safe Model Serialization)**: Standard model serialization must not rely on unvalidated Python `pickle`. Models must support safe serialization formats (JSON parameter schemas, Safetensors, or explicit array dictionaries).
- **NFR-SEC-003 (Vulnerability Scanning)**: The codebase must maintain zero known high/critical CVEs in dependencies, verified in CI using `pip-audit` or Bandit.

### 3.4 Scientific Reproducibility NFRs
- **NFR-REP-001 (Strict Determinism)**: Given identical input data, identical hyperparameter configurations, and a fixed integer `random_state`, all algorithms must produce deterministic results on identical CPU architectures.
- **NFR-REP-002 (Isolated Random Generators)**: Global random states (`np.random.seed()`) must never be modified by the library. Algorithms must instantiate and encapsulate private `numpy.random.Generator` instances.

### 3.5 Software Quality & Maintainability NFRs
- **NFR-MAINT-001 (Typing Coverage)**: 100% type annotation coverage enforced via `mypy --strict`.
- **NFR-MAINT-002 (Test Coverage)**: Minimum 90% unit test coverage for core algorithmic logic.
- **NFR-MAINT-003 (CI Speed)**: Standard test suite must execute completely on a standard 2-core GitHub Actions runner in $\le 10$ minutes.

---

## 4. Requirements Traceability Matrix

| Requirement ID | Module / Component | Verification Phase | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **FR-ALA-001..004** | `adaptiveml.ala` | Phase 8 | Unit tests verify drift detection, partial fit updates, and isolation. |
| **FR-RLA-001..005** | `adaptiveml.rla` | Phase 9 | Unit tests verify noise loss bounds and sample weighting isolation. |
| **FR-RAO-001..004** | `adaptiveml.rao` | Phase 10 | Unit tests verify memory reduction and CPU PyTorch/NumPy step API. |
| **FR-ULC-001..003** | `adaptiveml.ulc` | Phase 11 | Multi-pillar integration tests verify non-invasive coordination. |
| **NFR-DEP-001..003** | Core Package | Phase 14 & 16 | Packaging audit confirms zero mandatory dependencies beyond NumPy. |
| **NFR-SEC-001..003** | Core Package | Phase 14 & 16 | Security audit confirms zero network calls and safe serialization. |
| **NFR-REP-001..002** | Core Package | Phase 12 | Seed repeatability tests verify bitwise deterministic outputs on CPU. |
