# AdaptiveML: Strategic Decision Log & Architecture Decision Records (ADRs)

> **Document Status**: Approved Baseline (Phase 0 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-FDN-009`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Core engineering team, scientific leads, architecture committee, future maintainers

---

## 1. Decision Framework

AdaptiveML uses a structured Architecture Decision Record (ADR) framework to document foundational, strategic, and architectural choices. 

Every entry records:
- **Context**: The problem or tension requiring resolution.
- **Decision**: The chosen strategic path.
- **Status**: Proposed, Approved, Superseded, or Rejected.
- **Consequences**: Both positive advantages and trade-offs/obligations created.

---

## 2. Ratified Strategic Decisions (Phase 0)

### ADR-001: Working Codename and Trademark Clearance Safeguards
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: The project needs an identifiable working name. The name "AdaptiveML" was chosen, but other commercial entities (e.g., Adaptive ML SAS) and related trademarks may exist. Premature publishing to PyPI or public branding could trigger legal dispute or trademark infringement claims.
- **Decision**: "AdaptiveML" is ratified strictly as a **provisional internal codename**. No package shall be registered, reserved, or published to PyPI or other package registries until formal trademark searches and legal review are completed in Phase 3 and Phase 16.
- **Consequences**:
  - *Positive*: Protects the project from legal liability, domain disputes, and wasted branding effort.
  - *Trade-off*: Requires maintaining namespace flexibility; fallback names must be evaluated in Phase 3.

---

### ADR-002: Modular Multi-Pillar Architecture (Independent Pillars + Optional ULC)
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: Machine learning users often need a specific capability (e.g., drift detection) without adopting an entire monolithic learning framework. Tightly coupling ALA, RLA, and RAO into a single monolithic engine would repel developers wanting targeted solutions.
- **Decision**: AdaptiveML will structure its core capabilities into three completely autonomous pillars (ALA, RLA, RAO). Each pillar must be independently importable and executable without requiring any other pillar. The Unified Learning Controller (ULC) is designated strictly as an **optional higher-level orchestrator**.
- **Consequences**:
  - *Positive*: Maximum modularity; users can adopt only what they need; clean unit testing and boundary enforcement.
  - *Trade-off*: Requires disciplined abstraction layers and zero-leakage import boundaries between subpackages.

---

### ADR-003: Minimalist Core Dependency Philosophy
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: Modern ML libraries frequently suffer from dependency bloat, fragile version pinning, and massive installation overhead (e.g., requiring gigabytes of CUDA packages just to run a simple estimator on tabular data).
- **Decision**: The core runtime dependencies of AdaptiveML shall be strictly limited to:
  1. Python Standard Library.
  2. `numpy >= 1.24.0`.
  All framework integrations (PyTorch, scikit-learn, SciPy) must be optional extras (`pip install adaptiveml[torch]`) loaded lazily.
- **Consequences**:
  - *Positive*: Rapid, lightweight installation; zero dependency conflicts; minimal vulnerability surface; frictionless deployment in constrained environments.
  - *Trade-off*: Requires implementing standalone NumPy fallbacks for mathematical operations that could otherwise be delegated to heavier libraries.

---

### ADR-004: Execution Environment Priority (CPU-First and Local-First)
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: Most advanced deep learning libraries are optimized exclusively for high-end cloud GPUs, leaving local workstations, developer laptops, and edge CPU devices underserved.
- **Decision**: AdaptiveML adopts a strict **CPU-First and Local-First** execution policy. Every core algorithmic primitive must run efficiently on commodity CPUs without mandatory GPU access, cloud connectivity, or remote telemetry.
- **Consequences**:
  - *Positive*: Universal accessibility; runnable anywhere from Raspberry Pi to developer laptops; total user data privacy.
  - *Trade-off*: High compute performance requires careful vectorization and algorithmic efficiency rather than brute-force GPU parallelism.

---

### ADR-005: Proposed Open-Source Licensing (Apache-2.0 + DCO 1.1)
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: The library requires an open-source license that encourages broad commercial and academic adoption while providing legal protection against patent trolls.
- **Decision**: Adopt the **Apache License, Version 2.0 (Apache-2.0)** as the primary license, coupled with the Developer Certificate of Origin (DCO 1.1) via mandatory `Signed-off-by` commit sign-offs.
- **Consequences**:
  - *Positive*: Permissive adoption; explicit patent grant protects downstream users; clear provenance via DCO.
  - *Trade-off*: Copyleft protections are not present, meaning proprietary downstream forks are permissible.

---

### ADR-006: Empirical Verification Gate (No Claims Without Reproducibility)
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: Academic and commercial ML projects frequently advertise inflated performance numbers based on selective reporting or single cherry-picked seeds.
- **Decision**: AdaptiveML institutes a mandatory empirical verification gate. No performance number may be designated an "achieved result" or claimed as a marketing benefit until verified in Phase 12 across a minimum of 5 random seeds with statistical significance testing and published negative results.
- **Consequences**:
  - *Positive*: Bulletproof scientific credibility; trust from researchers and enterprise teams.
  - *Trade-off*: Slower marketing velocity; strict publication hurdles.

---

### ADR-007: Phase 0 Strict Scope Boundary (Foundations Only)
- **Status**: **APPROVED**
- **Date**: 2026-11-01
- **Context**: Eager engineering teams often jump directly into coding algorithms before governance, scope, mathematical formulation, and architecture are defined, leading to premature rework.
- **Decision**: Phase 0 is strictly confined to foundational documentation, governance rules, scope definitions, and repository setup. **No algorithmic source code shall be written during Phase 0.**
- **Consequences**:
  - *Positive*: Clear architectural roadmap; prevents ungrounded implementation churn.
  - *Trade-off*: Delays first executable code until Phase 8 (following design phases 1–7).

---

## 3. Unresolved Strategic Decisions Backlog

The following strategic questions remain open and are assigned to specific upcoming roadmap phases:

```
+-------------------------------------------------------------------------------------------------------+
|                                    UNRESOLVED DECISIONS LOG                                           |
+--------+---------------------------------------+---------------+--------------------------------------+
| ID     | Decision Topic                        | Target Phase  | Alternatives Under Consideration     |
+--------+---------------------------------------+---------------+--------------------------------------+
| U-001  | PyPI Namespace Resolution if          | Phase 3       | A) adaptiveml (if cleared)           |
|        | "adaptiveml" is contested             |               | B) pyadaptiveml                      |
|        |                                       |               | C) aml-core                          |
|        |                                       |               | D) adaptml                           |
+--------+---------------------------------------+---------------+--------------------------------------+
| U-002  | Baseline Supported Python Version     | Phase 7       | A) Python 3.10+ (broader compatibility)|
|        |                                       |               | B) Python 3.11+ (performance gains)  |
+--------+---------------------------------------+---------------+--------------------------------------+
| U-003  | CPU Low-Precision Arithmetic Strategy | Phase 6 & 10  | A) Pure NumPy simulated quantization |
|        | for RAO Optimizer States              |               | B) Optional CFFI/Rust micro-kernels  |
|        |                                       |               | C) Standard NumPy float16/int8       |
+--------+---------------------------------------+---------------+--------------------------------------+
| U-004  | Formal Engagement of External Legal   | Phase 3       | A) Open-source legal foundation      |
|        | Counsel for IP / Trademark Clearance  |               | B) Pro-bono academic legal clinic    |
|        |                                       |               | C) Retained specialist IP firm       |
+--------+---------------------------------------+---------------+--------------------------------------+
```

