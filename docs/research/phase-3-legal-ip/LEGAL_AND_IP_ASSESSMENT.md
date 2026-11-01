# AdaptiveML — Phase 3: Legal & Intellectual Property Master Assessment

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-RES-P3-001`  
> **Last Updated**: 2026-11-01  
> **Research Team**: IP Research Analyst, Open-Source Compliance Specialist, Framework Architect

---

## 1. Executive Summary & Strict Legal Disclaimers

> [!WARNING]
> **PRELIMINARY TECHNICAL ASSESSMENT ONLY — NOT LEGAL ADVICE**  
> This assessment represents an internal engineering and open-source compliance audit. It does **not** constitute a formal legal opinion, freedom-to-operate guarantee, or attorney-client communication. Formal legal clearance must be ratified by qualified intellectual property legal counsel prior to commercial release or public package publication.

### Key Legal Findings:
1. **Critical Trademark & Naming Conflict**:
   - `FACT`: The entity **Adaptive ML, Inc.** (founded 2023, acquired by **Datadog** in 2024) is a prominent venture-backed AI enterprise operating in the reinforcement learning and LLM fine-tuning domain.
   - `FACT`: Datadog / Adaptive ML controls the `AdaptiveML` organization on PyPI and publishes packages under that user namespace (`adaptive-sdk`, `adaptive-harmony`).
   - `RECOMMENDATION`: **Do not publish or register a PyPI package under the bare name "AdaptiveML".** The project must maintain "AdaptiveML" strictly as a provisional internal engineering codename. Formal fallback namespaces (`aml-core`, `libadaptive`, `adaptml-lib`) are evaluated in [`TRADEMARK_AND_NAMING_REVIEW.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/TRADEMARK_AND_NAMING_REVIEW.md).
2. **License Selection & Compatibility (Apache-2.0)**:
   - `FACT`: The proposed **Apache License, Version 2.0 (Apache-2.0)** is permissive, highly compatible with the target ecosystem (NumPy, PyTorch, scikit-learn), and provides essential downstream protections via its explicit patent grant (Section 3) and patent retaliation clause.
   - `OBSERVATION`: Cleanlab's core repository is licensed under **AGPL-3.0**. Under no circumstances may Cleanlab code be copied, vendored, or statically linked into AdaptiveML, as AGPL copyleft obligations would contaminate the Apache-2.0 distribution.
3. **Patent Boundaries & Clean-Room Implementation**:
   - Core algorithms (ADWIN, Page-Hinkley, GCE, SCE, AdamW, Reservoir Sampling) are **public domain academic inventions** published without patent encumbrance between 1954 and 2019.
   - Cleanlab, Inc. holds patents on Confident Learning joint distribution estimation (US11651239B2). AdaptiveML will use **clean-room implementations of public-domain robust loss functions and original density-margin scoring**, avoiding Confident Learning pruning claims entirely.
4. **Contributor Provenance & Governance**:
   - Adopt the **Developer Certificate of Origin (DCO 1.1)** via mandatory `Signed-off-by` git commit hooks, ensuring verifiable contributor provenance without imposing corporate CLA bureaucracy.

---

## 2. Scope of Legal & Intellectual Property Review

This audit covers eight operational dimensions across jurisdictions including India (home execution territory), the United States (major PyPI distribution hub), and the European Union:

```
+-------------------------------------------------------------------------------+
|                       LEGAL & IP AUDIT ARCHITECTURE                           |
+--------------------------+----------------------------------------------------+
| Dimension                | Key Focus Area                                     |
+--------------------------+----------------------------------------------------+
| **Trademark & Naming**   | Datadog / Adaptive ML conflict, PyPI namespaces,  |
|                          | Indian Trade Marks Registry Class 9 & Class 42     |
| **Project Licensing**    | Apache-2.0 terms, patent grant, license hygiene    |
| **Dependency Audit**     | NumPy (BSD), PyTorch (BSD), scikit-learn (BSD)     |
| **Incompatible Licenses**| AGPL-3.0 (Cleanlab), GPL-3.0 (avoiding copyleft)   |
| **Dataset Licensing**    | Benchmark usage: CoverType, CIFAR-10N, Clothing1M  |
| **Contributor Rights**   | DCO 1.1, clean-room authorship, NOTICE attribution |
| **Patent / FTO**         | Public-domain prior art vs. proprietary claims     |
| **Privacy / Telemetry**  | Zero telemetry compliance, local data autonomy     |
+--------------------------+----------------------------------------------------+
```

---

## 3. Summary of Deliverables in Phase 3

All Phase 3 research files are cataloged in `docs/research/phase-3-legal-ip/`:
- [`TRADEMARK_AND_NAMING_REVIEW.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/TRADEMARK_AND_NAMING_REVIEW.md)
- [`OPEN_SOURCE_LICENSE_ANALYSIS.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/OPEN_SOURCE_LICENSE_ANALYSIS.md)
- [`DEPENDENCY_LICENSE_REGISTER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/DEPENDENCY_LICENSE_REGISTER.md)
- [`DATASET_AND_BENCHMARK_LICENSE_REVIEW.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/DATASET_AND_BENCHMARK_LICENSE_REVIEW.md)
- [`COPYRIGHT_AND_CONTRIBUTOR_POLICY.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/COPYRIGHT_AND_CONTRIBUTOR_POLICY.md)
- [`PATENT_AND_FTO_PRELIMINARY_REVIEW.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/PATENT_AND_FTO_PRELIMINARY_REVIEW.md)
- [`LEGAL_IP_RISK_REGISTER.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/LEGAL_IP_RISK_REGISTER.md)
- [`PHASE_3_OWNER_DECISIONS.md`](file:///c:/projects/AdaptiveML/docs/research/phase-3-legal-ip/PHASE_3_OWNER_DECISIONS.md)
