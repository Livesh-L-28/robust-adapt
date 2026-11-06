# ADAPTIVEML STAGE 16.3.1 — COUNSEL SUBMISSION DOSSIER
## Master Trademark, Brand Identity & Commercial Risk Submission for Outside Legal Counsel

**Document Identifier:** `docs/verification/stage_16_3_1/COUNSEL_SUBMISSION_DOSSIER.md`<br>
**Distribution Reference:** `docs/verification/stage_16_3_1/counsel_submission/COUNSEL_SUBMISSION_DOSSIER.md`<br>
**Stage:** 16.3.1 — External Counsel Engagement & Legal Evidence Submission<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Current Technical Baseline:** `AdaptiveML` / `aml-core` v0.1.0.dev0 (`import adaptive_ml`)<br>
**Submission Date:** 2026-11-06<br>
**Auditor / Submitter:** Software Architecture Taskforce & IP Compliance Reviewer<br>
**Recipient:** Qualified External Intellectual Property & Trademark Counsel<br>

---

## Notice to Reviewing Counsel

> [!IMPORTANT]
> **PURPOSE AND LEGAL NATURE OF THIS DOSSIER:**<br>
> This submission package compiles factual, technical, and documentary evidence regarding the software library known technically as `AdaptiveML` (`aml-core`).<br>
>
> Technical auditors and software engineers **do not render legal opinions or establish legal clearance**. This document is prepared specifically for licensed intellectual property counsel to:
> 1. Conduct independent trademark clearance and likelihood-of-confusion searches across relevant jurisdictions and Nice classes.
> 2. Render a formal written legal opinion on trademark infringement risks, dilution risks, unfair competition exposure, and registrability.
> 3. Provide actionable recommendations on whether a clean-break rebrand is legally necessary prior to public open-source distribution.

---

## 1. Project Overview & Mission

* **Project Title:** AdaptiveML (pre-release working codename).
* **Technical Mission:** High-performance, streaming, adaptive machine learning library optimized for commodity CPU hardware.
* **Core Technological Pillars:**
  1. *Adaptive Learning Architecture (ALA):* Streaming concept drift detection, background shadow modeling, and dynamic ensemble adaptation.
  2. *Robust Learning Architecture (RLA):* Noise-resilient streaming loss functions (Symmetric Cross-Entropy, Generalized Cross-Entropy), sample reliability weighting, and label noise mitigation.
  3. *Resource-Aware Optimization (RAO):* CPU-cache-optimized optimizers (streaming AdamW), adaptive gradient memory budgeting, and dynamic quantization.
  4. *Unified Learning Controller (ULC):* Finite-state controller coordinating cross-pillar interactions, telemetry monitoring, and fallback stabilization.
* **Intended Audience:** Data scientists, machine learning engineers, and software developers building edge, streaming, and production ML systems on local CPUs.

---

## 2. Product Functionality and Intended Use

* **Software Class:** Computational software library / developer framework.
* **Execution Environment:** Local runtime execution in Python environments (Python 3.10–3.12).
* **Core Modality:**
  - Tabular, stream-based, and incremental supervised classification.
  - Interoperability with Scikit-Learn pipelines (`BaseEstimator`, `ClassifierMixin`) and PyTorch neural network modules (`nn.Module`, optimizers).
* **Non-Cloud / Non-Hosted Scope:** The software is distributed as downloadable Python source and pre-built wheel packages. It does **not** provide hosted cloud infrastructure, SaaS APIs, or remote model-training endpoints.

---

## 3. Open-Source Distribution Model

* **Software License:** Apache License, Version 2.0 (permissive open-source license).
* **Commercial Model:** Pure non-commercial, community-accessible open-source library.
* **Monetization:** None. Zero subscription fees, zero licensing fees, zero commercial service tiers.
* **Copyright Notice:** `Copyright 2026 AdaptiveML Contributors`.
* **Trademark Clause in Apache-2.0:** Section 6 of Apache-2.0 explicitly provides:
  > *"This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work..."*

---

## 4. Current Identity Inventory (The Five Identity Surfaces)

The project currently manifests its naming identity across five distinct surfaces:

```
+-----------------------------------------------------------------------------------+
|                        FIVE-SURFACE IDENTITY MATRIX                               |
+-----------------------------------------------------------------------------------+
| Surface 1: Public Project Codename    --> "AdaptiveML"                            |
| Surface 2: PyPI Package Distribution  --> "aml-core"                              |
| Surface 3: Python Import Namespace    --> "adaptive_ml"                           |
| Surface 4: Repository / Workspace     --> "AdaptiveML" (C:\projects\AdaptiveML)   |
| Surface 5: PyPI Organization Account  --> Unregistered / Unreserved               |
+-----------------------------------------------------------------------------------+
```

1. **Public Brand / Codename (`AdaptiveML`):** Used in documentation headers, tutorials, README files, and architectural designs.
2. **PyPI Distribution Package (`aml-core`):** Declared in `pyproject.toml` (`name = "aml-core"`). Generated wheel is `aml_core-0.1.0.dev0-py3-none-any.whl`.
3. **Python Import Namespace (`adaptive_ml`):** Root module directory `adaptive_ml/`. Invoked in Python code as `import adaptive_ml as aml` or `from adaptive_ml.ala import ConceptDriftClassifier`.
4. **Repository Slug (`AdaptiveML`):** Local repository path `C:\projects\AdaptiveML`; planned GitHub repository URL `https://github.com/[org]/AdaptiveML`.
5. **PyPI Organization Identifier:** Unregistered. Currently, the PyPI organization `AdaptiveML` is controlled by a third party.

---

## 5. Trademark Conflict Background: Adaptive ML, Inc. (Datadog)

### 5.1 The Conflicting Commercial Entity
* **Company Name:** Adaptive ML, Inc.
* **Commercial Status:** Commercial AI startup founded in late 2023.
* **Financing:** Raised a \$20 million seed funding round in March 2024 led by Index Ventures, with participation from Databricks Ventures and Bessemer Venture Partners.
* **Acquisition by Datadog:** In 2025, Adaptive ML was acquired by **Datadog, Inc.** (NASDAQ: DDOG), an enterprise cloud observability and security corporation. The entity was integrated into Datadog AI Research Labs.
* **Commercial Product:** "Adaptive Engine" — an enterprise platform for fine-tuning, evaluating, deploying, and serving domain-specialized large language models (LLMs) using reinforcement learning from human/AI feedback (RLHF/RLAIF).

### 5.2 Ecosystem and Registry Proximity
* **PyPI User Account:** Controls `https://pypi.org/user/AdaptiveML/` and `https://pypi.org/org/AdaptiveML/`.
* **PyPI Published Package:** Publishes [`adaptive-sdk`](https://pypi.org/project/adaptive-sdk/), described as *"Python Client SDK for Adaptive Engine (by Adaptive ML)"*.
* **Area of Overlap:** Both entities operate in the machine learning software ecosystem, targeting Python developers, data scientists, and ML infrastructure engineers.

---

## 6. Existing Research & Search Evidence

Technical auditors conducted preliminary scans of public trademark registries in Stage 16:

### 6.1 United States Patent and Trademark Office (USPTO)
* **Databases:** USPTO Trademark Search (TESS) & TSDR.
* **Search Terms:** `"ADAPTIVE ML"`, `"ADAPTIVE MACHINE LEARNING"`, `"ADAPTIVE ENGINE"`.
* **Relevant Classes:** Class 09 (Computer software), Class 42 (Technology services).
* **Preliminary Observations:**
  - Inherent descriptiveness scrutiny under 15 U.S.C. § 1052(e)(1) ("merely descriptive" software features).
  - Common-law commercial use by *Adaptive ML, Inc.* in interstate commerce since early 2024.
  - Exposure to Lanham Act § 43(a) (15 U.S.C. § 1125(a)) for false designation of origin and unfair competition.

### 6.2 Indian Trade Marks Registry (IP India)
* **Search Terms:** `"ADAPTIVE ML"`, `"ADAPTIVE"` in Classes 9 and 42.
* **Statutory Framework:**
  - Section 9(1)(a) (Absolute grounds for refusal: marks devoid of distinctive character).
  - Section 11(1) (Relative grounds for refusal: confusing similarity with earlier marks).

### 6.3 Package Repositories (PyPI Index)
* `aml-core` is currently available / unregistered on PyPI.
* `adaptive-ml` is unregistered on PyPI, but the organization account `AdaptiveML` is actively claimed by Datadog.

---

## 7. Relevant Corporate and Acquisition Evidence

The following distinction is established between verified facts, public records, and unverified deal terms:

* `[SECONDARY EVIDENCE - VERIFIED PUBLIC RECORD]`: TechCrunch, Index Ventures, and Datadog public statements confirm that Adaptive ML was acquired by Datadog in 2025 to develop RLOps and LLM post-training capabilities.
* `[SECONDARY EVIDENCE - VERIFIED REGISTRY RECORD]`: PyPI registry records confirm that `adaptive-sdk` is actively maintained under the `AdaptiveML` account.
* `[UNKNOWN - PRIVATE TRANSACTION TERMS]`: The specific asset assignment schedules, intellectual property transfer documents, and goodwill assignments between Adaptive ML, Inc. founders and Datadog, Inc. are private corporate contracts. Technical auditors have no access to these agreements. Counsel is requested to consider how corporate ownership structures affect common-law priority and enforcement standing.

---

## 8. Jurisdiction and Market Scope

* **Primary Release Jurisdictions:**
  1. **United States:** Primary developer adoption, hosting infrastructure, and competitor corporate locus.
  2. **India:** Development and initial contributor jurisdiction.
  3. **European Union & United Kingdom:** Key international open-source developer communities.
* **Target Nice Classification:**
  - **Class 09 (Software):** Downloadable machine learning computer software; software libraries; algorithms recorded on media.
  - **Class 42 (Services - Relevant for Competitor):** SaaS, cloud AI services, computer software consultancy.

---

## 9. Intended Distribution Channels

The project intends to distribute the software exclusively through standard developer package channels:
1. **Python Package Index (PyPI):** Via `pip install <package-name>`.
2. **Source Code Hosting (GitHub):** Open-source public repository with Git tags and releases.
3. **Documentation Portals:** Hosted on GitHub Pages / ReadTheDocs via MkDocs.
4. **Conda-Forge:** Future community recipe channel.

---

## 10. Candidate Identity Comparison

Four alternative naming candidate identities were identified by software architects for counsel investigation:

| Candidate Mark | Proposed PyPI Name | Proposed Namespace | Architectural & Conceptual Basis | Known Preliminary Search Results |
| :--- | :--- | :--- | :--- | :--- |
| **AdaptiveML** *(Baseline)* | `aml-core` | `adaptive_ml` | Current working codename; highly descriptive of adaptive learning algorithms. | Collides directly with *Adaptive ML, Inc.* (Datadog). `[NOT CLEARED]` |
| **ResiliML** *(Candidate 1)* | `resiliml` / `resiliml-core` | `resiliml` | Blends *resilience* (to drift, noise, resource bounds) with *ML*. Distinctive portmanteau. | Available on PyPI; 0 identical USPTO software marks found in basic scan. `[NOT CLEARED]` |
| **StreamAdapt** *(Candidate 2)* | `streamadapt` | `streamadapt` | References streaming continual adaptation. Highly descriptive. | Multiple academic papers and GitHub repos use the generic term. `[NOT CLEARED]` |
| **LibAdaptive** *(Candidate 3)* | `libadaptive` | `libadaptive` | Classical C/UNIX style naming. | Retains the descriptive root "Adaptive"; proximate to existing marks. `[NOT CLEARED]` |
| **The AML Core Project** | `aml-core` | `aml` | Formalizes acronym; drops "AdaptiveML" product name. | High proximity to Microsoft AzureML (`azureml-core`) and Anti-Money Laundering. `[NOT CLEARED]` |

> [!WARNING]
> None of the above candidates are declared legally cleared. Outside counsel is requested to conduct formal searches on *ResiliML* and advise on candidate viability.

---

## 11. Technical Namespace Implications

In Python software architecture, changing naming identifiers has distinct operational implications across surfaces:
1. **Public Product Name:** Can be renamed in documentation and marketing with zero code breakage.
2. **Distribution Package (`pyproject.toml`):** Renaming affects installation commands (`pip install <name>`), but does not break internal module imports if aliases are maintained.
3. **Python Import Namespace (`adaptive_ml`):** Renaming requires updating every internal import across 70 production modules and breaks all existing user scripts and tutorials.
4. **The Asymmetric Resolution Trap:** If the project changes only the distribution package (`aml-core`) while retaining "AdaptiveML" as the public brand and `import adaptive_ml` in code, the trademark collision remains active in the developer ecosystem.

---

## 12. Legal Questions Requiring Counsel Determination

Counsel is requested to review and answer the definitive **10-Point Legal Questionnaire** compiled in [`COUNSEL_QUESTIONNAIRE_FINAL.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/COUNSEL_QUESTIONNAIRE_FINAL.md).

---

## 13. Current Release Restrictions and Governance Locks

To ensure complete legal compliance and risk mitigation prior to counsel's formal advice:
- **`DEF-004` (Trademark Collision):** Formally held **`OPEN — COUNSEL REVIEW REQUIRED`**.
- **Owner Decision Record:** Unsigned (`DRAFT`). Stop condition notice [`OWNER_DECISION_PENDING.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3/OWNER_DECISION_PENDING.md) is active.
- **Controlled Alpha Release (Phase 17):** **`WITHHELD / DISTRIBUTION NOT AUTHORIZED`**. Zero packages distributed externally.
- **Public PyPI 1.0 Release (Phase 18):** **`STRICTLY LOCKED`**.
- **Standby AST Migration:** Refactoring scripts (`scripts/migrate_identity.py`) are tested in dry-run mode and standing by for owner authorization following counsel review.

---

## 14. Supporting Evidence Index

| Evidence ID | Description | Document Path |
| :--- | :--- | :--- |
| **EVID-01** | Stage 16.3.1 Repository & Evidence Inventory | [`REPOSITORY_AND_EVIDENCE_INVENTORY.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/REPOSITORY_AND_EVIDENCE_INVENTORY.md) |
| **EVID-02** | Stage 16.3.1 Governance Corrections | [`STAGE_16_3_GOVERNANCE_CORRECTIONS.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/STAGE_16_3_GOVERNANCE_CORRECTIONS.md) |
| **EVID-03** | Final Legal Questionnaire for Counsel | [`COUNSEL_QUESTIONNAIRE_FINAL.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/COUNSEL_QUESTIONNAIRE_FINAL.md) |
| **EVID-04** | Traceable Trademark Evidence Register | [`TRADEMARK_EVIDENCE_REGISTER.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/TRADEMARK_EVIDENCE_REGISTER.md) |
| **EVID-05** | Candidate Identity Investigation Brief | [`CANDIDATE_IDENTITY_INVESTIGATION_BRIEF.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/CANDIDATE_IDENTITY_INVESTIGATION_BRIEF.md) |
| **EVID-06** | Stage 16 Trademark Investigation Report | [`stage_16/TRADEMARK_AND_BRAND_INVESTIGATION.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16/TRADEMARK_AND_BRAND_INVESTIGATION.md) |
| **EVID-07** | Stage 16.3 Five-Surface Trademark Analysis | [`stage_16_3/TRADEMARK_DECISION_ANALYSIS.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3/TRADEMARK_DECISION_ANALYSIS.md) |

---

## 15. Evidence Limitations & Matters Reserved for Counsel

1. **Certified Trademark Searches:** Certified search reports from official national registries (USPTO, IP India, EUIPO) were not pulled by technical auditors. Counsel search required.
2. **Common-Law Trademark Audit:** Comprehensive common-law use investigation across AI developer tools and GitHub repositories was limited to public search engines.
3. **Corporate Goodwill & Assignment:** Asset transfer terms between Adaptive ML, Inc. and Datadog, Inc. remain confidential; counsel is requested to evaluate risks assuming Datadog owns all successor rights.
4. **Litigation Cost & Injunction Risk Modeling:** Prior informal estimates of \$250,000–\$500,000 have been struck as unverified; counsel is requested to provide objective risk guidance.
