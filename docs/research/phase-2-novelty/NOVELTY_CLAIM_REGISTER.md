# AdaptiveML — Phase 2: Novelty Claim Register

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-008`  
> **Last Updated**: 2026-11-01  
> **Epistemic Standard**: Strict Prior-Art Verification (Research Governance Rule 3)

---

## 1. Classification Categories for Proposed Directions

To prevent inflated marketing claims, every technical direction proposed for AdaptiveML is assigned one of five strict classifications:
1. **Established Prior Art**: Fully published and implemented in existing libraries. (Zero novelty claimed).
2. **Implementation / DX Improvement**: Re-engineering an established method for faster throughput or cleaner APIs. (No algorithmic novelty claimed).
3. **Adaptation of Existing Method**: Modifying an established technique to operate under new constraints (e.g. streaming or CPU).
4. **Underexplored Combination**: Synthesizing two previously isolated mathematical concepts to solve an intersectional failure mode.
5. **Potential Research Contribution**: A novel algorithmic formulation addressing an unresolved problem, requiring formal mathematical derivation in Phase 6 and empirical validation in Phase 12.

---

## 2. Technical Direction Novelty Audit

### Direction 1: Streaming Concept Drift Detection via Statistical Windowing (ALA)
- **Technical Problem**: Detecting distribution changes in live streaming features.
- **Closest Existing Method**: ADWIN (Bifet & Gavaldà, 2007).
- **Closest Existing Implementation**: `river.drift.ADWIN`, `menelaus.concept_drift.ADWIN`.
- **Mechanism Comparison**: Compares running means of exponentially sized sub-windows using Hoeffding's bound.
- **Novelty Classification**: **ESTABLISHED PRIOR ART**.
- **Assessment**: The core algorithm is public domain mathematics. AdaptiveML claims **zero algorithmic novelty**.

---

### Direction 2: Vectorized 2D NumPy Streaming Estimator Interface (ALA)
- **Technical Problem**: Python interpreter loop bottlenecks when streaming large numeric matrices through dictionary-based estimators (`learn_one(dict)`).
- **Closest Existing Implementation**: River's `learn_one` and `learn_many` (Pandas-based).
- **Mechanism Comparison**: Replaces single-instance dict unpacking with contiguous 2D NumPy array block processing (`partial_fit(X: np.ndarray, y: np.ndarray)`).
- **Novelty Classification**: **IMPLEMENTATION / DX IMPROVEMENT**.
- **Assessment**: No mathematical novelty. It is an engineering and API design improvement delivering higher computational throughput.

---

### Direction 3: In-Training Bounded Symmetric Loss Functions (RLA)
- **Technical Problem**: Neural network and linear model overfitting to corrupted or noisy labels.
- **Closest Existing Method**: Generalized Cross Entropy (Zhang & Sabuncu, 2018), Symmetric Cross Entropy (Wang et al., 2019).
- **Closest Existing Implementation**: Academic PyTorch research scripts.
- **Mechanism Comparison**: Combining forward cross-entropy with reverse cross-entropy to bound gradient magnitude on high-loss corruptions.
- **Novelty Classification**: **ESTABLISHED PRIOR ART / ADAPTATION**.
- **Assessment**: The mathematical formulations of GCE and SCE are published prior art. AdaptiveML provides a clean-room, modular implementation compatible with both PyTorch and scikit-learn. No algorithmic novelty is claimed for standard GCE/SCE.

---

### Direction 4: Density-Aware Minority-Preserving Sample Reliability Scoring (RLA)
- **Technical Problem**: Traditional small-loss noise filters (Confident Learning, MentorNet) mistakenly classify hard, low-frequency minority-class samples as "label noise", pruning legitimate tail patterns.
- **Closest Existing Method**: Confident Learning (Northcutt et al., 2021) and Class-Balanced Loss (Cui et al., 2019).
- **Closest Existing Implementation**: `cleanlab.filter.find_label_issues`.
- **Mechanism Comparison**: Rather than using pure loss or probability thresholds, the proposed method normalizes sample margin confidence by local feature-space density:
  $$\text{Reliability}(x_i, y_i) = \sigma\left( \frac{\mathcal{M}(x_i, y_i)}{\rho_k(x_i) + \epsilon} \right)$$
  where $\rho_k(x_i)$ is a local $k$-nearest neighbor density estimator. Samples with high loss in sparse regions are recognized as rare clean instances rather than noise.
- **Novelty Classification**: **POTENTIAL RESEARCH CONTRIBUTION**.
- **Uncertainty & Validation Gate**: Requires closed-form derivation in Phase 6 and empirical benchmarking against Cleanlab on imbalanced noisy datasets in Phase 12.

---

### Direction 5: Pure Python/NumPy Block-Quantized Optimizer State (RAO)
- **Technical Problem**: Standard AdamW consumes $8\text{ bytes per parameter}$ in state memory; existing 8-bit optimizers (bitsandbytes) fail to install on CPUs lacking AVX-512 or on non-CUDA platforms.
- **Closest Existing Method**: 8-bit block-wise quantization (Dettmers et al., 2022).
- **Closest Existing Implementation**: `bitsandbytes.optim.AdamW8bit`.
- **Mechanism Comparison**: Dettmers uses non-linear quantile codebooks on GPU CUDA kernels. The proposed direction uses block-wise linear dynamic scaling ($B=256$ or $2048$) with symmetric integer representation implemented strictly in vector NumPy / PyTorch tensor ops without compiled C++ libraries.
- **Novelty Classification**: **ADAPTATION / IMPLEMENTATION IMPROVEMENT**.
- **Assessment**: The conceptual premise of block-wise scaling is established. The contribution is engineering accessibility: providing a universal, zero-compilation optimizer that runs universally on any standard CPU.

---

### Direction 6: Dual-Evidence Drift-Noise Arbitration Automaton (ULC)
- **Technical Problem**: In streaming pipelines, transient label noise triggers false-positive drift alarms in ADWIN, prompting catastrophic model retraining on corrupted batches.
- **Closest Existing Systems**: Uncoordinated combinations of River + custom heuristic scripts; MLOps pipeline orchestrators (ZenML, Prefect).
- **Mechanism Comparison**: An in-loop finite state automaton that gates ALA drift triggers with RLA sample reliability distributions:
  $$\text{State Update} = \mathcal{T}(\text{Drift Alert}, \mathbb{E}[\text{Reliability}], \mathcal{M}_{\text{RAM}})$$
  If an error spike is driven by low-reliability samples, drift reset is suppressed, gradient step is attenuated, and replay memory is preserved.
- **Novelty Classification**: **UNDEREXPLORED COMBINATION / POTENTIAL RESEARCH CONTRIBUTION**.
- **Uncertainty & Validation Gate**: Must be mathematically formalized as a provably stable state machine in Phase 6 and benchmarked against uncoordinated pipelines in Phase 12.

---

## 3. Summary of Novelty Register

| Direction | Focus Pillar | Primary Prior Art | Classification | Target Validation Phase |
| :--- | :--- | :--- | :--- | :---: |
| 1. ADWIN / DDM Drift Detectors | ALA | Bifet & Gavalda (2007) | **Established Prior Art** | Phase 8 (Baseline) |
| 2. Vectorized 2D NumPy `partial_fit` | ALA | River / scikit-learn | **Implementation / DX** | Phase 8 (Benchmark) |
| 3. GCE / SCE Robust Losses | RLA | Zhang (2018), Wang (2019) | **Established Prior Art** | Phase 9 (Baseline) |
| 4. Density-Aware Reliability Scorer | RLA | Northcutt (2021), Cui (2019) | **Potential Research Contribution** | Phase 6 & Phase 12 |
| 5. Zero-Compilation CPU Low-Memory AdamW | RAO | Dettmers et al. (2022) | **Adaptation / Implementation** | Phase 10 & Phase 12 |
| 6. Drift-Noise Arbitration Automaton | ULC | ZenML / Stream mining lit | **Potential Research Contribution** | Phase 6 & Phase 12 |
