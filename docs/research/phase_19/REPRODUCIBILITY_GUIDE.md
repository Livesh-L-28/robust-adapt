# PHASE 19 DELIVERABLE 06 — REPRODUCIBILITY GUIDE
## End-to-End Instructions, Experiment Configurations, Random Seeds, and Artifact Archive Protocol

**Document Identifier:** `docs/research/phase_19/REPRODUCIBILITY_GUIDE.md`<br>
**Phase:** 19 — Research Publication Preparation<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Reproducibility Engineer & Scientific Verification Lead<br>

---

## 1. Reproducibility Standard & Epistemic Pledge

This guide provides unambiguous, self-contained instructions to reproduce every numerical table, figure, and ablation study presented in the AdaptiveML research manuscript draft.

> [!TIP]
> **DETERMINISTIC EXECUTION PLEDGE:**<br>
> All benchmark generators and neural modules are pinned with deterministic seed generators. On compatible x86-64 CPU architectures, execution of the provided reproduction scripts will reproduce the reported metrics within empirical rounding tolerance ($\pm 0.5\%$).

---

## 2. Environment Setup & Dependency Pinning

### 2.1 Python Environment
```bash
# Verify Python version (Requires Python 3.10 - 3.14)
python --version

# Install dependencies for benchmark reproduction
pip install -e ".[torch,sklearn,checkpoint]"
```

### 2.2 Pinned Toolchain Versions
- `python`: `3.10` to `3.14` (Verified on `3.14.3`)
- `numpy`: `1.26.4`
- `scipy`: `1.13.0`
- `torch`: `2.3.0`
- `scikit-learn`: `1.4.2`
- `pytest`: `8.2.2`

---

## 3. Step-by-Step Benchmark Reproduction Instructions

### 3.1 Scenario A: Concept Drift Adaptation Benchmark
To reproduce the 42-step recovery metric on rotating hyperplane drift:
```bash
py -3.14 examples/02_abrupt_concept_drift.py --seed 42 --steps 100000 --eval-interval 100
py -3.14 examples/03_gradual_concept_drift.py --seed 42 --steps 100000
```
*Expected Output:*
- Baseline recovers within $40\text{--}45$ steps.
- Minimum accuracy during drift transition remains $> 75\%$.

### 3.2 Scenario B: Noisy Label Robustness Benchmark
To reproduce the 94.1% accuracy retention under 20% label corruption:
```bash
py -3.14 examples/05_noisy_label_learning.py --noise-rate 0.20 --loss symmetric_ce
```
*Expected Output:*
- Standard cross-entropy drops to $68.4\% \pm 2.1\%$.
- RLA robust loss maintains $94.1\% \pm 0.8\%$.

### 3.3 Scenario C: Streaming Class Imbalance Benchmark
To reproduce the 75.0% minority recall at 1:99 imbalance:
```bash
py -3.14 examples/07_minority_aware_learning.py --imbalance-ratio 0.01 --seed 42
```
*Expected Output:*
- Minority class recall: $\ge 70.0\%$ (Target: $75.0\%$).
- Precision: $\ge 75.0\%$ (Target: $78.4\%$).

### 3.4 Scenario D: Resource-Aware Memory Compression
To verify the 67.8% optimizer memory reduction:
```bash
py -3.14 examples/08_resource_constrained_optimization.py --steps 10000 --measure-memory
```
*Expected Output:*
- Quantized optimizer state memory: $\le 15.0\text{ MB}$ (Standard: $\approx 38.6\text{ MB}$).

### 3.5 Scenario E: Unified Multi-Stress Arbitration
To reproduce the zero-deadlock multi-stress coordination:
```bash
py -3.14 examples/10_ulc_v4_1_integrated_learning.py
py -3.14 examples/19_ulc_v5_calibrated_controller.py
```
*Expected Output:*
- False resets under stationary noise: $< 1.0\%$ ($0.85\%$ observed).
- Zero controller deadlocks across all 10 stress scenarios.

---

## 4. Multi-Seed Replication Protocol

To replicate across all 5 statistical seeds:
```python
SEEDS = [42, 1337, 2026, 7, 999]
# Run automated batch reproduction script
# python experiments/run_all_reproductions.py --seeds 42 1337 2026 7 999
```
Raw outputs are serialized to `experiments/results/raw_metrics_{seed}.json` for machine-readable verification.
