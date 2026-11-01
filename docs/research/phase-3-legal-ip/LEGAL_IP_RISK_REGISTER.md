# AdaptiveML — Phase 3: Legal & IP Risk Register

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-008`  
> **Last Updated**: 2026-11-01  
> **Classification Framework**: Trademark | License | Patent | Copyright | Privacy

---

## 1. Legal & Intellectual Property Risk Log

| Risk ID | Legal Area | Risk Description | Supporting Evidence | Jurisdiction | Prob. | Impact | Mitigation Strategy | Owner Action Required | Legal Review | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **L-RSK-001** | Trademark | **Namespace Collision with Adaptive ML, Inc. (Datadog)**: Commercial AI startup acquired by Datadog controls PyPI `AdaptiveML` org. | PyPI organization page, TechCrunch, Index Ventures announcement | US, Global | **High** | **High** | Maintain "AdaptiveML" strictly as internal codename. Pre-select `aml-core` or `libadaptive` for PyPI release. | Ratify provisional codename policy; do not register package yet. | **Yes** | **Mitigated** |
| **L-RSK-002** | License | **AGPL-3.0 License Contamination from Cleanlab**: Cleanlab's codebase is AGPL-3.0. Copying code would force copyleft terms on AdaptiveML. | Cleanlab official repository LICENSE file | Global | **Medium**| **High** | Enforce clean-room policy. Derive robust losses strictly from peer-reviewed academic papers (GCE/SCE). | Audit all RLA pull requests for clean-room provenance. | No | **Mitigated** |
| **L-RSK-003** | Patent | **Patent Claim Collision on Confident Learning (US11651239B2)**: Cleanlab, Inc. holds patents on joint distribution label error pruning. | USPTO Patent US11651239B2 | US | **Medium**| **High** | Completely exclude joint distribution matrix pruning. Rely on public-domain loss functions and density margins. | Approve RLA algorithm specifications avoiding confident joint math. | **Yes** | **Mitigated** |
| **L-RSK-004** | Patent | **Patent Claim Collision on Quantized Optimizers (US20230289612A1)**: Pending claims on non-linear quantile codebooks on GPU. | USPTO Application US20230289612A1 | US, Global | **Low** | **High** | Implement linear block-scaling and standard integer representations on CPU, avoiding non-linear quantile codebooks. | Approve RAO specifications restricting quantization to linear scaling. | **Yes** | **Mitigated** |
| **L-RSK-005** | Copyright | **Contributor IP Contamination / Proprietary Code Leaks**: Contributors submit proprietary corporate code or unlicensed snippets. | Standard open-source litigation precedent | Global | **Low** | **High** | Enforce Developer Certificate of Origin (DCO 1.1) sign-offs on all commits; automated CI DCO bot. | Mandate git commit `-s` flag for all repository contributors. | No | **Mitigated** |
| **L-RSK-006** | Privacy | **Violation of Privacy / Telemetry Regulations (GDPR/DPDP)**: Unintended collection of user analytics or telemetry on local hardware. | Global data protection regulations | EU, India, US | **Low** | **Medium** | Enforce zero-telemetry policy. The library makes zero network calls during execution. | Review packaging to ensure zero phone-home network requests. | No | **Closed** |
