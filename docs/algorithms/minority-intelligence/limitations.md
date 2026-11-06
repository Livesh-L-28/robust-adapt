# Minority Intelligence: Known Limitations & Failure Modes

---

## 1. Zero-Variance or Overlapping Features

- **Behavior**: If the rare minority class shares identical feature distributions with the majority class (e.g. zero distinct signal in $X$), no threshold adjustment can separate them.
- **Consequence**: Sublinear cost weighting will elevate gradient penalties without improving separation, causing false positives to consume the entire budget.
- **Guidance**: Ensure feature engineering captures discriminatory signals prior to streaming ingestion.

## 2. Multi-Class Minority Distributions ($K > 2$)

- **Behavior**: `MinorityIntelligence20Learner` is optimized for binary imbalanced streams (majority class 0 vs. rare target class 1).
- **Consequence**: For multi-class imbalanced problems with multiple rare classes, prior tracking requires one-vs-rest binary decompositions.

## 3. Burn-in Sample Latency

- **Behavior**: The Beta-Binomial prior tracker requires observing a modest sequence of events (at least 50-100 samples) before its posterior mean converges from its hyper-prior ($\alpha_0=1.0, \beta_0=100.0$).
- **Mitigation**: Pre-initialize `alpha_prior` and `beta_prior` with domain historical estimates where available.
