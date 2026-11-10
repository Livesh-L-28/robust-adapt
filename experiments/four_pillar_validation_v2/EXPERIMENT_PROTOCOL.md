# Four-Pillar Validation v2 — Experiment Protocol & Specifications

**Document Identifier:** `EXP-PROTO-V2-001`  
**Distribution Identifier:** `aml-core` (`0.1.0.dev0`)  
**Execution Environment:** Python 3.14.3 (AMD64), Windows 11  
**Reproducibility Engine:** [`experiments/four_pillar_validation_v2/run_experiments.py`](file:///c:/projects/AdaptiveML/experiments/four_pillar_validation_v2/run_experiments.py)  

---

## 1. Streaming Data Generation & Dynamic Regimes

The benchmark stream is constructed to simulate a realistic, adverse edge streaming environment over 50 sequential batches of 30 samples ($N = 1,500$ instances total).

### 1.1 Class Imbalance Specification
- **Feature Dimension:** $d = 4$ continuous features sampled from multivariate Gaussians.
- **Classes:** Binary classification ($K = 2$, labels $\{0, 1\}$).
- **Imbalance Ratio:** $90:10$ fixed prior distribution per batch.
  - Majority Class ($y = 0$): 27 samples per batch ($90\%$).
  - Minority Class ($y = 1$): 3 samples per batch ($10\%$).

### 1.2 Four Dynamic Regimes

```
Stream Timeline (50 Batches = 1,500 Samples):
[Batches 1 - 15]   Regime 1: Clean Stationary Baseline (mu_0 = -1.5, mu_1 = +1.5; delta = 0.05)
[Batches 16 - 25]  Regime 2: Severe Label Noise Burst (40% majority flipped to 1; delta = 1.15)
[Batches 26 - 35]  Regime 3: Gradual Concept Drift (Centroids shift continuously over 10 batches)
[Batches 36 - 50]  Regime 4: Abrupt Inverted Drift (mu_0 = +2.5, mu_1 = -2.5; delta = 1.35)
```

1. **Regime 1: Clean Stationary Baseline (Batches 1–15, $N = 450$ samples)**
   - Majority: $\mathbf{x} \sim \mathcal{N}([-1.5, -1.5, -1.5, -1.5]^T, 0.6^2 \mathbf{I})$
   - Minority: $\mathbf{x} \sim \mathcal{N}([+1.5, +1.5, +1.5, +1.5]^T, 0.6^2 \mathbf{I})$
   - Drift signal: $\delta = 0.05$ (normal stationary variance).
   - Labels are clean; models establish initial structural representations.

2. **Regime 2: Severe Label Noise Burst (Batches 16–25, $N = 300$ samples)**
   - Centroids remain identical to Regime 1 (no true concept drift).
   - **Adverse Corruption:** In each batch, 11 out of 27 majority instances ($40.7\%$) have their labels artificially flipped from $0$ to $1$.
   - True underlying class distribution remains $90:10$, but observed distribution appears as $16:14$.
   - Drift signal: $\delta = 1.15$ (spurious error spike).
   - *Pillar Stress:* Tests RLA's ability to downweight corrupted labels and ULC's ability to suppress false drift resets.

3. **Regime 3: Gradual Concept Drift (Batches 26–35, $N = 300$ samples)**
   - Labels return to 100% clean ground truth.
   - Centroids linearly transition over 10 batches:
     $$\mu_0(b) = -1.5 \cdot (1 - \alpha) + 1.5 \cdot \alpha, \quad \mu_1(b) = +1.5 \cdot (1 - \alpha) - 1.5 \cdot \alpha, \quad \alpha = \frac{b - 25}{10}$$
   - Drift signal: $\delta = 0.35$ (elevated divergence triggering WARNING state).
   - *Pillar Stress:* Tests incremental adaptation without catastrophic model destruction.

4. **Regime 4: Abrupt Inverted Concept Drift (Batches 36–50, $N = 450$ samples)**
   - Distributions invert abruptly and separate further:
     - Majority ($y=0$): $\mathbf{x} \sim \mathcal{N}([+2.5, +2.5, +2.5, +2.5]^T, 0.6^2 \mathbf{I})$
     - Minority ($y=1$): $\mathbf{x} \sim \mathcal{N}([-2.5, -2.5, -2.5, -2.5]^T, 0.6^2 \mathbf{I})$
   - Drift signal: $\delta = 1.35$ at batches 36 and 37, stabilizing to $\delta = 0.10$.
   - *Pillar Stress:* Tests prompt transition to CONFIRMED_DRIFT, replay buffer purging, and rapid post-drift recovery.

### 1.3 Evaluation Protocol (Prequential Test-Then-Train)
To ensure strict absence of data leakage:
1. For each batch $b \in \{2, \dots, 50\}$, the model generates predictions $\hat{y}$ and probabilities $\hat{p}$ on $X_b$ **before** observing labels.
2. Predictions are evaluated strictly against **unpolluted ground truth** $y_{\text{clean}}$.
3. The model update step is executed using the observed (potentially corrupted) labels $y_{\text{observed}}$.

---

## 2. Experimental Configurations Evaluated

A total of 11 distinct model architectures and ablations were evaluated across identical streams:

| Config ID | Model Designation | Primary Estimator | Active Adaptation Mechanisms | Active Noise Filtering | Optimization Scheme |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **A** | `Static_Baseline` | Hoeffding Tree (`grace_period=20`) | None (Fixed baseline) | None | Unweighted counting |
| **B** | `ALA_Only` | Hoeffding Tree | ADWIN drift reset on $\delta \ge 1.0$ | None | Unweighted counting |
| **C** | `RLA_Only` | Hoeffding Tree | None | Density-aware margin filtering ($\ge 0.45$) | Reliability-weighted counting |
| **D** | `RAO_Only` | Linear Softmax ($4 \times 2$) | None | None | 8-bit `LowMemoryAdamW` ($B=16$) |
| **E** | `ALA_plus_RLA` | Hoeffding Tree | ADWIN drift reset on $\delta \ge 1.0$ | Density-aware margin filtering ($\ge 0.45$) | Reliability-weighted counting |
| **F** | `ALA_plus_RAO` | Linear Softmax | Momentum reset on $\delta \ge 1.0$ | None | 8-bit `LowMemoryAdamW` |
| **G** | `RLA_plus_RAO` | Linear Softmax | None | Density-aware gradient weighting | 8-bit `LowMemoryAdamW` |
| **H** | `Uncoordinated_Three_Pillars` | Hybrid (Tree + Linear) | Uncoordinated ADWIN reset | RLA sample filtering | 8-bit `LowMemoryAdamW` |
| **I1**| `Full_ULC_v1` | Coordinated Baseline | ULC-v1 (Original implementation) | ULC sample thresholding | 8-bit `LowMemoryAdamW` |
| **I2**| `Optimized_ULC_v2` | Remediated Tree | ULC-v2 (Fixed replay purge & tree reset) | ULC sample thresholding | 8-bit `LowMemoryAdamW` |
| **I3**| `MultiObjective_ULC_v3`| Multi-Objective Ensemble | ULC-v3 (Ensemble policy + aligned logits) | Dual-evidence arbitration | 8-bit `LowMemoryAdamW` |

---

## 3. Mathematical Metric Formulations

### 3.1 Classification & Imbalance Metrics
Let $N_{\text{eval}}$ denote the total prequential evaluation instances ($1,470$ samples across batches 2–50):
- **Prequential Accuracy:**
  $$\text{Acc} = \frac{1}{N_{\text{eval}}} \sum_{i=1}^{N_{\text{eval}}} \mathbb{I}(\hat{y}_i = y_i^{\text{clean}})$$
- **Class-Specific Recalls & Precisions:**
  $$\text{Recall}_{\text{min}} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad \text{Precision}_{\text{min}} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
  $$\text{Recall}_{\text{maj}} = \frac{\text{TN}}{\text{TN} + \text{FP}}, \quad \text{Precision}_{\text{maj}} = \frac{\text{TN}}{\text{TN} + \text{FN}}$$
- **Balanced Accuracy:**
  $$\text{BalAcc} = \frac{\text{Recall}_{\text{min}} + \text{Recall}_{\text{maj}}}{2}$$
- **Minority F1 Score:**
  $$\text{F1}_{\text{min}} = \frac{2 \cdot \text{Precision}_{\text{min}} \cdot \text{Recall}_{\text{min}}}{\text{Precision}_{\text{min}} + \text{Recall}_{\text{min}} + \epsilon}$$
- **Macro F1 Score:**
  $$\text{Macro F1} = \frac{\text{F1}_{\text{min}} + \text{F1}_{\text{maj}}}{2}$$

### 3.2 Calibration Metric (Brier Score)
Measures the mean squared error of predicted class-1 posterior probabilities $\hat{p}_i \in [0, 1]$ against binary ground truth:
$$\text{Brier} = \frac{1}{N_{\text{eval}}} \sum_{i=1}^{N_{\text{eval}}} (\hat{p}_i - y_i^{\text{clean}})^2$$

### 3.3 Controller Dynamics Metrics
- **False Drift Resets:** Count of transitions to `CONFIRMED_DRIFT` during the noise burst regime (Batches 16–25).
- **Drift Detection Delay:** Number of batches between drift onset (Batch 36) and confirmation.
- **Recovery Time:** Number of dwell batches spent in `RECOVERY` mode following concept drift.

### 3.4 Operational & Resource Metrics
- **Optimizer State Memory (Bytes):** Exact storage footprint of first and second moment tensors, block scales, and tracking dictionaries.
- **Step Latency (ms):** Wall-clock time per streaming step measured via `time.perf_counter()`, capturing mean, p50, p95, p99, and worst-case latency.

---

## 4. Multi-Seed Replication & Statistical Significance Testing

To ensure statistical rigor, all experiments are executed across five fixed random seeds:
$$\mathcal{S} = \{42, 101, 2024, 7, 99\}$$

### 4.1 Confidence Intervals
For any metric $X$ across $n=5$ seeds, the $95\%$ confidence interval is computed using the Student's $t$-distribution critical value ($t_{4, 0.025} = 2.776$):
$$\text{CI}_{95} = \bar{X} \pm 2.776 \cdot \frac{s_X}{\sqrt{5}}$$

### 4.2 Paired Hypothesis Testing
For comparisons between model $A$ and model $B$, a two-tailed **paired Student's $t$-test** is conducted on differences $D_i = X_{A, i} - X_{B, i}$:
$$t = \frac{\bar{D}}{s_D / \sqrt{n}}, \quad \text{df} = 4$$
Statistical significance is reported strictly at the $\alpha = 0.05$ and $\alpha = 0.01$ significance thresholds.

