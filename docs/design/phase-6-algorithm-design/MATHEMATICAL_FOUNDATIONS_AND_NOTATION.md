# AdaptiveML — Mathematical Foundations and Unified Notation

> **Document Status**: Complete Baseline Deliverable (Phase 6)  
> **Document Identifier**: `DOC-DES-P6-002`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Research Scientists, Applied Mathematicians, Core Algorithmic Engineers  
> **Cross-Reference**: `DOC-DES-P6-001` (Algorithm Design Document)

---

## 1. Executive Summary & Purpose

This document establishes the formal mathematical language, coordinate spaces, probability spaces, and algebraic conventions governing all algorithmic pillars within the **AdaptiveML** framework:
- **ALA**: Adaptive Learning Algorithms (concept drift detection, online stream adaptation, bounded replay)
- **RLA**: Robust Learning Algorithms (sample reliability, label corruption, robust loss formulation, class imbalance)
- **RAO**: Resource-Aware Optimization (memory-bounded optimization, block quantization, gradient accumulation)
- **ULC**: Unified Learning Controller (dual-evidence drift-noise arbitration automaton)

Every equation, proof, pseudocode listing, and software contract in Phases 6 through 11 strictly adheres to the definitions, bounds, and indexing conventions formalized herein.

---

## 2. Global Mathematical Notation

### 2.1 Typography & Symbol Taxonomy

| Symbol Class | Typographic Convention | Example | Meaning / Context |
| :--- | :--- | :--- | :--- |
| **Scalars** | Lowercase italic Roman or Greek | $s, \alpha, \lambda, \epsilon, \beta$ | Hyperparameters, loss values, learning rates |
| **Integers / Counts** | Lowercase italic Roman ($i, j, k, t, n, p$) | $t, n, d, C, B$ | Stream step $t$, batch size $B$, dimension $d$, classes $C$ |
| **Vectors** | Lowercase bold Roman or Greek | $\mathbf{x}, \mathbf{y}, \mathbf{g}, \boldsymbol{\theta}, \mathbf{m}$ | Instances $\mathbf{x} \in \mathbb{R}^d$, parameters $\boldsymbol{\theta} \in \mathbb{R}^p$ |
| **Matrices** | Uppercase bold Roman | $\mathbf{X}, \mathbf{W}, \mathbf{T}, \mathbf{H}$ | Mini-batch matrix $\mathbf{X} \in \mathbb{R}^{B \times d}$, transition matrix $\mathbf{T}$ |
| **Tensors** | Bold script or sans-serif uppercase | $\mathbf{\mathcal{T}}, \mathbf{\Theta}$ | Multi-dimensional weight tensors |
| **Sets / Domains** | Calligraphic or blackboard uppercase | $\mathcal{X}, \mathcal{Y}, \mathbb{R}, \mathbb{N}, \mathcal{S}$ | Feature space $\mathcal{X}$, label space $\mathcal{Y}$, state set $\mathcal{S}$ |
| **Probability Measures** | Uppercase Roman ($P, \mathbb{P}, \mathbb{E}, \mathbb{V}$) | $\mathbb{P}(A), \mathbb{E}_{X}[f(X)]$ | Probability, mathematical expectation, variance |
| **Estimators / Predictions**| Hat notation | $\hat{y}, \hat{\mathbf{y}}, \hat{\mu}, \hat{\boldsymbol{\theta}}$ | Class prediction $\hat{y}$, estimated mean $\hat{\mu}$ |
| **Noisy / Corrupted Variables** | Tilde notation | $\tilde{y}, \tilde{\mathbf{y}}, \tilde{\mathbf{g}}$ | Corrupted label $\tilde{y}$, quantized gradient $\tilde{\mathbf{g}}$ |
| **Optimal / Ground Truth** | Star notation | $y^*, \mathbf{y}^*, \boldsymbol{\theta}^*$ | True uncorrupted label $y^*$, optimal parameter $\boldsymbol{\theta}^*$ |

---

### 2.2 Vector and Matrix Operations

For vectors $\mathbf{u}, \mathbf{v} \in \mathbb{R}^d$ and matrix $\mathbf{A} \in \mathbb{R}^{m \times n}$:
- **Inner Product**: $\langle \mathbf{u}, \mathbf{v} \rangle = \mathbf{u}^\top \mathbf{v} = \sum_{i=1}^d u_i v_i$
- **Hadamard (Element-Wise) Product**: $\mathbf{u} \odot \mathbf{v} = [u_1 v_1, u_2 v_2, \dots, u_d v_d]^\top$
- **Hadamard Division**: $\frac{\mathbf{u}}{\mathbf{v}} = [u_1 / v_1, \dots, u_d / v_d]^\top$ (subject to $v_i \ne 0$)
- **Element-Wise Power**: $\mathbf{u}^p = [u_1^p, u_2^p, \dots, u_d^p]^\top$
- **Euclidean ($L_2$) Norm**: $\|\mathbf{u}\|_2 = \sqrt{\sum_{i=1}^d u_i^2}$
- **Manhattan ($L_1$) Norm**: $\|\mathbf{u}\|_1 = \sum_{i=1}^d |u_i|$
- **Infinity ($L_\infty$) Norm**: $\|\mathbf{u}\|_\infty = \max_{1 \le i \le d} |u_i|$
- **Frobenius Norm**: $\|\mathbf{A}\|_F = \sqrt{\sum_{i=1}^m \sum_{j=1}^n A_{ij}^2}$
- **Standard Probability Simplex**: $\Delta^{C-1} = \left\{ \mathbf{p} \in \mathbb{R}^C \;\middle|\; p_c \ge 0, \; \sum_{c=1}^C p_c = 1 \right\}$

---

## 3. Spaces, Domains, and Data Streams

### 3.1 Feature Space and Label Space

- **Feature Space**: $\mathcal{X} \subseteq \mathbb{R}^d$, compact metric space equipped with metric $D_{\mathcal{X}}(\mathbf{x}_i, \mathbf{x}_j) = \|\mathbf{x}_i - \mathbf{x}_j\|_2$.
- **Discrete Classification Space**: $\mathcal{Y} = \{0, 1, \dots, C-1\}$, with cardinal size $|\mathcal{Y}| = C \ge 2$.
- **Continuous Regression Space**: $\mathcal{Y} \subseteq \mathbb{R}$ or $\mathcal{Y} \subseteq \mathbb{R}^m$.
- **One-Hot Label Encoding**: Function $\mathbf{e}: \mathcal{Y} \to \Delta^{C-1}$ where $\mathbf{e}(y)_c = \mathbb{I}(y = c)$, $\mathbb{I}$ being the indicator function.
- **Hypothesis Space**: Class of parameter-indexed functions $\mathcal{H} = \{ f_{\boldsymbol{\theta}}: \mathcal{X} \to \Delta^{C-1} \mid \boldsymbol{\theta} \in \Theta \subseteq \mathbb{R}^p \}$. For an input $\mathbf{x}$, model output is $\hat{\mathbf{p}} = f_{\boldsymbol{\theta}}(\mathbf{x})$, with predicted class $\hat{y} = \arg\max_{c \in \mathcal{Y}} \hat{p}_c$.

---

### 3.2 Streaming Process and Time Horizon

Data arrives sequentially as a stochastic process over discrete time steps $t \in \mathbb{N}^+ = \{1, 2, 3, \dots\}$:
- **Instantaneous Observation**: $\mathbf{z}_t = (\mathbf{x}_t, y_t) \in \mathcal{Z} = \mathcal{X} \times \mathcal{Y}$.
- **Mini-Batch of Size $B$**: $\mathbf{Z}_\tau = \{ (\mathbf{x}_{\tau, b}, y_{\tau, b}) \}_{b=1}^B \in \mathcal{Z}^B$, where $\tau = \lfloor (t-1)/B \rfloor + 1$ indexes mini-batches.
- **Sliding History Window of Length $W$**: $\mathcal{W}_t = (\mathbf{z}_{t-W+1}, \dots, \mathbf{z}_t) \in \mathcal{Z}^W$.
- **Filtration**: $\mathcal{F}_t = \sigma(\mathbf{z}_1, \dots, \mathbf{z}_t)$ denotes the sigma-algebra representing information observable up to time $t$.

---

## 4. Formal Drift and Non-Stationarity Formulations

### 4.1 Joint Distribution Decomposition

At any time step $t$, the observation $\mathbf{z}_t = (\mathbf{x}_t, y_t)$ is drawn from an underlying joint probability measure $P_t(\mathbf{x}, y)$ defined over the measurable space $(\mathcal{X} \times \mathcal{Y}, \mathcal{B}(\mathcal{X}) \otimes 2^{\mathcal{Y}})$:
$$P_t(\mathbf{x}, y) = P_t(\mathbf{x}) \cdot P_t(y \mid \mathbf{x}) = P_t(y) \cdot P_t(\mathbf{x} \mid y)$$

### 4.2 Mathematical Taxonomy of Drift

1. **Strict Concept Drift**:
   $$\exists \, t_1, t_2 \in \mathbb{N}^+, \; t_1 \ne t_2 \quad \text{such that} \quad P_{t_1}(\mathbf{x}, y) \ne P_{t_2}(\mathbf{x}, y)$$

2. **Real Concept Drift (Posterior Shift)**:
   $$\exists \, \mathbf{x} \in \mathcal{X} \quad \text{such that} \quad P_{t_1}(y \mid \mathbf{x}) \ne P_{t_2}(y \mid \mathbf{x})$$
   Directly impacts optimal decision boundary $\arg\max_y P_t(y \mid \mathbf{x})$ and mandates model parameter adaptation.

3. **Virtual Drift (Covariate Shift)**:
   $$P_{t_1}(\mathbf{x}) \ne P_{t_2}(\mathbf{x}) \quad \text{while} \quad P_{t_1}(y \mid \mathbf{x}) = P_{t_2}(y \mid \mathbf{x}) \quad \forall \mathbf{x} \in \mathcal{X}$$
   The marginal distribution of inputs shifts, but the conditional posterior remains invariant.

4. **Class Prior Drift (Prior Shift)**:
   $$P_{t_1}(y) \ne P_{t_2}(y) \quad \text{while} \quad P_{t_1}(\mathbf{x} \mid y) = P_{t_2}(\mathbf{x} \mid y) \quad \forall y \in \mathcal{Y}$$

5. **Drift Velocity and Acceleration**:
   - Total Variation Drift Metric: $d_{TV}(P_{t_1}, P_{t_2}) = \sup_{A \in \mathcal{B}(\mathcal{X} \times \mathcal{Y})} |P_{t_1}(A) - P_{t_2}(A)|$.
   - Drift Velocity: $v(t) = \lim_{\Delta t \to 0} \frac{d_{TV}(P_t, P_{t+\Delta t})}{\Delta t}$.
   - Abrupt Drift: $v(t) \to \infty$ for isolated $t \in \{t^*\}$, where $P_{t^*-1} \ne P_{t^*}$.
   - Gradual Drift: $0 < v(t) < v_{\max} < \infty$ sustained over an interval $[t_a, t_b]$.

---

## 5. Formal Data Imperfection and Label Corruption Models

### 5.1 Latent Ground Truth and Observed Noisy Labels

Let $(\mathbf{x}_i, y_i^*)$ represent the uncorrupted instance with latent true label $y_i^* \in \mathcal{Y}$.  
The learner observes $(\mathbf{x}_i, \tilde{y}_i)$, where $\tilde{y}_i \in \mathcal{Y}$ is the observed label potentially corrupted by a stochastic transition channel.

### 5.2 Transition Matrices and Noise Regimes

1. **Transition Probability Matrix $\mathbf{T}(\mathbf{x}) \in \mathbb{R}^{C \times C}$**:
   $$T_{jk}(\mathbf{x}) = \mathbb{P}(\tilde{y} = k \mid y^* = j, \mathbf{X} = \mathbf{x})$$
   where $\sum_{k=0}^{C-1} T_{jk}(\mathbf{x}) = 1$ for all $j \in \mathcal{Y}$, $\mathbf{x} \in \mathcal{X}$.

2. **Uniform Symmetric Noise**:
   $$T_{jk} = \begin{cases} 1 - \eta, & j = k \\ \frac{\eta}{C - 1}, & j \ne k \end{cases}$$
   where $\eta \in [0, \frac{C-1}{C})$ is the overall corruption rate.

3. **Class-Conditional Asymmetric Noise**:
   $$T_{jk}(\mathbf{x}) = T_{jk} \quad \text{(independent of } \mathbf{x} \text{, but class-dependent)}$$

4. **Instance-Dependent (Feature-Dependent) Noise**:
   $$T_{jk}(\mathbf{x}) = \sigma\left(\mathbf{w}_{jk}^\top \phi(\mathbf{x})\right)$$
   where noise probability increases in regions of high feature ambiguity or low margin.

---

## 6. Optimization, Gradients, and Resource Constraints

### 6.1 Objective Functions and Empiric Risk

Given parameterized model $f_{\boldsymbol{\theta}}$ and loss function $\mathcal{L}: \Delta^{C-1} \times \mathcal{Y} \to \mathbb{R}_{\ge 0}$:
- **True Risk**: $R(\boldsymbol{\theta}) = \mathbb{E}_{(\mathbf{x}, y^*) \sim \mathcal{D}} [\mathcal{L}(f_{\boldsymbol{\theta}}(\mathbf{x}), y^*)]$
- **Observed Empirical Risk**: $\hat{R}_N(\boldsymbol{\theta}) = \frac{1}{N} \sum_{i=1}^N \mathcal{L}(f_{\boldsymbol{\theta}}(\mathbf{x}_i), \tilde{y}_i)$
- **Instance Loss**: $\ell_i(\boldsymbol{\theta}) = \mathcal{L}(f_{\boldsymbol{\theta}}(\mathbf{x}_i), \tilde{y}_i)$
- **Instantaneous Gradient**: $\mathbf{g}_t(\boldsymbol{\theta}) = \nabla_{\boldsymbol{\theta}} \ell_t(\boldsymbol{\theta}) \in \mathbb{R}^p$
- **Mini-Batch Gradient**: $\mathbf{g}_\tau(\boldsymbol{\theta}) = \frac{1}{B} \sum_{b=1}^B \nabla_{\boldsymbol{\theta}} \ell_{\tau, b}(\boldsymbol{\theta})$

### 6.2 Resource Constraints and State Budgets

- **Parameter Dimension**: $p = \dim(\boldsymbol{\theta}) \in \mathbb{N}^+$.
- **Host RAM Budget**: $M_{\text{RAM}} \le M_{\max}$ bytes.
- **Peak Working Memory**: $M_{\text{peak}} = \sup_t \text{MemoryUsage}(t) \le M_{\max}$.
- **Optimizer State Footprint**:
  - Uncompressed FP32 AdamW: $S_{\text{Adam}} = p \cdot (4_{\text{param}} + 4_{\text{grad}} + 4_{m_t} + 4_{v_t}) = 16p$ bytes.
  - Compressed 8-Bit AdamW: $S_{\text{Quant}} = p \cdot (4_{\text{param}} + 4_{\text{grad}} + 1_{m_t} + 1_{v_t}) + 2 \cdot \frac{p}{B_q} \cdot 4_{\text{scales}} = 10p + \mathcal{O}(p/B_q)$ bytes.
- **Compute Budget**: Maximum allowable floating-point operations per sample: $C_{\text{sample}} \le \kappa_{\text{FLOP}}$.

---

## 7. Pillar-Specific Formal Definitions

### 7.1 ALA: Adaptive Learning Foundations

- **Hoeffding Bound for Stream Split**:
  For an attribute evaluation metric $G \in [0, 1]$ computed over $n$ independent observations, the true mean $\mathbb{E}[G]$ lies within $[\hat{G} - \epsilon_H, \hat{G} + \epsilon_H]$ with probability at least $1 - \delta$, where:
  $$\epsilon_H = \sqrt{\frac{R_G^2 \ln(1 / \delta)}{2n}}$$
  where $R_G = \ln(C)$ for Information Gain and $R_G = 1$ for Gini Impurity.

- **ADWIN Window Invariant**:
  Given a sliding window $W$ partitioned into sub-windows $W_0$ and $W_1$ ($W = W_0 \cdot W_1$), a drift event is detected whenever:
  $$|\hat{\mu}_{W_0} - \hat{\mu}_{W_1}| \ge \epsilon_{\text{cut}}$$
  $$\epsilon_{\text{cut}} = \sqrt{\frac{1}{2m} \ln\left(\frac{4 |W|}{\delta}\right)}, \quad m = \left(\frac{1}{|W_0|} + \frac{1}{|W_1|}\right)^{-1}$$

### 7.2 RLA: Robust Learning Foundations

- **Margin Definition**:
  For model logits $\mathbf{z}(\mathbf{x}) \in \mathbb{R}^C$ and given label $y \in \mathcal{Y}$:
  $$\mathcal{M}(\mathbf{x}, y) = z_y(\mathbf{x}) - \max_{j \ne y} z_j(\mathbf{x})$$

- **Local Feature Density ($\rho_k$)**:
  Let $\mathcal{N}_k(\mathbf{x})$ denote the set of $k$-nearest neighbors of $\mathbf{x}$ in feature space $\mathcal{X}$:
  $$\rho_k(\mathbf{x}) = \left( \frac{1}{k} \sum_{\mathbf{x}' \in \mathcal{N}_k(\mathbf{x})} \|\mathbf{x} - \mathbf{x}'\|_2 \right)^{-1}$$

- **Class-Balanced Effective Number of Samples**:
  Given class sample count $n_y$, the effective number of samples $E_{n_y}$ under uniform random volume overlap parameter $\beta \in [0, 1)$ is:
  $$E_{n_y} = \frac{1 - \beta^{n_y}}{1 - \beta}$$

### 7.3 RAO: Resource-Aware Foundations

- **Block Quantization Operator**:
  For a vector slice $\mathbf{v} \in \mathbb{R}^{B_q}$ with block size $B_q$:
  $$\text{scale}(\mathbf{v}) = \frac{\max_{i} |v_i|}{q_{\max}} + \epsilon_{\text{quant}}$$
  $$Q(\mathbf{v}) = \text{clip}\left( \left\lfloor \frac{\mathbf{v}}{\text{scale}(\mathbf{v})} \right\rceil, -q_{\max}, q_{\max} \right) \in \mathbb{Z}^{B_q}$$
  $$\tilde{\mathbf{v}} = Q(\mathbf{v}) \cdot \text{scale}(\mathbf{v})$$
  where $\lfloor \cdot \rceil$ denotes round-to-nearest integer and $q_{\max} = 127$ for signed 8-bit integers (`int8`).

### 7.4 ULC: Unified Controller State Formulation

- **Controller Finite State Space**: $\mathcal{S} = \{ S_0: \text{STABLE}, \; S_1: \text{SUSPECTED\_DRIFT}, \; S_2: \text{DRIFT\_CONFIRMED}, \; S_3: \text{NOISY\_BURST} \}$.
- **Evidence Vector**: $\mathbf{e}_t = \left( \Delta_{\text{ADWIN}}(t), \; \bar{R}_{\mathcal{W}}(t), \; \nabla \mathcal{L}_{\text{trend}}(t), \; H_{\text{class}}(t) \right)^\top \in [0, 1]^4$.
- **State Transition Kernel**: $\Gamma: \mathcal{S} \times [0, 1]^4 \to \mathcal{S}$.

---

## 8. Summary & Standards Compliance

All subsequent Phase 6 specifications (`DOC-DES-P6-003` through `DOC-DES-P6-011`) directly import and conform to the definitions established in this document. Any extension or modification to these notations must be formally recorded in `PHASE_6_DECISIONS.md`.

