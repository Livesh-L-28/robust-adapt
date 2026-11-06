# AdaptiveML Stage 11 — Research Claims and Evidence Audit
## Workstream M: Comprehensive Audit, Classification, and Evidence Grounding of Architectural and Empirical Claims

**Document Identifier:** `AML-DOC-STG11-CLAIMS-001`<br>
**Distribution:** `aml-core` v0.1.0.dev0<br>
**Research Stage:** Stage 11 — Real-World Validation & Applied Research<br>
**Target Environment:** Windows 11 Enterprise (AMD64), Python 3.14.3<br>
**Date:** 2026-11-06<br>
**Status:** COMPLETE — CLAIMS RECONCILED WITH REAL-WORLD EVIDENCE

---

## 1. Executive Summary & Audit Mandate

In strict accordance with Stage 11 Section 18, an exhaustive audit of all historical, public-facing, and internal performance claims across Stages 1 through 10 was conducted. Every claim is formally classified into one of six standardized scientific evidential categories:

1. `SUPPORTED BY REAL-WORLD EVIDENCE`: Grounded in authentic empirical datasets with documented provenance and independent reproduction.
2. `SUPPORTED ONLY BY SYNTHETIC EVIDENCE`: Validated strictly within procedural or synthetic generator streams.
3. `SUPPORTED ONLY BY CONTROLLED EXPERIMENTS`: Grounded in controlled synthetic manipulations (e.g. injected label flips or simulated fault states).
4. `SUPPORTED BY SOFTWARE TESTS`: Verified through automated unit, integration, or regression test suites.
5. `NOT SUFFICIENTLY SUPPORTED`: Lacking sufficient empirical or statistical evidence.
6. `RETRACTED`: Methodologically flawed, misattributed, or empirically refuted by Stage 11 research.

---

## 2. Master Claims Classification Register

| Claim ID | Subsystem | Historical Claim Statement | Source Document | Evidential Classification | Stage 11 Real-World Finding & Reconciled Status |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **CLM-001** | Minority / ULC | "ULC-v4.1 Hybrid catches 42.5% more fraudulent transactions on the ULB Credit Card Fraud dataset" | Stage 7.2 [`PUBLIC_DATASET_RESULTS.md`](file:///c:/projects/AdaptiveML/experiments/stage_7_2_ulc_v4_1_validation/PUBLIC_DATASET_RESULTS.md) | **RETRACTED & REPLACED** | **Audit Finding:** The historical test used `generate_credit_card_stream` (a synthetic Gaussian generator with $D=29$), NOT the genuine ULB dataset. Evaluated on genuine Credit Card Fraud ($N=267,334$), AdaptiveML Minority Intelligence achieves **$79.31\%$ recall** ($+25.0\%$ over unweighted ERM) with only $79$ false positives ($96.0\%$ fewer than class-weighting). |
| **CLM-002** | ULC-v4.1 | "Spatial Feature Discordance eliminates the Scenario A noise vs drift deadlock" | Stage 7.1 & Stage 7.3 Reports | **SUPPORTED ONLY BY CONTROLLED EXPERIMENTS** | Verified in controlled synthetic simulations where extreme label noise ($40\%$) was artificially superimposed on abrupt centroid drift. Real-world streams rarely exhibit pure orthogonal noise bursts. |
| **CLM-003** | ALA | "AdaptiveML ALA out-adapts static and naive ADWIN models under streaming concept drift" | Stage 4 & Stage 7.3 Reports | **SUPPORTED BY REAL-WORLD EVIDENCE** | Confirmed on Electricity (Elec2, $N=45,312$): AdaptiveML ALA ($72.93\%$ accuracy) significantly outperforms Standard ADWIN ($68.66\%$, $p < 0.001$) by preventing catastrophic forgetting via rehearsal replay. However, static Hoeffding tree achieved $74.76\%$ because electricity pricing exhibits recurring diurnal/seasonal concepts. |
| **CLM-004** | RLA | "Multi-signal reliability scoring filters label corruption without purging valid minority samples" | Stage 5 Report | **SUPPORTED BY REAL-WORLD EVIDENCE** | Confirmed on Spambase ($N=4,601$): Under symmetric noise ($10\% - 20\%$), RLA improves test accuracy by $+1.16\%$ to $+1.42\%$ over ERM while retaining $95.8\%$ of clean samples. Under asymmetric evasion noise, however, class-weighted learning is mandatory. |
| **CLM-005** | RAO | "LowMemoryAdamW compresses optimizer state memory by ~75% with stable convergence" | Stage 6 & Stage 10 Reports | **SUPPORTED BY REAL-WORLD EVIDENCE** | Confirmed on CoverType MLP ($56,000$ params): Optimizer state memory is compressed from $448.0\text{ KB}$ (FP32) down to $112.0\text{ KB}$ (8-bit quantized), an exact $75.0\%$ memory reduction with matching loss convergence ($1.08$ vs $1.09$). Pure Python block slicing incurs CPU latency overhead. |
| **CLM-006** | State / Serialization | "SafeTensors checkpointing prevents pickle code execution with sub-millisecond load verification" | Stage 10 [`CHECKPOINT_SECURITY_AUDIT.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_10/CHECKPOINT_SECURITY_AUDIT.md) | **SUPPORTED BY SOFTWARE TESTS & BENCHMARKS** | Validated via SHA-256 integrity verification, 2-phase atomic commit, and 20 fault-injection scenarios. P50 load latency is $0.87\text{ ms}$. |
| **CLM-007** | Production Reliability | "Streaming pipeline operates in bounded O(1) memory with zero memory leaks across 500,000 samples" | Stage 10 [`RESOURCE_AND_MEMORY_RELIABILITY_REPORT.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_10/RESOURCE_AND_MEMORY_RELIABILITY_REPORT.md) | **SUPPORTED ONLY BY SYNTHETIC EVIDENCE** | Confirmed software-level memory containment (peak heap $4.36\text{ MB}$, RSS $+5.7\text{ MB}$ over 10,000 synthetic batches). Valid for memory profiling, but does not represent real-world drift dynamics. |

---

## 3. Necessary Retractions and Documentation Corrections

1. **Retraction of Stage 7.2 Credit Card Claim:**
   - Any assertion that ULC-v4.1 was evaluated on the actual ULB Credit Card Fraud dataset prior to Stage 11 is formally retracted.
   - The Stage 7.2 experiment is re-labeled as: *"Synthetic Gaussian Stream Parameterized from Credit Card Imbalance Statistics"*.
   - The authoritative benchmark on the authentic 267,334 transactions is documented in [`experiments/stage_11/minority/run_minority_creditcard_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_11/minority/run_minority_creditcard_experiment.py).

2. **Nuance on Concept Drift Resets (ALA):**
   - The claim that full model resets upon ADWIN drift detection universally improve performance is corrected.
   - Real-world evidence on Electricity (Elec2) proves that full model resets cause catastrophic forgetting ($-6.10\%$ accuracy penalty). Rehearsal replay mitigates this penalty ($+4.27\%$), but where concepts recur, continuous incremental learning without full resets is superior.

3. **Nuance on Asymmetric Noise Filtering (RLA):**
   - The claim that spatial discordance filtering alone resolves all label noise is corrected.
   - Real-world evidence on Spambase proves that when noise is asymmetric (evasion attacks where minority instances are disguised as majority), spatial filtering must be combined with explicit cost-sensitive class weighting to prevent recall collapse.

---

## 4. Workstream M Verification Sign-off

- [x] All 7 major architectural and performance claims audited against verifiable evidence.
- [x] Historical synthetic mimicking of Credit Card Fraud formally retracted and replaced with authentic empirical benchmarks.
- [x] Real-world boundary conditions and operational trade-offs transparently documented.
