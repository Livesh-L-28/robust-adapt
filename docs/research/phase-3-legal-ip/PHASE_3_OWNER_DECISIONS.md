# AdaptiveML — Phase 3: Owner Decisions & Governance Sign-Off

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-009`  
> **Last Updated**: 2026-11-01  
> **Action Level**: Project Leadership Council / Owner Action

---

## 1. Actionable Decisions for Project Leadership

The following strategic and legal recommendations derived from Phase 3 research require formal sign-off by project leadership:

### Decision 1: Codename Status & External Distribution Namespace
- **Recommendation**: Formally maintain "AdaptiveML" strictly as an **internal engineering codename**. Pre-approve **`aml-core`** as the primary candidate namespace for public PyPI and Conda-Forge distribution to avoid collision with Datadog's *Adaptive ML, Inc.*
- **Owner Action**: **APPROVED / RATIFIED**.

---

### Decision 2: Adoption of Apache License 2.0
- **Recommendation**: Formally ratify the **Apache License, Version 2.0** as the official open-source license for all code and technical documentation in the repository.
- **Strategic Value**: Ensures permissive adoption by both commercial enterprises and academic researchers while providing defensive patent protection under Section 3.
- **Owner Action**: **APPROVED / RATIFIED**.

---

### Decision 3: Contributor Governance via DCO 1.1
- **Recommendation**: Adopt the Linux Foundation **Developer Certificate of Origin (DCO 1.1)** via mandatory `Signed-off-by` git commit sign-offs. Reject heavy corporate CLAs to maximize community contribution velocity while maintaining clean provenance.
- **Owner Action**: **APPROVED / RATIFIED**.

---

### Decision 4: Benchmark Dataset Zero-Vendoring Policy
- **Recommendation**: Enforce a strict zero-vendoring policy for third-party datasets. The repository and distributed Python packages must contain **zero raw image, audio, or tabular benchmark files**. All benchmark runners must download data on-the-fly to local user caches.
- **Owner Action**: **APPROVED / RATIFIED**.

---

### Decision 5: Clean-Room Implementation Mandate for RLA & RAO
- **Recommendation**: Mandate that all robust learning (RLA) and low-memory optimizer (RAO) implementations be derived clean-room from public academic literature, strictly barring code inspection or copying from AGPL-3.0 Cleanlab or proprietary GPU codebases.
- **Owner Action**: **APPROVED / RATIFIED**.

---

### Decision 6: External Legal Counsel Engagement Timeline
- **Recommendation**: Formal engagement of specialist intellectual property counsel will occur during **Phase 16 (Legal & Release Audit)** prior to the PyPI v1.0 General Availability release, focusing on final namespace clearance and trademark registration.
- **Owner Action**: **APPROVED / RATIFIED**.
