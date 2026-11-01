# Software Bill of Materials (SBOM) & Dependency Audit

**Document ID:** `DOC-REL-P16-003`  
**Phase:** Phase 16 — Legal & Release Audit  
**Status:** READY FOR REVIEW  

---

## 1. Software Bill of Materials (CycloneDX / SPDX Specification)

### 1.1 Package Identity
- **Package Name:** `aml-core`
- **Version:** `0.1.0.dev0`
- **Supplier:** AdaptiveML Core Development Team (`maintainers@adaptiveml.internal`)
- **SPDX Identifier:** `SPDXRef-Package-aml-core`

### 1.2 Direct Dependencies Inventory

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "version": 1,
  "metadata": {
    "component": {
      "name": "aml-core",
      "version": "0.1.0.dev0",
      "type": "library",
      "licenses": [{"license": {"id": "Apache-2.0"}}]
    }
  },
  "components": [
    {
      "name": "numpy",
      "version": ">=1.24.0",
      "scope": "required",
      "licenses": [{"license": {"id": "BSD-3-Clause"}}]
    },
    {
      "name": "torch",
      "version": ">=2.0.0",
      "scope": "optional",
      "licenses": [{"license": {"id": "BSD-3-Clause"}}]
    },
    {
      "name": "scikit-learn",
      "version": ">=1.2.0",
      "scope": "optional",
      "licenses": [{"license": {"id": "BSD-3-Clause"}}]
    },
    {
      "name": "safetensors",
      "version": ">=0.4.0",
      "scope": "optional",
      "licenses": [{"license": {"id": "Apache-2.0"}}]
    },
    {
      "name": "psutil",
      "version": ">=5.9.0",
      "scope": "optional",
      "licenses": [{"license": {"id": "BSD-3-Clause"}}]
    }
  ]
}
```
Zero known vulnerabilities (CVEs) found across direct dependencies.
