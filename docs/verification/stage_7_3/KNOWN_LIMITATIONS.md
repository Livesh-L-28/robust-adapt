# Known Limitations: ULC-v4.1 Hybrid Controller

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Report Date:** 2026-11-06<br>
**Auditor:** Systems Architecture & Release Engineering Team<br>

---

## 1. Algorithmic & Architectural Limitations

### 1.1. Batch Size Constraints for Spatial Discordance ($n \le k$)
- **Mechanism:** Spatial feature discordance calculates label agreement across $k$ nearest neighbors (default $k=5$).
- **Limitation:** For micro-batches where batch size $n \le k$ (e.g., $n=1$ in pure point-by-point online processing), nearest neighbors cannot be reliably identified.
- **Current Behavior:** The engine defaults safely to $d_{\text{spatial}} = 0.0$ (assuming coherence), which permits adaptation if drift occurs.
- **Recommendation:** Users running point-by-point streams should accumulate sliding buffers of $n \ge 10$ samples before querying spatial discordance.

### 1.2. Pairwise Distance Scaling on Very Large Batches ($O(n^2 \cdot d)$)
- **Mechanism:** `compute_spatial_discordance` uses exact pairwise Euclidean distance broadcasting in NumPy.
- **Performance Profile:** Executes in $< 0.1\text{ms}$ for streaming batch sizes $n \le 100$ and $d \le 64$.
- **Limitation:** For very large batch training ($n > 5,000$), $O(n^2)$ memory and compute will degrade streaming throughput.
- **Recommendation:** Keep streaming micro-batch sizes between $16 \le n \le 256$, or enable reservoir subsampling for massive batches.

### 1.3. Distance Metric Space
- **Current Implementation:** Exclusively supports continuous Euclidean distance.
- **Limitation:** High-dimensional categorical features (one-hot or bag-of-words) or graph embeddings without normalization can exhibit distance concentration phenomena (curse of dimensionality).
- **Recommendation:** Standardize continuous features before passing to the controller.

---

## 2. Operational & Governance Limitations

### 2.1. Library Default Controller Unchanged
- **Status:** In accordance with Workstream D, `UnifiedLearningControllerV4` remains the library default when constructing generic controllers.
- **Promotion Status:** `UnifiedLearningControllerV4_1` is available as a promoted production candidate class and requires explicit owner acceptance before becoming the default controller.

### 2.2. Phase 17 Authorization Locked
- **Status:** Strictly **LOCKED and UNAUTHORIZED**.
- Stage 7.3 provides engineering integration and verification evidence; it does not authorize Phase 17 advancement.

### 2.3. DEF-004 Open Status
- **Status:** Strictly **OPEN and UNRESOLVED**.
- Trademark collision with Datadog's *Adaptive ML, Inc.* is cataloged in the Enterprise Defect Register and requires executive owner legal counsel before release.
