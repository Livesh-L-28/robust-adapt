# AdaptiveML — Phase 4: Literature Review Master Summary

> **Document Status**: Complete Baseline Deliverable (Phase 4)  
> **Document Identifier**: `DOC-LIT-007`  
> **Last Updated**: 2026-11-01  
> **Research Architecture**: Exactly Three Primary Dossiers (ALA, RLA, RAO) + Cross-Cutting ULC Synthesis

---

## 1. Executive Summary of Literature Review Findings

The academic literature review across 20 foundational papers (spanning 1951 to 2024) establishes the following scientific baselines:

```
+-------------------------------------------------------------------------------------------------------+
|                                  LITERATURE REVIEW SYNTHESIS MATRIX                                   |
+--------------------------+------------------------------------+---------------------------------------+
| Research Pillar          | Established Scientific Consensus   | Unresolved Theoretical / Applied Gap  |
+--------------------------+------------------------------------+---------------------------------------+
| **ALA (Adaptive)**       | ADWIN, DDM, and Hoeffding trees    | False alarms on noisy data; slow dict |
|                          | provide provable bounds on streams | iteration ignoring SIMD/BLAS arrays   |
+--------------------------+------------------------------------+---------------------------------------+
| **RLA (Robust)**         | Bounded symmetric losses (GCE/SCE) | "Small-loss" assumption prunes rare   |
|                          | prevent noise memorization         | minority tail classes systematically  |
+--------------------------+------------------------------------+---------------------------------------+
| **RAO (Resource-Aware)** | 8-bit dynamic quantization saves   | High CPU latency and AVX/CUDA traps;  |
|                          | 75% memory on GPU accelerators     | Adafactor momentum drop causes stalls |
+--------------------------+------------------------------------+---------------------------------------+
| **ULC (Unified)**        | Multi-objective learning must      | In-loop algorithmic state machine     |
|                          | balance stability and plasticity   | arbitrating drift, noise, and RAM     |
+--------------------------+------------------------------------+---------------------------------------+
```

---

## 2. Dossier Inventory in `docs/research/phase-4-literature/`

In strict compliance with Phase 4 guidelines (*"Exactly three primary research dossiers must exist. The ULC document is a synthesis, not a fourth dossier"*):
1. [`ALA_RESEARCH_DOSSIER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/ALA_RESEARCH_DOSSIER.md): **Primary Research Dossier 1** (Concept Drift, Streaming Estimators, Continual Learning).
2. [`RLA_RESEARCH_DOSSIER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/RLA_RESEARCH_DOSSIER.md): **Primary Research Dossier 2** (Noisy Labels, Robust Losses, Class Imbalance, Rare Sample Preservation).
3. [`RAO_RESEARCH_DOSSIER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/RAO_RESEARCH_DOSSIER.md): **Primary Research Dossier 3** (Optimizer Memory, Quantized States, Factorization, CPU-First Execution).
4. [`ULC_CROSS_CUTTING_SYNTHESIS.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/ULC_CROSS_CUTTING_SYNTHESIS.md): **Cross-Cutting Synthesis** (Why naive composition fails; drift-noise collision mode; arbitration automaton).
5. [`COMPREHENSIVE_LITERATURE_REGISTER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/COMPREHENSIVE_LITERATURE_REGISTER.md): Authoritative database of 20 verified papers with DOIs.
6. [`RESEARCH_METHODS_AND_DATASETS.md`](file:///c:/projects/AdaptiveML/docs/research/phase-4-literature/RESEARCH_METHODS_AND_DATASETS.md): Standardized prequential, noise-injection, and memory profiling protocols.

---

## 3. Transition to Phase 5 (Research Gap Identification)

Phase 4 literature evidence directly feeds Phase 5 by converting observed theoretical breakdowns into concrete, testable research gaps:
- **Gap 1 (RLA)**: The Small-Loss Breakdown under Class Imbalance.
- **Gap 2 (ALA/ULC)**: Drift-Noise Collision and False-Positive Retraining.
- **Gap 3 (RAO)**: The CPU Quantization Latency and Platform Portability Barrier.
- **Gap 4 (ALA)**: The Python Interpreter Loop Bottleneck on 2D Streaming Matrices.
