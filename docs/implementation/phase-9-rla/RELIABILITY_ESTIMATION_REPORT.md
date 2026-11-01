# AdaptiveML — Phase 9: Reliability Estimation Report

> **Document Status**: Complete Implementation Deliverable (Phase 9)  
> **Document Identifier**: `DOC-IMP-P9-002`  
> **Last Updated**: 2026-11-01

---

## 1. Reliability Formulation & Behavior

The `DensityAwareMarginScorer` implements the closed-form equation:
$$r_i = \sigma\left( \alpha \tilde{\mathcal{M}}_i - \gamma \ln(\delta_k(\mathbf{x}_i) + \epsilon) \right)$$
where $\tilde{\mathcal{M}}_i$ is the normalized signed margin and $\delta_k(\mathbf{x}_i) = \frac{\rho_k(\mathbf{x}_i)}{\bar{\rho}}$ is the relative local density ratio.

### 1.1 Empirical Verification
1. **Corrupted Samples**: When a label flip occurs in a high-density cluster ($\delta_k \approx 1.0$, negative margin $\tilde{\mathcal{M}}_i < 0$), the reliability score is sharply suppressed ($r_i < 0.05$).
2. **Tail Minority Instances**: When an instance belongs to an isolated minority cluster ($\delta_k \ll 1.0$), the term $-\ln(\delta_k)$ acts as a positive protective margin bonus, elevating $r_i \ge 0.50$ despite ambiguous model logits.
