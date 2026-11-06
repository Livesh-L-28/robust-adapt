# Stage 7 Limitations & Operational Boundaries
## ULC-v4 System Boundaries

**Document Identifier:** `VERIF-STAGE-7-006`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Target Package:** [`adaptive_ml/ulc/`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/)<br>

---

## 1. Operational Boundaries

1. **Step Execution Overhead:**
   - Unified evidence synthesis, multi-detector aggregation, and explainability text generation add \(\sim 2.5\text{--}4.5\,\text{ms}\) overhead per step relative to bare Hoeffding trees.
   - For ultra-high throughput applications (\(> 50,000\) samples/sec), developers should evaluate ULC at batch level rather than per-instance level, or use `skip_expensive_ops=True`.
2. **Concept Signature Dimensionality:**
   - Gaussian similarity matching in [`ConceptMemory`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/concept_memory.py) scales linearly with feature dimensionality \(O(D)\).
   - In extremely high-dimensional spaces (\(D > 10,000\)), random projections or PCA embedding extraction should precede concept storage.
3. **Delayed Label Queue Buffer Sizing:**
   - If stream delay exceeds `queue_capacity` (default 5,000 samples), unverified predictions are pruned. Sizing should reflect expected production latency.
4. **Hysteresis Threshold Tuning:**
   - Transitioning between `WARNING` and `STABLE` requires observing the \(\pm 0.15\) hysteresis band to prevent rapid thrashing under noisy stream fluctuations.

---

## 2. Recommended Operating Regimes

| Constraint Dimension | Recommended Range | Critical Ceiling |
| :--- | :--- | :--- |
| **Stream Batch Size** | 16 – 256 samples | 1024 samples |
| **Feature Dimensionality** | 2 – 500 dense features | 5,000 features |
| **Class Count** | 2 – 50 classes | 500 classes |
| **Concept Memory Size** | 5 – 20 distinct concepts | 100 concepts |
| **Peak Latency Budget** | 10.0 ms / step | 50.0 ms / step |
