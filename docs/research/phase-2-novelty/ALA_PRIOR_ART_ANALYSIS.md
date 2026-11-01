# AdaptiveML — Pillar 1: ALA Prior-Art Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-002`  
> **Focus**: Adaptive Learning Algorithms, Concept Drift Detection, Streaming ML, Continual Learning

---

## 1. Concept Drift Detection Primitives

### 1.1 Page-Hinkley Test & CUSUM
- **Original Source**: Page, E. S. (1954). *Continuous Inspection Schemes*. Biometrika, 41(1/2), 100–115; Hinkley, D. V. (1970). *Inference about the change-point in a sequence of random variables*. Biometrika, 57(1), 1–17.
- **Mathematical Mechanism**: Sequential analysis test monitoring the cumulative deviation of streaming variables from their running mean:
  $$m_t = \sum_{i=1}^t (x_i - \bar{x}_t - \delta), \quad M_t = \min_{1 \le i \le t} m_i, \quad PH_t = m_t - M_t$$
  A drift alarm triggers when $PH_t > \lambda$, where $\lambda$ is a user-defined threshold and $\delta$ is an allowed magnitude change.
- **Assumptions**: Observations are independent and identically distributed prior to the change-point; Gaussian or bounded variance.
- **Limitations**: High sensitivity to the parameter $\lambda$; slow to detect gradual drift; cannot handle multi-modal distributions without normalization.
- **Computational & Memory Cost**: $O(1)$ time complexity per sample; $O(1)$ memory (scalar accumulators).
- **Existing Implementations**: River (`river.drift.PageHinkley`), Menelaus (`menelaus.concept_drift.PageHinkley`).
- **Relationship to AdaptiveML**: Baseline change-point detector; public domain prior art.

---

### 1.2 DDM & EDDM (Drift Detection Method / Early Drift Detection Method)
- **Original Source**: Gama, J., Medas, P., Castillo, G., & Rodrigues, P. (2004). *Learning with drift detection*. SBIA 2004; Baena-García, M., et al. (2006). *Early drift detection method*. Fourth ECML PKDD.
- **Mathematical Mechanism**: Models classifier error as a Bernoulli random process. Tracks error rate $p_t$ and standard deviation $s_t = \sqrt{p_t(1-p_t)/t}$. Tracks minimum values $p_{\min}$ and $s_{\min}$.
  - Warning Level: $p_t + s_t \ge p_{\min} + 2 s_{\min}$ (triggers buffer accumulation).
  - Drift Level: $p_t + s_t \ge p_{\min} + 3 s_{\min}$ (triggers model reset).
  - EDDM modifies the mechanism to track distances between consecutive errors to detect slow gradual drift earlier.
- **Assumptions**: Classifier errors are independent Bernoulli trials; sample stream is sufficiently large for the normal approximation to hold.
- **Limitations**:
  - DDM fails when drift is very slow (the error rate increases so gradually that $p_{\min} + 3 s_{\min}$ is never crossed).
  - EDDM is notoriously susceptible to false alarms when errors occur in short noisy bursts.
- **Computational & Memory Cost**: $O(1)$ time per sample; $O(1)$ memory.
- **Existing Implementations**: River (`river.drift.DDM`, `EDDM`), Menelaus (`menelaus.concept_drift.DDM`).
- **Relationship to AdaptiveML**: Canonical baselines; public domain prior art.

---

### 1.3 ADWIN (Adaptive Windowing)
- **Original Source**: Bifet, A., & Gavaldà, R. (2007). *Learning from time-changing data with adaptive windowing*. SIAM International Conference on Data Mining (SDM 2007), 443–448.
- **Mathematical Mechanism**: Maintains a variable-length sliding window $W$ of recent real-valued observations. Automatically compresses historical data into exponentially sized buckets. Whenever two sub-windows $W_0, W_1$ (where $W = W_0 \cdot W_1$) exhibit statistically significant differences in their running means:
  $$|\mu_{W_0} - \mu_{W_1}| \ge \epsilon_{\text{cut}} = \sqrt{\frac{1}{2m} \ln\frac{4|W|}{\delta}}, \quad \frac{1}{m} = \frac{1}{|W_0|} + \frac{1}{|W_1|}$$
  ADWIN drops the older sub-window $W_0$ and asserts that drift occurred.
- **Assumptions**: Bounded values $x_i \in [0, 1]$; false positive rate bounded rigorously by $\delta$ via Hoeffding's inequality.
- **Limitations**:
  - Mistake transient noise for concept drift when $\delta$ is loose.
  - Bucket management creates minor computational overhead relative to scalar CUSUM.
- **Computational & Memory Cost**: $O(\log W)$ time complexity; $O(\log W)$ memory complexity.
- **Existing Implementations**: River (`river.drift.ADWIN`), Menelaus (`menelaus.concept_drift.ADWIN`).
- **Relationship to AdaptiveML**: The primary drift detector baseline. AdaptiveML will build upon its statistical guarantees while implementing **noise-gated confidence weighting** to prevent false triggers on transient label noise.

---

### 1.4 KSWIN (Kolmogorov-Smirnov Windowing)
- **Original Source**: Raab, C., Heusinger, M., & Schleif, F. M. (2020). *Reactive soft prototype computing for concept drift streams*. Neurocomputing, 416, 340–351.
- **Mathematical Mechanism**: Non-parametric drift detection based on the Kolmogorov-Smirnov test. Compares the empirical cumulative distribution function (ECDF) of a fixed historical reference window $R$ against a sliding current window $W$.
  $$D = \sup_x |F_R(x) - F_W(x)| > c(\alpha) \sqrt{\frac{|R| + |W|}{|R| \cdot |W|}}$$
- **Assumptions**: Non-parametric (makes zero distributional assumptions about input data).
- **Limitations**: High memory overhead (must store raw reference and sliding window arrays); $O(N \log N)$ sorting cost during KS evaluation.
- **Existing Implementations**: River (`river.drift.KSWIN`).

---

## 2. Online & Streaming Machine Learning Estimators

### 2.1 Hoeffding Trees & Adaptive Random Forest (ARF)
- **Original Source**: Domingos, P., & Hulten, G. (2000). *Mining high-speed data streams*. KDD 2000; Gomes, H. M., et al. (2017). *Adaptive random forests for evolving data stream classification*. Machine Learning, 106(9), 1469–1495.
- **Mechanism**:
  - Hoeffding Trees evaluate split criteria on continuous streams using Hoeffding bounds to guarantee with probability $1-\delta$ that an incremental split is identical to a batch split.
  - Adaptive Random Forest combines online bagging (Poisson distribution sampling with $\lambda = 6$) with independent ADWIN drift and warning detectors per tree. When warning triggers, a background tree trains in parallel; when drift triggers, the background tree replaces the stale tree.
- **Limitations**:
  - High memory usage per tree due to maintaining continuous attribute observers (Gaussian estimators or histograms).
  - In River, each observation is passed as a Python dictionary, creating massive CPU interpreter overhead on large tabular streams.
- **AdaptiveML Differentiation**: Re-implement online tree and bagging structures to operate on **contiguous 2D NumPy array chunks**, enabling vectorization across tree ensembles.

---

## 3. Deep Continual Learning Prior Art

| Method | Core Mechanism | Strengths | Limitations | Implementations |
| :--- | :--- | :--- | :--- | :--- |
| **EWC** (Kirkpatrick et al., 2017) | Quadratic penalty on weight shifts based on diagonal Fisher Information Matrix $F$: $\mathcal{L} = \mathcal{L}_B + \sum \frac{\lambda}{2} F_i (\theta_i - \theta_{A,i}^*)^2$ | Does not require storing raw historical data | Diagonal Fisher assumption is weak; scales poorly over many sequential tasks | Avalanche, PyTorch |
| **LwF** (Li & Hoiem, 2017) | Knowledge distillation from previous model snapshot | Zero historical buffer required | Suffers when task distributions are severely disjoint | Avalanche |
| **GEM / A-GEM** (Lopez-Paz 2017, Chaudhry 2018) | Projects gradients into non-conflicting subspaces using episodic memory buffer | Theoretical guarantee against negative backward transfer | Extremely heavy quadratic programming (QP) solver per step (GEM) | Avalanche |
| **Reservoir Sampling** (Vitter 1985) | Probabilistic stream buffer maintenance keeping uniform representation of infinite stream | Bounded memory footprint; simple implementation | Treats all past samples equally; does not adapt to non-stationary concept drift | River, Avalanche |

---

## 4. Prior-Art Conclusion for ALA

The foundational mathematics of drift detection and streaming estimators are **established public prior art**. 

AdaptiveML claims **zero algorithmic novelty** on standalone ADWIN, DDM, or Hoeffding logic. AdaptiveML's strategic contribution is:
1. **Ergonomic & Performance Innovation**: Native 2D NumPy array matrix processing (`partial_fit`) solving the interpreter bottleneck of River.
2. **Algorithmic Enhancement**: Gating ADWIN statistical cutting against local label noise metrics to prevent false-alarm window drops.
