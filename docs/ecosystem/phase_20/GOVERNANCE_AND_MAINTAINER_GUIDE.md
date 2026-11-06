# PHASE 20 DELIVERABLE 02 — GOVERNANCE AND MAINTAINER GUIDE
## Project Roles, Code of Conduct Enforcement, Security Vulnerability Disclosure, and Release Cadence

**Document Identifier:** `docs/ecosystem/phase_20/GOVERNANCE_AND_MAINTAINER_GUIDE.md`<br>
**Phase:** 20 — Ecosystem Growth<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Open-Source Governance Officer & Release Operations Lead<br>

---

## 1. Project Governance Model

AdaptiveML follows an open-source benevolent maintainer and technical steering committee (TSC) governance model under the Apache Software License 2.0.

### 1.1 Organizational Roles
- **Project Owner:** Retains ultimate legal authority, trademark stewardship, release authorization, and strategic brand decisions.
- **Maintainers:** Core technical contributors with repository write access, responsible for PR reviews, issue triage, CI/CD pipeline health, and code reviews.
- **Contributors:** Community developers who submit bug reports, documentation enhancements, feature pull requests, and benchmarks.
- **Security Team:** Dedicated subgroup responsible for triaging incoming CVEs, reviewing cryptographic routines, and coordinating private vulnerability fixes.

---

## 2. Code of Conduct Enforcement

The project has adopted the Contributor Covenant (Version 2.1) in [`CODE_OF_CONDUCT.md`](file:///c:/projects/AdaptiveML/CODE_OF_CONDUCT.md).

### Enforcement Ladder:
1. **Correction:** Private, written warning clarifying community norms.
2. **Warning:** Formal warning with consequences for continued unacceptable behavior.
3. **Temporary Suspension:** Temporary ban from community spaces and review queues.
4. **Permanent Expulsion:** Permanent ban from the organization and all project repositories.

---

## 3. Coordinated Vulnerability Disclosure Process

Security vulnerabilities must **not** be reported through public GitHub issues.

### Security Response Protocol:
1. **Intake:** Vulnerability reports are emailed securely to `security@adaptiveml.org` (or designated security inbox).
2. **Acknowledgment:** Security maintainers acknowledge receipt within **24 hours**.
3. **Assessment & Triage:** Severity is scored using CVSS v3.1 within **72 hours**.
4. **Private Remediation:** A private security patch branch is developed and tested.
5. **Release & Advisory:** A patch release is tagged and a GitHub Security Advisory (GHSA) is published with credit to the finder.

---

## 4. Maintainer Review & Release Engineering Cadence

* **Issue Triage SLA:** Initial response to bug reports and discussions within **48 business hours**.
* **Pull Request Review SLA:** Maintainer code review within **5 business days**.
* **Release Scheduling:**
  - *Patch Releases (0.1.x):* Bi-weekly or immediate for critical security/defect fixes.
  - *Minor Releases (0.x.0):* Quarterly, introducing backward-compatible algorithmic and adapter enhancements.
  - *Major Releases (x.0.0):* Annual or breaking architectural transitions, requiring formal deprecation warnings.
