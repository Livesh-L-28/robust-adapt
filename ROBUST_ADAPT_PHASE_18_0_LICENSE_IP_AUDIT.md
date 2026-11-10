# ROBUST-ADAPT — Phase 18.0: Licensing & Intellectual Property Audit Report

**Repository:** `C:\projects\AdaptiveML`<br>
**Branch:** `master`<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4`<br>
**Distribution Package:** `robust-adapt`<br>
**Canonical Python Import:** `robust_adapt`<br>
**Phase:** 18.0 — Licensing and Intellectual Property Audit (Gate 18.0.4)<br>
**Status:** AUDITED — TECHNICAL LICENSES CLEAR; TRADEMARK CLEARANCE OPEN (DEF-004)

---

## 1. Executive Summary & Legal Distinction

This audit evaluates the copyright, licensing, third-party dependency compatibility, academic attribution, and trademark standing of the ROBUST-ADAPT codebase.

### Critical Legal Distinction:
A clean copyright and open-source dependency license audit **must never be conflated with trademark clearance**. 
- **Copyright & Open Source Licensing:** The source code is original work of authorship licensed under Apache-2.0. All third-party dependencies carry compatible permissive licenses.
- **Trademark Standing (`DEF-004`):** The commercial name "Adaptive ML" / "AdaptiveML" is actively utilized by an external corporate entity. While the codebase has consolidated under the canonical mark **ROBUST-ADAPT**, formal written clearance from intellectual property counsel has **NOT BEEN OBTAINED**. Consequently, public package publication and brand registration remain legally blocked.

---

## 2. Core Project Licensing & Copyright Audit

### 2.1 Software License
- **License Type:** Apache License, Version 2.0 (`LICENSE` file in repository root).
- **Grant of Copyright License:** Section 2 grants perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare derivative works, publicly display, and distribute the work.
- **Grant of Patent License:** Section 3 provides an express grant of patent rights from contributors.
- **Trademark Reservation:** Section 6 expressly reserves trademark rights:
  > *"This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work."*

### 2.2 Package Metadata Conformance
- `pyproject.toml` declares:
  ```toml
  license = "Apache-2.0"
  authors = [{ name = "ROBUST-ADAPT Core Development Team" }]
  ```
- Built distribution artifacts (`.whl` and `.tar.gz`) bundle `licenses/LICENSE` and `licenses/NOTICE` in `.dist-info`.

### 2.3 Vendored Code Audit
- **Status:** **Zero vendored third-party code**.
- All modules in `robust_adapt/` (ALA, RLA, RAO, ULC, Minority, Core, Backends, Integrations, State) are original implementations authored by the development team. No third-party modules or external source files are copied or vendored into the package tree.

---

## 3. Dependency License Compatibility Inventory

Every direct and optional dependency was audited for compatibility with the Apache-2.0 license:

| Dependency | Scope | Version Constraint | License | Compatible with Apache-2.0? |
|:---|:---:|:---:|:---:|:---:|
| **numpy** | Mandatory Core | `>=1.24.0` | BSD-3-Clause | **YES** |
| **torch** | Optional Extra (`[torch]`) | `>=2.0.0` | Modified BSD | **YES** |
| **scikit-learn** | Optional Extra (`[sklearn]`) | `>=1.2.0` | BSD-3-Clause | **YES** |
| **scipy** | Optional Extra (`[sklearn]`) | `>=1.10.0` | BSD-3-Clause | **YES** |
| **safetensors** | Optional Extra (`[safetensors]`) | `>=0.4.0` | Apache-2.0 | **YES** |
| **pandas** | Optional Extra (`[dataframe]`) | `>=1.5.0` | BSD-3-Clause | **YES** |
| **polars** | Optional Extra (`[dataframe]`) | `>=0.18.0` | MIT | **YES** |
| **psutil** | Optional Extra (`[benchmarks]`) | `>=5.9.0` | BSD-3-Clause | **YES** |
| **pytest** | Development (`[dev]`) | `>=7.4.0` | MIT | **YES** |
| **mypy** | Development (`[dev]`) | `>=1.5.0` | MIT | **YES** |
| **ruff** | Development (`[dev]`) | `>=0.1.0` | MIT / Apache-2.0 | **YES** |

**Conclusion:** All runtime and optional dependencies utilize highly permissive open-source licenses (BSD, MIT, Apache-2.0). There are zero GPL/AGPL copyleft contaminations.

---

## 4. Academic & Research Paper Attribution

ROBUST-ADAPT builds upon foundational machine-learning literature. In accordance with academic integrity and Section 4 of the Apache-2.0 license, proper citations are maintained in module docstrings and documentation:

1. **ALA (ADWIN):** Bifet, A., & Gavaldà, R. (2007). *Learning from time-changing data with adaptive windowing*. SIAM International Conference on Data Mining (SDM).
2. **ALA (Streaming Trees):** Domingos, P., & Hulten, G. (2000). *Mining high-speed data streams*. ACM SIGKDD International Conference on Knowledge Discovery and Data Mining.
3. **RLA (Focal Loss):** Lin, T. Y., Goyal, P., Girshick, R., He, K., & Dollár, P. (2017). *Focal loss for dense object detection*. IEEE International Conference on Computer Vision (ICCV).
4. **RLA (Symmetric Cross Entropy):** Wang, Y., Ma, X., Chen, Z., Zeng, Y., Yi, J., & Bailey, J. (2019). *Symmetric cross entropy for robust learning with noisy labels*. IEEE International Conference on Computer Vision (ICCV).
5. **RAO (AdamW):** Loshchilov, I., & Hutter, F. (2019). *Decoupled weight decay regularization*. International Conference on Learning Representations (ICLR).
6. **RAO (Block Quantization):** Dettmers, T., Lewis, M., Belkada, Y., & Zettlemoyer, L. (2022). *LLM.int8(): 8-bit matrix multiplication for transformers at scale*. Advances in Neural Information Processing Systems (NeurIPS).

---

## 5. Dataset & Benchmark Provenance

All datasets utilized in benchmark suites and test examples were inspected for licensing and provenance:
- **SEA Concept Drift Generator:** Procedural synthetic stream generated dynamically in Python via mathematical hyperplane functions.
- **Electricity Benchmark:** Standard open research streaming dataset from the Australian New South Wales Electricity Market (publicly available for research evaluation).
- **Synthetic Noisy Label Generators:** Dynamically created via uniform random label flipping and class-conditional transition matrices; zero proprietary annotations.
- **Resource Profiling Workloads:** Pure synthetic tensor operations and synthetic classification batches; zero external data dependencies.

---

## 6. Critical Intellectual Property Risk: Defect DEF-004

### 6.1 Trademark Standing & Factual Assessment
1. **The Conflict:** During Phase 1-16, the engineering codename "AdaptiveML" was utilized. A commercial AI startup operates actively as "Adaptive ML Inc." (Adaptive ML SAS) providing commercial LLM fine-tuning solutions. Distributing software publicly under the distribution name `adaptive-ml` or import namespace `adaptive_ml` carries severe trademark infringement, brand confusion, and commercial dispute exposure.
2. **Technical Mitigation Executed:**
   - The legacy `adaptive_ml` namespace has been completely eliminated from the codebase.
   - The canonical project identity is officially established as **ROBUST-ADAPT** (`robust-adapt` / `robust_adapt`).
3. **Current Legal Status:**
   - **Trademark Availability:** Unverified. No preliminary clearance search (USPTO / EUIPO / WIPO) has been conducted by trademark attorneys for "ROBUST-ADAPT".
   - **Trademark Ownership:** The development team does NOT hold a registered trademark or pending application for "ROBUST-ADAPT".
   - **Outside Counsel Review:** Formal legal review is **PENDING**. No written opinion of non-infringement or availability has been rendered.

### 6.2 Formal Audit Determination
```
LEGAL CLEARANCE: NOT OBTAINED (DEF-004 OPEN)
```
- **Copyright & Software Licensing:** **CLEAR** (Apache-2.0, permissive dependencies, 100% original code).
- **Release Gating Consequence:** While technical release candidate artifacts can be compiled and validated internally, **public release, PyPI upload, and public marketing are strictly BLOCKED** until formal trademark counsel clearance is delivered in writing.

