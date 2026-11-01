# AdaptiveML — Pillar 2: RLA Prior-Art Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-003`  
> **Focus**: Robust Learning Algorithms, Noisy Labels, Outliers, Class Imbalance, Rare Pattern Preservation

---

## 1. Noise-Robust Loss Function Formulations

### 1.1 Generalized Cross Entropy (GCE)
- **Original Source**: Zhang, Z., & Sabuncu, M. (2018). *Generalized cross entropy loss for training deep neural networks with noisy labels*. NeurIPS 2018, 8771–8781.
- **Mathematical Mechanism**: Interpolates between standard Cross-Entropy (CE) and Mean Absolute Error (MAE) using the negative Box-Cox transformation parameter $q \in (0, 1]$:
  $$\mathcal{L}_{\text{GCE}}(f(x), y) = \frac{1 - f_y(x)^q}{q}$$
  When $q \to 0$, GCE approaches standard CE ($\lim_{q\to 0} \frac{1-f_y^q}{q} = -\ln f_y(x)$). When $q = 1$, GCE equals unweighted MAE ($\mathcal{L}_{\text{MAE}} = 1 - f_y(x)$), which is theoretically noise-robust under symmetric noise by Ghosh et al. (2017).
- **Assumptions**: Bounded loss; gradient scales by $f_y(x)^q$, naturally downweighting low-confidence (high-loss) predictions.
- **Limitations**:
  - Requires tuning the hyperparameter $q$ (typically $q=0.7$ on symmetric noise, but collapses under asymmetric or heavy noise).
  - Slower convergence than standard CE during early epochs because gradients on difficult clean samples are attenuated.
- **Computational Cost**: $O(K)$ per sample (identical to standard cross-entropy).
- **Existing Implementations**: Widely published in academic PyTorch repositories; no standardized scikit-learn estimator.

---

### 1.2 Symmetric Cross Entropy (SCE)
- **Original Source**: Wang, Y., Ma, X., Chen, Z., Zeng, Y., Yi, J., & Bailey, J. (2019). *Symmetric cross entropy for robust learning with noisy labels*. IEEE/CVF ICCV 2019, 322–330.
- **Mathematical Mechanism**: Combines Cross Entropy with Reverse Cross Entropy (RCE), where the ground truth label $y$ and predicted probability $p$ swap roles:
  $$\mathcal{L}_{\text{SCE}} = \alpha \mathcal{L}_{\text{CE}}(p, y) + \beta \mathcal{L}_{\text{RCE}}(p, y) = -\alpha \sum_{k=1}^K y_k \ln p_k - \beta \sum_{k=1}^K p_k \ln y_k$$
  To prevent $\ln(0)$ divergence, RCE uses a clamped one-hot representation: $\ln y_k = A$ if $y_k = 1$ and $B$ if $y_k = 0$.
- **Mechanism**: $\mathcal{L}_{\text{CE}}$ drives fast learning of clean patterns, while $\mathcal{L}_{\text{RCE}}$ acts as a symmetric regularizer that places an upper bound on the gradient of high-loss noisy samples.
- **Limitations**: Requires tuning two weighting parameters ($\alpha, \beta$). Does not account for severe class imbalance.
- **Existing Implementations**: Academic PyTorch repos; public domain prior art.

---

## 2. Sample Selection & Multi-Network Architectures

| Architecture | Foundational Source | Mechanism | Computational Cost | Critical Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **MentorNet** | Jiang et al. (ICML 2018) | Pretrained curriculum network provides sample weights to student | $2\times$ model forward passes | Requires clean validation set to pre-train mentor |
| **Co-teaching** | Han et al. (NeurIPS 2018) | Two independent networks; each selects its small-loss samples to train the other network | $2\times$ training parameters & compute | Assumes clean samples always have smaller loss than noisy samples |
| **Co-teaching+** | Yu et al. (ICML 2019) | Adds "disagreement" update rule to prevent networks from converging to identical representations | $2\times$ training parameters & compute | Higher variance; fails under low noise rates |
| **JoCoR** | Li et al. (CVPR 2020) | Joint loss combining Co-regularization with small-loss agreement | $2\times$ training compute | Heavy memory footprint; poor scaling on CPU |
| **DivideMix** | Li et al. (ICLR 2020) | Fits 2-component Gaussian Mixture Model (GMM) on per-sample losses, then applies MixMatch semi-supervised learning | $4\times$ to $6\times$ standard compute | SOTA accuracy on vision benchmarks, but completely unviable on CPU / streaming |

---

## 3. Confident Learning & Offline Data Curation

### 3.1 Confident Learning (Cleanlab)
- **Original Source**: Northcutt, C., Jiang, L., & Chuang, I. (2021). *Confident learning: Estimating uncertainty in dataset labels*. JAIR, 70, 1373–1411.
- **Mechanism**:
  1. Computes out-of-fold predicted probability matrix $\hat{P} \in \mathbb{R}^{N \times K}$ via $K$-fold cross-validation.
  2. Estimates class-specific confidence thresholds $t_j = \frac{1}{|X_{\tilde{y}=j}|} \sum_{x \in X_{\tilde{y}=j}} \hat{P}(s=j|x)$.
  3. Forms the **Confident Joint** matrix $C_{\tilde{y}, y^*}$ counting instances where $\hat{P}(s=j|x) \ge t_j$.
  4. Identifies label errors where given label $\tilde{y} \ne$ estimated true label $y^*$ and prunes or re-weights them.
- **Critical Limitations**:
  - `FACT`: **Requires offline multi-pass cross-validation.** Completely unusable in online streaming or single-pass training.
  - `OBSERVATION`: On imbalanced data, minority-class instances have sparse representation, leading to low predicted probabilities $\hat{P}$. Confident Learning routinely flags rare clean samples as label errors, pruning minority classes.
  - `FACT`: Cleanlab's codebase is licensed under **AGPL-3.0** (with commercial SaaS offerings).

---

## 4. Class Imbalance & Long-Tail Prior Art

### 4.1 Focal Loss
- **Source**: Lin, T. Y., et al. (ICCV 2017).
- **Mechanism**: Dynamically scales cross-entropy: $\mathcal{L}_{\text{Focal}} = -(1 - p_t)^\gamma \ln(p_t)$. Focuses training on hard negatives by downweighting easy clean negatives.
- **Interaction with Noise**: **Fatal flaw when noisy labels exist.** Focal Loss assigns the *highest* weights to hard samples. If a sample is mislabeled, Focal Loss treats it as a hard negative and magnifies its gradient by $(1-p_t)^\gamma$, accelerating model overfitting to label noise!

### 4.2 Class-Balanced Loss (Effective Number of Samples)
- **Source**: Cui, Y., Jia, M., Lin, T. Y., Song, Y., & Belongie, S. (CVPR 2019).
- **Mechanism**: Re-weights loss by the inverse effective volume of samples: $W_{n_y} = \frac{1 - \beta}{1 - \beta^{n_y}}$, where $\beta \in [0, 1)$ captures data overlap in feature space.
- **Strengths**: Statistically sound; avoids infinite weight explosion of naive $1/N_y$ inverse frequency.

---

## 5. The Critical Research Gap: The "Small-Loss" Breakdown

Every existing noisy-label selection method (Cleanlab, Co-teaching, MentorNet, DivideMix) relies on the **Small-Loss Criterion**:
$$\text{Clean Samples} \approx \text{Low Loss}, \quad \text{Noisy Samples} \approx \text{High Loss}$$

**Why it Fails on Imbalanced Data**:
- Rare minority-class instances naturally produce **High Loss** because the model has observed fewer supporting exemplars.
- Standard filters classify them as "noise" and prune them.
- In medical diagnostics (rare tumors) and fraud detection (rare chargebacks), this heuristic actively destroys minority-class accuracy.

**AdaptiveML RLA Opportunity**:
Engineer a **Density-Aware Margin Reliability Scorer** that evaluates sample difficulty relative to local $k$-NN feature space density:
$$\text{Reliability}(x_i, y_i) = \Phi\left( \text{Margin}(x_i, y_i), \rho(x_i) \right)$$
If a high-loss sample resides in a low-density region ($\rho(x_i) \to 0$), it is classified as a **Legitimate Rare Sample** and preserved.
