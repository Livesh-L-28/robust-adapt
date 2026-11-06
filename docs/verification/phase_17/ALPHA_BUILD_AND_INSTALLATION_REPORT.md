# ADAPTIVEML PHASE 17 — ALPHA BUILD AND INSTALLATION REPORT
## Local Artifact Verification, Clean-Environment Installation, and Package Integrity Audit

**Document Identifier:** `docs/verification/phase_17/ALPHA_BUILD_AND_INSTALLATION_REPORT.md`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Reported Version:** `0.1.0.dev0`<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Execution Scope:** Non-Public Local Packaging & Installation Verification<br>
**Status:** **`VERIFIED PASS (LOCAL BUILDS ONLY — NO PUBLIC UPLOAD)`**<br>
**Date:** 2026-11-06<br>

---

## 1. PURPOSE AND EXECUTION BOUNDARY

This report documents the local build, cryptographic validation, and clean-environment installation testing of the `aml-core` v0.1.0.dev0 distribution artifacts.

> [!IMPORTANT]
> All build and installation validations documented herein were performed strictly within **local, private test environments**. Exactly **zero distribution artifacts were uploaded to PyPI, TestPyPI, or any external repository**.

---

## 2. CRYPTOGRAPHIC ARTIFACT VERIFICATION

The local distribution artifacts in `dist/` were audited and cryptographically fingerprinted:

| Artifact Filename | Artifact Type | File Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| `aml_core-0.1.0.dev0-py3-none-any.whl` | Pure Python Wheel | 162,352 bytes | `75F20000BB3C4B1CE5D12CBD91FAF84D0A028E21256E634B9C23DFDC51C6795E` |
| `aml_core-0.1.0.dev0.tar.gz` | Source Distribution | 129,494 bytes | `427A74AA1F0352EA20B6A17C7F7B7306E59B606B812D4AE3E557B12F31DD12DC` |

### Wheel Archive Structural Audit
- **Total Files in Wheel:** 77
- **Root Directory:** Strictly `adaptive_ml/`
- **Type Information:** `py.typed` present
- **Metadata Files:** `METADATA`, `RECORD`, `WHEEL`, `licenses/LICENSE`, `licenses/NOTICE`, `top_level.txt`
- **Leakage Check:** Exactly **0 test files**, **0 benchmark scripts**, **0 raw data files**, and **0 secrets** present.

---

## 3. CLEAN-ENVIRONMENT INSTALLATION TESTING

Installation verification was conducted across isolated local test scenarios:

### Test Scenario 1: Core-Only Installation (Strictly Minimal)
- **Environment:** Clean Python virtual environment with standard library only.
- **Command:** `pip install dist/aml_core-0.1.0.dev0-py3-none-any.whl`
- **Observed Result:** Installed successfully. Single mandatory runtime dependency (`numpy >= 1.24.0`) resolved.
- **Import Verification:** `python -c "import adaptive_ml as aml; print(aml.__version__)"`
- **Output:** `0.1.0.dev0` (Exit code: 0).
- **Core Smoke Test:** Initialized ALA DriftDetector, RLA SymmetricNoiseLoss, and ULC v5 controller in RAM without error.

### Test Scenario 2: Optional Framework Extras Installation
- **Command:** `pip install "dist/aml_core-0.1.0.dev0-py3-none-any.whl[torch,sklearn,safetensors]"`
- **Observed Result:** Framework adapters resolved cleanly. PyTorch modules (`TorchAdaptiveModule`, `AdaptiveAdamW`) and scikit-learn estimators (`AdaptiveClassifierPipeline`) operational.
- **Graceful Degradation:** In environments without PyTorch, importing `adaptive_ml.integrations.torch_module` raises clean `ImportError` with actionable installation instructions.

### Test Scenario 3: Uninstallation & Clean Removal
- **Command:** `pip uninstall -y aml-core`
- **Observed Result:** All package files cleanly removed from site-packages; zero orphan artifacts.

---

## 4. AUDIT CONCLUSION

The `aml-core` v0.1.0.dev0 packaging and installation pipeline is robust, reproducible, and production-grade. External distribution remains withheld pending Stage 16.2 legal resolution.

---

## 5. STAGE 16.3 ADDITIVE RE-VERIFICATION (2026-11-06)

Stage 16.3 re-verified that artifact SHA-256 hashes (`75F20...` and `427A7...`) match the local artifacts in `dist/`, zero external uploads occurred, and local installation tests continue to pass with 0 errors.
