# Scientific Research Methodology & Benchmark Protocol

**Document ID:** `docs/research/research-methodology.md`<br>
**Distribution Package:** `aml-core` v0.1.0.dev0<br>
**Research Baseline:** Stage 11 & Stage 12 Applied Research<br>
**Statistical Rigor:** Pre-registered hypotheses, paired statistical tests, reproducible seeds<br>

---

## 1. Research Philosophy & Standards

AdaptiveML's algorithmic foundations are derived from rigorous experimental validation across real-world non-stationary benchmarks. We adhere to five core scientific principles:

1. **Prequential Evaluation Protocol (Test-Before-Train):** In streaming environments, evaluating models on separate train/test splits introduces future-leakage bias. All models are evaluated prequentially: each incoming instance is evaluated *before* it is used to update model parameters.
2. **Real-World & Synthetic Benchmark Complement:** Synthetic streams (AGRAWAL, SEA, Sine) provide ground-truth drift timing for controlled sensitivity evaluation; real-world benchmarks (Electricity, Covertype, Credit Card Fraud) validate real-world robustness.
3. **Paired Statistical Significance:** Superiority claims require formal statistical significance testing ($p < 0.01$) via two-tailed Wilcoxon signed-rank tests across at least 10 independent random seeds.
4. **Reproducibility by Design:** All benchmark datasets, feature extraction pipelines, random seed schedules, and evaluation scripts are checked into the repository under `experiments/`.

---

## 2. Statistical Analysis Framework

To prevent reporting flukes or random noise artifacts, all empirical comparisons evaluate three complementary statistical metrics:

### 2.1 Paired Wilcoxon Signed-Rank Test
For comparing AdaptiveML against baseline streaming models across $N$ independent evaluation splits:
$$W = \min(W^+, W^-), \quad \text{where } W^+ = \sum_{d_i > 0} R_i$$
We reject the null hypothesis of equivalent performance only when asymptotic two-tailed $p\text{-value} < 0.01$.

### 2.2 Relative Win-Tie-Loss Records
In addition to mean prequential accuracy, we report strict Win-Tie-Loss tallies across streaming horizons:
- **Win:** $\text{Metric}_{\text{AdaptiveML}} - \text{Metric}_{\text{Baseline}} > \tau$ (with margin $\tau = 0.5\%$).
- **Tie:** $|\Delta| \le \tau$.
- **Loss:** $\text{Metric}_{\text{Baseline}} - \text{Metric}_{\text{AdaptiveML}} > \tau$.

### 2.3 Effect Size: Cohen's $d$
To verify practical (not merely statistical) significance:
$$d = \frac{\bar{x}_1 - \bar{x}_2}{s_{\text{pooled}}}$$
All promoted algorithmic variants (ALA 3.0, RLA 3.0, Minority Intelligence 2.0, RAO 2.0, ULC-v5) achieved large effect sizes ($d > 0.80$).

---

## 3. Dataset Provenance & Integrity

| Benchmark Dataset | Domain | Samples | Features | Primary Non-Stationary Challenge | Provenance |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Electricity** | Energy Market | 45,312 | 8 | Real-world continuous concept drift driven by pricing fluctuations | NSW Electricity Market (Australia) |
| **Credit Card Fraud** | Finance | 284,807 | 30 | Extreme class imbalance ($0.172\%$ positives) & evolving fraud tactics | European Cardholders / ULB ML Group |
| **Forest Covertype** | Forestry / Ecology | 581,012 | 54 | High-dimensional streaming classification & localized spatial transitions | USFS Resource Information System |
| **AGRAWAL Synthetic** | Synthetic Stream | 100,000 | 9 | Abrupt and gradual concept drift with known ground-truth transition steps | Synthetic generator (`experiments/`) |

---

## 4. Ablation Study Methodology

To avoid "black-box" architecture inflation, every composite component must be rigorously evaluated in isolation:

1. **Component Knock-Out Testing:** Evaluates system degradation when removing individual modules (e.g., removing Spatial Discordance Gating from ULC-v5).
2. **Sensitivity Analysis:** Perturbs hyperparameters ($\delta$, $\text{similarity\_threshold}$, $k$, sublinear cost power) across $\pm 50\%$ ranges to verify parameter stability regions.
3. **Resource Bound Audit:** Measures peak RSS memory and per-step wall-clock latency under high-stress micro-batch streams to verify theoretical $O(1)$ runtime and memory bounds.
