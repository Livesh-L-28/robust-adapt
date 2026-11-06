# STAGE 16.1 DELIVERABLE 03
# Trademark Evidence Register & Commercial Entity Audit Dossier (DEF-004)

**Document Identifier:** `docs/verification/stage_16_1/TRADEMARK_EVIDENCE_REGISTER.md`<br>
**Stage:** 16.1 — External Legal Counsel Review & Owner Decision Preparation<br>
**Defect Reference:** `DEF-004` (Trademark Collision with *Adaptive ML, Inc.*)<br>
**Distribution Identifier:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Working Codename:** AdaptiveML<br>
**Audit Date:** 2026-11-06<br>
**Auditor:** Senior Trademark Research Analyst & Open-Source Compliance Specialist<br>
**Review Status:** `COUNSEL DETERMINATION REQUIRED`<br>

---

## 1. Executive Summary & Legal Boundary

> [!WARNING]
> **TECHNICAL & DOCUMENTARY EVIDENCE REGISTER (NON-LEGAL OPINION)**<br>
> This register compiles factual, traceable evidence from authoritative trademark registries, corporate acquisitions, package indexes, and developer platforms. It does **not** constitute a formal legal opinion, an assessment of trademark infringement, or a guarantee of freedom to operate.<br>
>
> Under international trademark law (including the Lanham Act 15 U.S.C. in the United States, the Trade Marks Act 1999 in India, and the EU Trade Mark Regulation), the likelihood of consumer confusion is a judicial determination governed by commercial channels of trade, target audience sophistication, visual/phonetic similarity, and common-law priority.<br>
>
> **Finding DEF-004 remains STRICTLY OPEN AND UNRESOLVED.** Only licensed intellectual property counsel can determine legal clearance.

---

## 2. Evidence Classification Taxonomy

Every factual statement, database query, and corporate record in this register is categorized according to the authoritative Stage 16.1 classification standard:

- `[VERIFIED TECHNICAL FACT]`: Invariant verified directly within the local codebase or compilation pipeline.
- `[EXTERNAL SOURCE EVIDENCE]`: Corroborated record retrieved from public registries, corporate filings, or package repositories.
- `[ENGINEERING ASSESSMENT]`: Technical evaluation made by software architects regarding code and systems architecture.
- `[LEGAL QUESTION]`: Invariant requiring formal legal analysis by qualified counsel.
- `[COUNSEL DETERMINATION REQUIRED]`: Action or conclusion that only licensed counsel can render.
- `[OWNER DECISION REQUIRED]`: Business or project governance choice reserved exclusively for project leadership.
- `[UNVERIFIED]`: Statement requiring further documentary confirmation.
- `[MISSING EVIDENCE]`: Data point currently absent from local records.

---

## 3. Commercial Entity Evidence: Adaptive ML, Inc. (Datadog)

### Record TE-01: Corporate Formation & Provenance
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` *Adaptive ML, Inc.* was incorporated in late 2023 by former researchers and engineers from Hugging Face and contributors to the open-source BLOOM and Falcon LLM initiatives.
- **Source URL:** `https://en.wikipedia.org/wiki/Adaptive_ML` / `https://adaptive-ml.com`
- **Publication / Filing Date:** Late 2023 (Founding announcements).
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (High confidence).
- **Limitations:** Corporate registration state (Delaware C-Corp assumed; certified corporate charter not pulled).

### Record TE-02: Institutional Financing Round
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` In early 2024, Adaptive ML, Inc. raised a \$20 million seed funding round led by Index Ventures, with participation from Databricks Ventures, Bessemer Venture Partners, and prominent AI angel investors.
- **Source URL:** TechCrunch, Index Ventures announcement (`https://indexventures.com`).
- **Publication / Record Date:** March 2024.
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Corroborated by multiple financial news sources).
- **Limitations:** Venture capital announcements establish commercial activity, but do not specify individual trademark registration numbers.

### Record TE-03: Acquisition by Datadog, Inc.
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` In 2025, Adaptive ML was acquired by Datadog, Inc. (NASDAQ: DDOG), an enterprise cloud observability and security corporation with ~$40B market cap. The team was integrated into Datadog AI Research Labs to advance RLOps, agent post-training, and foundation model adaptation.
- **Source URL:** `https://www.datadoghq.com` (Official Press Release) / SEC Form 8-K filings.
- **Publication / Record Date:** 2025.
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Verified corporate event).
- **Limitations:** Acquisition agreements and asset assignment schedules (confirming whether common-law trademark rights and goodwill were formally transferred to Datadog) are private transaction documents. `[COUNSEL DETERMINATION REQUIRED]`.

### Record TE-04: Commercial Product Offering ("Adaptive Engine")
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` The commercial entity markets "Adaptive Engine", an enterprise software platform for fine-tuning, evaluating, deploying, and serving domain-specialized large language models (LLMs) using reinforcement learning (RLHF/RLAIF).
- **Source URL:** `https://adaptive-ml.com` / `https://www.datadoghq.com`.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Verified active product).
- **Relevance:** Demonstrates active commercial presence in the enterprise machine learning and AI optimization sector.

---

## 4. Package Index Evidence: PyPI Registry

### Record PE-01: PyPI Organization Account `AdaptiveML`
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` The PyPI namespace registry maintains an active organization/user account named `AdaptiveML` controlled by Datadog / Adaptive ML.
- **Source URL:** `https://pypi.org/user/AdaptiveML/` / `https://pypi.org/org/AdaptiveML/`.
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Direct registry inspection).
- **Limitations:** Under PEP 541, PyPI account ownership grants distribution rights on PyPI, but does *not* establish statutory trademark ownership. `[LEGAL QUESTION]`.

### Record PE-02: Active Distribution `adaptive-sdk`
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` The package `adaptive-sdk` is an actively published library on PyPI described as: *"Python Client SDK for Adaptive Engine (by Adaptive ML), designed to evaluate, tune, and serve large language models (LLMs)"*.
- **Source URL:** `https://pypi.org/project/adaptive-sdk/`.
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Active package).
- **Relevance:** Confirms active distribution of Python software in the ML developer ecosystem under the "Adaptive" naming umbrella.

### Record PE-03: Status of `aml-core` on PyPI
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` The package identifier `aml-core` is currently available / uncontested as a standalone root distribution name on PyPI.
- **Source URL:** `https://pypi.org/project/aml-core/` (Returns HTTP 404 / Unregistered).
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE` (Verified registry absence).
- **Relevance:** Confirms technical availability for future reservation if approved by owners and counsel.

### Record PE-04: Ecosystem Proximity: `azureml-core`
- **Exact Claim:** `[EXTERNAL SOURCE EVIDENCE]` Microsoft Corporation distributes `azureml-core` on PyPI for Azure Machine Learning services.
- **Source URL:** `https://pypi.org/project/azureml-core/`.
- **Access Date:** 2026-11-06.
- **Evidence Classification:** `EXTERNAL SOURCE EVIDENCE`.
- **Relevance:** Demonstrates that the acronym "aml" is widely recognized in Python ML ecosystems as shorthand for "Automated Machine Learning" or "Azure Machine Learning", which could cause minor developer ambiguity. `[ENGINEERING ASSESSMENT]`.

---

## 5. Authoritative Trademark Registry Evidence

Audits were conducted across national and international trademark databases:

### Record TM-01: United States Patent and Trademark Office (USPTO)
- **Search Date:** 2026-11-06.
- **Search Terms:** `"ADAPTIVE ML"`, `"ADAPTIVE MACHINE LEARNING"`, `"ADAPTIVE ENGINE"`.
- **Target Nice Classes:**
  - **Class 09 (Computer Software):** Downloadable software; machine learning algorithms; recorded programs.
  - **Class 42 (Technology Services):** SaaS; software development; cloud AI model training.
- **Factual Observations:** `[EXTERNAL SOURCE EVIDENCE]`
  1. No live Principal Register wordmark registration was identified granting an exclusive monopoly over the bare two-word string `"ADAPTIVE ML"` for generic machine learning algorithms.
  2. Under Trademark Act Section 2(e)(1) (15 U.S.C. § 1052(e)(1)), descriptive combinations of industry terms routinely encounter descriptiveness refusals on the Principal Register absent proof of acquired distinctiveness (secondary meaning).
  3. However, commercial use in commerce by Datadog's Adaptive ML creates potential common-law trademark rights under Section 43(a) (15 U.S.C. § 1125(a)).
- **Limitations:** TSDR database public search interface; comprehensive certified title search across all stylized design marks not performed. `[COUNSEL DETERMINATION REQUIRED]`.

### Record TM-02: Indian Trade Marks Registry (IP India)
- **Search Date:** 2026-11-06.
- **Search Jurisdiction:** India (Trade Marks Act, 1999).
- **Target Nice Classes:** Class 9 (Computer software), Class 42 (Scientific & technological services).
- **Factual Observations:** `[EXTERNAL SOURCE EVIDENCE]`
  1. Section 9(1)(a) mandates refusal of marks devoid of distinctive character or indicating characteristics of goods/services.
  2. Section 11(1) prohibits registration if the mark is identical or deceptively similar to an earlier mark for similar goods and services where public confusion or association is likely.
- **Limitations:** Online public TMR search portal results are indicative; formal search report by an Indian trademark attorney is required. `[COUNSEL DETERMINATION REQUIRED]`.

### Record TM-03: WIPO Global Brand Database & EUIPO
- **Search Date:** 2026-11-06.
- **Search Jurisdiction:** International (Madrid System) & European Union (EUIPO eSearch Plus).
- **Search Terms:** `"ADAPTIVE ML"`, `"AML CORE"`.
- **Factual Observations:** `[EXTERNAL SOURCE EVIDENCE]`
  1. Multiple software marks incorporate "Adaptive" in composite marks across Nice Classes 9 and 42.
  2. International presence of Datadog in Europe (Adaptive ML had engineering offices in Paris, France) establishes territorial European common-law and trade-name presence.
- **Limitations:** International search limited to public electronic databases. Certified multi-jurisdictional clearances require local counsel. `[COUNSEL DETERMINATION REQUIRED]`.

---

## 6. Summary Traceability Matrix for Trademark Evidence

| Evidence ID | Identifier | Source System | Verifiable URL / Citation | Evidentiary Status | Key Finding |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **TE-01** | Corporate Entity | Wikipedia / Corporate Web | `https://adaptive-ml.com` | Verified | Adaptive ML, Inc. founded late 2023 by ex-Hugging Face team. |
| **TE-02** | Venture Funding | Index Ventures / TechCrunch | `https://indexventures.com` | Verified | \$20M seed round in March 2024 for LLM RLOps platform. |
| **TE-03** | Datadog Acquisition | Datadog Investor Relations | `https://datadoghq.com` | Verified | Acquired in 2025; forms Datadog AI Research Labs. |
| **TE-04** | Commercial Product | Product Documentation | `https://adaptive-ml.com` | Verified | "Adaptive Engine" enterprise fine-tuning and deployment platform. |
| **PE-01** | PyPI Organization | PyPI Registry | `https://pypi.org/user/AdaptiveML/` | Verified | Datadog / Adaptive ML owns official `AdaptiveML` PyPI account. |
| **PE-02** | PyPI Package | PyPI Registry | `https://pypi.org/project/adaptive-sdk/` | Verified | `adaptive-sdk` actively distributed as client library. |
| **PE-03** | PyPI Package | PyPI Registry | `https://pypi.org/project/aml-core/` | Verified | `aml-core` currently unregistered / available on PyPI. |
| **PE-04** | PyPI Ecosystem | PyPI Registry | `https://pypi.org/project/azureml-core/` | Verified | Microsoft uses `azureml-core`; potential acronym overlap. |
| **TM-01** | USPTO Registry | USPTO TSDR | `https://tsdr.uspto.gov/` | Indicative | Descriptive term scrutiny; Section 43(a) common-law exposure. |
| **TM-02** | IP India Registry | IP India TMR Portal | `https://ipindia.gov.in/` | Indicative | Section 9(1)(a) distinctiveness and Section 11(1) similarity rules. |
| **TM-03** | WIPO / EUIPO | WIPO Global Brand DB | `https://branddb.wipo.int/` | Indicative | European trade-name presence in France (ex-Hugging Face team). |

---

## 7. Evidence Gaps & Explicit Unknowns

The following questions cannot be answered from public registry searches alone:

1. `[MISSING EVIDENCE]` **Private Settlement / Coexistence Agreements:** Public records do not show whether Datadog has executed trademark coexistence agreements with other entities utilizing "Adaptive".
2. `[MISSING EVIDENCE]` **Unpublished Pending Applications:** Trademark applications filed within the preceding six months in certain foreign jurisdictions under the Paris Convention priority system may not yet appear on international public databases.
3. `[MISSING EVIDENCE]` **Acquisition Trademark Assignment Schedules:** The precise scope of intellectual property assets transferred from Adaptive ML, Inc. to Datadog has not been publicly filed in complete schedule form.

---

## 8. Official Recommendation for Counsel Review

This register confirms that the commercial naming conflict under **DEF-004 is substantive, documented, and actively present in the Python ML trade channels**.

All evidence gathered herein shall be submitted without modification to qualified trademark counsel alongside [`TRADEMARK_COUNSEL_QUESTIONS.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_1/TRADEMARK_COUNSEL_QUESTIONS.md).
