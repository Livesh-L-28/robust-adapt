# AdaptiveML — Phase 9: RLA Known Limitations

> **Document Status**: Complete Implementation Deliverable (Phase 9)  
> **Document Identifier**: `DOC-IMP-P9-006`  
> **Last Updated**: 2026-11-01

---

## 1. Documented Technical Limitations

1. **Quadratic Batch Distance Complexity**:
   `DensityAwareMarginScorer` computes pairwise Euclidean distances within the mini-batch ($\mathcal{O}(B^2 \cdot d)$). For large batches ($B > 2048$), approximate nearest neighbor indexing (e.g. ScaNN/HNSW) or sliding historical feature reservoirs will be investigated in Phase 14.
2. **Extreme Class Imbalance Convergence Rate**:
   While `ClassBalancedWeights` corrects gradient starvation on rare classes, optimizing extremely long-tailed distributions ($> 1:500$) on non-convex deep models may still require higher warmup step budgets.
