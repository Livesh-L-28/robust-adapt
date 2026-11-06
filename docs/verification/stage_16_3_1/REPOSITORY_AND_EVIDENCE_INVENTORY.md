# ADAPTIVEML STAGE 16.3.1 — REPOSITORY AND EVIDENCE INVENTORY
## Repository Baseline Audit, Historical Document Survey, and Evidence Classification Matrix

**Document Identifier:** `docs/verification/stage_16_3_1/REPOSITORY_AND_EVIDENCE_INVENTORY.md`<br>
**Stage:** 16.3.1 — External Counsel Engagement & Legal Evidence Submission<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Working Tree Status:** 100% Intact & Preserved (60 tracked modifications preserved, 0 commits, 0 tags, 0 pushes)<br>
**Audit Date:** 2026-11-06<br>
**Auditor:** Software Quality Auditor & Legal Evidence Archivist<br>

---

## 1. Executive Purpose & Verification Philosophy

This inventory establishes a complete, traceable baseline of all codebase artifacts, documentation reports, and factual claims across Stages 16, 16.1, 16.2, 16.3, and Phase 17.

> [!WARNING]
> **EPISTEMIC SKEPTICISM & INDEPENDENT VERIFICATION:**<br>
> Historical verification reports cannot be assumed to be independently verified merely because they exist in the repository. Every claim regarding corporate ownership, financing, litigation probability, or statutory clearance must be audited against primary authoritative sources or explicitly classified according to its evidentiary grounding.

---

## 2. Repository Git State & File System Status

### 2.1 Git Repository Invariants
- **Active Branch:** `master`
- **HEAD Commit Hash:** `67e9ef1b347ca223828a1f225e85e35a086a1f30`
- **Upstream Tracking:** Detached from remote pushes; zero unpushed or pushed releases.
- **Staging Status:** Clean staging area; zero files added to index (`Changes not staged for commit`).

### 2.2 Preserved Working-Tree Modifications
The 60 tracked modifications generated during production stabilization and historical documentation audits are preserved without alteration:
- **Core Governance & Licenses:** `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `NOTICE`, `SECURITY.md`, `pyproject.toml`, `mkdocs.yml`.
- **Production Source Code (Untouched in 16.3.1):** 21 modules in `adaptive_ml/` (`__init__.py`, `ala/`, `core/`, `integrations/`, `rao/`, `rla/`, `state/`, `ulc/`).
- **Documentation & Guides:** 32 files in `docs/` (`concepts/`, `engineering/`, `guides/`, `getting-started/`, `integrations/`, `tutorials/`).

### 2.3 Package Metadata and Licensing Records
- **`pyproject.toml` (Distribution Identity):**
  - Distribution Package Name: `aml-core`
  - Version: `0.1.0.dev0`
  - Import Namespace: `packages.find = ["adaptive_ml*"]`
  - License Expression: `Apache-2.0`
  - Author: `AdaptiveML Contributors`
- **`LICENSE`:** Standard Apache License, Version 2.0 (January 2004).
- **`NOTICE`:**
  - Product Name Cited: `AdaptiveML`
  - Copyright Attribution: `Copyright 2026 AdaptiveML Contributors`
  - Foundation: Apache Software Foundation terms.

---

## 3. Evidence Classification Taxonomy

All claims and records in the repository are classified under the six-tier evidentiary taxonomy:

| Classification | Meaning | Treatment in Legal Submission |
| :--- | :--- | :--- |
| **VERIFIED PRIMARY EVIDENCE** | Directly supported by an authoritative primary source (e.g., USPTO TSDR, IP India registry, SEC 8-K filing, local codebase artifact). | Admissible as established fact for counsel evaluation. |
| **SECONDARY EVIDENCE** | Supported by credible secondary sources (e.g., TechCrunch, Index Ventures press releases, reputable trade publications). | Included as corroborating evidence subject to primary verification by counsel. |
| **INTERNAL PROJECT CLAIM** | Asserted in project documentation or internal design specs without external independent corroboration. | Labeled as project assumptions; not presented as legal facts. |
| **ENGINEERING ESTIMATE** | Technical or cost calculation requiring empirical validation (e.g., migration duration, litigation defense costs). | Subject to verification; excluded from legal justification. |
| **LEGAL QUESTION** | Statutory interpretation, likelihood of confusion, or clearance inquiry requiring licensed legal counsel. | Formally referred to outside counsel via questionnaire. |
| **UNKNOWN** | Insufficient or absent evidence to substantiate the claim. | Cataloged in the Legal Evidence Gap Register for counsel research. |

---

## 4. Comprehensive Inventory of Historical Verification Artifacts

An audit of all verification packages was conducted on 2026-11-06:

### 4.1 Stage 16 Package: Legal, IP & Release Audit (`docs/verification/stage_16/`)
*Total Documents: 19* | *Audit Baseline Date: 2026-11-06*

| File Name | Primary Subject | Evidentiary Basis | Classification |
| :--- | :--- | :--- | :--- |
| `STAGE_16_EXECUTIVE_SUMMARY.md` | Master Stage 16 summary and governance baseline | Synthesis of Stage 16 reports | `INTERNAL PROJECT CLAIM` |
| `INITIAL_LEGAL_AND_RELEASE_AUDIT.md` | Pre-flight audit across all 10 release dimensions | Local repository inspection | `VERIFIED PRIMARY EVIDENCE` |
| `TRADEMARK_AND_BRAND_INVESTIGATION.md` | Investigation of *Adaptive ML, Inc.* and marks | Public USPTO/IP India search & news | `SECONDARY EVIDENCE` |
| `LICENSE_COMPLIANCE_REPORT.md` | Apache-2.0 and dependency license audit | `pip-licenses` and dependency files | `VERIFIED PRIMARY EVIDENCE` |
| `COPYRIGHT_AND_CODE_PROVENANCE_AUDIT.md` | Git author and provenance investigation | Git log history and commit trees | `VERIFIED PRIMARY EVIDENCE` |
| `PATENT_AND_PRIOR_ART_REVIEW.md` | Prior art search on continual learning & ULC | Google Patents & academic papers | `SECONDARY EVIDENCE` |
| `DATASET_AND_ASSET_COMPLIANCE_REPORT.md` | Licensing of synthetic & benchmark datasets | Local benchmark script inspection | `VERIFIED PRIMARY EVIDENCE` |
| `RELEASE_SECURITY_AND_SUPPLY_CHAIN_AUDIT.md` | Bandit, pip-audit, and pinning audit | Static security tool logs | `VERIFIED PRIMARY EVIDENCE` |
| `PACKAGE_IDENTITY_AND_NAMESPACE_AUDIT.md` | PyPI index availability for `aml-core` | PyPI JSON API and web scrape | `SECONDARY EVIDENCE` |
| `BRAND_CONTINGENCY_AND_RENAMING_PLAN.md` | Rebrand blueprints (*ResiliML*, etc.) | Software architecture specs | `ENGINEERING ESTIMATE` |
| `LEGAL_COUNSEL_QUESTIONS.md` | Preliminary 10 legal questions for counsel | Legal compliance questions | `LEGAL QUESTION` |
| `LEGAL_COUNSEL_REVIEW_PACKAGE.md` | Pre-submission brief for trademark counsel | Synthesis of legal findings | `INTERNAL PROJECT CLAIM` |
| `REMEDIATION_AND_OWNER_DECISION_REGISTER.md` | Defect tracking and owner choices | Project governance records | `INTERNAL PROJECT CLAIM` |
| `GOVERNANCE_AND_LEGAL_DOCUMENTATION_AUDIT.md` | Audit of CONTRIBUTING, SECURITY, etc. | Local repository inspection | `VERIFIED PRIMARY EVIDENCE` |
| `INDEPENDENT_RELEASE_AUDIT.md` | Independent verification of Stage 16 | QA audit log | `INTERNAL PROJECT CLAIM` |
| `RELEASE_AUTHORIZATION_SCORECARD.md` | Release gate evaluation (Release Withheld) | Governance gate matrix | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_COMPLETION_REPORT.md` | Final Stage 16 sign-off and next steps | Stage sign-off log | `INTERNAL PROJECT CLAIM` |
| `CONFIDENTIALITY_AND_SECRET_EXPOSURE_AUDIT.md` | Trufflehog / Gitleaks scan of secrets | Secret scanner output | `VERIFIED PRIMARY EVIDENCE` |
| `CONSOLIDATED_EVIDENCE_INDEX.md` | Cross-report index of evidence citations | Index metadata | `INTERNAL PROJECT CLAIM` |

### 4.2 Stage 16.1 Package: Counsel Preparation & ODR (`docs/verification/stage_16_1/`)
*Total Documents: 15* | *Audit Baseline Date: 2026-11-06*

| File Name | Primary Subject | Evidentiary Basis | Classification |
| :--- | :--- | :--- | :--- |
| `STAGE_16_1_EXECUTIVE_SUMMARY.md` | Master Stage 16.1 executive report | Synthesis of Stage 16.1 | `INTERNAL PROJECT CLAIM` |
| `TRADEMARK_EVIDENCE_REGISTER.md` | Structured claims on *Adaptive ML, Inc.* | TechCrunch, Index, PyPI, USPTO | `SECONDARY EVIDENCE` |
| `TRADEMARK_COUNSEL_QUESTIONS.md` | 10 refined statutory counsel questions | Statutory trademark questions | `LEGAL QUESTION` |
| `PACKAGE_IDENTITY_AND_NAMESPACE_DECISION_MATRIX.md` | 5-surface naming conflict analysis | Architectural mapping | `INTERNAL PROJECT CLAIM` |
| `BRAND_MIGRATION_SCENARIO_ANALYSIS.md` | Analysis of Options A, B, C, D | Scenario risk analysis | `INTERNAL PROJECT CLAIM` |
| `DEF_004_REMEDIATION_AND_CLOSURE_CRITERIA.md` | 10 mandatory closure preconditions | Governance criteria | `INTERNAL PROJECT CLAIM` |
| `OWNER_DECISION_MEMORANDUM.md` | Owner briefing on rebranding | Project decision brief | `INTERNAL PROJECT CLAIM` |
| `COPYRIGHT_AND_PROVENANCE_COUNSEL_DOSSIER.md` | Author and copyright transfer dossier | Contributor agreements / Git logs | `VERIFIED PRIMARY EVIDENCE` |
| `PATENT_AND_FTO_COUNSEL_DOSSIER.md` | Freedom to operate dossier on algorithms | Algorithmic analysis & patents | `SECONDARY EVIDENCE` |
| `OPEN_SOURCE_AND_COMMERCIAL_LICENSING_REVIEW.md` | Dual-use and commercial licensing review | Apache-2.0 legal analysis | `SECONDARY EVIDENCE` |
| `RELEASE_GATE_AND_AUTHORIZATION_MATRIX.md` | 10 pre-release gates evaluation | Release gate matrix | `INTERNAL PROJECT CLAIM` |
| `COUNSEL_SUBMISSION_MASTER_DOSSIER.md` | Master dossier for external counsel | Comprehensive legal brief | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_1_EVIDENCE_TRACEABILITY_MATRIX.md` | Traceability mapping of 50+ claims | Claim-to-source mapping | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_1_INDEPENDENT_REVIEW.md` | QA review of Stage 16.1 deliverables | QA verification report | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_1_COMPLETION_REPORT.md` | Sign-off report for Stage 16.1 | Stage sign-off log | `INTERNAL PROJECT CLAIM` |

### 4.3 Stage 16.2 Package: Decision Execution Preparation (`docs/verification/stage_16_2/`)
*Total Documents: 12* | *Audit Baseline Date: 2026-11-06*

| File Name | Primary Subject | Evidentiary Basis | Classification |
| :--- | :--- | :--- | :--- |
| `STAGE_16_2_EXECUTIVE_SUMMARY.md` | Master Stage 16.2 executive briefing | Synthesis of Stage 16.2 | `INTERNAL PROJECT CLAIM` |
| `EXTERNAL_COUNSEL_OPINION_REVIEW.md` | Intake check for counsel opinion (Pending) | Workspace audit (0 letters) | `VERIFIED PRIMARY EVIDENCE` |
| `FORMAL_OWNER_DECISION_RECORD.md` | Draft ODR (`AML-ODR-2026-001`) | Draft governance template | `INTERNAL PROJECT CLAIM` |
| `PACKAGE_IDENTITY_DECISION.md` | Provisional baseline retention record | Architectural record | `INTERNAL PROJECT CLAIM` |
| `TRADEMARK_CLEARANCE_DECISION.md` | Pre-clearance assessment (Withheld) | Trademark compliance audit | `INTERNAL PROJECT CLAIM` |
| `IDENTITY_REMEDIATION_PLAN.md` | AST migration execution protocol | Standby script specs | `ENGINEERING ESTIMATE` |
| `IDENTITY_MIGRATION_REPORT.md` | Migration log confirming `NOT EXECUTED` | Codebase audit (0 changes) | `VERIFIED PRIMARY EVIDENCE` |
| `POST_REMEDIATION_LEGAL_AND_TECHNICAL_AUDIT.md` | Post-remediation verification plan | Verification test suite plan | `INTERNAL PROJECT CLAIM` |
| `DEF_004_FINAL_STATUS_REPORT.md` | Defect audit confirming DEF-004 `OPEN` | Defect tracking audit | `INTERNAL PROJECT CLAIM` |
| `UPDATED_RELEASE_AUTHORIZATION_SCORECARD.md` | Release gate scorecard (Alpha Withheld) | Release gate matrix | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_2_INDEPENDENT_REVIEW.md` | Independent QA review of Stage 16.2 | QA verification report | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_2_COMPLETION_REPORT.md` | Sign-off report for Stage 16.2 | Stage sign-off log | `INTERNAL PROJECT CLAIM` |

### 4.4 Stage 16.3 Package: External Counsel Decision & Gate Closure (`docs/verification/stage_16_3/`)
*Total Documents: 14* | *Audit Baseline Date: 2026-11-06*

| File Name | Primary Subject | Evidentiary Basis | Classification |
| :--- | :--- | :--- | :--- |
| `STAGE_16_3_EXECUTIVE_SUMMARY.md` | Master Stage 16.3 governance dashboard | Synthesis of Stage 16.3 | `INTERNAL PROJECT CLAIM` |
| `EXTERNAL_COUNSEL_FINAL_OPINION_ASSESSMENT.md` | Intake audit & 10 statutory questions | Workspace audit (0 letters) | `VERIFIED PRIMARY EVIDENCE` |
| `TRADEMARK_DECISION_ANALYSIS.md` | 5-surface trademark risk analysis | Trademark doctrine mapping | `SECONDARY EVIDENCE` |
| `LEGAL_RISK_AND_REMEDIATION_REGISTER.md` | Multi-pillar legal & regulatory risk matrix | Legal risk assessment | `INTERNAL PROJECT CLAIM` |
| `FINAL_OWNER_DECISION_RECORD.md` | Final ODR template (`STAGE16-3-FINAL`) | Draft governance template | `INTERNAL PROJECT CLAIM` |
| `OWNER_DECISION_PENDING.md` | Stop condition notice halting migration | Active stop condition notice | `VERIFIED PRIMARY EVIDENCE` |
| `APPROVED_IDENTITY_DECISION.md` | Identity determination (Baseline retained) | Identity record (Corrected in 16.3.1) | `INTERNAL PROJECT CLAIM` |
| `DEF_004_CLOSURE_ASSESSMENT.md` | 10-precondition audit (0/10 met, OPEN) | Precondition evaluation | `VERIFIED PRIMARY EVIDENCE` |
| `IDENTITY_MIGRATION_EXECUTION_REPORT.md` | Migration log confirming `NOT EXECUTED` | Codebase audit (0 changes) | `VERIFIED PRIMARY EVIDENCE` |
| `POST_REMEDIATION_VERIFICATION_REPORT.md` | Invariant re-affirmation & test plan | Test runner verification | `VERIFIED PRIMARY EVIDENCE` |
| `PHASE_17_AUTHORIZATION_DECISION.md` | 11-gate audit (Alpha Not Authorized) | Gate evaluation matrix | `INTERNAL PROJECT CLAIM` |
| `UPDATED_RELEASE_GATE_SCORECARD.md` | Updated release pipeline scorecard | Release gate matrix | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_3_INDEPENDENT_REVIEW.md` | Independent review certifying release locks | QA audit verification | `INTERNAL PROJECT CLAIM` |
| `STAGE_16_3_COMPLETION_REPORT.md` | Master sign-off report for Stage 16.3 | Stage sign-off log | `INTERNAL PROJECT CLAIM` |

### 4.5 Phase 17 Package: Controlled Alpha/Beta Release (`docs/verification/phase_17/`)
*Total Documents: 19* | *Audit Baseline Date: 2026-11-06*

| File Name | Primary Subject | Evidentiary Basis | Classification |
| :--- | :--- | :--- | :--- |
| `PHASE_17_EXECUTIVE_SUMMARY.md` | Master Phase 17 dashboard (`NOT AUTHORIZED`) | Phase 17 synthesis | `INTERNAL PROJECT CLAIM` |
| `ALPHA_RELEASE_READINESS_REPORT.md` | Readiness audit across technical & legal gates | Multi-gate evaluation | `INTERNAL PROJECT CLAIM` |
| `ALPHA_BUILD_AND_INSTALLATION_REPORT.md` | Wheel/sdist build & clean environment install | Local build and pip logs | `VERIFIED PRIMARY EVIDENCE` |
| `ALPHA_TEST_PLAN.md` | Internal test plan & test distribution scope | Test specification | `INTERNAL PROJECT CLAIM` |
| `EXTERNAL_DEVELOPER_FEEDBACK_REPORT.md` | Feedback tracking (**Formally Marked NOT EXECUTED**) | Feedback register (0 testers) | `VERIFIED PRIMARY EVIDENCE` |
| `DEFECT_AND_ISSUE_REGISTER.md` | Defect tracking (DEF-004 OPEN; 0 technical) | Defect audit log | `VERIFIED PRIMARY EVIDENCE` |
| `BETA_READINESS_REPORT.md` | Beta prerequisites audit (**STRICTLY LOCKED**) | Beta gating criteria | `INTERNAL PROJECT CLAIM` |
| `BETA_RELEASE_VALIDATION_REPORT.md` | Beta validation report (**NOT EXECUTED**) | Validation specification | `INTERNAL PROJECT CLAIM` |
| `RELEASE_CANDIDATE_ASSESSMENT.md` | Release candidate assessment (**WITHHELD**) | RC certification criteria | `INTERNAL PROJECT CLAIM` |
| `PHASE_17_INDEPENDENT_VERIFICATION.md` | Independent verification of release locks | QA audit certification | `INTERNAL PROJECT CLAIM` |
| `PHASE_17_COMPLETION_REPORT.md` | Phase 17 completion sign-off (`NOT AUTHORIZED`) | Phase sign-off log | `INTERNAL PROJECT CLAIM` |
| Algorithmic Alpha Reports (7 files) | Verification of ALA, RLA, RAO, Minority, ULC | Local test run results (1,745 tests) | `VERIFIED PRIMARY EVIDENCE` |

---

## 5. Critical Evidence Audit and Provenance Assessment

Every major factual assertion previously utilized to guide project decisions was audited to establish whether authoritative primary-source evidence exists:

### 5.1 Corporate Formation of Adaptive ML, Inc.
- **Claim:** Founded in late 2023 by former researchers from Hugging Face and contributors to BLOOM / Falcon LLM.
- **Audited Sources:** `https://en.wikipedia.org/wiki/Adaptive_ML`, `https://adaptive-ml.com`, founding news articles.
- **Audit Finding:** **SECONDARY EVIDENCE**. Credible industry press confirms founders' backgrounds. However, certified Articles of Incorporation (e.g., Delaware Division of Corporations) are not in the repository.
- **Action for Counsel:** Counsel may confirm formal corporate standing if relevant to trademark priority.

### 5.2 \$20 Million Institutional Financing Round
- **Claim:** Raised \$20M seed round in March 2024 led by Index Ventures with Databricks Ventures and Bessemer Venture Partners.
- **Audited Sources:** Index Ventures official blog (`https://indexventures.com`), TechCrunch coverage.
- **Audit Finding:** **SECONDARY EVIDENCE**. Widely corroborated across authoritative venture capital news outlets. Sufficient to establish substantial commercial investment and active market presence.

### 5.3 Corporate Acquisition by Datadog, Inc.
- **Claim:** In 2025, Adaptive ML was acquired by Datadog, Inc. (NASDAQ: DDOG).
- **Audited Sources:** Datadog press releases and SEC filings (10-Q / 8-K references to strategic talent/technology acquisitions).
- **Audit Finding:** **SECONDARY EVIDENCE / CREDIBLE PUBLIC RECORD**. The acquisition is established in public market reporting. However, the private Asset Purchase Agreement or Merger Agreement—which governs the specific assignment of common-law trademark rights and commercial goodwill—is private.
- **Classification:** **`LEGAL QUESTION / UNKNOWN PRIVATE DEAL TERMS`**. Outside counsel must evaluate whether trademark rights were formally assigned to Datadog or retained by a subsidiary.

### 5.4 PyPI Presence (`AdaptiveML` Org and `adaptive-sdk`)
- **Claim:** Datadog / Adaptive ML controls PyPI user/org `AdaptiveML` and actively publishes `adaptive-sdk`.
- **Audited Sources:** `https://pypi.org/project/adaptive-sdk/`, `https://pypi.org/user/AdaptiveML/`.
- **Audit Finding:** **VERIFIED PRIMARY EVIDENCE**. The package exists on the public index, is categorized in AI/LLM tooling, and actively uses the "Adaptive" naming umbrella in the Python developer ecosystem.

### 5.5 USPTO Trademark Registrations for "ADAPTIVE ML"
- **Claim:** USPTO searches show high descriptiveness scrutiny under Section 2(e)(1) and active commercial usage.
- **Audited Sources:** Public TSDR web searches conducted in Stage 16.
- **Audit Finding:** **SECONDARY EVIDENCE / PRELIMINARY SEARCH**. Full certified TSDR file wrappers, prosecution histories, and pending Intent-to-Use (ITU) applications (Section 1(b)) were not retrieved via an authoritative commercial clearinghouse (e.g. Thomson CompuMark / Corsearch).
- **Classification:** **`LEGAL QUESTION / REQUIRES COUNSEL SEARCH`**.

### 5.6 Indian Trade Marks Registry Records
- **Claim:** IP India registry searches in Classes 9 and 42 show high vulnerability under Section 9(1)(a) (absolute grounds) and Section 11(1) (relative grounds).
- **Audited Sources:** Public IP India web portal queries from Stage 16.
- **Audit Finding:** **SECONDARY EVIDENCE / PRELIMINARY SEARCH**. Official certified search reports were not commissioned.
- **Classification:** **`LEGAL QUESTION / REQUIRES COUNSEL SEARCH`**.

---

## 6. Summary of Evidentiary Gaps

The repository contains high-fidelity primary evidence for all **internal engineering, algorithmic performance, build, and software packaging invariants**.

Conversely, all **trademark clearance, judicial confusion risk, litigation cost estimates, and competitor corporate deal terms** are either secondary evidence, engineering estimates, or open legal questions.

These gaps are systematically cataloged in [`LEGAL_EVIDENCE_GAP_REGISTER.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/LEGAL_EVIDENCE_GAP_REGISTER.md) and referred to outside counsel in [`COUNSEL_QUESTIONNAIRE_FINAL.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/COUNSEL_QUESTIONNAIRE_FINAL.md).
