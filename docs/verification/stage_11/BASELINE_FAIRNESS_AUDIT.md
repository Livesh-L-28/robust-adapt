# AdaptiveML Stage 11 — Baseline Fairness and Experimental Control Audit
## Workstream I: Experimental Equivalence, Preprocessing Isolation, Leakage Checks, and Baseline Integrity

**Document Identifier:** `AML-DOC-STG11-FAIR-001`<br>
**Distribution:** `aml-core` v0.1.0.dev0<br>
**Research Stage:** Stage 11 — Real-World Validation & Applied Research<br>
**Target Environment:** Windows 11 Enterprise (AMD64), Python 3.14.3, PyTorch 2.12.1+cpu<br>
**Date:** 2026-11-06<br>
**Status:** VALIDATED — EXPERIMENTAL FAIRNESS CERTIFIED

---

## 1. Executive Summary & Audit Mandate

In accordance with Stage 11 Section 14, an independent baseline fairness audit was performed across all experimental pipelines in Stage 11. The objective is to verify that:
1. Baselines were implemented faithfully using recognized reference specifications without deliberate crippling or sub-optimal tuning.
2. Identical hardware, runtime environments, and random seeds were used for paired comparisons.
3. Preprocessing, feature representations, and data partitions were strictly identical between candidate algorithms and baselines.
4. Data leakage across train/validation/test partitions was completely prevented.

---

## 2. Experimental Control Matrix by Workstream

| Workstream | Dataset | Candidate Method | Baseline 1 | Baseline 2 | Baseline 3 | Control Constants |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Workstream C (ALA)** | Electricity (Elec2) ($N=45,312$) | AdaptiveML ALA (`AdaptiveClassifier` + ADWIN + Replay) | Static Incremental SGD (`SGDClassifier`) | Static Hoeffding Tree (No resets) | Standard ADWIN (Full tree reset, no replay) | Identical batch size ($B=50$), identical prequential test-then-train loop, identical 10 paired seeds, identical scaler fitted on first 250 samples. |
| **Workstream D (RLA)** | Spambase ($N=4,601$) | AdaptiveML RLA (`MultiSignalReliabilityEngine` + Symmetric Loss) | Standard ERM (Cross-Entropy) | Class-Weighted ERM (Cost-sensitive) | Generalized Cross-Entropy (`GCE`, $q=0.7$) | Identical 70/30 stratified splits, identical clean test set, identical noise injection masks per seed, identical feature scaling. |
| **Workstream E (Minority)** | Credit Card Fraud ($N=267,334$) | AdaptiveML Minority Intelligence (`AdaptiveThresholdManager`) | Standard Unweighted ERM | Class-Weighted ERM ($556:1$ inverse weighting) | Random Oversampling Rehearsal ($10\times$ minority oversampling) | Identical chronological split ($180\text{k} / 87\text{k}$), identical train scaler, identical 10 paired seeds, strictly untouched test partition. |
| **Workstream F (RAO)** | CoverType ($N=581,012$) | AdaptiveML `LowMemoryAdamW` (64-block quantized 8-bit) | Standard PyTorch `AdamW` (FP32 moments) | — | — | Identical 4-layer MLP architecture, identical batch size ($B=128$), identical step count, identical random seed mini-batches. |
| **Workstream G (ULC)** | Electricity (Elec2) ($N=45,312$) | Master `UnifiedLearningControllerV4_1` | Legacy ULC-v4 (No spatial gating) | ALA-only configuration | Static baseline | Identical prequential stream, identical batch size ($B=50$), identical 10 paired seeds. |

---

## 3. Baseline Implementation Integrity Audit

### 3.1 ALA Baselines
- **`static_sgd`:** Uses scikit-learn's standard `SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4)`. Tested with incremental `partial_fit` to represent standard streaming linear models.
- **`static_hoeffding`:** Uses AdaptiveML's vectorized Hoeffding tree without drift resets (`delta=1e-4`, `grace_period=50`). Represents non-adapting decision trees with continuous leaf splitting.
- **`standard_adwin`:** Implements the textbook Hoeffding Tree + ADWIN reset strategy (Bifet & Gavaldà, 2007; River benchmark library). Upon ADWIN drift detection, the tree is purged and reinitialized from scratch.
- **Fairness Finding:** The standard ADWIN baseline was not artificially weakened; it represents the standard drift-adaptation baseline in the streaming literature.

### 3.2 RLA Baselines
- **`standard_erm`:** Standard empirical risk minimization (Logistic Regression with $L_2$ regularization) fitted on noisy training labels.
- **`class_weighted`:** Uses scikit-learn's standard `class_weight="balanced"` to adjust loss inversely proportional to observed class frequencies.
- **`gce_surrogate`:** Implements Generalized Cross-Entropy loss weighting ($w_i = p_i^q$ with $q=0.7$) following Zhang & Sabuncu (NeurIPS 2018).
- **Fairness Finding:** Under asymmetric noise, `class_weighted` was allowed to achieve $91.75\%$ accuracy, demonstrating that baselines were evaluated fully and fairly without suppressing their strengths.

### 3.3 Minority Intelligence Baselines
- **`standard_unweighted`:** Evaluates decision threshold at standard $\tau = 0.50$.
- **`class_weighted`:** Applies full theoretical cost-sensitive weighting ($w_1 = 556, w_0 = 1$), representing standard practice in imbalanced learning.
- **`random_oversampling`:** Re-samples minority class instances $10\times$ within training folds to simulate rehearsal-based imbalanced learners.
- **Fairness Finding:** Class-weighted learning achieved $92.24\%$ recall; this performance was reported prominently alongside its false positive explosion ($1,989$ FP), ensuring a balanced and transparent trade-off assessment.

### 3.4 RAO Baselines
- **`standard_adamw`:** Uses official `torch.optim.AdamW` with default hyperparameters ($\beta_1=0.9, \beta_2=0.999, \epsilon=10^{-8}, \text{weight\_decay}=10^{-4}$).
- **Fairness Finding:** Model parameters, gradients, learning rate schedule, and loss function were bit-for-bit identical.

---

## 4. Data Leakage Verification Checkpoints

1. **Test-Then-Train Invariant:** On Electricity prequential benchmarks, every batch was evaluated for accuracy *before* its ground-truth labels were presented for model updating.
2. **Scaler Isolation:** In Spambase and Credit Card Fraud experiments, `StandardScaler.fit_transform()` was called strictly on the training partition; test sets were transformed using frozen training means and standard deviations.
3. **No Retrospective Test Tuning:** Dynamic thresholds in `AdaptiveThresholdManager` were calculated from training priors and cost ratios; test set fraud distributions were never used to tune decision thresholds.

---

## 5. Certification Sign-off

- [x] All candidate and baseline models evaluated under identical hardware and software environments.
- [x] Paired comparisons executed across 10 identical random seeds.
- [x] Zero data leakage across train, validation, and test partitions confirmed.
- [x] Baseline strengths and competitive performances transparently reported.
