# AdaptiveML — RLA Algorithm Specifications: Robust Learning Algorithms

> **Document Status**: Complete Baseline Deliverable (Phase 6)  
> **Document Identifier**: `DOC-DES-P6-004`  
> **Last Updated**: 2026-11-01  
> **Pillar**: RLA (Robust Learning Algorithms)  
> **Target Downstream Deliverable**: `DOC-DES-P7-004` (Public API Specification), `DOC-DES-P6-009` (Pseudocode Catalog)

---

## 1. Executive Pillar Architecture

The **Robust Learning Algorithms (RLA)** pillar provides mathematically grounded safeguards against label corruption, uncalibrated outliers, and severe class imbalance.

RLA operates through three mathematically rigorous modules:
1. **`DensityAwareMarginScorer`**: Closed-form reliability scoring combining model logit margins with local $k$-NN feature space density to prevent incorrect removal of legitimate minority instances.
2. **`SymmetricCrossEntropyLoss` (SCE) & `GeneralizedCrossEntropyLoss` (GCE)**: Robust loss functions with closed-form gradient derivations bounding gradient distortion under symmetric and asymmetric label noise.
3. **`ClassBalancedReweighting`**: Non-linear loss reweighting parameterized by the *effective number of samples* $(1 - \beta)/(1 - \beta^{n_y})$.

```
                           RLA PIPELINE FLOW
                                   │
              Input Instance Batch (X_tau, y_tau) [B x d]
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
    ┌─────────────────────────┐         ┌─────────────────────────┐
    │   k-NN Density Metric   │         │    Logit Margin Metric  │
    │        rho_k(x_i)       │         │      M(x_i, y_i)        │
    └────────────┬────────────┘         └────────────┬────────────┘
                 └─────────────────┬─────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │  Density-Aware Margin Scorer  │
                    │   r_i = Phi(M_norm + gamma*D) │
                    └──────────────┬────────────────┘
                                   │
           ┌───────────────────────┴───────────────────────┐
           ▼                                               ▼
    [Soft Sample Weighting]                         [Hard Filtering]
        w_i = r_i                               Drop if r_i < theta_filter
           │                                               │
           └───────────────────────┬───────────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │   Class-Balanced Weighting    │
                    │      W_y = (1-beta)/(1-beta^n)│
                    └──────────────┬────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │    Robust Loss (SCE / GCE)    │
                    │  Forward Loss & Grad Backprop │
                    └───────────────────────────────┘
```

---

## 2. Algorithm 1: Density-Aware Margin Reliability Scoring (`DensityAwareMarginScorer`)

### 2.1 Problem Definition & Failure Mode of Prior Art

Standard label-cleansing heuristics (e.g. Cleanlab Confident Learning, standard margin thresholding) assume that instances with negative or small margins $z_y(\mathbf{x}) - \max_{j \ne y} z_j(\mathbf{x}) \le 0$ are corrupted.  
**Critical Flaw**: In long-tailed or complex real-world data, legitimate minority class instances naturally lie in low-density feature regions near decision boundaries, producing low margins. Naive filtering systematically purges rare classes, accelerating model collapse on tail distributions.

---

### 2.2 Mathematical Formulation

Let model logits for instance $\mathbf{x}_i \in \mathbb{R}^d$ be $\mathbf{z}(\mathbf{x}_i) = [z_0(\mathbf{x}_i), \dots, z_{C-1}(\mathbf{x}_i)]^\top \in \mathbb{R}^C$.

#### 2.2.1 Normalized Logit Margin
The signed margin $\mathcal{M}(\mathbf{x}_i, y_i)$ with respect to observed label $y_i$ is:
$$\mathcal{M}(\mathbf{x}_i, y_i) = z_{y_i}(\mathbf{x}_i) - \max_{j \ne y_i} z_j(\mathbf{x}_i)$$
We normalize the margin over a sliding window or batch:
$$\tilde{\mathcal{M}}_i = \frac{\mathcal{M}(\mathbf{x}_i, y_i) - \mu_{\mathcal{M}}}{\sigma_{\mathcal{M}} + \epsilon_{\text{div}}}$$
where $\mu_{\mathcal{M}}$ and $\sigma_{\mathcal{M}}$ denote the batch/window mean and standard deviation of margins.

#### 2.2.2 Local Feature Space Density Estimation ($\rho_k$)
Let $\mathcal{N}_k(\mathbf{x}_i)$ be the set of $k$-nearest neighbors of $\mathbf{x}_i$ in feature space $\mathcal{X}$. The mean neighbor distance is:
$$\bar{d}_k(\mathbf{x}_i) = \frac{1}{k} \sum_{\mathbf{x}' \in \mathcal{N}_k(\mathbf{x}_i)} \|\mathbf{x}_i - \mathbf{x}'\|_2$$
The local feature density is defined as:
$$\rho_k(\mathbf{x}_i) = \frac{1}{\bar{d}_k(\mathbf{x}_i) + \epsilon_\rho}$$
To eliminate scale sensitivity across different datasets, we compute the relative density ratio:
$$\delta_k(\mathbf{x}_i) = \frac{\rho_k(\mathbf{x}_i)}{\bar{\rho}_{\text{batch}} + \epsilon_\rho} \in (0, \infty)$$
where $\bar{\rho}_{\text{batch}} = \frac{1}{B} \sum_{j=1}^B \rho_k(\mathbf{x}_j)$.

#### 2.2.3 Closed-Form Reliability Function
We formalize the density-aware reliability score $r_i \in (0, 1)$ via the coupled logistic sigmoid:
$$r_i = \sigma\left( \alpha \cdot \tilde{\mathcal{M}}_i + \gamma \cdot \psi(\delta_k(\mathbf{x}_i)) \right)$$
where:
- $\sigma(u) = \frac{1}{1 + e^{-u}}$ is the standard logistic function.
- $\alpha > 0$ is the margin sensitivity parameter (default $\alpha = 1.0$).
- $\gamma \ge 0$ is the density protection coefficient (default $\gamma = 0.5$).
- $\psi(\delta) = -\ln(\delta + \epsilon_{\text{log}})$ is the density penalty moderation function:
  - In high-density regions ($\delta \gg 1$), $\psi(\delta) < 0$: an instance with a negative margin in high density is penalized severely because it is almost certainly a label error.
  - In low-density regions ($\delta \ll 1$), $\psi(\delta) > 0$: an instance with a negative margin is given a protective bonus, recognizing it as a difficult or rare-class instance rather than an error.

#### 2.2.4 Theorem: Minority Class Preservation Bound
> **Theorem 2 (Minority Preservation Guarantee)**:  
> Let $\mathbf{x}_i$ belong to an extreme minority class with local density ratio $\delta_k(\mathbf{x}_i) \le \delta_{\text{rare}} \ll 1$.  
> Even if model uncertainty yields a negative margin $\tilde{\mathcal{M}}_i = -m_0$ ($m_0 > 0$), the reliability score is strictly lower-bounded by:
> $$r_i \ge \sigma\left( -\alpha m_0 + \gamma \ln\left( \frac{1}{\delta_{\text{rare}}} \right) \right)$$
> For any chosen margin deficit $m_0$, setting $\gamma \ge \frac{\alpha m_0 + \sigma^{-1}(r_{\text{threshold}})}{\ln(1 / \delta_{\text{rare}})}$ guarantees that $r_i \ge r_{\text{threshold}}$, preventing false purging of rare instances.

---

## 3. Algorithm 2: Robust Loss Functions (`SymmetricCrossEntropyLoss`, `GeneralizedCrossEntropyLoss`)

### 3.1 Generalized Cross Entropy Loss (GCE)

GCE generalizes Mean Absolute Error (MAE, robust to noise) and Cross Entropy (CE, fast convergence) via the Box-Cox transformation of probabilities.

#### 3.1.1 Forward Formulation
For predicted probabilities $\mathbf{p} = \text{softmax}(\mathbf{z}) \in \Delta^{C-1}$ and true label $y \in \{0, \dots, C-1\}$:
$$\mathcal{L}_{\text{GCE}}(\mathbf{p}, y; q) = \frac{1 - p_y^q}{q}, \quad q \in (0, 1]$$
- When $q \to 0$: $\lim_{q \to 0} \frac{1 - p_y^q}{q} = -\ln(p_y) = \mathcal{L}_{\text{CE}}(\mathbf{p}, y)$.
- When $q = 1$: $\mathcal{L}_{\text{GCE}}(\mathbf{p}, y; 1) = 1 - p_y = \frac{1}{2} \mathcal{L}_{\text{MAE}}(\mathbf{p}, \mathbf{e}(y))$.

#### 3.1.2 Analytical Logit Gradient Derivation
Let $\mathbf{z} \in \mathbb{R}^C$ be logits with $p_k = \frac{e^{z_k}}{\sum_{j=0}^{C-1} e^{z_j}}$. Using the chain rule:
$$\frac{\partial \mathcal{L}_{\text{GCE}}}{\partial z_k} = \sum_{j=0}^{C-1} \frac{\partial \mathcal{L}_{\text{GCE}}}{\partial p_j} \frac{\partial p_j}{\partial z_k}$$
Since $\frac{\partial \mathcal{L}_{\text{GCE}}}{\partial p_y} = -p_y^{q-1}$ and $\frac{\partial \mathcal{L}_{\text{GCE}}}{\partial p_j} = 0$ for $j \ne y$:
$$\frac{\partial p_y}{\partial z_k} = \begin{cases} p_y (1 - p_y), & k = y \\ -p_y p_k, & k \ne y \end{cases}$$
Substituting:
$$\frac{\partial \mathcal{L}_{\text{GCE}}}{\partial z_k} = \begin{cases} -p_y^q (1 - p_y), & k = y \\ p_y^q p_k, & k \ne y \end{cases} = p_y^q (p_k - \mathbb{I}(k = y))$$
**Robustness Proof**: Notice the gradient magnitude is scaled by $p_y^q$. If an instance is corrupted and the model is confident in another class ($p_y \approx 0$), the gradient scaling factor $p_y^q \to 0$, vanishing the gradient from corrupted labels.

---

### 3.2 Symmetric Cross Entropy Loss (SCE)

Symmetric Cross Entropy balances Cross Entropy (CE) with Reverse Cross Entropy (RCE), providing strong gradient signals on easy examples while bounding gradient distortion from noisy labels.

#### 3.2.1 Forward Formulation
$$\mathcal{L}_{\text{SCE}}(\mathbf{p}, y; \alpha, \beta) = \alpha \cdot \mathcal{L}_{\text{CE}}(\mathbf{p}, y) + \beta \cdot \mathcal{L}_{\text{RCE}}(\mathbf{p}, y)$$
where:
$$\mathcal{L}_{\text{CE}}(\mathbf{p}, y) = -\ln(p_y + \epsilon_{\text{clip}})$$
$$\mathcal{L}_{\text{RCE}}(\mathbf{p}, y) = -\sum_{c=0}^{C-1} p_c \ln\left( \mathbf{e}(y)_c + \epsilon_{\text{clip}} \right) = -p_y \ln(1) - \sum_{j \ne y} p_j \ln(\epsilon_{\text{clip}}) = -A \cdot \sum_{j \ne y} p_j = A \cdot (p_y - 1)$$
where constant $A = \ln(\epsilon_{\text{clip}}) < 0$.  
To ensure numerical stability without requiring arbitrary clipping bounds, AdaptiveML adopts the normalized information-theoretic form:
$$\mathcal{L}_{\text{RCE}}(\mathbf{p}, y) = 1 - p_y + \frac{1}{C - 1} \sum_{j \ne y} p_j \ln\left( \frac{p_j + \epsilon}{\frac{1}{C-1}} \right)$$

#### 3.2.2 Analytical Gradient of Normalized SCE
For the standard bounded formulation $\mathcal{L}_{\text{RCE}}(\mathbf{p}, y) = -p_y \ln(1) - (1 - p_y) \ln(\epsilon_{\text{clip}}) = -C_{\epsilon} (1 - p_y)$:
$$\nabla_{\mathbf{z}} \mathcal{L}_{\text{SCE}} = \alpha \left( \mathbf{p} - \mathbf{e}(y) \right) + \beta \cdot C_{\epsilon} \cdot \mathbf{p} \left( p_y - \mathbb{I}(k = y) \right)$$
This gradient is strictly bounded: $\|\nabla_{\mathbf{z}} \mathcal{L}_{\text{SCE}}\|_2 \le \alpha \sqrt{2} + \beta |C_\epsilon| \sqrt{2} < \infty$, preventing gradient explosion under arbitrary label corruption.

---

## 4. Algorithm 3: Class-Balanced Loss Reweighting (`ClassBalancedReweighting`)

### 4.1 Effective Number of Samples Derivation

Given a class $c \in \{0, \dots, C-1\}$ with $n_c$ total observed instances. Let the volume of the feature space occupied by $n_c$ samples grow with diminishing returns due to data overlap:
$$E_{n_c} = \sum_{j=1}^{n_c} \beta^{j-1} = \frac{1 - \beta^{n_c}}{1 - \beta}$$
where $\beta = \frac{N - 1}{N} \in [0, 1)$ represents the probability that a new instance falls within the existing convex hull of observed instances.

### 4.2 Normalization and Weight Calculation
The raw inverse effective weight is:
$$W_c = \frac{1}{E_{n_c}} = \frac{1 - \beta}{1 - \beta^{n_c} + \epsilon_{\text{div}}}$$
To prevent overall learning rate drift, weights are normalized across all $C$ active classes such that their mean is 1.0:
$$w_c = C \cdot \frac{W_c}{\sum_{j=0}^{C-1} W_j}$$

### 4.3 Total Composite Batch Loss Formulation
Given mini-batch $\{(\mathbf{x}_i, y_i)\}_{i=1}^B$ with predicted probabilities $\mathbf{p}_i = f(\mathbf{x}_i)$, sample reliabilities $r_i$ from `DensityAwareMarginScorer`, and class weights $w_{y_i}$:
$$\mathcal{L}_{\text{final}}(\mathbf{X}, \mathbf{y}) = \frac{\sum_{i=1}^B r_i \cdot w_{y_i} \cdot \mathcal{L}_{\text{robust}}(\mathbf{p}_i, y_i)}{\sum_{i=1}^B r_i + \epsilon_{\text{div}}}$$

---

## 5. Summary of Mathematical Guarantees

| Algorithm Component | Time Complexity (per batch $B$) | Space Complexity | Guarantees / Bounds |
| :--- | :--- | :--- | :--- |
| **`DensityAwareMarginScorer`** | $\mathcal{O}(B \cdot d \cdot k + B \cdot C)$ | $\mathcal{O}(B \cdot d)$ | Minority instances provably protected via Theorem 2 |
| **`GeneralizedCrossEntropy`** | $\mathcal{O}(B \cdot C)$ | $\mathcal{O}(B \cdot C)$ | Vanishing gradient on high-confidence noisy samples |
| **`SymmetricCrossEntropy`** | $\mathcal{O}(B \cdot C)$ | $\mathcal{O}(B \cdot C)$ | $L_2$ gradient norm strictly bounded by $\sqrt{2}(\alpha + \beta |C_\epsilon|)$ |
| **`ClassBalancedReweighting`** | $\mathcal{O}(C)$ | $\mathcal{O}(C)$ | Asymptotically smooth transition between no-weighting and inverse-frequency |

