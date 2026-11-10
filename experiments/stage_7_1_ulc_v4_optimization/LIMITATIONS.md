# Stage 7.1 Limitations, Boundaries & Open Research Problems

**Author:** AdaptiveML Research Governance & Systems Architecture Team  
**Scope:** Boundary Conditions, Theoretical Assumptions, and Engineering Constraints of ULC-v4.1  
**Artifact Path:** [LIMITATIONS.md](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/LIMITATIONS.md)  
**Related Components:** [`HybridMasterControllerV4_1`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py), [`SpatialNoiseDiscriminator`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py)

---

## 1. Executive Summary

While the optimized controller [`HybridMasterControllerV4_1`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py) successfully resolves the adaptation deadlock, eliminates false drift resets, and establishes record multi-objective performance ($86.47\%$ accuracy, $62.22\%$ minority recall, $0.7003$ Macro F1), scientific integrity requires a rigorous accounting of its operational boundaries and assumptions.

This document formalizes the theoretical, algorithmic, and practical limitations of the Stage 7.1 optimizations.

---

## 2. Theoretical and Algorithmic Limitations

### 2.1. Metric Space Assumption in Spatial Feature Discordance
The spatial noise discriminator relies on localized $k$-Nearest Neighbors ($k=3$) over batch instances:
$$\mathcal{D}_{\text{spatial}}(B) = \frac{1}{|B|} \sum_{i=1}^{|B|} \frac{1}{k} \sum_{j \in \mathcal{N}_k(x_i)} \mathbf{1}\{y_j \neq y_i\}$$
This formulation assumes that:
1. **Meaningful Metric Space:** The feature space $\mathcal{X} \subseteq \mathbb{R}^D$ admits a meaningful metric (e.g., Euclidean distance) where proximity correlates with label homogeneity under stationary conditions.
2. **Curse of Dimensionality:** In extremely high-dimensional spaces ($D > 1000$), Euclidean distance concentrates ($\frac{D_{\max} - D_{\min}}{D_{\min}} \to 0$), degrading $k$-NN discriminative power unless dimensionality reduction or metric learning is applied.
3. **Categorical and Sparse Features:** For high-cardinality categorical features or sparse text representations (e.g., bag-of-words), Euclidean discordance must be replaced with cosine dissimilarity, Jaccard distance, or embedding-space projections.

### 2.2. Intra-Batch Sample Size Dependency
- In the benchmark stream, batches arrive with $B=30$ instances. Within $30$ instances, $k=3$ neighbors provide reliable localized density estimates.
- **Pure Online Streaming ($B=1$):** If the production pipeline operates strictly in pure single-sample mode ($B=1$), intra-batch spatial discordance cannot be computed directly. It requires maintaining a rolling FIFO sliding window buffer of past feature vectors (e.g., $W=50$ feature-label pairs) to evaluate localized neighborhood discordance for each incoming instance.

### 2.3. Label Noise vs Feature Noise Discrimination
- The spatial discordance metric $\mathcal{D}_{\text{spatial}}$ is tailored to detect **label noise** (random label flips occurring while feature distributions remain geometrically continuous). Under label noise, feature vectors remain clustered, but neighbor labels disagree, elevating $\mathcal{D}_{\text{spatial}} \approx 0.55$.
- **Feature Noise Confounding:** If the stream instead experiences sudden high-variance feature distortion (e.g., sensor failure injecting Gaussian noise $\mathcal{N}(0, \sigma^2)$ into $X$), spatial neighborhoods become diffuse. If feature noise scatters samples across decision boundaries, $\mathcal{D}_{\text{spatial}}$ could rise, potentially confounding feature noise with label noise.

### 2.4. Static Discordance Thresholds
In ULC-v4.1, the gating thresholds are set statically:
- $\tau_{\text{noise\_disc}} = 0.25$
- $\tau_{\text{drift\_disc}} = 0.20$

While these values generalized impeccably across all 8 tested random seeds, streams with overlapping Bayes-optimal class distributions (where intrinsic Bayes error $E_{\text{Bayes}} > 0.25$) would naturally exhibit high spatial discordance even without external noise. In such environments, static thresholds must be replaced with adaptive online baseline tracking:
$$\tau_{\text{dynamic}} = \bar{\mathcal{D}}_{\text{baseline}} + 3 \cdot \sigma_{\mathcal{D}}$$

---

## 3. Engineering and System Boundaries

### 3.1. Memory and Time Trade-off
- Computing pairwise distances takes $O(B^2 D)$ operations. For $B=30, D=4$, this requires $< 0.2\text{ ms}$.
- If batch size expands to $B=5,000$, $B^2 = 25,000,000$ operations, which would introduce tens of milliseconds of latency unless approximate nearest neighbor structures ($k$-d trees, HNSW) or sub-sampling is employed.

### 3.2. Coupling with Classifier Internal States
- ULC-v4.1 relies on the classifier providing meaningful probability estimates or logits margin.
- While the spatial discriminator liberates the controller from relying solely on classifier margin during abrupt drift, downstream threshold adaptation still assumes calibrated relative class probabilities.

---

## 4. Governance and Project Scope Boundaries

1. **Experimental Isolation:** All implementations of Candidates 1–7 and `HybridMasterControllerV4_1` reside strictly within `experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py`.
2. **Production Integrity:** The production package in `adaptive_ml/` has not been altered during Stage 7.1. All existing 110 unit and integration tests remain pristine and passing.
3. **DEF-004 Status:** The trademark and package naming issue (DEF-004) remains **STRICTLY OPEN AND UNRESOLVED**. No branding changes have been authorized.
4. **Phase 17 Status:** Phase 17 of the authoritative 22-phase roadmap remains **STRICTLY LOCKED AND UNAUTHORIZED**.
5. **No Release Authorization:** No git commits, tags, package versions, or PyPI distributions are authorized or generated.

