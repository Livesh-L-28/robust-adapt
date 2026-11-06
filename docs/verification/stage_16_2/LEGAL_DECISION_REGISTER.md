# ADAPTIVEML STAGE 16.2 — LEGAL DECISION REGISTER
## Multi-Pillar Legal Governance Status, Strategic Options Assessment, and Decision Registry

**Document Identifier:** `docs/verification/stage_16_2/LEGAL_DECISION_REGISTER.md`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Reported Version:** `0.1.0.dev0`<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Governing Milestone:** Stage 16.2 — Legal Decision Execution & Identity Remediation<br>
**Status:** `ACTIVE — LEGAL DETERMINATIONS PENDING OUTSIDE COUNSEL OPINION`<br>
**Date:** 2026-11-06<br>

---

## 1. PURPOSE AND GOVERNANCE PRINCIPLES

This register serves as the authoritative legal decision tracking document for Stage 16.2. It records the legal evaluation status across all intellectual property domains, documents the four strategic options available to the project, and enforces the principle that **technical teams cannot self-authorize trademark clearance or public software distribution**.

---

## 2. LEGAL DECISION TRACKING MATRIX

The following table documents the decision status across all legal, intellectual property, and governance domains:

| Decision ID | Legal / IP Domain | Governing Subject Matter | Technical Recommendation | Formal Legal Decision Status | Next Required Operational Step |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LDEC-001** | **Trademark & Brand (DEF-004)** | Conflict with Datadog / Adaptive ML, Inc. ("Adaptive Engine" / `adaptive-sdk`) | Option C (Full Clean-Break Rebrand to *ResiliML*) | **`PENDING OUTSIDE COUNSEL OPINION`** | Outside trademark counsel review of 10 statutory questions. |
| **LDEC-002** | **Distribution Identifier** | Use of `aml-core` on PyPI index | Retain `aml-core` or rebrand synchronously to `resiliml` | **`PENDING COUNSEL / OWNER DECISION`** | Dependent on LDEC-001 option selection. |
| **LDEC-003** | **Python Import Namespace** | Use of `import adaptive_ml` vs. `import resiliml` | Clean-break to `import resiliml` to avoid Asymmetric Confusion Trap | **`PENDING COUNSEL / OWNER DECISION`** | Dependent on LDEC-001 option selection. |
| **LDEC-004** | **Copyright & Provenance** | Clean-room derivation under 17 U.S.C. § 102(b) and DCO 1.1 sign-offs | Acceptable — 100% academic literature derivations, 0 vendored code | **`CONDITIONALLY CLEARED (COUNSEL SIGN-OFF PENDING)`** | Outside copyright counsel formal sign-off. |
| **LDEC-005** | **Patent & Prior-Art (FTO)** | Pure-CPU dynamic block quantization vs. GPU hardware patents | Acceptable — host CPU RAM software implementation; arXiv pre-print recommended | **`CONDITIONALLY CLEARED (COUNSEL SIGN-OFF PENDING)`** | Outside patent counsel formal review. |
| **LDEC-006** | **Open-Source Licensing** | Apache-2.0 compliance, Section 4(d) NOTICE, permissive runtime graph | Passed — 100% permissive runtime dependencies, 0 copyleft | **`INTERNALLY VERIFIED & APPROVED`** | Continuous CI verification via `pip-licenses`. |
| **LDEC-007** | **Security & Supply Chain** | Safe serialization, zero secrets, pinned dependencies, CycloneDX SBOM | Passed — 0 leaks, 0 CVEs, reproducible wheel/sdist | **`INTERNALLY VERIFIED & APPROVED`** | CI automated security scanning. |
| **LDEC-008** | **Alpha/Beta Authorization** | Permission to distribute pre-release artifacts under Phase 17 | Withhold until LDEC-001, LDEC-002, LDEC-003 resolved | **`STRICTLY LOCKED / NOT AUTHORIZED`** | Satisfaction of Stage 16.2 Acceptance Gate. |
| **LDEC-009** | **PyPI 1.0 Production Release** | Public publication under Phase 18 | Withhold until Phase 17 completed and DEF-004 closed | **`STRICTLY LOCKED / NOT AUTHORIZED`** | Full Release Board unanimous sign-off. |

---

## 3. STRATEGIC OPTIONS COMPARISON & COUNSEL DEPENDENCY

Four distinct strategic options are formally registered:

```
+-----------------------------------------------------------------------------------------+
|                               STRATEGIC OPTIONS REGISTER                                |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [OPTION A: Status Quo with Defensive Safeguards]                                       |
|  - Retain "AdaptiveML", aml-core, and adaptive_ml.                                      |
|  - Mandatory Condition: Requires formal written clearance from outside counsel         |
|    confirming that the tripartite buffer and disclaimers provide sufficient defense.    |
|  - Legal Risk: HIGH RESIDUAL RISK. Engineering Effort: 0h.                              |
|  - Decision Status: PENDING COUNSEL REVIEW.                                             |
|                                                                                         |
|  [OPTION B: Partial Rebrand / Asymmetric Shield]                                        |
|  - Rebrand public project to e.g. "ResiliML"; retain aml-core and import adaptive_ml.   |
|  - Mandatory Condition: Requires counsel advice confirming that internal import         |
|    namespaces do not trigger Lanham Act § 43(a) false designation of origin.           |
|  - Legal Risk: MODERATE-HIGH (Asymmetric Resolution Trap). Effort: 2-3h.                |
|  - Decision Status: PENDING COUNSEL REVIEW.                                             |
|                                                                                         |
|  [OPTION C: Full Clean-Break Rebrand (RECOMMENDED)]                                     |
|  - Synchronously rename Brand (ResiliML), Package (resiliml), and Namespace (resiliml). |
|  - Mandatory Condition: Requires counsel knockout search confirming target name clean. |
|  - Legal Risk: ZERO TRADEMARK RISK (Permanent resolution of DEF-004). Effort: 6-8h.     |
|  - Decision Status: PENDING OWNER SELECTION & TARGET CLEARANCE.                         |
|                                                                                         |
|  [OPTION D: Deferred Decision & Deep Discovery]                                         |
|  - Hold project freeze; commission multi-jurisdiction certified registry searches.      |
|  - Legal Risk: NEUTRAL (Freezes exposure, but delays release timeline by 6-12 weeks).   |
|  - Decision Status: ACTIVE DEFAULT PENDING COUNSEL / OWNER ACTION.                      |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 4. FORMAL DECISION CONCLUSION

No final legal decision to rebrand, retain, or publish has been rendered or approved by the Project Owner as of 2026-11-06. The project remains governed by **Option D (Default Discovery / Legal Hold)** until outside counsel delivers its opinion and the Project Owner executes a binding decision record.
