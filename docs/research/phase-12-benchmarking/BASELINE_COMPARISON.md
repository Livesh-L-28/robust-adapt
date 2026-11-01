# Baseline Comparison & Trade-Off Analysis

**Document ID:** `DOC-RES-P12-007`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Objective Assessment of Performance & Trade-Offs

In accordance with Section 12.1 of the Project Charter, AdaptiveML maintains scientific honesty regarding where its algorithms excel, where they perform comparably to prior art, and where performance trade-offs exist:

### 1.1 Where AdaptiveML Excels
1. **Extreme Class Imbalance under Noise**:
   Standard Cross-Entropy suffered a complete wipeout ($0.0\%$ recall) on the 100:1 rare class. AdaptiveML preserved $60.0\%$ recall by virtue of Theorem 2 density moderation.
2. **Optimizer State RAM**:
   `LowMemoryAdamW` provides a deterministic $73.44\%$ reduction in state memory across all parameter dimensions ($2.125\text{ B/param}$ vs $8.00\text{ B/param}$).
3. **Catastrophic Forgetting Suppression**:
   In multi-regime streaming with noise bursts, ULC completely prevented the 10 false model wipes suffered by uncoordinated drift detectors.

### 1.2 Where AdaptiveML Performs Comparably
1. **Stationary Clean Streaming**:
   On stationary streams without drift, `AdaptiveClassifier` achieves comparable accuracy to standard static Hoeffding Trees ($76.52\%$).
2. **Standard Symmetric Label Noise**:
   At moderate noise rates ($20\% - 40\%$) on well-separated synthetic clusters, both standard Cross-Entropy and Symmetric Cross-Entropy achieve near $100\%$ accuracy after multiple epochs.

### 1.3 Trade-Offs & Overhead
1. **CPU Step Latency in Block Quantization**:
   While `LowMemoryAdamW` saves $73.44\%$ RAM, pure Python/NumPy block quantization incurs a per-step latency of $\sim 3.2\text{ ms}$ per 10k parameters. On small models ($P < 1,000$), standard FP32 AdamW is faster.
2. **Nearest-Neighbor Computation in High Dimensions**:
   `DensityAwareMarginScorer` requires pairwise distance estimation to compute local density $\rho_k$, adding $O(B^2 D)$ compute overhead per batch.

