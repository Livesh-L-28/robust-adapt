# AdaptiveML — Dataset Licensing & Privacy Audit
## Phase 16 Legal & Release Audit Deliverable

**Document Identifier:** `DOC-REL-013`<br>
**Working Codename:** AdaptiveML<br>
**Distribution Package Identifier:** `aml-core`<br>
**Current Version:** `0.1.0.dev0`<br>
**Date:** November 2026<br>
**Status:** `READY FOR REVIEW`

---

## 1. Executive Summary & Policy Mandate

This report evaluates all datasets, generators, and data streams utilized across benchmarks, unit tests, integration tests, and tutorials in AdaptiveML.

Per Phase 0 and Phase 3 Research Governance:
1. **Zero Proprietary Data Vendoring**: The repository and distribution packages must never bundle proprietary, restricted, or unverified third-party datasets.
2. **Zero Personally Identifiable Information (PII)**: All training streams must be devoid of individual personal data, GDPR/CCPA regulated identifiers, or biometric attributes.
3. **Synthetic Generator Priority**: Benchmarks and tutorials must prioritize mathematically specified synthetic data generators that execute in-memory with deterministic random seeds.

---

## 2. Dataset & Data Generator Inventory

An exhaustive file-by-file inspection of the workspace, wheel distribution, and source archive was conducted:

| Dataset / Generator | File Location | Data Category | Source / Provenance | License / Permissibility | PII / Privacy Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEA Streaming Concepts** | `benchmarks/phase-12/datasets/generators.py` | Procedural Synthetic | Street & Kim (2001) mathematical specification: $f(x) = x_0 + x_1 > \theta$ | Public Domain algorithmic formulation; generated in-memory via NumPy | **NONE** (Pure math) |
| **Rotating Hyperplane** | `benchmarks/phase-12/datasets/generators.py` | Procedural Synthetic | Hulten et al. (2001) mathematical specification: $\sum w_i x_i > w_0$ with drift rotation | Public Domain algorithmic formulation; generated in-memory via NumPy | **NONE** (Pure math) |
| **Label Noise Injector** | `benchmarks/phase-12/datasets/generators.py` | Procedural Synthetic | Symmetric, asymmetric, and instance-dependent noise simulation routines | Clean-room implementation under Apache-2.0 | **NONE** (Pure math) |
| **Extreme Imbalance Stream** | `benchmarks/phase-12/datasets/generators.py` | Procedural Synthetic | Synthetic Gaussian mixture clusters with $100:1$ ratio ($990$ majority / $10$ minority) | Clean-room implementation under Apache-2.0 | **NONE** (Pure math) |
| **Quickstart Stream** | `examples/quickstart.py` | Procedural Synthetic | Deterministic Gaussian random vectors with threshold classification | Clean-room implementation under Apache-2.0 | **NONE** (Pure math) |
| **Integration Test Feeds** | `tests/unit/`, `tests/integration/` | Procedural Synthetic | Ephemeral mock arrays generated via `np.random` within test fixtures | Generated in RAM, discarded post-test | **NONE** (Pure math) |

---

## 3. Distribution Artifact Audit (Zero Bundled Data)

The built distribution packages were audited:
- `aml_core-0.1.0.dev0-py3-none-any.whl`: Contains **zero** `.csv`, `.tsv`, `.parquet`, `.jsonl`, `.sqlite`, or raw data files.
- `aml_core-0.1.0.dev0.tar.gz`: Contains **zero** bundled data files.

All data used in tests, examples, and benchmarks is **synthesized ephemerally in RAM during execution** using NumPy pseudo-random number generators with explicit seeds (`np.random.seed(42)`).

---

## 4. Privacy & Regulatory Compliance Assessment

1. **GDPR (Regulation EU 2016/679)**: Fully compliant. No personal data processed or distributed.
2. **CCPA / CPRA (California)**: Fully compliant. No consumer personal information collected or transmitted.
3. **HIPAA / FERPA**: Not applicable; no medical or educational records utilized.

---

## 5. Audit Verdict

**Dataset License & Privacy Audit Verdict**: **`PASSED — 100% SYNTHETIC & ZERO BUNDLED THIRD-PARTY DATA`**.
