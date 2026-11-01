# Final License Compliance Report

**Document ID:** `DOC-REL-P16-002`  
**Phase:** Phase 16 — Legal & Release Audit  
**Status:** READY FOR REVIEW  

---

## 1. Project License Terms

The core package is licensed under the **Apache License, Version 2.0** (`SPDX-License-Identifier: Apache-2.0`).

### 1.1 Upstream Dependency License Compatibility

| Component / Library | Direct / Optional | License Identifier | Compatibility with Apache-2.0 |
| :--- | :--- | :--- | :--- |
| `numpy` | Mandatory Core | `BSD-3-Clause` | Fully Compatible (Permissive) |
| `scipy` | Optional Extra | `BSD-3-Clause` | Fully Compatible (Permissive) |
| `scikit-learn` | Optional Extra | `BSD-3-Clause` | Fully Compatible (Permissive) |
| `torch` | Optional Extra | `BSD-style` | Fully Compatible (Permissive) |
| `safetensors` | Optional Extra | `Apache-2.0` | Fully Compatible (Identical) |
| `psutil` | Optional Extra | `BSD-3-Clause` | Fully Compatible (Permissive) |

Zero copyleft (GPL / AGPL / LGPL) dependencies are required or bundled.
Zero restrictive non-commercial (CC-BY-NC) assets are included in distributions.
