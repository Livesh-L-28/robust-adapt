# AdaptiveML — Cross-Pillar Mathematical Contracts and Decoupling Proofs

> **Document Status**: Complete Baseline Deliverable (Phase 6)  
> **Document Identifier**: `DOC-DES-P6-007`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Applied Mathematicians, Core Systems Architects, API Engineers  
> **Cross-Reference**: `DOC-DES-P6-002` through `DOC-DES-P6-006`

---

## 1. Executive Contract Architecture

AdaptiveML enforces a foundational architectural requirement:
> **The algorithmic pillars (ALA, RLA, RAO) must be mathematically self-contained and completely independent.**  
> A practitioner must be able to use any single pillar in isolation without importing or executing code from any other pillar. The Unified Learning Controller (ULC) is strictly an optional orchestration coordinator.

To achieve both **complete modular independence** and **seamless composition when combined**, this document specifies the formal mathematical contracts, tensor interfaces, type invariants, and decoupling proofs governing cross-pillar communication.

```
+─────────────────────────────────────────────────────────────────────────────+
|                          CROSS-PILLAR INTERACTION MATRIX                    |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
| Source \ Dest| ALA          | RLA          | RAO          | ULC (Optional)  |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
| **ALA**      | Self         | None         | None         | Drift Metric    |
|              |              |              |              | Delta_drift     |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
| **RLA**      | Reliability  | Self         | Loss Values  | Mean Window     |
|              | r_i in [0,1] |              | ell_i in R+  | Reliability R_W |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
| **RAO**      | None         | None         | Self         | Memory State &  |
|              |              |              |              | Step Budget     |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
| **ULC**      | Adapt Direct.| Filter Direct| LR Scaling   | Self            |
|              | (Reset/Split)| (Threshold)  | (m_t reset)  |                 |
+──────────────+──────────────+──────────────+──────────────+─────────────────+
```

---

## 2. Shared Mathematical Variables and Boundary Contracts

### 2.1 Contract 1: Sample Reliability Vector ($\mathbf{r}$)

- **Origin**: RLA (`DensityAwareMarginScorer`).
- **Consumers**: ALA (`ReliabilityWeightedADWIN`), ULC (`ArbitrationAutomaton`), RAO (weighted loss).
- **Mathematical Specification**:
  $$\mathbf{r} = [r_1, r_2, \dots, r_B]^\top \in [\epsilon_r, 1.0]^B, \quad \epsilon_r = 10^{-4}$$
- **Preconditions**:
  - $B \in \mathbb{N}^+$ (batch size $\ge 1$).
  - For all $i \in \{1, \dots, B\}$, $r_i$ is finite and non-NaN.
- **Postconditions & Invariants**:
  - Bound invariant: $\epsilon_r \le r_i \le 1.0$.
  - Monotonicity: Higher $r_i$ indicates strictly higher confidence that observed label $y_i$ matches latent true label $y_i^*$.
- **Fallback / Standalone Default (Zero-RLA Mode)**:
  $$\mathbf{r}_{\text{default}} = [1.0, 1.0, \dots, 1.0]^\top \in \mathbb{R}^B$$
  When RLA is absent, ALA functions as standard unweighted streaming algorithms without error.

---

### 2.2 Contract 2: Normalized Class Weights ($\mathbf{w}_{\text{class}}$)

- **Origin**: RLA (`ClassBalancedReweighting`).
- **Consumers**: Model Loss (`GeneralizedCrossEntropy`, `SymmetricCrossEntropy`).
- **Mathematical Specification**:
  $$\mathbf{w}_{\text{class}} = [w_0, w_1, \dots, w_{C-1}]^\top \in \mathbb{R}_{>0}^C$$
- **Preconditions**:
  - $C \ge 2$, observed class counts $\mathbf{n} \in \mathbb{N}_0^C$.
- **Invariants**:
  - Mean normalization invariant:
    $$\frac{1}{C} \sum_{c=0}^{C-1} w_c = 1.0 \pm 10^{-6}$$
  - Positivity invariant: $w_c > 0$ for all $c \in \{0, \dots, C-1\}$.
- **Fallback / Standalone Default (Zero-Imbalance Mode)**:
  $$\mathbf{w}_{\text{default}} = [1.0, 1.0, \dots, 1.0]^\top \in \mathbb{R}^C$$

---

### 2.3 Contract 3: Drift Divergence Metric ($\Delta_{\text{drift}}$)

- **Origin**: ALA (`ReliabilityWeightedADWIN`).
- **Consumers**: ULC (`ArbitrationAutomaton`).
- **Mathematical Specification**:
  $$\Delta_{\text{drift}} = \frac{|\hat{\mu}_{W_0}^{(r)} - \hat{\mu}_{W_1}^{(r)}|}{\epsilon_{\text{cut}}^{(r)} + \epsilon_{\text{div}}} \in [0, \infty)$$
- **Boundary Interpretation**:
  - $\Delta_{\text{drift}} < 0.50$: Stationary stream.
  - $0.50 \le \Delta_{\text{drift}} < 1.00$: Drift suspected (warning).
  - $\Delta_{\text{drift}} \ge 1.00$: Statistically significant drift detected.
- **Fallback / Standalone Default (Zero-ALA Mode)**:
  $$\Delta_{\text{default}} = 0.0$$
  When ALA is absent, ULC assumes stationary conditions unless externally signaled.

---

### 2.4 Contract 4: Parameter & Gradient Tensors ($\boldsymbol{\theta}, \mathbf{g}$)

- **Origin**: Model / User Framework (PyTorch or NumPy autograd).
- **Consumers**: RAO (`LowMemoryAdamW`, `AdaptiveGradientAccumulator`).
- **Mathematical Specification**:
  $$\boldsymbol{\theta} \in \mathbb{R}^p, \quad \mathbf{g} = \nabla_{\boldsymbol{\theta}} \mathcal{L} \in \mathbb{R}^p$$
- **Precision Contracts**:
  - $\boldsymbol{\theta}$ is maintained in IEEE 754 `float32` (or `float64`).
  - $\mathbf{g}$ is supplied in `float32`.
  - Compressed optimizer state $\tilde{\mathbf{m}} \in \text{int8}^p$, $\tilde{\mathbf{v}} \in \text{uint8}^p$.
  - Scales $\mathbf{s}^{(m)}, \mathbf{s}^{(v)} \in \mathbb{R}^{\lceil p / B_q \rceil}$ in `float32`.
- **Numerical Stability Invariant**:
  - Gradient norm clipping: $\|\mathbf{g}\|_2 \le G_{\max}$ enforced prior to quantization to prevent scale explosion.

---

### 2.5 Contract 5: Controller Directive Protocol ($\mathcal{D}$)

- **Origin**: ULC (`ArbitrationAutomaton`).
- **Consumers**: ALA, RLA, RAO engines.
- **Data Structure**:
  $$\mathcal{D} = \left\langle \text{state} \in \mathcal{S}, \; \alpha_{\text{lr}} \in \mathbb{R}_{>0}, \; \theta_{\text{filter}} \in [0, 1], \; \text{flags} \in \{0, 1\}^4 \right\rangle$$
  where:
  - $\text{flags}_0$: `SPLIT_IMMEDIATE` (directive to ALA)
  - $\text{flags}_1$: `PURGE_REPLAY` (directive to ALA)
  - $\text{flags}_2$: `SUPPRESS_ADWIN_RESET` (directive to ALA)
  - $\text{flags}_3$: `RESET_MOMENTUM` (directive to RAO)

---

## 3. Mathematical Decoupling Proofs

### 3.1 Theorem: ALA Independence from RLA and RAO
> **Theorem 5 (ALA Decoupling)**:  
> Let an arbitrary stream $(\mathbf{x}_t, y_t)$ be processed by `VectorizedHoeffdingTree` and `ReliabilityWeightedADWIN` without RLA or RAO.  
> By substituting the identity reliability vector $\mathbf{r} = \mathbf{1}$ into the RW-ADWIN cut bound:
> $$N_{\text{eff}}(W_k) = \frac{(\sum 1)^2}{\sum 1^2} = |W_k|, \quad m_{\text{eff}} = \left( \frac{1}{|W_0|} + \frac{1}{|W_1|} \right)^{-1}$$
> $$\epsilon_{\text{cut}}^{(r)} = \sqrt{\frac{1}{2 m_{\text{eff}}} \ln\left(\frac{4 |W|}{\delta}\right)} \equiv \epsilon_{\text{cut}}^{\text{ADWIN}}$$
> The RW-ADWIN algorithm mathematically collapses to standard Hoeffding-ADWIN with zero degradation in theoretical properties.  
> *Proof Conclusion*: ALA is strictly closed and self-consistent without RLA.

---

### 3.2 Theorem: RLA Independence from ALA and RAO
> **Theorem 6 (RLA Decoupling)**:  
> Let a fixed dataset or batch $(\mathbf{X}, \mathbf{y})$ with corrupted labels be provided to `DensityAwareMarginScorer` and `SymmetricCrossEntropyLoss`.  
> The reliability computation $r_i = \sigma(\alpha \tilde{\mathcal{M}}_i + \gamma \psi(\delta_k(\mathbf{x}_i)))$ and loss $\mathcal{L}_{\text{SCE}}(\mathbf{p}_i, y_i)$ depend strictly on the instantaneous feature matrix $\mathbf{X}$ and logits $\mathbf{z}(\mathbf{X})$.  
> No temporal stream index $t$, sliding window $W$, drift metric $\Delta_{\text{drift}}$, or optimizer state is referenced.  
> *Proof Conclusion*: RLA is strictly closed and self-consistent in standalone batch and mini-batch contexts.

---

### 3.3 Theorem: RAO Independence from ALA and RLA
> **Theorem 7 (RAO Decoupling)**:  
> Let an arbitrary loss $\mathcal{L}(\boldsymbol{\theta})$ generate gradients $\mathbf{g}_t \in \mathbb{R}^p$.  
> The quantization operator $Q(\mathbf{v})$, block scale calculation $s_b$, and parameter update rule in `LowMemoryAdamW` operate exclusively on $\boldsymbol{\theta}$ and $\mathbf{g}_t$.  
> The optimizer treats the objective function as an abstract black-box oracle.  
> *Proof Conclusion*: RAO is strictly closed and functions as a drop-in replacement for standard optimizers across arbitrary neural network architectures.

---

## 4. Invariant Preservation Matrix

| Boundary Invariant | Mathematical Check | Enforcing Module | Failure Remediation |
| :--- | :--- | :--- | :--- |
| **Probability Simplex** | $\sum_c p_{ic} = 1.0, \; p_{ic} \ge 0$ | Model Output / Softmax | Re-normalize: $\mathbf{p} \leftarrow \mathbf{p} / \sum p$ |
| **Reliability Support** | $r_i \in [10^{-4}, 1.0]$ | `DensityAwareMarginScorer` | Numerical clip: $\max(10^{-4}, \min(1.0, r_i))$ |
| **Positive Scale Factor**| $s_b \ge 10^{-12}$ | `LowMemoryAdamW` | Add $\epsilon_{\text{quant}} = 10^{-12}$ |
| **Finite Loss Value** | $\mathcal{L} \in [0, 10^6]$ | Robust Loss Functions | Clip log probabilities at $\ln(\epsilon_{\text{clip}})$ |
| **Dwell Counter Non-Negativity** | $c_{\text{dwell}} \ge 0 \in \mathbb{Z}$ | ULC Automaton | Saturating decrement: $\max(0, c - 1)$ |

