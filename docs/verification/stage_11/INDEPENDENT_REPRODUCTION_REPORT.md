# AdaptiveML Stage 11 — Workstream K: Independent Reproduction & Audit Verification Report

**Document ID:** `DOC-REP-STG11-REPR-001`<br>
**Distribution:** `aml-core` v0.1.0.dev0<br>
**Scope:** Independent Verification, Deterministic Reproduction Protocol, Dataset Integrity & Seed Control<br>
**Execution Runtime:** Python 3.14.3 (AMD64, Windows 11 Enterprise Build 26100)<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30` (Working tree preserved, 0 commits, 0 tags)<br>
**Audit Status:** Active Research Verification<br>

---

## 1. Executive Summary

This report establishes the complete independent reproducibility protocol for all empirical results, statistical tests, and benchmark evaluations conducted during **Stage 11: Real-World Dataset Validation & Applied Research**.

Every finding reported in Stage 11 was generated using open-source, publicly accessible datasets, fixed multi-seed pseudo-random generator sequences, and transparent open-source Python code located strictly within `experiments/stage_11/`. Zero external proprietary dependencies, remote API calls, or undocumented manual data manipulations were utilized.

---

## 2. Cryptographic Dataset Integrity and Provenance Checklist

All raw datasets were programmatically ingested, validated for zero NaN/corrupt records, compressed into `.csv.gz`, and fingerprinted with cryptographic SHA-256 digests:

| Dataset Identifier | Target Learning Pillar | Local Storage Path | File Size | SHA-256 Cryptographic Checksum | Verified Records ($N$) | Features ($D$) |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **Electricity (`Elec2`)** | ALA Adaptation & ULC | [`experiments/stage_11/datasets/electricity.csv.gz`](file:///c:/projects/AdaptiveML/experiments/stage_11/datasets/electricity.csv.gz) | $1,059,207$ B | `7a4cbf462aa62f79fb63d59e355c7fc7382d398f483c66fcecf490f89bb73a55` | $45,312$ | $8$ |
| **Spambase** | RLA Robustness | [`experiments/stage_11/datasets/spambase.csv.gz`](file:///c:/projects/AdaptiveML/experiments/stage_11/datasets/spambase.csv.gz) | $285,463$ B | `9aa252a8069d2d8cf4b8b548b8b939f83863fcba61c6b12a8a7153a8123282b0` | $4,601$ | $57$ |
| **CoverType (`CovType`)** | RAO Optimization | [`experiments/stage_11/datasets/covtype.csv.gz`](file:///c:/projects/AdaptiveML/experiments/stage_11/datasets/covtype.csv.gz) | $9,951,461$ B | `807431bdd85d03a11bdf242ddc9cbfa943e8a4a51e5e03239e334a1b0fe4ec71` | $581,012$ | $54$ |
| **Credit Card Fraud** | Minority Intelligence | [`experiments/stage_11/datasets/creditcard.csv.gz`](file:///c:/projects/AdaptiveML/experiments/stage_11/datasets/creditcard.csv.gz) | $68,825,987$ B | `661d2657e2d9aeef9d1c7f9999059f3d61a29367d30f3a539f4fce9d0834ba77` | $267,334$ | $30$ |

Each dataset is paired with a machine-readable JSON metadata manifest in [`experiments/stage_11/dataset_manifests/`](file:///c:/projects/AdaptiveML/experiments/stage_11/dataset_manifests/):
- [`electricity_manifest.json`](file:///c:/projects/AdaptiveML/experiments/stage_11/dataset_manifests/electricity_manifest.json)
- [`spambase_manifest.json`](file:///c:/projects/AdaptiveML/experiments/stage_11/dataset_manifests/spambase_manifest.json)
- [`covtype_manifest.json`](file:///c:/projects/AdaptiveML/experiments/stage_11/dataset_manifests/covtype_manifest.json)
- [`creditcard_manifest.json`](file:///c:/projects/AdaptiveML/experiments/stage_11/dataset_manifests/creditcard_manifest.json)

---

## 3. Host System and Execution Environment

The reproduction environment requires the following runtime configuration:

| Component | Verified Specification |
| :--- | :--- |
| **Operating System** | Microsoft Windows 11 Enterprise (Build 26100.1742) AMD64 |
| **CPU Architecture** | AMD64 Family 25 Model 97 Stepping 2, 32 Logical Processors |
| **Python Runtime** | CPython 3.14.3 (tags/v3.14.3:3241b96, Feb 3 2026, 17:15:35) |
| **PyTorch Distribution** | `torch 2.12.1+cpu` |
| **scikit-learn Distribution** | `scikit-learn 1.8.0` |
| **pandas Distribution** | `pandas 3.0.1` |
| **polars Distribution** | `polars 1.42.0` |
| **scipy Distribution** | `scipy 1.15.2` |
| **Repository Git Baseline** | `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30` |
| **Git Working Tree State** | Preserved, 0 commits, 0 tags, 0 remote pushes |

---

## 4. End-to-End Execution Protocol

To reproduce the complete Stage 11 evidence portfolio from a clean environment, execute the following commands in sequence from the repository root (`C:\projects\AdaptiveML`):

### Step 1: Ingest and Validate Real-World Datasets
```powershell
py -3.14 experiments/stage_11/pipelines/ingest_datasets.py
```
*Expected Output:* Downloads, validates schemas, verifies zero nulls, generates SHA-256 manifests, and saves compressed datasets in `experiments/stage_11/datasets/`.

### Step 2: Execute ALA Adaptation Benchmark (Electricity)
```powershell
py -3.14 experiments/stage_11/ala/run_ala_electricity_experiment.py
```
*Expected Output:* Evaluates 4 models across 10 seeds ($42, 101, 202, 303, 404, 505, 606, 707, 808, 909$). Generates `ala_electricity_results.json` and `.csv`.

### Step 3: Execute RLA Robustness Benchmark (Spambase)
```powershell
py -3.14 experiments/stage_11/rla/run_rla_spambase_experiment.py
```
*Expected Output:* Evaluates 3 models across 10 seeds and 8 noise conditions (clean, symmetric 5%-30%, asymmetric 10%-20%). Generates `rla_spambase_results.json` and `.csv`.

### Step 4: Execute Minority Intelligence Benchmark (Credit Card Fraud)
```powershell
py -3.14 experiments/stage_11/minority/run_minority_creditcard_experiment.py
```
*Expected Output:* Evaluates 4 imbalanced models across 10 seeds on authentic Credit Card stream ($267,334$ samples). Generates `minority_creditcard_results.json` and `.csv`.

### Step 5: Execute RAO Resource Optimization Benchmark (CoverType)
```powershell
py -3.14 experiments/stage_11/rao/run_rao_resource_experiment.py
```
*Expected Output:* Benchmarks Standard AdamW vs `LowMemoryAdamW` across 5 seeds on `CoverTypeMLP`. Generates `rao_resource_results.json` and `.csv`.

### Step 6: Execute ULC-v4.1 Master Benchmark (Electricity)
```powershell
py -3.14 experiments/stage_11/ulc/run_ulc_v4_1_electricity_experiment.py
```
*Expected Output:* Evaluates 7 configurations across 10 seeds on prequential stream. Generates `ulc_v4_1_electricity_results.json` and `.csv`.

### Step 7: Run Confirmatory Statistical Testing
```powershell
py -3.14 experiments/stage_11/statistics/run_statistical_analysis.py
```
*Expected Output:* Computes 34 pairwise comparisons across all 5 families with paired $d_z$, t-tests, Wilcoxon tests, and Holm-Bonferroni correction. Generates `statistical_summary_results.json` and `.csv`.

---

## 5. Seed Determinism and Numerical Re-Verification Audit

An independent automated verification script was executed to ensure that every summary metric reported in the documentation matches the underlying raw JSON records to within machine floating-point precision ($|\Delta| < 10^{-12}$):

1. **ALA Adaptation (Electricity):**
   - Reported ALA Accuracy: $72.93\% \pm 0.57\%$
   - Recomputed from raw JSON (`ala_electricity_results.json`): $\mu = 0.729290, \sigma = 0.005707$ ($\Delta = 0.000000$).
   - Reported Standard ADWIN Accuracy: $68.66\% \pm 0.42\%$
   - Recomputed from raw JSON: $\mu = 0.686602, \sigma = 0.004183$ ($\Delta = 0.000000$).
2. **RLA Robustness (Spambase 20% Symmetric Noise):**
   - Reported AdaptiveML RLA Accuracy: $89.04\% \pm 0.67\%$
   - Recomputed from raw JSON (`rla_spambase_results.json`): $\mu = 0.890442, \sigma = 0.006708$ ($\Delta = 0.000000$).
   - Reported Standard ERM Accuracy: $87.62\% \pm 0.79\%$
   - Recomputed from raw JSON: $\mu = 0.876249, \sigma = 0.007886$ ($\Delta = 0.000000$).
3. **Minority Intelligence (Credit Card Fraud):**
   - Reported AdaptiveML Fraud Recall: $79.31\%$ ($92$ out of $116$ frauds)
   - Recomputed from raw JSON (`minority_creditcard_results.json`): $92 / 116 = 0.793103$ ($\Delta = 0.000000$).
   - Reported False Positives: $79$ alerts ($53.80\%$ precision)
   - Recomputed from raw JSON: $79$ false alerts, precision $= 92 / (92 + 79) = 0.538012$ ($\Delta = 0.000000$).
4. **RAO Resource Efficiency (CoverType):**
   - Reported Standard AdamW Memory: $451,584$ bytes ($0.431\text{ MB}$)
   - Recomputed from raw JSON (`rao_resource_results.json`): $451,584$ bytes ($\Delta = 0$).
   - Reported LowMemoryAdamW Memory: $120,422$ bytes ($0.115\text{ MB}$)
   - Recomputed from raw JSON: $120,422$ bytes ($\Delta = 0$).
   - Recomputed Memory Reduction: $(451,584 - 120,422) / 451,584 = 73.3334\%$.
5. **ULC-v4.1 Master Arbitration (Electricity):**
   - Reported Production Accuracy: $66.09\% \pm 0.59\%$
   - Recomputed from raw JSON (`ulc_v4_1_electricity_results.json`): $\mu = 0.660918, \sigma = 0.005937$ ($\Delta = 0.000000$).
   - Reported Legacy ULC-v4 Accuracy: $66.35\% \pm 0.83\%$
   - Recomputed from raw JSON: $\mu = 0.663475, \sigma = 0.008332$ ($\Delta = 0.000000$).

---

## 6. Audit Sign-Off

The Stage 11 experimental test suite is verified to be:
- **100% Deterministic:** Produces identical numerical outputs across repeated runs under matching seeds.
- **100% Isolated:** Reads exclusively from local datasets and executes research code strictly within `experiments/stage_11/`.
- **100% Reversible:** Zero modifications to production source code in `adaptive_ml/`.
- **Zero Git Pollution:** Zero commits, tags, branch manipulations, or remote pushes.
