# PHASE 19 DELIVERABLE 07 — RESEARCH LIMITATIONS AND VALIDITY
## Threats to Internal, External, and Construct Validity, and Methodological Boundaries

**Document Identifier:** `docs/research/phase_19/RESEARCH_LIMITATIONS_AND_VALIDITY.md`<br>
**Phase:** 19 — Research Publication Preparation<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Scientific Integrity Officer & Methodology Reviewer<br>

---

## 1. Threats to Internal Validity

* **Hyperparameter Sensitivity:** The spatial discordance threshold $\tau_{\text{discordance}} = 0.35$ and margin scaling parameter $\tau_{\text{margin}} = 1.0$ were tuned on validation splits of benchmark streams. While performance remains stable across $\tau_{\text{discordance}} \in [0.25, 0.45]$, extreme parameter settings in uncalibrated domains may degrade gating precision.
* **Neighborhood Buffer Latency:** Spatial discordance requires filling a minimum sliding neighborhood buffer ($M \ge 50$ samples). During the initial $50$ samples of an uninitialized stream, the controller falls back to standard error thresholding.

---

## 2. Threats to External Validity

* **Feature Modality Limitations:** The empirical validation was conducted on dense numerical feature spaces ($d \le 1,000$). High-dimensional sparse token streams (such as raw text or click-through sparse IDs) require sparse cosine similarity rather than Euclidean k-NN.
* **Synthetic vs. Real-World Streaming Realities:** While synthetic streams (Agrawal, Sea, Rotating Plane) permit exact mathematical control over drift onset and noise percentage, real-world industrial streams often exhibit compound non-stationarities (e.g., sensor degradation occurring simultaneously with seasonality).
* **Hardware Architecture Constraints:** The reported $67.8\%$ optimizer compression was demonstrated on x86-64 CPUs with SIMD vectorized operations. Performance on specialized embedded architectures (ARM Cortex-M, RISC-V) requires dedicated profiling.

---

## 3. Threats to Construct Validity

* **Drift Recovery Metric Formulation:** Recovery is defined as returning to $\ge 95\%$ of pre-drift steady-state accuracy within a window of $W$ steps. In streams where a concept change fundamentally increases task difficulty (e.g. from separable to overlapping classes), steady-state accuracy may be lower than historical accuracy, affecting the recovery step count.
* **Optimizer Memory Attribution:** Memory compression was measured via Python `tracemalloc` on allocated array buffers and process RSS. Secondary operating system page cache fragmentation can cause minor fluctuations in transient memory reports.

---

## 4. Methodological Safeguards Implemented

To counter these threats to validity:
1. **Multi-Seed Averaging:** All findings report means and standard deviations across 5 distinct random seeds.
2. **Prequential Integrity:** Strict test-then-train protocol guarantees that zero test data leaks into parameter updates.
3. **No Overclaiming:** The manuscript explicitly refrains from claiming universal generalization, unbounded $O(1)$ memory, or unconstrained edge deployment.
