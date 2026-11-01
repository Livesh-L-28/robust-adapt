# Phase 12 Ablation Study Report

**Document ID:** `DOC-RES-P12-008`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Component Contribution Analysis

To determine whether each algorithmic design component provides meaningful utility, systematic ablation experiments were conducted:

### 1.1 Ablation A: Impact of Density Moderation ($\gamma$) on Rare-Class Recall
- **Ablation Baseline ($\gamma = 0.0$)**: Standard margin thresholding without density penalty moderation.
- **Full AdaptiveML ($\gamma = 0.8$)**: Density-aware margin moderation ($\psi(\delta_k) = -\ln(\delta_k)$).
- **Finding**: Setting $\gamma = 0.0$ resulted in rare-class instances near decision boundaries being scored with negative margins and purged. Enabling $\gamma = 0.8$ raised minority class recall from $0.0\%$ to $60.0\%$.

### 1.2 Ablation B: Impact of Reliability Weighting in ADWIN
- **Ablation Baseline**: Standard ADWIN with uniform sample weights ($w_i = 1.0$).
- **Full AdaptiveML**: Reliability-weighted ADWIN ($w_i = r_i$).
- **Finding**: Under high label noise, unweighted ADWIN suffered false positive window cuts due to variance spikes in noisy predictions. Reliability weighting suppressed cuts on corrupted observations.

### 1.3 Ablation C: Impact of ULC Arbitration vs Independent Drift Reset
- **Ablation Baseline**: Independent drift detector resetting model whenever $\Delta_{\text{drift}} \ge 1.0$.
- **Full AdaptiveML**: ULC 5-state arbitration automaton with $\bar{R}_{\mathcal{W}}$ gating.
- **Finding**: Independent drift reset wiped model weights 10 consecutive times during an 85% noise burst. ULC successfully suppressed the reset (0 false resets).

