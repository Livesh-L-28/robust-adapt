# AdaptiveML — Phase 3: Open-Source License Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-003`  
> **Last Updated**: 2026-11-01  
> **Proposed Project License**: Apache License, Version 2.0 (Apache-2.0)

---

## 1. Comparative Analysis of Open-Source Licenses

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            OPEN-SOURCE LICENSE COMPARISON SPECTRUM                                            |
+---------------------+-------------------+-------------------+-------------------+---------------------+-----------------------+
| License             | Commercial Use    | Copyleft (Viral)  | Patent Grant      | Patent Retaliation  | Ecosystem Fit         |
+---------------------+-------------------+-------------------+-------------------+---------------------+-----------------------+
| **Apache-2.0**      | Permitted         | **None**          | **Explicit (§3)** | **Yes (§3)**        | **Optimal (Selected)**|
| **MIT**             | Permitted         | None              | Implied / Silent  | No                  | High (Minimalist)     |
| **BSD 3-Clause**    | Permitted         | None              | Implied / Silent  | No                  | High (NumPy standard) |
| **MPL-2.0**         | Permitted         | Weak (File-level) | Explicit          | Yes                 | Moderate              |
| **LGPL-3.0**        | Permitted         | Moderate (Dynamic)| Explicit          | Yes                 | Poor (Binding risks)  |
| **GPL-3.0**         | Permitted         | **Strong**        | Explicit          | Yes                 | **Incompatible**      |
| **AGPL-3.0**        | Restricted (SaaS) | **Network Viral** | Explicit          | Yes                 | **Strictly Prohibited**|
+---------------------+-------------------+-------------------+-------------------+---------------------+-----------------------+
```

---

## 2. In-Depth Strategic Rationale for Apache License 2.0

### 2.1 The Value of the Explicit Patent Grant (Section 3)
In modern machine learning, algorithmic patents (especially concerning optimization heuristics, quantization methods, and streaming data structures) represent a continuous risk for open-source users.
- Under **MIT** or **BSD**, patent licenses are not explicitly defined, leaving downstream enterprise adopters vulnerable to patent infringement claims by corporate contributors.
- Under **Apache-2.0 Section 3**, each contributor grants a perpetual, worldwide, non-exclusive, royalty-free patent license to make, have made, use, sell, and offer for sale the contribution.

### 2.2 The Patent Retaliation Clause
Apache-2.0 Section 3 contains an automatic defensive termination provision:
> *"If You institute patent litigation against any entity... alleging that the Work or a contribution incorporated within the Work constitutes direct or contributory patent infringement, then any patent licenses granted to You under this License for that Work shall terminate as of the date such litigation is filed."*
This clause strongly deters patent assertion entities and aggressive corporations from using patents against the AdaptiveML community.

### 2.3 Trademark Reservation (Section 6)
Unlike public-domain dedications, Apache-2.0 explicitly clarifies that the license does **not** grant rights to use the trademarks, trade names, or service marks of the licensor.

---

## 3. The AGPL-3.0 Threat & Copyleft Quarantine

### 3.1 The Cleanlab Precedent
- The core open-source repository of **Cleanlab is licensed under GNU Affero General Public License v3.0 (AGPL-3.0)**.
- AGPL-3.0 triggers strong copyleft obligations whenever software is modified or executed over a network (e.g. cloud SaaS endpoints). If AGPL code is incorporated into an Apache-2.0 library:
  1. The resulting derivative work must be licensed under AGPL-3.0.
  2. Any enterprise running a cloud service utilizing the library would be forced to open-source their entire proprietary backend infrastructure.
- **Strict Compliance Directive**:
  - **Zero copying, vendoring, or direct dynamic linking of Cleanlab source code.**
  - All robust loss functions and sample scoring algorithms in AdaptiveML RLA must be clean-room implementations constructed strictly from academic publications (Zhang & Sabuncu 2018, Wang et al. 2019, Cui et al. 2019).
