# Trademark & Intellectual Property Recheck

**Document ID:** `DOC-REL-P16-004`  
**Phase:** Phase 16 — Legal & Release Audit  
**Status:** READY FOR REVIEW  

---

## 1. Project Naming & Trademark Review

1. **Provisional Codename**:
   The working title "AdaptiveML" remains an **unregistered engineering codename**.
2. **PyPI Namespace Protection**:
   To prevent premature trademark collision or namespace squatting, the distribution package is named `aml-core` in `pyproject.toml`.
3. **Owner Action Required (Phase 16 Blocker for Public PyPI Publication)**:
   Formal trademark clearance search across USPTO (US), EUIPO (Europe), and WIPO registers must be completed by intellectual property legal counsel before registering `adaptiveml` or `adaptive-ml` as a public top-level package name.

---

## 2. Research Provenance & Clean-Room Verification

- All algorithms were authored as clean-room Python implementations based on published peer-reviewed mathematical formulations (e.g. Bifet & Gavaldà 2007 for ADWIN; Domingos & Hulten 2000 for Hoeffding Trees; Loshchilov & Hutter 2019 for AdamW; Wang et al. ICCV 2019 for SCE).
- Zero third-party source files or proprietary code bases were copied into this repository.
