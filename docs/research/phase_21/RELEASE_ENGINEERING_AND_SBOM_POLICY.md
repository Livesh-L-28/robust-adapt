# PHASE 21 DELIVERABLE 05 — RELEASE ENGINEERING & SBOM POLICY
## Semantic Versioning, Software Bill of Materials (SBOM), Cryptographic Provenance, and Release Checklist

**Document Identifier:** `docs/research/phase_21/RELEASE_ENGINEERING_AND_SBOM_POLICY.md`<br>
**Phase:** 21 — Continuous R&D<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Release Engineering Architect & Supply-Chain Security Specialist<br>

---

## 1. Important Release Governance Rule

> [!WARNING]
> **PRE-RELEASE ENGINEERING SPECIFICATION ONLY:**<br>
> This document defines future release engineering policies, SBOM generation routines, and release checklists.<br>
> In accordance with Section 18 of the Master Execution Prompt:
> 1. **Original Phase 18 (Public PyPI 1.0 Publication) remains STRICTLY LOCKED.**
> 2. Zero packages shall be published or uploaded to PyPI / TestPyPI.
> 3. Zero release tags shall be pushed to remote repositories.
> 4. These procedures are prepared for execution only upon explicit, separate Project Owner authorization.

---

## 2. Semantic Versioning & Deprecation Policy

AdaptiveML adheres to **Semantic Versioning 2.0.0 (SemVer)**:
- **Major Releases (X.0.0):** Breaking architectural changes or incompatible public API modifications. Must be preceded by deprecation warnings in at least two preceding minor releases.
- **Minor Releases (0.Y.0):** New algorithmic pillars, framework adapters, or performance enhancements added in a backward-compatible manner.
- **Patch Releases (0.0.Z):** Backward-compatible defect fixes, security patches, or documentation corrections.

---

## 3. Software Bill of Materials (SBOM) Generation

To maintain supply-chain transparency, every build artifact produces a cryptographically signed Software Bill of Materials in **SPDX 2.3 JSON** format and **CycloneDX 1.5 JSON** format:

```bash
# Automated SBOM generation command
pip install cyclonedx-bom
cyclonedx-py environment --outfile sbom/adaptiveml-bom.json
```

### SBOM Manifest Contents:
- Exact package metadata (`aml-core` / approved identity).
- Pinned dependency graph with direct and transitive hashes (SHA-256).
- Standardized SPDX license identifiers for all dependencies (`Apache-2.0`, `BSD-3-Clause`, `MIT`).
- Author identity and cryptographic commit hash.

---

## 4. Cryptographic Artifact Signing & Provenance

When public release is authorized:
1. **Sigstore / Cosign Signing:** All `.whl` and `.tar.gz` artifacts are signed using OIDC keyless signing via Sigstore.
2. **SLSA Level 3 Provenance:** GitHub Actions builds generate cryptographic provenance attestations documenting the exact runner, source commit, and build environment.
3. **Reproducible Wheels:** Wheels are built with normalized timestamps (`SOURCE_DATE_EPOCH`) to guarantee byte-for-byte build reproducibility.

---

## 5. Pre-Release Engineering Gate Checklist

Before any future release artifact can be promoted to public staging:
- [ ] 100% of tests pass across Python 3.10, 3.11, 3.12, 3.13, 3.14 on Linux, Windows, macOS.
- [ ] Bandit security scan reports 0 High and 0 Medium issues.
- [ ] Pip-audit reports 0 known CVEs in the dependency closure.
- [ ] Clean environment test installs wheel into an empty virtual environment.
- [ ] Generated SBOM is validated against CycloneDX schema.
- [ ] Release notes and changelog are reviewed by the maintainer team.
- [ ] **Owner Decision Record & Release Authorization is formally executed.**
