# AdaptiveML — Phase 3: Copyright and Contributor Policy

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-006`  
> **Last Updated**: 2026-11-01  
> **Governance Model**: Developer Certificate of Origin (DCO 1.1) + Apache-2.0 Licensing

---

## 1. Contributor Provenance Framework

To guarantee that all code, documentation, and mathematical specifications introduced into AdaptiveML have verifiable legal provenance and zero copyright contamination:

### 1.1 Developer Certificate of Origin (DCO 1.1)
AdaptiveML adopts the Linux Foundation standard **Developer Certificate of Origin (DCO Version 1.1)**. Every commit to the repository must include a cryptographically or textually verified sign-off in the git commit message:

```text
Signed-off-by: Full Legal Name <developer@domain.com>
```

By adding this line, the contributor certifies that:
1. The contribution was created in whole or in part by the contributor, who has the right to submit it under the Apache License 2.0; OR
2. The contribution is based upon previous work that is covered by an appropriate permissive open-source license; OR
3. The contribution was provided directly to the submitter by a person who certified items (1) or (2).

### 1.2 Rejection of Heavy Corporate CLAs
- Many corporate projects impose complex, multi-page Contributor License Agreements (CLAs) requiring legal department approval before a developer can contribute a bug fix.
- **Decision**: AdaptiveML rejects heavy CLAs. The combination of **Apache-2.0 (with its explicit patent grant) and DCO 1.1** provides full legal protection while eliminating friction for open-source and academic contributors.

---

## 2. Clean-Room Implementation Standards

To eliminate risk of copyright infringement or trade secret misappropriation:
1. **Academic Re-Implementation Only**:
   - Algorithms must be written from scratch using published mathematical equations, pseudo-code, and technical specifications.
   - Copy-pasting code from existing GitHub repositories (especially AGPL Cleanlab, GPL packages, or proprietary internal corporate code) is **strictly prohibited**.
2. **AI-Assisted Code Generation Policy**:
   - Code generated with AI coding assistants must be reviewed, understood, tested, and certified by a human contributor under the DCO. AI cannot be listed as an author or copyright holder.
3. **Attribution in NOTICE File**:
   - The root repository will maintain an official `NOTICE` file in accordance with Section 4(d) of Apache-2.0, crediting foundational research sources and required copyright notices.
