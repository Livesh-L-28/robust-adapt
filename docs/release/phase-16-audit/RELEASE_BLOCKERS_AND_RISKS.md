# Release Blockers & Risk Classification

**Document ID:** `DOC-REL-P16-009`  
**Phase:** Phase 16 — Legal & Release Audit  
**Status:** READY FOR REVIEW  

---

## 1. Risk Classification Matrix

Findings from the legal, release, and security audits are classified into four severity tiers:

### 1.1 CRITICAL (Release Blocker)
- **None**: Zero technical, security, or licensing blockers prevent internal release or Alpha testing.

### 1.2 HIGH (Action Required Prior to Public PyPI Release)
- **Finding ID:** `RSK-HIGH-001`
- **Description:** Trademark Clearance for Public Name "AdaptiveML".
- **Detail:** While the source package uses `aml-core` as its package namespace, public publishing under "AdaptiveML" on PyPI and GitHub requires formal trademark clearance search across USPTO, EUIPO, and WIPO registers by a qualified intellectual property attorney.
- **Remediation:** Complete formal trademark clearance prior to Phase 18 (PyPI 1.0 Release).

### 1.3 MEDIUM (Documented & Tracked)
- **Finding ID:** `RSK-MED-001`
- **Description:** Pure Python Block Quantization CPU Latency on Very Small Models.
- **Detail:** On models with $P < 1,000$ parameters, quantization loop overhead in Python is slower than native C++ FP32 math.
- **Remediation:** Explicitly documented in `RAO_KNOWN_LIMITATIONS.md`. C++ / Cython extension will be evaluated in Phase 21.

### 1.4 LOW & INFORMATIONAL (Resolved)
- **Finding ID:** `RSK-INFO-001`: Setuptools SPDX license string updated in `pyproject.toml` (`license = "Apache-2.0"`).
