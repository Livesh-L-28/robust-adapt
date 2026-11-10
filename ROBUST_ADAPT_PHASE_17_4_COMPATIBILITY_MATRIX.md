# ROBUST-ADAPT — Phase 17.4: Comprehensive Compatibility Matrix

**Document ID:** MATRIX-PHASE17-4-COMPAT-001<br>
**Version:** 0.1.0-alpha.0<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4` (`4103b87`)<br>
**Canonical Package:** `robust_adapt`<br>
**Distribution Name:** `robust-adapt`<br>
**Evaluation Date:** November 2026<br>
**Overall Status:** **VERIFIED WITH LIMITATIONS (LOCAL HOST BOUNDARY)**<br>

---

## 1. Specification Baseline & Declared Scope

The distribution metadata declared in `pyproject.toml` establishes the supported boundaries:

| Parameter | Specification | Evidence Source |
| :--- | :--- | :--- |
| **Python Support Declaration** | `>=3.10` | `pyproject.toml:10` |
| **Declared Python Classifiers** | 3.10, 3.11, 3.12, 3.13, 3.14 | `pyproject.toml:20-24` |
| **Operating System Target** | `OS Independent` | `pyproject.toml:27` |
| **Mandatory Core Runtime** | `numpy>=1.24.0` | `pyproject.toml:33` |
| **Optional Framework Extras** | `torch`, `sklearn`, `safetensors`, `dataframe` | `pyproject.toml:36-50` |

---

## 2. Multi-Version Python Compatibility Matrix

In accordance with strict Phase 17.4 governance rules, only runtimes with empirical, reproducible local execution evidence are marked **PASSED**. Uninstalled interpreters are explicitly marked **NOT TESTED** with reproducible setup instructions.

| Python Version | Requirement Role | Local Environment Status | Empirical Test Result | Finding / Assessment |
| :--- | :--- | :--- | :---: | :--- |
| **Python 3.10** | Declared Minimum (`>=3.10`) | Not Installed Locally | **NOT TESTED** | Requires Python 3.10 interpreter installation or CI runner execution. |
| **Python 3.11** | High-Volume LTS Runtime | Installed (`3.11.9` AMD64) | **TESTED — PASSED** | Clean wheel installation in fresh venv; DEF-ALPHA-001 eager annotation fix verified; 145 unit tests passed (2 skipped for torch); 18/19 examples passed (1 requires torch); 4/4 SDK tests passed; `adaptive_ml` confirmed unimportable. |
| **Python 3.12** | Active Release Runtime | Not Installed Locally | **NOT TESTED** | Requires Python 3.12 interpreter installation or CI runner execution. |
| **Python 3.13** | Recent Release Runtime | Not Installed Locally | **NOT TESTED** | Requires Python 3.13 interpreter installation or CI runner execution. |
| **Python 3.14** | Latest Release Runtime | Installed (`3.14.3` AMD64) | **TESTED — PASSED** | Clean wheel install; sdist rebuild install; full 337-test suite passed (100% pass rate in 38.26s); full framework stack verified (PyTorch, scikit-learn, safetensors, pandas, polars). |

---

## 3. Operating System Platform Matrix

| Operating System | Architecture | Environment Type | Validation Status | Evidence Summary |
| :--- | :--- | :--- | :---: | :--- |
| **Microsoft Windows 11** | AMD64 (x86_64) | Local Workstation (Build 26200) | **TESTED — PASSED** | Verified on Python 3.14.3 and 3.11.9. Full test suite, packaging build, isolated venv installations, and sdist rebuild pass. |
| **Linux (Ubuntu/Debian)** | x86_64 / aarch64 | External CI Runner | **NOT TESTED** | No local Linux kernel, container, or WSL instance configured in current session. Configured in `.github/workflows/ci.yml`. |
| **macOS (Darwin)** | ARM64 (Apple Silicon) / x86_64 | External CI Runner | **NOT TESTED** | No Apple Darwin host available in local workspace. Configured in `.github/workflows/ci.yml`. |

> [!IMPORTANT]
> **Zero Assumption Policy:** In strict adherence to governance guidelines, Windows empirical results are **not** extrapolated to Linux or macOS. Multi-platform execution will occur upon dispatch of GitHub Actions workflows on `ubuntu-latest` and `macos-latest`.

---

## 4. Subsystem & Pillar Compatibility Audit

| Scientific Subsystem | Canonical Module | Python 3.11 (Minimal NumPy) | Python 3.14 (Full Stack) | Cross-Version Status |
| :--- | :--- | :---: | :---: | :---: |
| **Adaptive Learning (ALA)** | `robust_adapt.ala` | **PASSED** | **PASSED** | Deterministic drift detection & streaming tree updates |
| **Robust Learning (RLA)** | `robust_adapt.rla` | **PASSED** | **PASSED** | Loss computation, finite output & zero-gradient masking |
| **Resource-Aware (RAO)** | `robust_adapt.rao` | **PASSED** | **PASSED** | Block quantizer & budget manager operational |
| **Unified Controller (ULC)** | `robust_adapt.ulc` | **PASSED** | **PASSED** | ULC-v4.1 and ULC-v5 arbitration automata verified |
| **Minority Intelligence** | `robust_adapt.minority` | **PASSED** | **PASSED** | Prior tracking and calibrated threshold management |
| **State Serialization** | `robust_adapt.state` | **PASSED** (NumPy) | **PASSED** (SafeTensors) | Safe fallbacks active when optional packages absent |
| **Framework Integrations** | `robust_adapt.integrations`| **SKIPPED** (Graceful) | **PASSED** | Torch optimizer & scikit-learn estimators verified |
| **Legacy Namespace Absence** | `adaptive_ml` | **PASSED** (`ModuleNotFoundError`) | **PASSED** (`ModuleNotFoundError`) | 100% absence confirmed across both runtimes |

