# AdaptiveML: Licensing and Intellectual Property Policy

> **Document Status**: Approved Baseline (Phase 0 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-FDN-006`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Core contributors, corporate counsel, open-source compliance officers, scientific partners

---

## 1. Executive Summary & Legal Disclaimers

> [!WARNING]
> **PRELIMINARY LEGAL ASSESSMENT DISCLAIMER**  
> All intellectual property, copyright, patent, and trademark analyses in this document represent internal technical evaluations conducted by engineering leadership. They do **not** constitute formal legal advice. Formal legal audits and clearance opinions must be executed by qualified intellectual property legal counsel during **Phase 3 (Legal & IP Assessment)** and **Phase 16 (Legal & Release Audit)**.

---

## 2. Primary Project License: Apache License 2.0

### 2.1 License Selection Justification
AdaptiveML proposes adoption of the **Apache License, Version 2.0 (Apache-2.0)** as its primary open-source license.

**Strategic Justification**:
1. **Permissive Commercial & Academic Use**: Permits both commercial enterprises and academic institutions to freely use, modify, redistribute, and integrate the library into proprietary systems without forced copyleft licensing.
2. **Explicit Patent Grant (Section 3)**: Provides users and downstream adopters with an explicit, perpetual, worldwide, non-exclusive patent grant covering patent claims licensable by contributors that are necessarily infringed by their contributions.
3. **Patent Retaliation Clause**: Automatically terminates patent licenses granted under Apache-2.0 to any party that initiates patent litigation against a contributor alleging patent infringement by the software, protecting the open-source community from patent aggression.
4. **Trademark Protection (Section 6)**: Apache-2.0 explicitly does not grant trademark rights to use the trade names, trademarks, service marks, or product names of the licensor, protecting project identity.

---

## 3. Contributor Provenance & Developer Certificate of Origin (DCO)

To guarantee that all code introduced into the repository has clear legal provenance and does not infringe upon third-party intellectual property or proprietary trade secrets:

### 3.1 Developer Certificate of Origin (DCO 1.1)
AdaptiveML adopts the standard Linux Foundation Developer Certificate of Origin (DCO), Version 1.1. Every commit submitted to the project repository must include a cryptographic or git sign-off (`Signed-off-by: Full Name <email@domain.com>`) certifying that:
- The contribution was created in whole or part by the author, who has the right to submit it under Apache-2.0; OR
- The contribution is based on previous work covered under an appropriate open-source license, and the submitter has the right to submit it; OR
- The contribution was provided directly to the author by a person who certified DCO compliance.

### 3.2 Clean-Room Implementation Rules
To prevent contamination from proprietary source code (e.g., code from previous employers, proprietary corporate libraries, or code under restrictive NDAs):
- All algorithmic implementations in AdaptiveML must be **clean-room implementations** developed strictly from published mathematical papers, open documentation, or original conceptualization.
- Decompiling, reverse-engineering, or copy-pasting proprietary source code into AdaptiveML is strictly prohibited.
- Authors must document the mathematical equations and academic papers used to construct the algorithm in the PR description.

---

## 4. Third-Party Dependency & Licensing Hygiene

AdaptiveML strictly monitors and categorizes all dependencies into acceptable and prohibited licensing categories:

```
+-------------------------------------------------------------------------------+
|                     DEPENDENCY LICENSE COMPATIBILITY MATRIX                   |
+------------------------------------+------------------------------------------+
| ACCEPTABLE (Permissive)            | PROHIBITED FOR RUNTIME (Copyleft/Viral)  |
+------------------------------------+------------------------------------------+
| - Apache-2.0                       | - GPL v2 / GPL v3                        |
| - MIT / Expat                      | - AGPL v3 (Strictly prohibited)          |
| - BSD 2-Clause / BSD 3-Clause      | - LGPL (Prohibited for direct vendoring) |
| - ISC License                      | - CC-BY-NC (Non-Commercial restrictions) |
| - Python Software Foundation (PSF) | - Proprietary / Commercial SDKs          |
+------------------------------------+------------------------------------------+
```

### 4.1 Dependency Audit Automation
- In Phase 14 and Phase 16, automated license scanning (`pip-licenses` or `license-check`) must be integrated into CI to block pull requests introducing dependencies with non-compliant licenses.
- Mandatory runtime dependencies must have zero copyleft obligations.

---

## 5. Provisional Naming, Trademark, and Namespace Clearance

### 5.1 Provisional Codename Status
- The name **"AdaptiveML"** is currently a **working engineering codename**.
- It has **not** been officially cleared through formal trademark searches or registered with intellectual property authorities (USPTO, EUIPO, WIPO).

### 5.2 Mandatory Clearance Safeguards
Prior to publishing official package distributions on the Python Package Index (PyPI), releasing binary wheels, or launching public domain websites:
1. **Namespace Verification**:
   - Verify ownership, reservations, and potential namespace conflicts on PyPI, Conda-Forge, GitHub, and major social/developer platforms.
   - If `adaptiveml` or confusingly similar package names are already registered or contested, evaluate alternative namespace candidates (e.g., `pyadaptiveml`, `aml-core`, `adaptml`).
2. **Trademark Search (Phase 3 & Phase 16)**:
   - Perform comprehensive searches across Nice Class 09 (software/downloadable code) and Class 42 (scientific & technology services) for conflicting marks containing "Adaptive", "Adaptive ML", or phonetic equivalents.
3. **Zero Publication Rule**:
   - **No packages shall be registered or published to PyPI under the name "AdaptiveML" until formal Phase 3 and Phase 16 clearance gates are approved and signed off.**

---

## 6. Unresolved Legal Questions & Risk Log

The following legal matters are unresolved and scheduled for formal analysis in Phase 3:

| Question ID | Legal Matter Description | Assigned Phase | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **LEGAL-Q-01** | Prior existence of commercial entities or startups operating under similar names (e.g., Adaptive ML SAS / adaptive.ml). | Phase 3 | Conduct trademark risk analysis. Select fallback namespaces (`libadaptive`, `aml-core`) if brand conflict arises. |
| **LEGAL-Q-02** | Patent landscape on low-memory optimizer states (e.g., factored or quantized momentum). | Phase 3 | Review prior patents in optimization algorithms; verify public domain status of baseline formulations. |
| **LEGAL-Q-03** | Contributor employer IP assignment policies for open-source research contributions. | Phase 3 & 16 | Enforce DCO sign-offs; provide corporate CLA templates for institutional contributors if required. |
