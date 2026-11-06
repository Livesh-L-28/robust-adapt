# Adaptive Minority Intelligence 2.0 Overview

**Adaptive Minority Intelligence** provides specialized algorithmic machinery designed for extreme streaming class imbalance, where critical target instances represent $<1\%$ (or $<0.1\%$) of the data stream.

---

## 1. Key Capabilities

- **Beta-Binomial Bayesian Prior Tracking (`BetaBinomialPriorTracker`)**: Continually updates an empirical estimate of the active minority arrival rate $\hat{\pi}_t \in (0, 1)$ without requiring stationary batch windows.
- **Dynamic PID False-Positive Budget Regulation (`DynamicFPBudgetThresholdManager`)**: Continuously tunes the operational classification threshold $\theta_t$ using a Proportional-Integral-Derivative (PID) feedback loop to satisfy strict false positive quotas (e.g. $\le 1.5$ false positives per 1,000 transactions).
- **Sublinear Cost Weighting**: Dynamically scales minority gradient penalties with a calibrated sublinear exponent $\hat{\pi}_t^{-\alpha}$ ($\alpha \approx 0.52$), preventing loss saturation while maintaining sharp discrimination boundaries.
- **Turnkey Integration (`MinorityIntelligence20Learner`)**: Encapsulates prior tracking, cost-weighted learning, and dynamic threshold regulation into a single Scikit-Learn compatible estimator.

---

## 2. When to Use Minority Intelligence

- The positive/critical class represents a tiny fraction of incoming events (e.g. fraud, network intrusion, rare medical anomalies).
- Overall accuracy is misleading or useless because a trivial negative classifier achieves $>99\%$ accuracy.
- Operational human review capacity imposes a strict ceiling on allowable false alarms.
- Class distribution shifts over time (e.g. fraud waves or attacks that surge and abate).
