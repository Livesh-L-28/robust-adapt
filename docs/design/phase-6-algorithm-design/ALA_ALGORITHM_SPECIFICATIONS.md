# AdaptiveML — ALA Algorithm Specifications: Adaptive Learning Algorithms

> **Document Status**: Complete Baseline Deliverable (Phase 6)  
> **Document Identifier**: `DOC-DES-P6-003`  
> **Last Updated**: 2026-11-01  
> **Pillar**: ALA (Adaptive Learning Algorithms)  
> **Target Downstream Deliverable**: `DOC-DES-P7-004` (Public API Specification), `DOC-DES-P6-009` (Pseudocode Catalog)

---

## 1. Executive Pillar Architecture

The **Adaptive Learning Algorithms (ALA)** pillar provides online learning, concept drift adaptation, and continuous knowledge retention under changing data distributions without requiring historical data re-storage.

The pillar comprises three mathematically synchronized algorithm specifications:
1. **`VectorizedHoeffdingTree` / `StreamingTreeEnsemble`**: Vectorized streaming decision trees executing Hoeffding-bound splitting over contiguous 2D NumPy arrays.
2. **`ReliabilityWeightedADWIN` (RW-ADWIN)**: An adaptive sliding window drift detector that weights error signals by sample reliability to suppress false-positive resets caused by label noise.
3. **`ClassBalancedReservoirReplay`**: A bounded-memory experience replay buffer executing stratified reservoir retention to prevent catastrophic forgetting.

```
                           ALA DATA PIPELINE
                                   │
              Input Stream Batch (X_tau, y_tau) [B x d]
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
    ┌─────────────────────────┐         ┌─────────────────────────┐
    │  Vectorized Sufficient  │         │   Loss Computation &    │
    │    Statistics Update    │         │  Reliability Weighting  │
    └────────────┬────────────┘         └────────────┬────────────┘
                 ▼                                   ▼
    ┌─────────────────────────┐         ┌─────────────────────────┐
    │  Hoeffding Bound Check  │         │  RW-ADWIN Drift Check   │
    │  (Split / Defer / Leaf) │         │ (Confidence Cut Bound)  │
    └────────────┬────────────┘         └────────────┬────────────┘
                 │                                   │
                 ▼                                   ▼
       Updated Tree Structure               Drift Alert & Scale Factor
                 │                                   │
                 └─────────────────┬─────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │ Class-Balanced Bounded Replay │
                    │   (Reservoir Retention Pool)  │
                    └───────────────────────────────┘
```

---

## 2. Algorithm 1: Vectorized Streaming Decision Tree (`VectorizedHoeffdingTree`)

### 2.1 Formal Problem Definition

Let a data stream generate instances sequentially: $(\mathbf{x}_t, y_t) \sim P_t(\mathbf{x}, y)$ with $\mathbf{x}_t \in \mathbb{R}^d$ and $y_t \in \{0, \dots, C-1\}$.  
The objective is to incrementally induce an optimal decision tree classifier $f_t: \mathbb{R}^d \to \Delta^{C-1}$ such that:
$$\lim_{t \to \infty} \mathbb{P}_{(\mathbf{x}, y) \sim \mathcal{D}}\left( \arg\max_{c} f_t(\mathbf{x})_c \ne y \right) = \inf_{f \in \mathcal{F}_{\text{tree}}} \mathbb{P}\left( \arg\max_c f(\mathbf{x})_c \ne y \right)$$
subject to the constraints:
1. Each instance or mini-batch $\mathbf{X} \in \mathbb{R}^{B \times d}$ is processed in $\mathcal{O}(B \cdot d \cdot K)$ time ($K$ being quantile bins).
2. Historical samples are discarded immediately after the statistics update.
3. The tree structure asymptotically converges to the batch-optimal decision tree with high probability $1 - \delta$.

---

### 2.2 Mathematical Formulation & Splitting Criteria

#### 2.2.1 Hoeffding Bound Condition
Let $G(X_j, s)$ denote the split evaluation heuristic (Information Gain or Gini Impurity Reduction) for splitting attribute $X_j$ at threshold $s$.  
At any leaf node $u$ with accumulated sample count $n_u \ge n_{\min}$, let:
- $X_a = \arg\max_{X_j} G(X_j)$ (best candidate split)
- $X_b = \arg\max_{X_j \ne X_a} G(X_j)$ (second-best candidate split)
- $\Delta \bar{G} = \bar{G}(X_a) - \bar{G}(X_b) \ge 0$

By the Hoeffding Inequality, the true difference between the expected split values satisfies:
$$\mathbb{P}\left( \Delta \mathbb{E}[G] < \Delta \bar{G} - \epsilon_H \right) \le \delta$$
where the Hoeffding error bound $\epsilon_H$ is given by:
$$\epsilon_H = \sqrt{\frac{R_G^2 \cdot \ln(1 / \delta)}{2 n_u}}$$
where $R_G$ is the dynamic range of the heuristic:
$$R_G = \begin{cases} \ln(C), & \text{if } G \text{ is Information Gain} \\ 1.0 - \frac{1}{C}, & \text{if } G \text{ is Gini Impurity} \end{cases}$$

#### 2.2.2 Splitting Decision Rule
A split on $X_a$ is executed if and only if:
$$\Delta \bar{G} > \epsilon_H \quad \lor \quad \epsilon_H < \tau_H$$
where $\tau_H \in (0, 0.1]$ is a predefined tie-breaking threshold preventing indefinite starvation when two attributes exhibit near-identical split quality.

---

### 2.3 Vectorized Sufficient Statistics (2D NumPy Matrix Representation)

Traditional streaming trees (e.g., in River) iterate sample-by-sample through Python dictionary mappings. AdaptiveML formalizes a contiguous tensor sufficient statistic.

For each leaf node $u$, feature $j \in \{1, \dots, d\}$, discretization bin $k \in \{1, \dots, K\}$, and target class $c \in \{0, \dots, C-1\}$:
$$\mathbf{S}_u \in \mathbb{R}^{d \times K \times C}$$
where entry $S_u[j, k, c]$ holds the count of instances reaching node $u$ with feature $X_j$ falling into bin $k$ and having true label $y = c$.

#### 2.3.1 Vectorized Batch Accumulation
Given mini-batch $\mathbf{X} \in \mathbb{R}^{B \times d}$ and one-hot labels $\mathbf{Y} \in \{0, 1\}^{B \times C}$ mapped to leaf $u$:
1. Quantize continuous features into integer bin indices via pre-computed quantile edges $\mathbf{E} \in \mathbb{R}^{d \times (K-1)}$:
   $$\mathbf{K}_{\text{idx}} = \text{digitize}(\mathbf{X}, \mathbf{E}) \in \{0, \dots, K-1\}^{B \times d}$$
2. Vectorized histogram accumulation:
   $$S_u[j, k, c] \leftarrow S_u[j, k, c] + \sum_{b=1}^B \mathbb{I}\left( K_{\text{idx}}[b, j] = k \right) \cdot Y[b, c]$$
   Implemented via NumPy `np.add.at` or vectorized flat bincount without Python loops.

#### 2.3.2 Split Evaluation via Matrix Reduction
For attribute $j$ at split bin $s \in \{0, \dots, K-2\}$:
- Left partition class counts: $\mathbf{c}_L(s) = \sum_{k=0}^s \mathbf{S}_u[j, k, :] \in \mathbb{R}^C$
- Right partition class counts: $\mathbf{c}_R(s) = \sum_{k=s+1}^{K-1} \mathbf{S}_u[j, k, :] \in \mathbb{R}^C$
- Total partition weights: $n_L = \sum_{c=0}^{C-1} c_L(s)_c$, $n_R = \sum_{c=0}^{C-1} c_R(s)_c$, $n = n_L + n_R$.
- Gini Impurity:
  $$\text{Gini}(\mathbf{c}) = 1 - \sum_{c=0}^{C-1} \left(\frac{c_c}{n}\right)^2$$
  $$\bar{G}(X_j, s) = \text{Gini}(\mathbf{c}_{\text{total}}) - \left[ \frac{n_L}{n} \text{Gini}(\mathbf{c}_L(s)) + \frac{n_R}{n} \text{Gini}(\mathbf{c}_R(s)) \right]$$
All candidate splits across all $d$ features and $K$ thresholds are evaluated simultaneously via vectorized matrix broadcasting in $\mathcal{O}(d \cdot K \cdot C)$ operations.

---

### 2.4 Mathematical Invariants & Failure Modes

1. **Conservation Invariant**: $\sum_{k=0}^{K-1} \sum_{c=0}^{C-1} S_u[j, k, c] = n_u \quad \forall j \in \{1, \dots, d\}$.
2. **Failure Mode 1 (Quantization Boundary Drift)**: If the streaming distribution undergoes extreme feature scale expansion, fixed quantile edges lead to boundary saturation.  
   *Mitigation*: Adaptive dynamic quantile estimation using a P-Square or t-digest online sketch updated at leaf nodes.
3. **Failure Mode 2 (Split Starvation on Noise)**: When attribute noise is perfectly uniform across classes, $\Delta \bar{G} \approx 0$, causing $\epsilon_H$ to govern until $n_u \to \infty$.  
   *Mitigation*: Enforced tie-breaking condition $\epsilon_H < \tau_H$ with maximum leaf depth limit $D_{\max}$.

---

## 3. Algorithm 2: Reliability-Weighted ADWIN (`ReliabilityWeightedADWIN`)

### 3.1 Problem Definition & Limitations of Standard ADWIN

Standard ADWIN maintains a variable-length window $W$ of scalar real values $z_t \in [0, 1]$ (e.g. 0-1 loss). When the window is partitioned into $W = W_0 \cdot W_1$, it detects drift whenever:
$$|\hat{\mu}_{W_0} - \hat{\mu}_{W_1}| \ge \epsilon_{\text{cut}}$$

**Vulnerability**: Under random label corruption (e.g., label flip probability $\eta = 0.2$), a burst of mislabeled instances induces an artificial jump in window loss $\hat{\mu}_{W_1}$, triggering false-positive drift alarms and unnecessary model resets.

---

### 3.2 Formal Mathematical Derivation of RW-ADWIN

Let each observation in window $W$ consist of a pair: $(z_t, r_t)$ where:
- $z_t \in [0, 1]$ is the learner's instantaneous loss or error signal.
- $r_t \in [\epsilon_r, 1]$ is the sample reliability score supplied by the RLA pillar ($\epsilon_r > 0$ ensures non-zero support).

#### 3.2.1 Weighted Window Partition Statistics
For any partition $W = W_0 \cdot W_1$:
- Sum of weights: $S_r(W_k) = \sum_{t \in W_k} r_t$ for $k \in \{0, 1\}$.
- Weighted mean:
  $$\hat{\mu}_{W_k}^{(r)} = \frac{1}{S_r(W_k)} \sum_{t \in W_k} r_t z_t$$
- Effective sample size (Kish's Effective Sample Formula):
  $$N_{\text{eff}}(W_k) = \frac{\left( \sum_{t \in W_k} r_t \right)^2}{\sum_{t \in W_k} r_t^2} \le |W_k|$$
- Harmonic effective sample size:
  $$m_{\text{eff}} = \left( \frac{1}{N_{\text{eff}}(W_0)} + \frac{1}{N_{\text{eff}}(W_1)} \right)^{-1} = \frac{N_{\text{eff}}(W_0) \cdot N_{\text{eff}}(W_1)}{N_{\text{eff}}(W_0) + N_{\text{eff}}(W_1)}$$

#### 3.2.2 Reliability-Weighted Cut Bound
By applying the weighted Hoeffding-Azuma inequality for bounded martingales, the difference between the true weighted expectations is bounded by:
$$\epsilon_{\text{cut}}^{(r)} = \sqrt{\frac{1}{2 m_{\text{eff}}} \ln\left( \frac{4 |W|}{\delta} \right)}$$

#### 3.2.3 Drift Trigger Condition
A concept drift is declared if and only if:
$$\left| \hat{\mu}_{W_0}^{(r)} - \hat{\mu}_{W_1}^{(r)} \right| \ge \epsilon_{\text{cut}}^{(r)}$$

#### 3.2.4 Theorem: False-Alarm Suppression Under Bursty Noise
> **Theorem 1**: Let clean data have error mean $\mu_0$. Suppose an adversarial burst of $M$ mislabeled instances with error $z_t = 1$ is injected into $W_1$.  
> If the RLA module assigns reliability $r_t \le \epsilon_r \ll 1$ to corrupted instances, the distortion in the test statistic satisfies:
> $$\left| \hat{\mu}_{W_1}^{(r)} - \mu_0 \right| \le \frac{\epsilon_r M}{S_r(W_1^{\text{clean}}) + \epsilon_r M} \cdot (1 - \mu_0) \ll \frac{M}{|W_1^{\text{clean}}| + M} \cdot (1 - \mu_0)$$
> Consequently, the probability of false drift detection $\mathbb{P}_{\text{false}}$ decays exponentially with $\frac{1}{\epsilon_r}$, provably suppressing noise-induced resets.

---

## 4. Algorithm 3: Class-Balanced Reservoir Replay (`ClassBalancedReservoirReplay`)

### 4.1 Problem Definition

Continuous stream learning suffers from catastrophic forgetting of rare or historical modes. Standard reservoir sampling (Vitter's Algorithm R) samples uniformly from stream history:
$$P(\text{retain instance } t) = \frac{M_{\text{buf}}}{t} \quad \text{for } t > M_{\text{buf}}$$
Under severe class imbalance (e.g. minority class ratio 1:100), uniform reservoir sampling results in the minority class representation decaying to $\frac{M_{\text{buf}}}{100}$, leading to complete loss of minority decision boundaries.

---

### 4.2 Class-Balanced Reservoir Retention Policy

We define a partitioned reservoir buffer $\mathcal{B}$ with fixed total capacity $M_{\text{buf}}$:
$$\mathcal{B} = \bigcup_{c=0}^{C-1} \mathcal{B}_c, \quad |\mathcal{B}| = \sum_{c=0}^{C-1} |\mathcal{B}_c| \le M_{\text{buf}}$$
where each class bucket $\mathcal{B}_c$ has dynamic capacity allocation $M_c(t)$:
$$M_c(t) = \max\left( \left\lfloor \frac{M_{\text{buf}}}{C} \right\rfloor, \; 1 \right)$$
ensuring that rare classes are guaranteed at least $\frac{1}{C}$ of total buffer capacity regardless of stream arrival frequency.

#### 4.2.1 Insertion and Replacement Mechanics
Let stream instance $(\mathbf{x}_t, y_t)$ arrive with class $y_t = c$:
1. Let $n_c(t)$ denote the total number of class $c$ instances observed since stream initialization.
2. If $|\mathcal{B}_c| < M_c$:
   - Insert $(\mathbf{x}_t, y_t)$ directly into $\mathcal{B}_c$.
3. Else ($|\mathcal{B}_c| = M_c$):
   - Draw random integer $k \sim \text{Uniform}(1, n_c(t))$.
   - If $k \le M_c$:
     - Replace element $\mathcal{B}_c[k]$ with $(\mathbf{x}_t, y_t)$.
   - Else:
     - Discard $(\mathbf{x}_t, y_t)$.

#### 4.2.2 Stratified Replay Batch Generation
During any mini-batch update with incoming batch size $B$, the learner samples a replay batch $\mathbf{Z}_{\text{replay}}$ of size $B_{\text{replay}} = \lfloor \alpha_{\text{rep}} \cdot B \rfloor$ from $\mathcal{B}$:
1. Uniformly draw $\lfloor B_{\text{replay}} / C \rfloor$ samples from each non-empty bucket $\mathcal{B}_c$.
2. Form composite training batch: $\mathbf{Z}_{\text{train}} = \mathbf{Z}_{\text{stream}} \cup \mathbf{Z}_{\text{replay}}$.
3. Total memory footprint is strictly bounded:
   $$\text{RAM}(\mathcal{B}) = M_{\text{buf}} \cdot (d \cdot 8_{\text{bytes}} + 8_{\text{bytes}}) = \mathcal{O}(M_{\text{buf}} \cdot d) \le M_{\max}$$

---

## 5. Summary of Mathematical Guarantees

| Algorithm Component | Time Complexity (per batch $B$) | Space Complexity | Guarantees / Bounds |
| :--- | :--- | :--- | :--- |
| **`VectorizedHoeffdingTree`** | $\mathcal{O}(B \cdot d + d \cdot K \cdot C)$ | $\mathcal{O}(U \cdot d \cdot K \cdot C)$ | Error rate bounded by $\delta$ via Hoeffding inequality |
| **`ReliabilityWeightedADWIN`** | $\mathcal{O}(\log |W|)$ amortized | $\mathcal{O}(\log |W|)$ | Provable false-alarm suppression under bounded noise |
| **`ClassBalancedReservoirReplay`**| $\mathcal{O}(B_{\text{replay}})$ | $\mathcal{O}(M_{\text{buf}} \cdot d)$ | Exact uniform sampling per class; bounded memory $M_{\text{buf}}$ |
