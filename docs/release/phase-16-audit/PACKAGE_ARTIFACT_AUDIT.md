# Package Artifact Audit Report

**Document ID:** `DOC-REL-P16-006`  
**Phase:** Phase 16 — Legal & Release Audit  
**Status:** READY FOR REVIEW  

---

## 1. Distribution Artifact Inspection

Built package files in `dist/` were decompressed and audited:

### 1.1 Wheel Archive: `aml_core-0.1.0.dev0-py3-none-any.whl`
- **Total Files:** 35 files
- **File Structure:** Contains exclusively `adaptive_ml/` packages, submodules, `py.typed`, and standard `aml_core-0.1.0.dev0.dist-info/` metadata.
- **Excluded Directories:**
  - `tests/` successfully excluded from wheel.
  - `benchmarks/` successfully excluded from wheel.
  - `docs/` successfully excluded from wheel.
  - `.github/` successfully excluded from wheel.
  - Build caches (`__pycache__`, `.pytest_cache`) successfully excluded.

### 1.2 Source Distribution: `aml_core-0.1.0.dev0.tar.gz`
- Contains clean source files, `pyproject.toml`, `README.md`, and module trees.
- Validated tarball unpacks cleanly on POSIX and Windows file systems.
