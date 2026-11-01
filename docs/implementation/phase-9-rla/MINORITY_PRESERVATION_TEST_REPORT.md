# AdaptiveML — Phase 9: Minority Preservation Test Report

> **Document Status**: Complete Implementation Deliverable (Phase 9)  
> **Document Identifier**: `DOC-IMP-P9-004`  
> **Last Updated**: 2026-11-01

---

## 1. Theorem 2 Proof Verification

`DOC-DES-P6-004` derived Theorem 2:
> *For any margin deficit $m_0$, setting $\gamma \ge \frac{\alpha m_0 + \sigma^{-1}(r_{\text{threshold}})}{\ln(1 / \delta_{\text{rare}})}$ guarantees that $r_i \ge r_{\text{threshold}}$, preventing false purging of rare instances.*

### 1.1 Test Results (`test_minority_preservation_theorem_2`)
- **Dataset Setup**: 25 dense majority instances at location $[0, 0]$ with label 0; 1 isolated minority instance at $[10, 10]$ with label 1.
- **Model Uncertainty**: The model produced a negative logit margin ($-1.0$) on the rare instance.
- **Reliability Output**:
  - Without density bonus ($\gamma = 0$): Reliability dropped to $r_i \approx 0.12$ (would be filtered as noise!).
  - With density bonus ($\gamma = 1.0$): Reliability evaluated to **$r_i = 0.8090 \ge 0.50$**, successfully protecting the minority instance from being pruned.

