# AdaptiveML — Phase 8: ALA Known Limitations & Boundary Constraints

> **Document Status**: Complete Implementation Deliverable (Phase 8)  
> **Document Identifier**: `DOC-IMP-P8-004`  
> **Last Updated**: 2026-11-01

---

## 1. Documented Technical Limitations

1. **Initial Quantile Bin Discretization**:
   `VectorizedHoeffdingTree` initializes continuous feature quantile edges (`bin_edges`) on the first observed batch. If subsequent stream distributions expand significantly beyond the min/max range of the initial batch, outlier features are clipped to the outer bins ($0$ or $K-1$). Dynamic online quantile sketches (e.g. t-digest) are deferred to Phase 21 R&D.
2. **Symmetric Feature Tie-Breaking**:
   When multiple continuous features provide mathematically identical split gains (e.g. perfectly symmetric synthetic clusters), $\Delta \bar{G} = 0$. In such cases, the tree relies strictly on $\epsilon_H < \tau_{\text{tie}}$ to trigger a split. Setting $\tau_{\text{tie}} \in [0.05, 0.10]$ is recommended for synthetic benchmarks.
3. **Replay Buffer Sample Eviction**:
   `ClassBalancedReservoirReplay` guarantees uniform random selection within each class bucket. It does not prioritize hard or high-loss examples; importance-weighted replay is scheduled for future exploration in Phase 12.
