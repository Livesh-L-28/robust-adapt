# AdaptiveML — Phase 3: Dataset and Benchmark License Review

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-005`  
> **Last Updated**: 2026-11-01  
> **Scope**: Benchmark datasets for empirical validation in Phase 12

---

## 1. Dataset Licensing & Usage Matrix

To ensure absolute legal safety during research experimentation and public benchmark publishing, candidate benchmark datasets are audited for license compatibility, redistribution terms, and privacy risks:

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            BENCHMARK DATASET LICENSING AUDIT                                                  |
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
| Dataset Name        | Target Pillar     | Primary Domain  | Verified License      | Commercial Rights   | Redistribution Rule |
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
| **Electricity (ELEC2)**| ALA Drift      | Tabular Time-Ser| **Public Domain**     | Permitted           | Download on-the-fly |
| **Forest CoverType**| ALA / RLA         | Tabular Multi-Cl| **Public Domain**     | Permitted           | Download on-the-fly |
| **Synthetic SEA**   | ALA Drift         | Synthetic Data  | **Generated on-the-fly**| Fully Unrestricted | Code generator only |
| **Split-MNIST**     | ALA Continual     | Vision Digits   | **CC BY-SA 3.0**      | Permitted (Attrib)  | Download on-the-fly |
| **CIFAR-10 / 100**  | RLA / RAO         | Vision Tiny     | **MIT / Academic**    | Research Fair Use   | Download via Torch  |
| **CIFAR-10N**       | RLA Human Noise   | Real Label Noise| **MIT License**       | Permitted           | Download on-the-fly |
| **Clothing1M**      | RLA Real Noise    | E-Commerce Cloth| **Academic Only**     | **Restricted**      | **DO NOT REDISTRIBUTE**|
| **California Housing**| RAO Regression  | Tabular Regress | **Public Domain**     | Permitted           | Download via sklearn|
+---------------------+-------------------+-----------------+-----------------------+---------------------+---------------------+
```

---

## 2. Dataset Legal Safeguards & Zero-Vendoring Policy

### 2.1 The Zero-Vendoring Rule
- **AdaptiveML will never vendor or bundle raw image, audio, or tabular dataset files inside the Python package or git repository.**
- All benchmark drivers (`benchmarks/download_data.py`) must fetch public data directly from their authoritative academic hosting URLs into a local user cache directory (`~/.cache/adaptiveml/data/`) with checksum validation (SHA-256).

### 2.2 Privacy & Sensitive Data Safeguards
- None of the target public benchmark datasets (CoverType, CIFAR-10, Split-MNIST) contain Personally Identifiable Information (PII) or biometric facial data.
- Proprietary or restricted datasets (e.g. Clothing1M, which contains web-scraped images under academic-only terms) will be used solely for optional academic replication scripts, with explicit warnings that commercial redistributions must omit Clothing1M data.

### 2.3 Synthetic Data Generators
- For ALA stream drift experiments, AdaptiveML will provide native **synthetic data generators** (SEA concepts, Rotating Hyperplane, Stagger concepts) implemented in pure NumPy.
- Synthetic generators carry **zero third-party copyright, license restrictions, or privacy risks**.
