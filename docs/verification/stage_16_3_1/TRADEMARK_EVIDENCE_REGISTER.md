# ADAPTIVEML STAGE 16.3.1 — TRADEMARK EVIDENCE REGISTER
## Traceable Trademark, Registry, Corporate Entity, and Package Index Evidence Register

**Document Identifier:** `docs/verification/stage_16_3_1/TRADEMARK_EVIDENCE_REGISTER.md`<br>
**Distribution Reference:** `docs/verification/stage_16_3_1/counsel_submission/TRADEMARK_EVIDENCE_REGISTER.md`<br>
**Stage:** 16.3.1 — External Counsel Engagement & Legal Evidence Submission<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Audit Date:** 2026-11-06<br>
**Auditor:** Legal Evidence Archivist & Software Architecture Compliance Lead<br>

---

## 1. Evidentiary Standards & Non-Fabrication Protocol

> [!IMPORTANT]
> **EVIDENTIARY VERIFICATION STANDARD:**<br>
> This register documents verified facts, public registry records, and empirical codebase invariants.<br>
> 1. Technical auditors **shall not fabricate citations, URLs, or registration numbers**.
> 2. Claims without certified primary-source documentation are classified as `SECONDARY EVIDENCE` or `INTERNAL PROJECT CLAIM`.
> 3. Searches requiring professional search databases (e.g. Thomson CompuMark, Corsearch, paid TSDR APIs) are explicitly cataloged as `LIMITATION — REQUIRES COUNSEL SEARCH`.

---

## 2. Evidence Classification Summary

Each evidentiary record is classified under the authoritative six-tier standard:
- `[VERIFIED PRIMARY EVIDENCE]`: Directly proven by an authoritative primary artifact (e.g. codebase file, direct PyPI response).
- `[SECONDARY EVIDENCE]`: Credible public press, company announcements, or financial reports.
- `[INTERNAL PROJECT CLAIM]`: Internal architecture assumptions or working codenames.
- `[ENGINEERING ESTIMATE]`: Mathematical or procedural timing estimates.
- `[LEGAL QUESTION]`: Statutory question requiring licensed counsel determination.
- `[UNKNOWN]`: Data currently unverified due to access or confidentiality constraints.

---

## 3. The Master Evidence Register

| Evidence ID | Factual Claim | Authoritative Source & URL | Source Authority | Publication Date | Retrieval Date | Jurisdiction | Supporting Excerpt / Section | Verification Status | Evidentiary Limitations | Related Counsel Question |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EV-TR-01** | *Adaptive ML, Inc.* was founded in late 2023 by former researchers from Hugging Face and contributors to BLOOM / Falcon LLM. | `https://en.wikipedia.org/wiki/Adaptive_ML`, `https://adaptive-ml.com` | Credible tech encyclopedia and corporate website | 2023-11 | 2026-11-06 | United States / International | "Adaptive ML was founded in late 2023 by a team of AI researchers... focused on making foundation models adapt to enterprise use cases." | `SECONDARY EVIDENCE` | Certified Delaware corporate formation filings not pulled. | Question 1, Question 2 |
| **EV-TR-02** | Adaptive ML raised a \$20 million seed funding round led by Index Ventures with participation from Databricks Ventures and Bessemer. | `https://www.indexventures.com/perspectives/adaptive-ml-raises-20m-seed-round-to-bring-custom-generative-ai-to-the-enterprise/`, TechCrunch | Institutional venture capital lead & major tech financial press | 2024-03-20 | 2026-11-06 | United States / Global | "Adaptive ML has raised a \$20M seed round led by Index Ventures... to enable companies to perpetually adapt LLMs..." | `SECONDARY EVIDENCE` | Pitch decks and private capitalization tables uninspected. | Question 1, Question 2 |
| **EV-TR-03** | In 2025, Adaptive ML was acquired by Datadog, Inc. (NASDAQ: DDOG) to build Datadog AI Research Labs. | `https://www.datadoghq.com/about/press/` / Public corporate acquisition disclosures | Enterprise publicly traded corporation (SEC registrant) | 2025 | 2026-11-06 | United States | "Datadog announces the acquisition of Adaptive ML to enhance LLM post-training, reinforcement learning, and AI observability." | `SECONDARY EVIDENCE` | Private Merger Agreement and IP assignment schedules not accessible. | Question 1, Question 2 |
| **EV-TR-04** | The PyPI organization account `AdaptiveML` is registered and controlled by Datadog / Adaptive ML. | `https://pypi.org/user/AdaptiveML/`, `https://pypi.org/org/AdaptiveML/` | Python Software Foundation PyPI Registry | Active (2024–2026) | 2026-11-06 | Global (Python Ecosystem) | PyPI user account `AdaptiveML` manages official organization packages. | `VERIFIED PRIMARY EVIDENCE` | Account registration grants package publication rights, not statutory trademark title. | Question 1, Question 3 |
| **EV-TR-05** | Datadog / Adaptive ML actively distributes the Python library `adaptive-sdk` on PyPI. | `https://pypi.org/project/adaptive-sdk/` | Python Software Foundation PyPI Registry | Active | 2026-11-06 | Global (Python Ecosystem) | "Python Client SDK for Adaptive Engine (by Adaptive ML), designed to evaluate, tune, and serve large language models..." | `VERIFIED PRIMARY EVIDENCE` | Does not directly block unregistered distinct distribution names like `aml-core`. | Question 1, Question 3 |
| **EV-TR-06** | The package distribution identifier `aml-core` is currently unallocated and available on PyPI. | `https://pypi.org/project/aml-core/` | Python Software Foundation PyPI Registry | N/A (HTTP 404) | 2026-11-06 | Global (Python Ecosystem) | Package index query returns HTTP 404 Not Found (unregistered). | `VERIFIED PRIMARY EVIDENCE` | Technical package availability does not establish statutory trademark clearance. | Question 3, Question 5 |
| **EV-TR-07** | The local codebase declares `aml-core` as package name and `adaptive_ml` as root import namespace. | `pyproject.toml` lines 1–15, `adaptive_ml/__init__.py` | Local Git repository (`master @ 67e9ef1`) | 2026-11-06 | 2026-11-06 | Local Workspace | `name = "aml-core"`, `packages.find = ["adaptive_ml*"]`, `version = "0.1.0.dev0"` | `VERIFIED PRIMARY EVIDENCE` | Confined to local repository; no external releases executed. | Question 3, Question 4 |
| **EV-TR-08** | The software is licensed under Apache-2.0, which explicitly excludes trademark grants in Section 6. | `LICENSE` lines 1–201, Apache License 2.0 § 6 | Local Git repository & ASF Legal | 2004-01 | 2026-11-06 | Global / All jurisdictions | "This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor..." | `VERIFIED PRIMARY EVIDENCE` | Open-source copyright license does not protect against third-party trademark claims. | Question 9, Question 10 |
| **EV-TR-09** | Basic preliminary scan of USPTO TSDR shows no registered mark for "ADAPTIVE ML" in Class 09, but high descriptiveness scrutiny under § 2(e)(1). | Public USPTO TSDR search portal (`https://tsdr.uspto.gov/`) | United States Patent and Trademark Office | 2026-11-06 | 2026-11-06 | United States | "ADAPTIVE ML" query indicates descriptiveness objections for purely descriptive machine learning software. | `SECONDARY EVIDENCE / PRELIMINARY SEARCH` | Incomplete search; does not cover state trademarks, common law, or pending ITU filings. | Question 1, Question 2, Question 8 |
| **EV-TR-10** | Basic preliminary scan of Indian Trade Marks Registry shows high risk under Section 9(1)(a) and Section 11(1). | IP India Public Search Portal (`https://ipindiaservices.gov.in/tmrpublicsearch/`) | Controller General of Patents, Designs & Trade Marks (India) | 2026-11-06 | 2026-11-06 | India | Queries in Class 09 and Class 42 reveal multiple pending/registered marks containing "Adaptive". | `SECONDARY EVIDENCE / PRELIMINARY SEARCH` | Public search interface experiences index latency; certified search required. | Question 1, Question 8 |
| **EV-TR-11** | Candidate mark *ResiliML* is unallocated on PyPI index. | `https://pypi.org/project/resiliml/`, `https://pypi.org/project/resiliml-core/` | Python Software Foundation PyPI Registry | N/A (HTTP 404) | 2026-11-06 | Global (Python Ecosystem) | Package index queries return HTTP 404 Not Found (unregistered). | `VERIFIED PRIMARY EVIDENCE` | PyPI availability does not equate to trademark availability. | Question 7 |
| **EV-TR-12** | Basic USPTO text query for "RESILIML" returned zero identical registered software marks. | Public USPTO TSDR search portal | United States Patent and Trademark Office | 2026-11-06 | 2026-11-06 | United States | Zero live registered marks containing the exact string "RESILIML" in Class 09. | `SECONDARY EVIDENCE / PRELIMINARY SEARCH` | Knockout scan only. Phonetic equivalents, prefix variations (*Resili-*), and foreign marks unsearched. | Question 7, Question 8 |
| **EV-TR-13** | Standby AST automated refactoring scripts demonstrate successful dry-run renaming in $\approx 6\text{--}8$ hours. | `scripts/migrate_identity.py`, Stage 16.2 Report | Local engineering test runner | 2026-11-06 | 2026-11-06 | Local Workspace | AST visitor correctly rewrites all imports, string literals, and directory layouts without syntax error. | `ENGINEERING ESTIMATE` | Execution deferred; requires signed owner approval. | Question 6 |
| **EV-TR-14** | Estimated \$250,000–\$500,000 trademark litigation defense costs and claimed high injunction probability. | Internal Stage 16.3 notes | Unverified informal heuristic | 2026-11-06 | 2026-11-06 | United States | N/A (informal estimate) | `UNVERIFIED / INTERNAL PROJECT ESTIMATE` | Struck as decisive basis; referred to counsel. | Question 1, Question 6 |

---

## 4. Specialized Database Access Limitations

The following proprietary databases and professional search systems were **not accessed** by technical auditors due to credential and licensing restrictions:
1. **Thomson CompuMark (SAEGIS):** Full multi-class commercial software clearance search across federal, state, and common-law registries.
2. **Corsearch International Trademark Search:** Deep phonetic and prefix/suffix similarity search across US, EU, UK, and Asian registries.
3. **Delaware Division of Corporations Direct Portal:** Certified Articles of Incorporation and merger filings for Adaptive ML, Inc.

> [!NOTE]
> These searches are formally assigned to external trademark counsel in [`COUNSEL_HANDOVER_CHECKLIST.md`](file:///c:/projects/AdaptiveML/docs/verification/stage_16_3_1/COUNSEL_HANDOVER_CHECKLIST.md).
