# Robust Learning Algorithms (RLA) — Evolution Register v2.0

**Document Identifier:** `DOC-STRAT-EVO-RLA-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Target Module:** [`adaptive_ml.rla`](file:///c:/projects/AdaptiveML/adaptive_ml/rla)<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Approved Strategic Architecture<br>

---

## 1. Pillar Mission & Architectural Scope

The **Robust Learning Algorithms (RLA)** pillar provides algorithmic defenses against contaminated training data, corrupted or noisy labels, adversarial outliers, and severe class imbalance.

In strict compliance with **Research Governance Rule 6 (Prohibition Against Discarding Rare Samples)**, RLA mechanisms must never discard or downweight difficult-to-learn minority-class exemplars under the false assumption that high initial loss implies label noise. In compliance with **Research Governance Rule 7 (Pillar Independence)**, RLA operates as a fully decoupled module in pure Python/NumPy, maintaining zero mandatory dependencies on ALA, RAO, or ULC.

---

## 2. Baseline Capabilities Grounded in Verified Source Evidence

The verified implementation of RLA in `aml-core==0.1.0.dev0` consists of four modules in [`adaptive_ml/rla`](file:///c:/projects/AdaptiveML/adaptive_ml/rla):

```
adaptive_ml/rla/
├── __init__.py           # Exports DensityAwareMarginScorer, SymmetricCrossEntropyLoss,
│                         # GeneralizedCrossEntropyLoss, ClassBalancedWeights, RobustLearningPipeline
├── scorer.py             # DensityAwareMarginScorer (Reliability scoring using margin and local density)
├── losses.py             # SymmetricCrossEntropyLoss, GeneralizedCrossEntropyLoss (Noise-tolerant losses)
├── weighting.py          # ClassBalancedWeights (Effective number of samples sample reweighting)
└── pipeline.py           # RobustLearningPipeline (Coordinated robust estimation workflow)
```

### 2.1 Verified Capabilities Inventory

| Component | Source File & Class | Mathematical Formulation / Implementation | Verified Invariants |
| :--- | :--- | :--- | :--- |
| **Reliability Scoring** | [`DensityAwareMarginScorer`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py#L20) in [`scorer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py) | Combines prediction margin $m_i = p(y_i \vert x_i) - \max_{k \neq y_i} p(k \vert x_i)$ with local density metric: $r_i = \sigma(\alpha m_i + \beta \log \rho_i)$ | $r_i \in [0, 1]$; zero division guarded by [`EPS_DIV`](file:///c:/projects/AdaptiveML/adaptive_ml/core/constants.py); preserves samples in sparse minority clusters |
| **Symmetric Robust Loss** | [`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py#L22) in [`losses.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py) | $\mathcal{L}_{\text{SCE}} = \alpha \mathcal{L}_{\text{CE}}(p, q) + \beta \mathcal{L}_{\text{RCE}}(q, p)$, where Reverse Cross Entropy bounds noise overfitting | Gradient bounded by $\beta$; symmetric invariance under uniform label noise; pure NumPy vectorized implementation |
| **Generalized Robust Loss** | [`GeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py#L85) in [`losses.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py) | Box-Cox transformation of cross entropy: $\mathcal{L}_{\text{GCE}} = \frac{1 - p(y \vert x)^q}{q}$, interpolating between MAE ($q=1$) and CCE ($q \to 0$) | Controlled gradient magnitude $p(y \vert x)^{q-1} \nabla p$; stable across $q \in (0, 1]$ |
| **Class-Balanced Weighting** | [`ClassBalancedWeights`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/weighting.py#L18) in [`weighting.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/weighting.py) | Effective number of samples: $E_n = \frac{1 - \beta^n}{1 - \beta}$; class weight $W_c = \frac{1}{E_{n_c}}$ normalized such that $\sum W_c = C$ | Numerically stable under extreme class imbalance ($>1000:1$); supports dynamic online count updates |
| **Robust Pipeline** | [`RobustLearningPipeline`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/pipeline.py#L25) in [`pipeline.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/pipeline.py) | Chains sample scoring, class-balanced weight modulation, and robust loss evaluation for arbitrary base estimators | Scikit-learn estimator compatible; clean logging of filtered sample statistics |

---

## 3. Current Limitations

Based on Phase 12 empirical benchmarks and independent verification findings:

1. **High Noise Asymmetry Vulnerability:** While [`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py) and [`GeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py) demonstrate verified stability under symmetric noise ($\le 40\%$), asymmetric (class-conditional) noise exceeding $30\%$ causes class boundary distortion without explicit noise transition matrix $\mathbf{T}$ estimation.
2. **Computational Complexity of Density Estimation:** [`DensityAwareMarginScorer`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py) computes local density via Euclidean $k$-nearest neighbors. In batch sizes $N > 10,000$ with dimension $d > 100$, exact pairwise distance computation scales as $\mathcal{O}(N^2 d)$, creating latency overhead on CPU.
3. **Absence of Streaming Continuous Regression Losses:** Current RLA loss functions are formulated exclusively for discrete multi-class categorical targets. Robust losses for continuous streaming regression targets contaminated by heavy-tailed Cauchy or Student-t measurement errors are not yet implemented.
4. **Binary Noise Partitioning:** The pipeline currently provides soft weights $r_i \in [0, 1]$ or hard thresholding. It lacks the ability to distinguish whether a low-confidence sample is a random annotation error, an out-of-distribution (OOD) sample, or an unmodeled subclass.

---

## 4. RLA Evolution Itemized Register

| Identifier | Priority | Classification | Original Phase Mapping | Complexity | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-RLA-001** | **P1** | Proposed Enhancement | Phase 9 (RLA Development) | Medium | Low | Pure NumPy |
| **EVO-RLA-002** | **P1** | New Research | Phase 9 & Phase 12 | High | Medium | Phase 12 Benchmarks |
| **EVO-RLA-003** | **P2** | New Research | Phase 9 (RLA Development) | High | Medium | [`adaptive_ml.rla.losses`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py) |
| **EVO-RLA-004** | **P2** | New Engineering | Phase 9 & Phase 13 | Medium | Low | NumPy Vectorization |
| **EVO-RLA-005** | **P3** | Proposed Enhancement | Phase 9 (RLA Development) | Medium | Low | [`adaptive_ml.rla.weighting`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/weighting.py) |
| **EVO-RLA-006** | **P4** | Deferred Opportunity | Phase 21 (Continuous R&D) | Very High | High | Deep Feature Embeddings |

---

### Detailed Specification of Evolution Items

#### EVO-RLA-001: Approximate Random-Projection Density Estimation for Streaming RLA
- **Classification:** Proposed Enhancement
- **Priority:** P1
- **Phase Mapping:** Phase 9 (RLA Development)
- **Problem Statement:** Exact $k$-NN density computation in [`DensityAwareMarginScorer`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py) requires $\mathcal{O}(N^2 d)$ operations, which throttles streaming throughput when buffer sizes exceed $5,000$ samples.
- **Mathematical Design Requirements:** Implement streaming Locality-Sensitive Hashing (LSH) or random projection histograms to approximate local density $\rho(x_i)$ in $\mathcal{O}(N \cdot K \cdot \log d)$:
  $$\hat{\rho}(x_i) = \frac{1}{M} \sum_{m=1}^M \text{count}\left( \text{bucket}_m(x_i) \right)$$
- **Implementation Dependencies:** Pure NumPy, zero external dependencies.
- **Validation Requirements:** Compare sample ranking correlation (Spearman's $\rho \ge 0.92$) against exact $k$-NN density across standard benchmark datasets.
- **Acceptance Criteria:** Throughput of reliability scoring increased by $\ge 8\times$ on $N = 10,000, d = 64$; memory overhead $\le 2\text{ MB}$.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RLA-002: Online Peer Loss for Noise-Rate-Agnostic Learning
- **Classification:** New Research
- **Priority:** P1
- **Phase Mapping:** Phase 9 (RLA Development) & Phase 12 (Benchmarking)
- **Problem Statement:** Existing robust losses ([`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py), [`GeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py)) require tuning hyperparameters ($\alpha, \beta, q$) according to the unknown noise fraction $\eta$. If noise rate is misestimated, performance drops significantly.
- **Research Hypothesis:** Implementing an online Peer Loss formulation achieves risk-minimization consistency without requiring prior knowledge or estimation of the label corruption rate:
  $$\mathcal{L}_{\text{peer}}(f(x_i), y_i) = \mathcal{L}(f(x_i), y_i) - \mathcal{L}(f(x_{p_1}), y_{p_2})$$
  where $(x_{p_1}, y_{p_2})$ are randomly paired exemplars drawn independently from a decoupled running stream buffer.
- **Relevant Prior Art:**
  - Liu & Guo (2020): *Peer Loss Functions: Learning from Noisy Labels without Knowing Noise Rates* (ICML).
  - Charoenphakdee et al. (2019): *On Symmetric Losses for Learning from Corrupted Labels* (ICML).
- **Validation Requirements:** Evaluate on CIFAR-10 and Synthetic Stream with 20% to 60% symmetric and asymmetric label noise without providing noise rate to the optimizer.
- **Acceptance Criteria:** Outperforms standard Cross-Entropy by $\ge 12\%$ accuracy on $40\%$ symmetric noise; performs within $2\%$ of oracle-tuned GCE without hyperparameter search.
- **Estimated Complexity:** High.
- **Risk:** Medium (variance of peer sample gradient estimates during early training).

---

#### EVO-RLA-003: Streaming Noise Transition Matrix ($\mathbf{T}$) Estimation
- **Classification:** New Research
- **Priority:** P2
- **Phase Mapping:** Phase 9 (RLA Development)
- **Problem Statement:** Under class-conditional asymmetric noise (e.g., Class 1 flipped to Class 2 with probability $P(Y=2 \vert Y^*=1) = 0.4$), standard robust losses experience asymmetric boundary shrinkage.
- **Research Hypothesis:** Tracking out-of-fold calibrated class prediction probabilities across high-confidence anchor exemplars allows online estimation of the noise transition matrix $\mathbf{T}_{j, k} = P(\tilde{Y} = k \vert Y^* = j)$, enabling backward loss correction:
  $$\vec{\ell}_{\text{corrected}}(x) = \mathbf{T}^{-1} \vec{\ell}(f(x))$$
- **Relevant Prior Art:**
  - Patrini et al. (2017): *Making Deep Neural Networks Robust to Label Noise: A Loss Correction Approach* (CVPR).
  - Northcutt et al. (2021): *Confident Learning: Estimating Uncertainty in Dataset Labels* (JAIR).
- **Validation Requirements:** Synthetic asymmetric noise benchmark on Forest CoverType with known transition matrix.
- **Acceptance Criteria:** Frobenius norm error $\| \widehat{\mathbf{T}} - \mathbf{T} \|_F \le 0.08$ within $5,000$ stream samples; test accuracy within $4\%$ of clean oracle model.
- **Estimated Complexity:** High.
- **Risk:** Medium (inversion instability when $\det(\mathbf{T}) \to 0$; requires regularized pseudo-inverse).

---

#### EVO-RLA-004: Robust Continuous Loss Functions for Streaming Regression
- **Classification:** New Engineering
- **Priority:** P2
- **Phase Mapping:** Phase 9 (RLA Development) & Phase 13 (Framework Integrations)
- **Problem Statement:** Real-world continuous streaming data (e.g., IoT sensor telemetry, financial pricing) is contaminated by non-Gaussian outliers, sensor clipping, and transient spikes that corrupt standard MSE/MAE estimators.
- **Mathematical Design Requirements:** Implement vectorized Huber loss, Cauchy loss, and Tukey Bisquare loss with adaptive scale parameter estimation:
  $$\mathcal{L}_{\text{Huber}}(r, \delta) = \begin{cases} \frac{1}{2} r^2 & \text{if } \vert r \vert \le \delta \\ \delta \vert r \vert - \frac{1}{2} \delta^2 & \text{otherwise} \end{cases}$$
  where $\delta = 1.345 \cdot \text{MAD}(r)$ is updated online using Welford median absolute deviation.
- **Implementation Dependencies:** Pure NumPy, compatible with scikit-learn `SGDRegressor` and PyTorch custom loss.
- **Validation Requirements:** Test on California Housing with $20\%$ injected heavy-tailed Cauchy noise.
- **Acceptance Criteria:** Relative Mean Absolute Error (MAE) reduced by $\ge 35\%$ compared to standard MSE under heavy noise.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RLA-005: Tail Distribution Guardian for Extreme Class Imbalance ($>10,000:1$)
- **Classification:** Proposed Enhancement
- **Priority:** P3
- **Phase Mapping:** Phase 9 (RLA Development)
- **Problem Statement:** In ultra-rare anomaly detection (fraud rate $< 0.01\%$), standard sample reliability scoring penalizes minority class instances because their prediction margins are initially low, mistaking legitimate anomalies for noise.
- **Mathematical Design Requirements:** Formulate an intrinsic rarity prior modulation into [`DensityAwareMarginScorer`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py):
  $$r_i^* = \max\left( r_i, \left(\frac{N_{\min}}{N_{y_i}}\right)^\gamma \cdot \mathbb{I}(\rho(x_i) > \tau_{\text{cluster}}) \right)$$
- **Implementation Dependencies:** [`adaptive_ml.rla.scorer`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/scorer.py), [`adaptive_ml.rla.weighting`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/weighting.py).
- **Validation Requirements:** Credit Card Fraud detection benchmark ($0.17\%$ positive rate) with $10\%$ simulated label noise.
- **Acceptance Criteria:** False negative rate on rare class reduced by $\ge 25\%$ compared to unadjusted Confident Learning baseline; zero legitimate rare-class pruning verified.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RLA-006: Representation-Space Contrastive Sample Purification
- **Classification:** Deferred Opportunity
- **Priority:** P4
- **Phase Mapping:** Phase 21 (Continuous R&D)
- **Problem Statement:** Disentangling semantic noise from aleatoric uncertainty in complex unstructured data (e.g., vision/audio) requires deep representation geometry.
- **Proposed Exploration:** Investigate streaming self-supervised contrastive anchor clustering to detect label noise in latent feature space.
- **Acceptance Criteria:** Accurate label noise identification on WebVision without external supervision.
- **Estimated Complexity:** Very High.
- **Risk:** High (demands GPU compute for contrastive representations, violating core CPU-first constraint).
