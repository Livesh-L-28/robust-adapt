# Long-Term Scientific Research Roadmap v2.0

**Document Identifier:** `DOC-STRAT-EVO-RES-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Strategic Planning Document (Submitted for Project Owner Review — Formal Acceptance Pending)<br>

---

## 1. Research Philosophy & Governance Compliance

The research program of **AdaptiveML** is governed by the **Ten Inviolable Research Governance Rules** established in [`docs/foundation/RESEARCH_GOVERNANCE.md`](file:///c:/projects/AdaptiveML/docs/foundation/RESEARCH_GOVERNANCE.md).

To ensure absolute scientific integrity:
1. **Rule 1 (Separation of Fact and Hypothesis):** Every research inquiry is formally designated as a **Working Hypothesis** until corroborated by formal mathematical proof or multi-seed empirical reproduction.
2. **Rule 3 (Novelty Claim Restriction):** No algorithmic novelty is claimed without exhaustive prior-art vetting across IEEE, ACM, NeurIPS, ICML, ICLR, and international patent databases.
3. **Rule 4 (Superiority Claim Restriction):** Algorithmic superiority claims require a minimum of 5 randomized seeds, Wilcoxon signed-rank significance testing ($p < 0.01$), and open benchmark artifacts.
4. **Rule 5 (Preservation of Negative Results):** Algorithmic failure regimes and negative outcomes are preserved and published in the repository without suppression.

---

## 2. Seven Core Research Directions

```
+-------------------------------------------------------------------------------------------------------+
|                                    ADAPTIVEML SCIENTIFIC FRONTIERS                                    |
+-----------------------------+-------------------------------+-----------------------------------------+
| 1. Adaptive Learning        | 2. Robust Learning            | 3. Resource-Aware Optimization          |
|   - Multivariate drift MMD  |   - Noise-rate-agnostic loss  |   - 4-bit CPU NormalFloat quantization  |
|   - Dynamic tree histograms |   - Asymmetric noise matrices |   - Stochastic rounding convergence     |
+-----------------------------+-------------------------------+-----------------------------------------+
| 4. Unified Decision-Making  | 5. Continual Learning         | 6. Explainable Interventions            |
|   - Bayesian belief fusion  |   - Elastic parameter masks   |   - Counterfactual attribution          |
|   - Drift/noise disentangle |   - Recency-decayed replay    |   - Spatial error variance ratios       |
+-----------------------------+-------------------------------+-----------------------------------------+
| 7. Resource-Constrained Edge Adaptation: Sub-10MB streaming ML models for local-first computing        |
+-------------------------------------------------------------------------------------------------------+
```

---

## 3. Comprehensive Direction Specifications

### Research Direction 1: Adaptive Learning — Multivariate Streaming Covariate Shift

- **Problem Statement:** Real-world concept drift often begins as subtle virtual covariate shift $P(X)$ before inducing observable label error degradation $P(Y \vert X)$. Tracking hundreds of univariate detectors is statistically fragile and computationally prohibitive.
- **Existing Prior Art to Investigate:**
  - Bifet & Gavaldà (2007): *Learning from Time-Changing Data with Adaptive Windowing* (ADWIN).
  - Gretton et al. (2012): *A Kernel Two-Sample Test* (JMLR).
  - Hulten, Spencer, Domingos (2001): *Mining Time-Changing Data Streams* (KDD - VFDT).
  - Dasgupta & Gupta (2003): *An Elementary Proof of a Theorem of Johnson and Lindenstrauss*.
- **Research Hypothesis (Proposed):** Streaming random projections coupled with online Maximum Mean Discrepancy (MMD) on compressed Gaussian kernels can detect high-dimensional covariate shift within $\le 120$ samples while maintaining a bounded false alarm rate $\le 2\%$.
- **Mathematical Questions:**
  1. What is the minimum projection dimension $k$ that preserves test power $\ge 0.95$ under bounded Johnson-Lindenstrauss distortion $\epsilon$?
  2. Can streaming kernel bandwidth $\sigma$ be updated adaptively using online median heuristics without storing quadratic distance matrices?
- **Required Datasets:** Synthetic Rotating Hyperplane, SEA concepts, ELEC2, Forest CoverType.
- **Baselines:** Univariate ADWIN per feature, DDM, EDDM, Offline MMD two-sample test.
- **Evaluation Metrics:** Mean detection lag (samples), False Positive Rate (FPR), Post-drift recovery time.
- **Potential Failure Modes:** Kernel bandwidth collapse under sudden variance explosion; projection blind spots for adversarial low-rank shifts.
- **Publication Potential:** High (Target: *ICML* / *NeurIPS* - Learning in Non-Stationary Environments).

---

### Research Direction 2: Robust Learning — Noise-Rate-Agnostic Streaming Risk Minimization

- **Problem Statement:** Existing robust loss functions (e.g., GCE, SCE) require manual tuning of hyperparameters ($\alpha, \beta, q$) that depend directly on the unknown label corruption rate $\eta$. When noise rates fluctuate dynamically across a stream, static hyperparameters either overfit or fail to learn.
- **Existing Prior Art to Investigate:**
  - Zhang & Sabuncu (2018): *Generalized Cross Entropy Loss for Training Deep Neural Networks with Noisy Labels* (NeurIPS).
  - Wang et al. (2019): *Symmetric Cross Entropy for Robust Learning with Noisy Labels* (ICCV).
  - Liu & Guo (2020): *Peer Loss Functions: Learning from Noisy Labels without Knowing Noise Rates* (ICML).
  - Northcutt et al. (2021): *Confident Learning: Estimating Uncertainty in Dataset Labels* (JAIR).
- **Research Hypothesis (Proposed):** An online Peer Loss formulation that dynamically pairs incoming mini-batches with decorrelated historical exemplars achieves risk minimization consistency without requiring prior knowledge or manual calibration of noise rates.
- **Mathematical Questions:**
  1. Under what buffer decorrelation lag $\tau$ does the empirical peer loss gradient $\nabla \mathcal{L}_{\text{peer}}$ remain an unbiased estimator of clean-risk gradients?
  2. What is the variance bound of the peer gradient estimator under extreme class imbalance?
- **Required Datasets:** CIFAR-10N (human noise), WebVision, Corrupted Tabular (California Housing, CoverType).
- **Baselines:** Standard Cross-Entropy, Symmetric Cross-Entropy (SCE), Generalized Cross-Entropy (GCE), Cleanlab Confident Learning.
- **Evaluation Metrics:** Test set Accuracy / F1 under $20\%$, $40\%$, and $60\%$ symmetric/asymmetric noise; hyperparameter sensitivity curve.
- **Potential Failure Modes:** Gradient variance explosion during early warm-up phases; class collapse when peer samples are drawn from majority classes under imbalance.
- **Publication Potential:** High (Target: *NeurIPS* / *ICLR* - Robust Representation & Optimization).

---

### Research Direction 3: Resource-Aware Optimization — Sub-8-bit CPU Optimization with Stochastic Rounding

- **Problem Statement:** First-order optimizers dominate memory during local-first model training. 8-bit block quantization saves $50\%$ memory, but reducing precision to 4 bits on CPU causes optimization stagnation due to directional quantization bias.
- **Existing Prior Art to Investigate:**
  - Dettmers et al. (2022): *8-bit Optimizers via Block-wise Quantization* (ICLR).
  - Dettmers et al. (2023): *QLoRA: Efficient Finetuning of Quantized LLMs* (NeurIPS).
  - Shazeer & Stern (2018): *Adafactor: Adaptive Learning Rates with Sublinear Memory Cost* (ICML).
  - Connolly et al. (2021): *Stochastic Rounding and Its Numerical Properties* (SIAM Scientific Computing).
- **Research Hypothesis (Proposed):** Applying hardware-efficient stochastic rounding to non-linear NormalFloat (NF4) quantile representations guarantees unbiased gradient expectation $\mathbb{E}[\text{quant}(x)] = x$, enabling smooth convergence for 4-bit CPU optimizer states without custom CUDA kernels.
- **Mathematical Questions:**
  1. What is the asymptotic convergence rate $\mathcal{O}(1/\sqrt{T})$ under $L$-smooth non-convex objectives when first and second moments are quantized to 4-bit NF4 with stochastic rounding?
  2. Can stochastic rounding pseudo-random bits be generated using lightweight xorshift algorithms with zero CPU vector stalls?
- **Required Datasets:** Mini-Transformer (WikiText-103), ResNet-18 (CIFAR-10), Tabular MLP (CoverType).
- **Baselines:** Standard 32-bit AdamW, 16-bit Adam, 8-bit AdamW, Adafactor.
- **Evaluation Metrics:** Peak state memory footprint (bytes/param), step execution wall-clock time (ms), final validation perplexity / accuracy.
- **Potential Failure Modes:** CPU cache misses due to bit-packing/unpacking routines; pseudo-random number generator throughput overhead.
- **Publication Potential:** High (Target: *MLSys* / *JMLR* - Systems and Optimization for Machine Learning).

---

### Research Direction 4: Unified Decision-Making — Disentangling Concept Drift from Noise Bursts

- **Problem Statement:** When predictive performance suddenly drops in streaming environments, naive systems cannot determine whether the underlying distribution changed (demanding high model plasticity) or whether sensor noise surged (demanding aggressive sample rejection). Confusing the two causes catastrophic parameter corruption.
- **Existing Prior Art to Investigate:**
  - Ditzler et al. (2015): *Learning under Concept Drift: An Overview* (IEEE Computational Intelligence Magazine).
  - Lipton et al. (2018): *Detecting and Correcting for Label Shift with Black Box Predictors* (ICML).
  - Gama et al. (2014): *A Survey on Concept Drift Adaptation* (ACM Computing Surveys).
- **Research Hypothesis (Proposed):** The spatial neighborhood variance of prediction errors $\Lambda(t) = \frac{\text{Var}_{\text{local}}(e_t)}{\text{Var}_{\text{global}}(e_t)}$ provides a statistically sufficient discriminator: concept drift manifests as localized cluster errors ($\Lambda \ll 1$), whereas label noise manifests as globally dispersed errors ($\Lambda \approx 1$).
- **Mathematical Questions:**
  1. What is the minimum local neighborhood sample size $k$ required to guarantee bounded type-I error in classifying drift vs noise?
  2. Can the spatial error ratio be tracked in $\mathcal{O}(1)$ time per sample using streaming randomized hashing?
- **Required Datasets:** Synthetic streaming benchmarks with alternating drift and noise bursts; Industrial sensor telemetry (Turbofan Engine).
- **Baselines:** Standalone ADWIN, Standalone RLA Margin Scorer, Static Heuristic ULC Automaton.
- **Evaluation Metrics:** Attribution classification accuracy ($\%$), model recovery rate, parameter stability score.
- **Potential Failure Modes:** High-dimensional manifolds where local neighborhoods are sparsely populated; boundary drift affecting solitary outliers.
- **Publication Potential:** Very High (Target: *JMLR* / *IEEE TPAMI* - Foundational Machine Learning Theory).

---

### Research Direction 5: Continual Learning — Elastic Parameter Masking with Sub-Linear State Memory

- **Problem Statement:** Neural networks suffer catastrophic forgetting when exposed to sequentially shifting data regimes. Standard Elastic Weight Consolidation (EWC) requires storing full diagonal Fisher matrices, doubling memory consumption.
- **Existing Prior Art to Investigate:**
  - Kirkpatrick et al. (2017): *Overcoming Catastrophic Forgetting in Neural Networks* (PNAS).
  - Lopez-Paz & Ranzato (2017): *Gradient Episodic Memory for Continual Learning* (NeurIPS).
  - Mallya & Lazebnik (2018): *PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning* (CVPR).
- **Research Hypothesis (Proposed):** A dynamic parameter volatility accumulator combined with sparse binary masking achieves comparable backward transfer protection to EWC while consuming $\le 1\text{ bit per parameter}$ of auxiliary state memory.
- **Mathematical Questions:**
  1. Does gradient magnitude volatility over streaming windows correlate asymptotically with empirical Fisher information eigenvalues?
  2. What is the theoretical capacity bound (number of sequential tasks) before parameter masking induces representational deadlocks?
- **Required Datasets:** Permuted-MNIST, Split-CIFAR-10, Split-MiniImageNet.
- **Baselines:** Naive Fine-Tuning, EWC, GEM, Reservoir Replay.
- **Evaluation Metrics:** Average Accuracy (ACC), Backward Transfer (BWT), Forward Transfer (FWT), State Memory Overhead (MB).
- **Potential Failure Modes:** Gradient volatility saturation in deep layers causing premature weight freezing.
- **Publication Potential:** High (Target: *ICLR* / *NeurIPS* - Continual & Lifelong Learning).

---

### Research Direction 6: Explainable Interventions — Counterfactual Attribution for Controller Decisions

- **Problem Statement:** In regulated industries (e.g., credit, insurance, healthcare), automated controller adjustments to learning rates, sample weights, or pruning must be transparent and legally defensible.
- **Existing Prior Art to Investigate:**
  - Wachter et al. (2017): *Counterfactual Explanations without Opening the Black Box: Automated Decisions and the GDPR* (Harvard JL&T).
  - Lundberg & Lee (2017): *A Unified Approach to Interpreting Model Predictions* (NeurIPS - SHAP).
- **Research Hypothesis (Proposed):** Tracking the gradient contribution of each evidence signal vector component $\frac{\partial \text{Directive}}{\partial E_k}$ provides instant, exact Shapley-consistent attribution of why a specific adaptation or suppression directive was issued.
- **Mathematical Questions:**
  1. Can exact linear attribution be computed in $\mathcal{O}(1)$ time from the continuous controller belief state Jacobian?
- **Required Datasets:** Synthetic audit traces, Credit Card Fraud detection with documented shift events.
- **Baselines:** Post-hoc surrogate models, Rule-based logging.
- **Evaluation Metrics:** Attribution fidelity score, explanation computation latency ($\mu\text{s}$), compliance audit pass rate.
- **Potential Failure Modes:** Nonlinear directive saturation regions where gradients vanish ($\nabla \to 0$).
- **Publication Potential:** Medium-High (Target: *FAccT* / *AIES* - Transparency and Accountability in AI).

---

### Research Direction 7: Resource-Constrained Adaptation — Sub-10MB Streaming ML Models for Edge Hardware

- **Problem Statement:** Embedded microcontrollers and edge gateways (e.g., Raspberry Pi Zero, Cortex-M) operate with extreme memory constraints ($\le 32\text{ MB}$ total RAM). Most ML libraries cannot even initialize within this memory window.
- **Existing Prior Art to Investigate:**
  - David et al. (2021): *TensorFlow Lite Micro: Embedded Machine Learning on TinyML Systems*.
  - Kumar et al. (2017): *Resource-Efficient Machine Learning in 2 KB RAM for the Internet of Things* (ICML - Bonsai).
- **Research Hypothesis (Proposed):** Combining quantized streaming decision trees, 8-bit state buffers, and fixed-size circular replay enables online continual adaptation within a strictly guaranteed $\le 10\text{ MB}$ physical memory ceiling on 32-bit/64-bit embedded CPU cores.
- **Mathematical Questions:**
  1. What is the trade-off curve between reservoir buffer capacity $M$, leaf quantization precision $b$, and streaming classification accuracy on edge sensor streams?
- **Required Datasets:** UCI HAR (Human Activity Recognition), Gas Sensor Array Drift, Bosch Industrial Telemetry.
- **Baselines:** TFLite Micro, scikit-learn SGDClassifier (streaming mode), River HoeffdingTree.
- **Evaluation Metrics:** Peak physical RSS memory (MB), CPU execution cycles per sample, accuracy retention under drift.
- **Potential Failure Modes:** Memory fragmentation in standard CPython allocators; stack overflow on deep tree branches.
- **Publication Potential:** High (Target: *MLSys* / *TinyML* / *IEEE IoT Journal*).

---

## 4. Itemized Research Evolution Register

| Identifier | Priority | Research Direction | Target Academic Venue | Theoretical Risk | Estimated Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-RES-001** | **P1** | Multivariate Covariate Shift MMD | *ICML* / *NeurIPS* | Medium | High |
| **EVO-RES-002** | **P1** | Noise-Rate-Agnostic Peer Loss | *NeurIPS* / *ICLR* | Medium | High |
| **EVO-RES-003** | **P1** | 4-bit CPU NormalFloat Optimization | *MLSys* / *JMLR* | Medium | High |
| **EVO-RES-004** | **P1** | Drift vs Noise Spatial Disentanglement | *JMLR* / *IEEE TPAMI* | Medium | Very High |
| **EVO-RES-005** | **P2** | Elastic Parameter Masking | *ICLR* / *NeurIPS* | High | High |
| **EVO-RES-006** | **P3** | Counterfactual Controller Attribution | *FAccT* / *AIES* | Low | Medium |
| **EVO-RES-007** | **P3** | Sub-10MB TinyML Adaptation | *MLSys* / *TinyML* | Low | High |

---

## 5. Negative Results Registry Protocol

In compliance with **Research Governance Rule 5**, any empirical evaluation where an AdaptiveML research hypothesis fails to outperform standard baselines (e.g., standard AdamW or unweighted ERM) or exhibits pathological convergence failure must be documented in `docs/research/NEGATIVE_RESULTS_REGISTRY.md`.

Each negative entry must detail:
1. Hypothesis Identifier.
2. Dataset and seed configuration.
3. Observed vs expected mathematical behavior.
4. Root cause analysis (e.g., gradient variance, manifold sparsity, numerical underflow).
5. Theoretical boundaries established by the negative outcome.

---

## 6. Academic Citation & Evidence Verification Table

The following table documents and verifies every academic literature citation supporting the research roadmap, distinguishing verified established prior art from proposed research hypotheses:

| Ref ID | Full Citation (Authors, Title, Venue, Year) | DOI / Stable Identifier | Claim Supported in Literature | Relevance to AdaptiveML | Scientific Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REF-001** | Bifet & Gavaldà, *Learning from Time-Changing Data with Adaptive Windowing*, SDM, 2007. | DOI: 10.1137/1.9781611972771.42 | Hoeffding bounds on sliding sub-windows bound univariate error drift. | Theoretical basis for [`ReliabilityWeightedADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py). | **Established Prior Art** |
| **REF-002** | Gretton et al., *A Kernel Two-Sample Test*, JMLR, 13:723–773, 2012. | Stable: jmrl.org/papers/v13/gretton12a.html | Maximum Mean Discrepancy (MMD) tests divergence between multivariate distributions. | Foundation for proposed multivariate covariate drift detector (**EVO-ALA-002**). | **Established Prior Art** |
| **REF-003** | Hulten et al., *Mining Time-Changing Data Streams*, ACM KDD, pp. 97–106, 2001. | DOI: 10.1145/502512.502529 | Concept-drifting Hoeffding decision trees using sub-tree replacement. | Architectural inspiration for streaming tree splitting in ALA. | **Established Prior Art** |
| **REF-004** | Dasgupta & Gupta, *An Elementary Proof of a Theorem of Johnson and Lindenstrauss*, Random Struct. & Alg., 22(1):60–65, 2003. | DOI: 10.1002/rsa.10073 | Random linear projections preserve pairwise $\ell_2$ distances within bounded distortion. | Justification for dimension reduction in multivariate drift detection. | **Established Prior Art** |
| **REF-005** | Zhang & Sabuncu, *Generalized Cross Entropy Loss for Training Deep Neural Networks with Noisy Labels*, NeurIPS, 31:8778–8788, 2018. | Stable: proceedings.neurips.cc/paper/2018/hash/f2925f97bc1379f4420f3e50f3157a14-Abstract.html | Box-Cox $q$-loss provides noise tolerance by bounding gradient magnitudes. | Directly implemented in [`GeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py). | **Established Prior Art** |
| **REF-006** | Wang et al., *Symmetric Cross Entropy for Robust Learning with Noisy Labels*, IEEE ICCV, pp. 322–330, 2019. | DOI: 10.1109/ICCV.2019.00041 | Reverse Cross Entropy balances standard Cross Entropy to bound gradient explosion under noise. | Directly implemented in [`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py). | **Established Prior Art** |
| **REF-007** | Liu & Guo, *Peer Loss Functions: Learning from Noisy Labels without Knowing Noise Rates*, ICML, PMLR 119:6226–6236, 2020. | Stable: proceedings.mlr.press/v119/liu20e.html | Random peer sample penalty achieves empirical risk consistency under unknown noise rates. | Theoretical basis for proposed streaming peer loss (**EVO-RLA-002**). | **Established Prior Art** |
| **REF-008** | Northcutt et al., *Confident Learning: Estimating Uncertainty in Dataset Labels*, JAIR, 70:1373–1411, 2021. | DOI: 10.1613/jair.1.12125 | Out-of-fold calibrated probabilities estimate noise transition matrix $\mathbf{T}$. | Foundation for proposed streaming transition matrix estimation (**EVO-RLA-003**). | **Established Prior Art** |
| **REF-009** | Charoenphakdee et al., *On Symmetric Losses for Learning from Corrupted Labels*, ICML, PMLR 97:961–970, 2019. | Stable: proceedings.mlr.press/v97/charoenphakdee19a.html | Inherent classification calibration trade-offs in symmetric loss functions. | Guides hyperparameter bounds for RLA loss implementations. | **Established Prior Art** |
| **REF-010** | Patrini et al., *Making Deep Neural Networks Robust to Label Noise: A Loss Correction Approach*, CVPR, pp. 1944–1952, 2017. | DOI: 10.1109/CVPR.2017.210 | Forward and backward loss correction using estimated noise transition matrices. | Informs backward loss correction in streaming RLA. | **Established Prior Art** |
| **REF-011** | Cui et al., *Class-Balanced Loss Based on Effective Number of Samples*, CVPR, pp. 9268–9277, 2019. | DOI: 10.1109/CVPR.2019.00949 | Effective volume of sample space scales as $(1 - \beta^n)/(1 - \beta)$. | Directly implemented in [`ClassBalancedWeights`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/weighting.py). | **Established Prior Art** |
| **REF-012** | Dettmers et al., *8-bit Optimizers via Block-wise Quantization*, ICLR, 2022. | Stable: openreview.net/forum?id=shpkpfgZExQ | Independent block quantization maintains non-linear dynamic range for optimizer states. | Directly implemented in [`BlockQuantizer`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/quantizer.py) and [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py). | **Established Prior Art** |
| **REF-013** | Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs*, NeurIPS, 36:10088–10115, 2023. | Stable: proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87518f700445d42... | NormalFloat 4-bit (NF4) quantile grid is information-theoretically optimal for $\mathcal{N}(0, 1)$. | Informs CPU 4-bit NormalFloat exploration (**EVO-RAO-002**). | **Established Prior Art** |
| **REF-014** | Shazeer & Stern, *Adafactor: Adaptive Learning Rates with Sublinear Memory Cost*, ICML, PMLR 80:4596–4604, 2018. | Stable: proceedings.mlr.press/v80/shazeer18a.html | Rank-1 row and column sums reduce second-moment storage from $\mathcal{O}(d_1 d_2)$ to $\mathcal{O}(d_1 + d_2)$. | Foundation for proposed NumPy Adafactor (**EVO-RAO-001**). | **Established Prior Art** |
| **REF-015** | Connolly et al., *Stochastic Rounding and Its Numerical Properties*, SIAM J. Sci. Comput., 43(1):A566–A585, 2021. | DOI: 10.1137/20M1334047 | Probabilistic rounding ensures unbiased expectation $\mathbb{E}[\text{SR}(x)] = x$. | Mathematical foundation for proposed unbiased 4-bit accumulator (**EVO-RAO-005**). | **Established Prior Art** |
| **REF-016** | Banner et al., *Post-Training 4-bit Quantization of Convolutional Networks for Rapid-Deployment*, NeurIPS, 32:7948–7956, 2019. | Stable: proceedings.neurips.cc/paper/2019/hash/c0a6496f8c7b89d6e49... | Per-channel 4-bit integer quantization bounds accuracy loss in feedforward networks. | Prior art for low-bit state representation. | **Established Prior Art** |
| **REF-017** | Ditzler et al., *Learning under Concept Drift: An Overview*, IEEE CIM, 10(4):12–25, 2015. | DOI: 10.1109/MCI.2015.2471238 | Comprehensive taxonomy of concept drift adaptation mechanisms. | Theoretical foundation for ULC multi-state arbitration. | **Established Prior Art** |
| **REF-018** | Lipton et al., *Detecting and Correcting for Label Shift with Black Box Predictors*, ICML, PMLR 80:3122–3130, 2018. | Stable: proceedings.mlr.press/v80/lipton18a.html | Confusion matrix inversion corrects target distribution shifts without retraining. | Informs label shift correction in ULC. | **Established Prior Art** |
| **REF-019** | Kirkpatrick et al., *Overcoming Catastrophic Forgetting in Neural Networks*, PNAS, 114(13):3521–3526, 2017. | DOI: 10.1073/pnas.1611835114 | Diagonal Fisher Information penalty protects critical parameters from task overwrite. | Benchmark baseline for continual learning comparisons. | **Established Prior Art** |
| **REF-020** | Lopez-Paz & Ranzato, *Gradient Episodic Memory for Continual Learning*, NeurIPS, 30:6467–6476, 2017. | Stable: proceedings.neurips.cc/paper/2017/hash/f8752270902be78b57d... | Constraining gradient updates to non-negative inner products with historical buffers prevents forgetting. | Baseline for streaming replay evaluation in ALA. | **Established Prior Art** |
| **REF-021** | Mallya & Lazebnik, *PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning*, CVPR, pp. 7765–7773, 2018. | DOI: 10.1109/CVPR.2018.00810 | Binary parameter masking isolates task parameters without memory overhead. | Informs proposed elastic parameter volatility mask (**EVO-ALA-005**). | **Established Prior Art** |
| **REF-022** | Wachter et al., *Counterfactual Explanations without Opening the Black Box*, Harvard JL&T, 31(2):841–887, 2017. | Stable: jolt.law.harvard.edu/assets/articlePDFs/v31/Counterfactual-Explanations-Wachter.pdf | Counterfactual interventions provide interpretable explanations for algorithmic decisions under GDPR. | Informs explainable controller audit logging (**EVO-ULC-003**). | **Established Prior Art** |
| **REF-023** | Lundberg & Lee, *A Unified Approach to Interpreting Model Predictions*, NeurIPS, 30:4765–4774, 2017. | Stable: proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c... | Shapley values provide additive feature attribution for predictive models. | Guides attribution formulation in ULC evidence explanation. | **Established Prior Art** |
| **REF-024** | David et al., *TensorFlow Lite Micro: Embedded Machine Learning on TinyML Systems*, MLSys, 3:800–811, 2021. | Stable: proceedings.mlsys.org/paper/2021/hash/9b8619251a19057cff7... | Interpreted TinyML kernels run within constrained physical RAM on microcontrollers. | Sets hardware baselines for proposed TinyML adaptation (**EVO-RES-007**). | **Established Prior Art** |
| **REF-025** | Kumar et al., *Resource-Efficient Machine Learning in 2 KB RAM for the Internet of Things*, ICML, PMLR 70:1935–1944, 2017. | Stable: proceedings.mlr.press/v70/kumar17a.html | Tree-based models can be optimized to execute within extreme micro-memory boundaries. | Feasibility proof for sub-10MB edge streaming trees. | **Established Prior Art** |
| **REF-026** | Li et al., *A Contextual-Bandit Approach to Personalized News Article Recommendation*, ACM WWW, pp. 661–670, 2010. | DOI: 10.1145/1772690.1772758 | LinUCB algorithm achieves sublinear regret in online contextual decision making. | Theoretical basis for proposed contextual bandit ULC tuning (**EVO-ULC-005**). | **Established Prior Art** |
| **REF-027** | Auer et al., *Finite-time Analysis of the Multiarmed Bandit Problem*, Machine Learning, 47(2):235–256, 2002. | DOI: 10.1023/A:1013689704352 | Upper Confidence Bound (UCB1) balances exploration and exploitation with logarithmic regret bounds. | Informs directive self-tuning in ULC. | **Established Prior Art** |


### 6.2 Epistemological Classification: Established Prior Art vs. Proposed Research Hypotheses

In strict adherence to **Research Governance Rule 1 (Separation of Fact and Hypothesis)**:
- **Established Prior Art:** All 27 works cataloged in the evidence table above (REF-001 through REF-027) represent peer-reviewed, published academic literature with verified experimental findings.
- **Proposed Research Hypotheses:** The architectural extensions proposed for AdaptiveML (e.g., streaming peer loss with decoupled FIFO buffers, CPU-native NormalFloat with bit-packing, and spatial error variance ratios for drift vs noise attribution) are **strictly unproven research hypotheses**.
- In compliance with **Research Governance Rules 3, 4, and 5**, no claims of performance superiority or novelty will be asserted until multi-seed empirical benchmarking and statistical significance testing ( < 0.01$) are executed in future research phases.
