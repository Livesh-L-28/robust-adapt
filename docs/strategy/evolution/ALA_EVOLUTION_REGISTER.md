# Adaptive Learning Algorithms (ALA) — Evolution Register v2.0

**Document Identifier:** `DOC-STRAT-EVO-ALA-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Target Module:** [`adaptive_ml.ala`](file:///c:/projects/AdaptiveML/adaptive_ml/ala)<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Approved Strategic Architecture<br>

---

## 1. Pillar Mission & Architectural Scope

The **Adaptive Learning Algorithms (ALA)** pillar provides CPU-first, local-first streaming algorithms capable of continuous adaptation to changing data distributions, non-stationary concept drift, and incremental data arrival without catastrophic forgetting.

In strict compliance with **Research Governance Rule 7 (Pillar Independence)**, ALA algorithms operate as standalone mathematical primitives implemented in pure Python and NumPy. ALA maintains zero imports from RLA or RAO. Optional coordination occurs exclusively through the Unified Learning Controller (ULC).

---

## 2. Baseline Capabilities Grounded in Verified Source Evidence

The current verified implementation of ALA in `aml-core==0.1.0.dev0` comprises five core components in [`adaptive_ml/ala`](file:///c:/projects/AdaptiveML/adaptive_ml/ala):

```
adaptive_ml/ala/
├── __init__.py           # Exports VectorizedHoeffdingTree, ReliabilityWeightedADWIN,
│                         # ClassBalancedReservoirReplay, StreamingEnsemble, AdaptiveClassifier
├── tree.py               # VectorizedHoeffdingTree (Streaming decision tree with Hoeffding bounds)
├── adwin.py              # ReliabilityWeightedADWIN (Adaptive sliding window drift detector)
├── replay.py             # ClassBalancedReservoirReplay (Experience replay with class balance)
├── ensemble.py           # StreamingEnsemble (Streaming bagging/boosting with drift adaptation)
└── classifier.py         # AdaptiveClassifier (Unified scikit-learn compatible estimator)
```

### 2.1 Verified Capabilities Inventory

| Component | Source File & Class | Mathematical Formulation / Implementation | Verified Invariants |
| :--- | :--- | :--- | :--- |
| **Streaming Decision Tree** | [`VectorizedHoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py#L32) in [`tree.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py) | Hoeffding bound $\epsilon = \sqrt{\frac{R^2 \ln(1/\delta)}{2n}}$; vectorized histogram split evaluation using information gain / Gini impurity | Validated under standard and `python -O` execution; raises [`ValidationError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py) on missing initialization (DEF-002 remediation) |
| **Adaptive Drift Detection** | [`ReliabilityWeightedADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py#L22) in [`adwin.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py) | Exponential histogram bucket compression; split evaluation $\vert \hat{\mu}_{W_0} - \hat{\mu}_{W_1} \vert > \epsilon_{\text{cut}}$ weighted by sample reliability $r_i$ | Bounded window size; dynamic bucket merging; exact sub-window variance calculation |
| **Experience Replay Buffer** | [`ClassBalancedReservoirReplay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py#L18) in [`replay.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) | Per-class reservoir sampling maintaining uniform empirical representation across rare and majority classes | Bounded total capacity $M$; $\mathcal{O}(1)$ sample insertion; zero memory allocation after warm-up |
| **Streaming Ensemble** | [`StreamingEnsemble`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/ensemble.py#L24) in [`ensemble.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/ensemble.py) | Online bagging with Poisson bootstrap ($\lambda = 1$); dynamic replacement of underperforming base learners upon drift alarm | Model pool pruning; drift alarm subscription; majority voting and soft probability aggregation |
| **Streaming Classifier** | [`AdaptiveClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py#L25) in [`classifier.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py) | Integrates tree/ensemble learning, ADWIN drift monitoring, and experience replay buffer into scikit-learn `partial_fit` API | Deterministic seed control via `numpy.random.Generator`; scikit-learn EstimatorProtocol compliance |

---

## 3. Current Limitations

Based on empirical profiling from Phase 12 benchmarks and Phase 14 memory audits:

1. **Univariate Drift Monitoring Constraint:** [`ReliabilityWeightedADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py) operates on scalar error streams $e_t \in [0, 1]$. Covariate drift in high-dimensional feature spaces ($X \in \mathbb{R}^d, d > 100$) requires either tracking $d$ independent scalar detectors or relying exclusively on posterior error rate degradation.
2. **High-Dimensional Tree Splitting Footprint:** In [`VectorizedHoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py), maintaining discrete bin histograms for continuous attributes across $L$ active leaves scales as $\mathcal{O}(L \cdot d \cdot B \cdot C)$ where $B$ is bin count and $C$ is class count. When $d > 500$, memory consumption on commodity CPU can exceed constrained budgets.
3. **Uniform Replay Decay:** [`ClassBalancedReservoirReplay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) enforces standard reservoir replacement within class partitions, which treats all stored historical samples with equal retention probability, lacking explicit recency decay or drift-aware sample invalidation.
4. **Binary & Multi-Class Restriction:** Existing streaming tree implementations support discrete classification. Streaming continuous regression trees ($y \in \mathbb{R}$) with variance reduction splits are currently unaddressed in the core library.

---

## 4. ALA Evolution Itemized Register

| Identifier | Priority | Classification | Original Phase Mapping | Complexity | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-ALA-001** | **P1** | Proposed Enhancement | Phase 8 (ALA Development) | Medium | Low | None (Pure NumPy) |
| **EVO-ALA-002** | **P1** | New Research | Phase 8 & Phase 12 | High | Medium | Phase 12 Benchmarks |
| **EVO-ALA-003** | **P2** | Proposed Enhancement | Phase 8 (ALA Development) | Medium | Low | `adaptive_ml.ala.replay` |
| **EVO-ALA-004** | **P2** | New Engineering | Phase 8 & Phase 13 | Medium | Low | `adaptive_ml.ala.tree` |
| **EVO-ALA-005** | **P3** | New Research | Phase 8 & Phase 21 | High | High | Mathematical Design |
| **EVO-ALA-006** | **P4** | Deferred Opportunity | Phase 21 (Continuous R&D) | Very High | High | External Vector Engines |

---

### Detailed Specification of Evolution Items

#### EVO-ALA-001: Streaming Quantile Summarizer for Tree Histogram Pruning
- **Classification:** Proposed Enhancement
- **Priority:** P1
- **Phase Mapping:** Phase 8 (ALA Development)
- **Problem Statement:** Continuous attribute split finding in [`VectorizedHoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py) currently pre-allocates uniform static bin edges. In non-stationary streams, feature ranges shift, causing bins to cluster or saturate, degrading Hoeffding split quality.
- **Mathematical Design Requirements:** Implement Greenwald-Khanna streaming quantile summaries or K-Means dynamic histograms per leaf attribute:
  $$\vert \text{rank}(x) - \widehat{\text{rank}}(x) \vert \le \epsilon_{\text{GK}} \cdot N$$
- **Implementation Dependencies:** Pure NumPy, zero external dependencies.
- **Validation Requirements:** Test split quality invariance on synthetic Gaussian streams whose variance shifts dynamically by $10\times$.
- **Acceptance Criteria:** Memory footprint per leaf node reduced by $\ge 40\%$ on $d \ge 100$ features without decreasing post-split test accuracy by $>0.5\%$.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ALA-002: Multivariate Covariate Shift Detector via Streaming Random Projections
- **Classification:** New Research
- **Priority:** P1
- **Phase Mapping:** Phase 8 (ALA Development) & Phase 12 (Benchmarking)
- **Problem Statement:** Concept drift often manifests as virtual covariate shift $P(X)$ before inducing observable label error degradation $P(Y \vert X)$. Existing [`ReliabilityWeightedADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py) detects only posterior loss degradation.
- **Research Hypothesis:** Projecting streaming features $X \in \mathbb{R}^d$ into a low-dimensional sketch space $\tilde{X} = X R \in \mathbb{R}^k$ ($k \ll d$) using an orthogonal Rademacher matrix enables early detection of covariate shift via streaming Maximum Mean Discrepancy (MMD) with bounded false positive rate:
  $$\text{MMD}^2(\mathcal{W}_{\text{ref}}, \mathcal{W}_{\text{curr}}) = \left\| \frac{1}{\vert\mathcal{W}_{\text{ref}}\vert} \sum_{x \in \mathcal{W}_{\text{ref}}} \phi(x) - \frac{1}{\vert\mathcal{W}_{\text{curr}}\vert} \sum_{x \in \mathcal{W}_{\text{curr}}} \phi(x) \right\|^2_{\mathcal{H}}$$
- **Relevant Prior Art:**
  - Bifet & Gavaldà (2007): *Learning from Time-Changing Data with Adaptive Windowing*.
  - Gretton et al. (2012): *A Kernel Two-Sample Test*.
  - Dasgupta & Gupta (2003): *An Elementary Proof of a Theorem of Johnson and Lindenstrauss*.
- **Validation Requirements:** Evaluate on synthetic rotating hyperplane, SEA concepts, and real-world Electricity (ELEC2) dataset. Measure detection lag against abrupt and gradual drift.
- **Acceptance Criteria:** Abrupt covariate drift detected within $\le 120$ samples; false positive rate $\le 2.0\%$ under stationary Gaussian noise.
- **Estimated Complexity:** High.
- **Risk:** Medium (calibration of kernel bandwidth $\sigma$ in streaming environments).

---

#### EVO-ALA-003: Exponentially Recency-Decayed Reservoir Replay
- **Classification:** Proposed Enhancement
- **Priority:** P2
- **Phase Mapping:** Phase 8 (ALA Development)
- **Problem Statement:** [`ClassBalancedReservoirReplay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) treats all historical exemplars equally once admitted. In severely non-stationary regimes, obsolete concepts remain indefinitely in the buffer, retarding adaptation.
- **Mathematical Design Requirements:** Formulate time-decayed inclusion probability:
  $$P(\text{retain sample } i \text{ at step } t) \propto \exp\left(-\gamma \cdot (t - t_i)\right) \cdot r_i$$
  where $\gamma > 0$ is the forgetting rate and $r_i \in [0, 1]$ is sample reliability from RLA.
- **Implementation Dependencies:** [`adaptive_ml.ala.replay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py).
- **Validation Requirements:** Verify catastrophic forgetting resistance on Split-MNIST benchmark with 5 tasks.
- **Acceptance Criteria:** Backward transfer (BWT) improved by $\ge 15\%$ relative to uniform reservoir sampling; zero memory leakage across $10^6$ streaming steps.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ALA-004: Vectorized Streaming Regression Trees
- **Classification:** New Engineering
- **Priority:** P2
- **Phase Mapping:** Phase 8 (ALA Development) & Phase 13 (Framework Integrations)
- **Problem Statement:** Current [`VectorizedHoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py) is restricted to discrete classification. Users requiring streaming continuous target estimation ($y \in \mathbb{R}$) cannot utilize ALA trees.
- **Mathematical Design Requirements:** Implement continuous split evaluation using SDR (Standard Deviation Reduction):
  $$\text{SDR} = \sigma(T) - \sum_{i} \frac{\vert T_i \vert}{\vert T \vert} \sigma(T_i)$$
  using running variance accumulators via Welford's algorithm to ensure numerical stability.
- **Implementation Dependencies:** NumPy, [`adaptive_ml.core.base`](file:///c:/projects/AdaptiveML/adaptive_ml/core/base.py).
- **Validation Requirements:** Compare against scikit-learn `SGDRegressor` and River `HoeffdingTreeRegressor` on California Housing and synthetic streaming Friedman datasets.
- **Acceptance Criteria:** Mean Squared Error (MSE) within $5\%$ of batch decision tree baselines; streaming inference throughput $\ge 25,000\text{ samples/sec}$ on standard x86_64 CPU.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ALA-005: Elastic Parameter Masking for Deep Streaming Adaptation
- **Classification:** New Research
- **Priority:** P3
- **Phase Mapping:** Phase 8 & Phase 21 (Continuous R&D)
- **Problem Statement:** Applying streaming adaptation to neural network backbones causes catastrophic forgetting of earlier representations. Existing Elastic Weight Consolidation (EWC) requires computing and storing full diagonal Fisher Information Matrices, which doubles memory consumption.
- **Research Hypothesis:** Maintaining a sparse binary parameter mask based on accumulated gradient volatility allows selective freezing of the top $20\%$ critical weights, preventing representational drift with $\le 5\%$ memory overhead:
  $$m_j = \mathbb{I}\left( \sum_{t=1}^T \vert g_{t, j} \cdot \theta_{t, j} \vert \ge \tau_{\text{importance}} \right)$$
- **Relevant Prior Art:**
  - Kirkpatrick et al. (2017): *Overcoming Catastrophic Forgetting in Neural Networks* (PNAS).
  - Mallya & Lazebnik (2018): *PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning*.
- **Validation Requirements:** Sequential task learning on Permuted-MNIST and Split-CIFAR-10 using PyTorch integration.
- **Acceptance Criteria:** Retention accuracy on Task 1 after 5 sequential tasks exceeds $88\%$; total parameter storage overhead $\le 1\text{ bit per parameter}$.
- **Estimated Complexity:** High.
- **Risk:** High (sensitivity of importance threshold under non-stationary learning rates).

---

#### EVO-ALA-006: Asynchronous Multi-Stream Partitioning Engine
- **Classification:** Deferred Opportunity
- **Priority:** P4
- **Phase Mapping:** Phase 21 (Continuous R&D)
- **Problem Statement:** Large-scale telemetry pipelines generate hundreds of parallel IoT sensor streams. Running sequential `partial_fit` in a single thread creates processing backpressure.
- **Proposed Exploration:** Investigate zero-copy lock-free thread pool partitions in Python 3.14 free-threaded mode (PEP 703) to enable parallel independent ALA model evaluation.
- **Acceptance Criteria:** Linear scaling up to 8 CPU physical cores without memory lock contention.
- **Estimated Complexity:** Very High.
- **Risk:** High (cross-platform Python GIL elimination maturity).
