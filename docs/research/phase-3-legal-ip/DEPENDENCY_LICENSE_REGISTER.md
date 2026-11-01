# AdaptiveML — Phase 3: Dependency License Register

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-004`  
> **Last Updated**: 2026-11-01  
> **Target Scope**: Direct runtime, optional extras, and build/test dependencies

---

## 1. Dependency Licensing Audit Matrix

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                DEPENDENCY LICENSING AUDIT                                                     |
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
| Package Name        | Dependency Tier   | Version Target  | Verified License      | Official License URL| Compatibility Status|
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
| **numpy**           | **Mandatory Core**| `>= 1.24.0`     | **BSD 3-Clause**      | [NumPy License](https://github.com/numpy/numpy/blob/main/LICENSE.txt) | **100% Compatible** |
| **typing-extensions**| Mandatory Core   | `>= 4.5.0`      | **PSF License**       | [PSF License](https://docs.python.org/3/license.html)                 | **100% Compatible** |
| **scipy**           | Optional Extra    | `>= 1.10.0`     | **BSD 3-Clause**      | [SciPy License](https://github.com/scipy/scipy/blob/main/LICENSE.txt) | **100% Compatible** |
| **scikit-learn**    | Optional Extra    | `>= 1.3.0`      | **BSD 3-Clause**      | [sklearn License](https://github.com/scikit-learn/scikit-learn/blob/main/COPYING) | **100% Compatible** |
| **torch**           | Optional Extra    | `>= 2.0.0`      | **Modified BSD (Meta)**| [PyTorch License](https://github.com/pytorch/pytorch/blob/main/LICENSE) | **100% Compatible** |
| **pytest**          | Development Only  | `>= 7.4.0`      | **MIT**               | [Pytest License](https://github.com/pytest-dev/pytest/blob/main/LICENSE) | Non-distributable   |
| **pytest-cov**      | Development Only  | `>= 4.1.0`      | **MIT**               | [Pytest-cov License](https://github.com/pytest-dev/pytest-cov/blob/master/LICENSE.txt) | Non-distributable |
| **mypy**            | Development Only  | `>= 1.5.0`      | **MIT**               | [Mypy License](https://github.com/python/mypy/blob/master/LICENSE)     | Non-distributable   |
| **ruff**            | Development Only  | `>= 0.1.0`      | **MIT / Apache-2.0**  | [Ruff License](https://github.com/astral-sh/ruff/blob/main/LICENSE-MIT)| Non-distributable   |
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
```

---

## 2. Dependency Tier Analysis & Isolation Rules

### 2.1 Mandatory Core Runtime (`pip install adaptiveml`)
- **Direct Dependencies**: Exclusively Python standard library + `numpy >= 1.24.0` + `typing_extensions >= 4.5.0`.
- **Transitive Dependency Tree**: `numpy` has **zero** required transitive third-party dependencies.
- **Licensing Footprint**: BSD 3-Clause + PSF License. Both are fully permissive and permit re-distribution under Apache-2.0 without copyleft encumbrance.

### 2.2 Optional Framework Integrations
- `adaptiveml[sklearn]`: BSD 3-Clause.
- `adaptiveml[torch]`: Modified BSD. PyTorch's license contains standard disclaimer clauses and does not impose copyleft obligations on external libraries importing its modules.
- **Isolation Rule**: Optional modules reside in `adaptiveml.integrations.*` and are protected by `try...except ImportError` guards, preventing runtime linkage when not installed.

### 2.3 Prohibited Dependencies
- Any package distributed under **GPL-2.0, GPL-3.0, AGPL-3.0, or CC-BY-NC** is strictly prohibited from direct or optional runtime dependencies.
