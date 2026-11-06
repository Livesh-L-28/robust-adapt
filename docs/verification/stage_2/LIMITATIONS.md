# Stage 2: Technical Limitations & Architectural Boundaries
## Production Defect Remediation & Architecture Hardening

**Document Identifier:** `VERIF-STAGE-2-007`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Technical Scope & Design Boundaries

The Stage 2 implementation addresses the interface defect contracts DEF-006 and DEF-007. The following boundaries and operational limitations apply:

### 1.1 In-Memory Buffer Scope
- **RAM Constraints**: `ClassBalancedReservoirReplay` retains instances in CPU RAM as lists of NumPy arrays. While bucket capacity is strictly bounded by `capacity // n_classes`, memory usage scales linearly with feature dimension ($D$) and instance count ($K$). For extremely high dimensions ($D > 10{,}000$), external or compressed disk-backed buffers should be deployed.
- **Dynamic Minority Identification**: If `minority_classes` is not passed explicitly to `purge()`, minority classes are inferred dynamically based on current bucket counts ($\le \min(\text{counts})$ or $\le 20\%$ of max count). In rapidly shifting multi-class streams where classes appear intermittently, explicit class-prior tracking (implemented in Stage 3) is strongly recommended.

### 1.2 Optimizer Momentum Flushes
- **Second-Order Moments ($v_t$)**: By default, `reset_momenta()` resets only the first-order momentum ($m_t$, $q_m$, $\text{scale}_m$) and step counter, preserving the second-order uncentered variance estimate ($v_t$). This ensures stable adaptive scaling while shedding directional momentum. If a complete re-initialization of variance is required, state dict clearing should be used.
- **Multi-Group Indexing**: Parameter group indexing assumes 0-indexed sequences. If external frameworks mutate group layouts during streaming, `reset_momenta` should be invoked without `param_indices` to apply globally.

### 1.3 State Automaton Scopes
- The expanded state automaton adds definitions for `ADAPTATION_PENDING`, `ADAPTING`, `COOLDOWN`, and `SAFE_FALLBACK`. Full automated transition algorithms for these states will be fully utilized in Stage 7 (ULC-v4).

---

## 2. Non-Goals

1. **Production Version Bump**: The package version remains `0.1.0.dev0` in compliance with preservation rules.
2. **Trademark Resolution**: DEF-004 remains strictly open for project owner legal counsel.
3. **Phase 17 Authorization**: Phase 17 remains locked.
