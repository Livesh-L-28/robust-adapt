# ULC-v5: Known Limitations & Failure Modes

---

## 1. Single Continuous Observation Streams

- **Behavior**: ULC-v5 is designed for single-stream prequential processing. Distributing a single `UnifiedLearningControllerV5` instance across multiple independent uncoordinated threads without synchronization is unsupported.
- **Guidance**: In multi-tenant systems, instantiate a separate `UnifiedLearningControllerV5` per stream partition or tenant.

## 2. Micro-Batches Smaller Than 1 Sample

- **Behavior**: Ingesting empty batches ($N=0$) raises a `ValidationError`. Single-sample processing ($N=1$) is supported.
- **Recommendation**: Ensure input buffers provide at least one sample ($N \ge 1$) per step.

## 3. Irreversible Catastrophic Hard Reset

- **Behavior**: Tier 4 (`TIER_4_HARD_RESET`) purges the active tree model, internal counters, and experience replay buffer. It is an emergency fallback intended strictly for unrecoverable distribution collapse.
- **Protection**: ULC-v5 requires confidence $\ge 0.95$, drift magnitude $> 0.85$, and at least 2 consecutive failed prior interventions before unlocking Tier 4.
