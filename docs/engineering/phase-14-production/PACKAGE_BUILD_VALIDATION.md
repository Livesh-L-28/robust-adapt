# Package Build Validation Report

**Document ID:** `DOC-ENG-P14-002`  
**Phase:** Phase 14 — Production Engineering  
**Status:** READY FOR REVIEW  

---

## 1. Artifact Verification

Distribution artifacts were built directly from the clean workspace:

```
dist/
├── aml_core-0.1.0.dev0-py3-none-any.whl (61,291 bytes)
└── aml_core-0.1.0.dev0.tar.gz          (48,510 bytes)
```

### 1.1 Wheel Inspection
- **Package Name:** `aml-core` (provisional namespace; avoids PyPI conflicts pending clearance)
- **Version:** `0.1.0.dev0`
- **Wheel Tag:** `py3-none-any` (pure Python, OS independent)
- **PEP 561 Type Data:** Verified inclusion of `adaptive_ml/py.typed`
- **Included Packages:**
  - `adaptive_ml/`
  - `adaptive_ml/ala/`
  - `adaptive_ml/rla/`
  - `adaptive_ml/rao/`
  - `adaptive_ml/ulc/`
  - `adaptive_ml/backends/`
  - `adaptive_ml/integrations/`
  - `adaptive_ml/state/`
  - `adaptive_ml/core/`

### 1.2 Isolated Environment Installation Test
- Wheel installed via `pip install dist/aml_core-0.1.0.dev0-py3-none-any.whl` without internet connectivity.
- Import test: `import adaptive_ml; print(adaptive_ml.__version__)` executed with exit code 0.
- Mandatory runtime dependencies verified: strictly standard library + `numpy >= 1.24.0`.
