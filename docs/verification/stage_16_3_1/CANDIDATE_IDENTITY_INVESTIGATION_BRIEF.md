# ADAPTIVEML STAGE 16.3.1 — CANDIDATE IDENTITY INVESTIGATION BRIEF
## Comparative Naming Evaluation, Preliminary Registry Data, and Trademark Clearance Protocol

**Document Identifier:** `docs/verification/stage_16_3_1/CANDIDATE_IDENTITY_INVESTIGATION_BRIEF.md`<br>
**Distribution Reference:** `docs/verification/stage_16_3_1/counsel_submission/CANDIDATE_IDENTITY_INVESTIGATION_BRIEF.md`<br>
**Stage:** 16.3.1 — External Counsel Engagement & Legal Evidence Submission<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Investigation Date:** 2026-11-06<br>
**Auditor:** Software Architecture Team & Legal Compliance Reviewer<br>
**Purpose:** Technical brief submitted to outside counsel to guide professional trademark searches.<br>

---

## 1. Important Legal Notice & Scope of Investigation

> [!WARNING]
> **PRELIMINARY TECHNICAL SCREENING ONLY (NOT LEGAL CLEARANCE):**<br>
> This brief compiles candidate naming identities proposed by software engineers and technical contributors.<br>
>
> Technical auditors **shall not label any candidate as "AVAILABLE" or "LEGALLY CLEARED"** based merely on domain name availability, package index (PyPI) lookups, or preliminary web search engine queries.<br>
>
> Trademark availability depends on multi-jurisdictional, multi-class statutory clearance (USPTO, IP India, EUIPO, UKIPO) and comprehensive common-law searches for confusingly similar marks. This brief is provided exclusively to define search parameters for qualified external trademark counsel.

---

## 2. Five-Surface Architectural Alignment Model

To prevent the *Asymmetric Resolution Trap* (where changing one identifier leaves other conflicting surfaces exposed), every candidate is evaluated across all five naming tiers:

```
+---------------------------------------------------------------------------------------------------------+
|                                  FIVE-SURFACE IDENTITY EVALUATION MATRIX                                |
+------------------+-----------------------+--------------------+---------------------+-------------------+
| Candidate Name   | Surface 1: Product    | Surface 2: PyPI    | Surface 3: Import   | Surface 4: Repo   |
+------------------+-----------------------+--------------------+---------------------+-------------------+
| 1. AdaptiveML    | AdaptiveML            | aml-core           | adaptive_ml         | AdaptiveML        |
| 2. ResiliML      | ResiliML              | resiliml           | resiliml            | ResiliML          |
| 3. StreamAdapt   | StreamAdapt           | streamadapt        | streamadapt         | StreamAdapt       |
| 4. LibAdaptive   | LibAdaptive           | libadaptive        | libadaptive         | LibAdaptive       |
| 5. AML Core      | The AML Core Project  | aml-core           | aml                 | aml-core          |
+------------------+-----------------------+--------------------+---------------------+-------------------+
```

---

## 3. Detailed Investigation Profiles for Candidate Marks

### Candidate 1: `AdaptiveML` (Current Technical Baseline)
* **Proposed Product Name:** `AdaptiveML`
* **Proposed PyPI Package Identifier:** `aml-core`
* **Proposed Python Import Namespace:** `adaptive_ml`
* **Repository and Documentation Naming:** `AdaptiveML` / `docs/`
* **Conceptual & Architectural Rationale:** Reflects the core algorithmic capability: streaming adaptive machine learning under concept drift, label noise, and resource limits.
* **Known Search Results:**
  - *PyPI:* `aml-core` is unallocated. However, the organization `AdaptiveML` is claimed by Datadog, which publishes `adaptive-sdk`.
  - *USPTO TSDR:* No registered mark for exact "ADAPTIVE ML" in Class 09, but extensive commercial use and descriptiveness scrutiny under § 2(e)(1).
  - *IP India:* Multiple pending/registered marks containing "Adaptive" in Classes 9 and 42.
* **Jurisdictions Searched:** US (USPTO public TSDR), India (IP India public search), Global (PyPI).
* **Search Date:** 2026-11-06.
* **Source Links:** `https://pypi.org/user/AdaptiveML/`, `https://pypi.org/project/adaptive-sdk/`, `https://tsdr.uspto.gov/`.
* **Similar Marks & Conflicting Entities:**
  - *Adaptive ML, Inc.* (acquired by Datadog, Inc., 2025; \$20M seed round; markets "Adaptive Engine").
  - *Adaptive.js* / *Adaptive AI* (various minor open-source projects).
* **Unresolved Legal Questions:**
  - Does public release under "AdaptiveML" create an unacceptable risk of a cease-and-desist or preliminary injunction from Datadog?
  - Does using `aml-core` and `adaptive_ml` insulate the project from Lanham Act § 43(a) claims?
* **Current Legal Status:** **`NOT LEGALLY CLEARED — UNRESOLVED DEFECT DEF-004`**.

---

### Candidate 2: `ResiliML` (Engineering Recommended Architecture)
* **Proposed Product Name:** `ResiliML` (pronounced *reh-ZIL-ee-em-ell*)
* **Proposed PyPI Package Identifier:** `resiliml` (or `resiliml-core`)
* **Proposed Python Import Namespace:** `resiliml` (e.g. `import resiliml as rml`)
* **Repository and Documentation Naming:** `ResiliML` / `docs/`
* **Conceptual & Architectural Rationale:** A distinctive portmanteau uniting *Resilience* (robustness to noise, drift, memory pressure) with *Machine Learning* (*ML*). Accurately describes the library's technical mission without utilizing the conflicting "Adaptive" mark.
* **Known Search Results:**
  - *PyPI Index:* `resiliml` and `resiliml-core` are unallocated (HTTP 404).
  - *USPTO TSDR Preliminary Scan:* Zero exact matches for "RESILIML" in Class 09 (software) or Class 42 (technology services).
  - *GitHub / Source Repositories:* No active major projects utilizing `resiliml` as an established brand.
* **Jurisdictions Searched:** US (USPTO preliminary web query), Global (PyPI web query).
* **Search Date:** 2026-11-06.
* **Source Links:** `https://pypi.org/project/resiliml/` (404), `https://tsdr.uspto.gov/`.
* **Similar Marks & Phonetic Collisions Requiring Counsel Search:**
  - Marks with prefix *Resili-* in software: e.g., *Resiligo*, *Resilient Systems* (IBM cybersecurity), *Resilio* (peer-to-peer file sync).
  - Marks with suffix *-ML*: e.g., *ResilientML* (academic workshops or unfiled marks).
* **Unresolved Legal Questions:**
  - Does "ResiliML" possess sufficient inherent distinctiveness on the *Abercrombie* scale (suggestive vs. descriptive)?
  - Are there pending Intent-to-Use (ITU) applications or foreign registrations that block "ResiliML" in Class 09 or Class 42?
* **Current Legal Status:** **`UNASSESSED — PENDING INDEPENDENT TRADEMARK CLEARANCE BY OUTSIDE COUNSEL`**.

---

### Candidate 3: `StreamAdapt`
* **Proposed Product Name:** `StreamAdapt`
* **Proposed PyPI Package Identifier:** `streamadapt`
* **Proposed Python Import Namespace:** `streamadapt`
* **Repository and Documentation Naming:** `StreamAdapt`
* **Conceptual & Architectural Rationale:** Highlights streaming continual adaptation.
* **Known Search Results:**
  - *PyPI:* Unallocated.
  - *Academic / Web Presence:* Multiple academic papers, master's theses, and small GitHub repositories use "stream adapt" as a generic descriptive phrase for streaming adaptation algorithms.
* **Jurisdictions Searched:** Global web search, PyPI.
* **Search Date:** 2026-11-06.
* **Similar Marks & Collisions:**
  - *StreamLit* (Snowflake), *StreamPipes* (Apache), *DataStream*.
* **Unresolved Legal Questions:**
  - Is "StreamAdapt" merely descriptive under 15 U.S.C. § 1052(e)(1) and Indian Trade Marks Act § 9(1)(b)?
  - Does it create dilution or confusion risks with well-known streaming data marks?
* **Current Legal Status:** **`NOT LEGALLY CLEARED`**.

---

### Candidate 4: `LibAdaptive`
* **Proposed Product Name:** `LibAdaptive`
* **Proposed PyPI Package Identifier:** `libadaptive`
* **Proposed Python Import Namespace:** `libadaptive`
* **Repository and Documentation Naming:** `LibAdaptive`
* **Conceptual & Architectural Rationale:** Classical C/UNIX style naming convention (`lib*`).
* **Known Search Results:**
  - Retains the core word "Adaptive". Proximity to Datadog's *Adaptive ML* remains elevated.
* **Jurisdictions Searched:** Global web search.
* **Search Date:** 2026-11-06.
* **Similar Marks & Collisions:** High proximity to *Adaptive ML*, *Adaptive Insights* (Workday), *Adaptive Computing*.
* **Unresolved Legal Questions:**
  - Does adding the prefix "Lib-" sufficiently distinguish the software from *Adaptive ML, Inc.*? (Likely insufficient under anti-dissection and dominant-feature doctrines).
* **Current Legal Status:** **`NOT LEGALLY CLEARED / HIGH CONFUSION RISK`**.

---

### Candidate 5: `The AML Core Project` / `aml-core`
* **Proposed Product Name:** `The AML Core Project` (dropping "AdaptiveML" entirely)
* **Proposed PyPI Package Identifier:** `aml-core`
* **Proposed Python Import Namespace:** `aml`
* **Repository and Documentation Naming:** `aml-core`
* **Conceptual & Architectural Rationale:** Avoids full words; relies strictly on the acronym AML.
* **Known Search Results:**
  - *PyPI:* `aml-core` is available.
  - *Commercial Collisions:* High collision with Microsoft Azure Machine Learning (`azureml-core`, `azure-ai-ml`) and widespread financial industry software for Anti-Money Laundering (AML).
* **Jurisdictions Searched:** Global web / PyPI.
* **Search Date:** 2026-11-06.
* **Similar Marks & Collisions:** *Azure ML* (Microsoft), *Amazon Machine Learning* (AWS), AML compliance vendors.
* **Unresolved Legal Questions:**
  - Does `aml-core` create confusion with Microsoft's Azure ML software distribution?
* **Current Legal Status:** **`NOT LEGALLY CLEARED / HIGH DILUTION & AMBIGUITY RISK`**.

---

## 4. Counsel Action Request

Outside counsel is requested to:
1. Conduct formal clearance searches (USPTO, IP India, EUIPO) on **Candidate 2 (`ResiliML`)** across Class 09 and Class 42.
2. Evaluate whether any candidate proposed by counsel provides superior distinctiveness and defensibility.
3. Deliver written clearance advice prior to owner execution of the final Owner Decision Record.
