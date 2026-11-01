# Phase 12 Decisions & Architecture Adjustments

**Document ID:** `DOC-RES-P12-011`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Architecture Decision Records Grounded in Empirical Data

### DEC-P12-001: Retain 8-bit Block Quantization in Core Library
- **Context**: Evaluated whether $8\text{-bit}$ block quantization in `LowMemoryAdamW` should remain a permanent core feature or be deferred.
- **Decision**: **Retained as Core**. Empirical data confirmed a deterministic $73.44\%$ state RAM reduction across all parameter dimensions ($2.125\text{ B/param}$ vs $8.00\text{ B/param}$) with guaranteed convergence.

### DEC-P12-002: Mandate Density Penalty Moderation ($\gamma > 0$) for Imbalanced Streams
- **Context**: In ablation tests, disabling density penalty moderation ($\gamma = 0.0$) caused rare classes to be purged under label cleansing heuristics.
- **Decision**: **Adopted**. Default $\gamma = 0.5 - 0.8$ will be enforced across all high-level RLA and ULC pipelines to guarantee Theorem 2 minority preservation.

### DEC-P12-003: Dual-Evidence Gating in ULC Automaton
- **Context**: Uncoordinated drift detection suffered 10 catastrophic model wipes under an 85% label noise burst.
- **Decision**: **Adopted**. ULC arbitration automaton with hysteresis deadband $\Delta_{\text{hyst}} = 0.15$ and recovery dwell counter is approved as the production arbitration model.

