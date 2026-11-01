# AdaptiveML — Testing & Validation Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-009`  
> **Last Updated**: 2026-11-01  
> **Scope**: Test pyramid, property-based verification, numerical gradient checks, and 5-seed reproducibility  
> **Target Audience**: QA Engineers, Scientific Reproducibility Leads, Core Developers

---

## 1. Testing Pyramid & Architectural Tiers

AdaptiveML defines a four-tier testing pyramid to guarantee mathematical accuracy, memory safety, and cross-platform reproducibility:

```
                                  / \
                                 /   \
                                / L4  \      L4: 5-Seed Reproducibility & Benchmarks
                               /-------\
                              /   L3    \    L3: End-to-End Integration Tests
                             /-----------\
                            /     L2      \  L2: Property-Based Invariant Tests
                           /---------------\
                          /       L1        \ L1: Unit & Numerical Gradient Tests
                         /-------------------\
```

---

## 2. Test Tiers & Execution Standards

### 2.1 Tier 1: Unit & Numerical Gradient Tests (`tests/unit/`)
- **Coverage Requirement**: $\ge 90\%$ line coverage across all modules in `adaptive_ml/`.
- **Numerical Finite-Difference Verification**:
  Every analytical gradient implementation (e.g. `SymmetricCrossEntropyLoss`, `GeneralizedCrossEntropyLoss`) is verified against numerical finite differences:
  $$\left\| \nabla_{\mathbf{z}}^{\text{analytical}} - \frac{\mathcal{L}(\mathbf{z} + \epsilon \mathbf{e}_k) - \mathcal{L}(\mathbf{z} - \epsilon \mathbf{e}_k)}{2 \epsilon} \right\|_\infty \le 10^{-5}$$
- **Execution Speed**: All Tier 1 tests must complete in $< 15$ seconds on a standard 4-core CPU.

### 2.2 Tier 2: Property-Based Invariant Tests (`tests/property/`)
Uses the `hypothesis` library to generate thousands of random, degenerate, and adversarial tensor inputs:
- **Probability Simplex Invariant**: Probabilities must satisfy $\sum_c p_c = 1.0 \pm 10^{-6}$ for all generated inputs.
- **Reliability Invariant**: Sample reliability $r_i$ must lie strictly in $[\epsilon_r, 1.0]$ across extreme logit margins ($z \in [-10^4, 10^4]$).
- **Quantization Roundtrip Bound**: Absolute error $|x - \text{dequant}(\text{quant}(x))| \le \frac{\text{scale}}{2}$.

### 2.3 Tier 3: Framework Integration Tests (`tests/integration/`)
- Validates drop-in compatibility with `scikit-learn` estimators:
  - Passes `sklearn.utils.estimator_checks.check_estimator(AdaptiveClassifier)`.
  - Works seamlessly inside `sklearn.pipeline.Pipeline` and `sklearn.model_selection.GridSearchCV`.
- Validates drop-in compatibility with `PyTorch`:
  - `LowMemoryAdamW` optimizes a standard multi-layer perceptron (MLP) and ConvNet.
  - Successfully executes `state_dict()` serialization and reload with identical loss on the next step.

---

## 3. Tier 4: The 5-Seed Scientific Reproducibility Harness

In accordance with AdaptiveML's scientific governance charter, all reported benchmarks, novelty claims, and regression tests must be executed across **five mandatory random seeds**:
$$\mathcal{S}_{\text{seeds}} = \{ 42, \; 1337, \; 2024, \; 7, \; 999 \}$$

### 3.1 Reproducibility Protocol
1. The test runner executes the identical benchmark pipeline independently for each seed $s \in \mathcal{S}_{\text{seeds}}$.
2. Metric values (Accuracy, F1-Score, Drift Detection Latency, Peak RAM) are aggregated.
3. Tests assert against both the mean and the standard deviation:
   $$\mu_{\text{metric}} \ge \text{Target}, \quad \sigma_{\text{metric}} \le \text{Threshold}$$
   A test that passes on one seed but exhibits high variance ($\sigma > \text{Threshold}$) fails the build.

---

## 4. Test Directory Layout

```
tests/
├── conftest.py                           # Pytest fixtures, random seeds, synthetic generators
├── unit/
│   ├── test_hoeffding_tree.py            # Unit tests for tree splitting and statistics
│   ├── test_rw_adwin.py                  # Unit tests for reliability-weighted drift
│   ├── test_margin_scorer.py             # Unit tests for density-margin scorer
│   ├── test_robust_losses.py             # Numerical gradient check tests
│   ├── test_low_memory_adamw.py          # Quantization and step tests
│   └── test_ulc_automaton.py             # State machine transition tests
├── property/
│   ├── test_simplex_invariants.py        # Hypothesis tests for probability simplex
│   └── test_quantization_bounds.py       # Hypothesis tests for quantization error
├── integration/
│   ├── test_sklearn_pipeline.py          # Scikit-learn Pipeline tests
│   └── test_torch_training_loop.py       # PyTorch optimizer tests
└── benchmarks/
    ├── benchmark_tree_throughput.py      # Throughput comparison vs River
    └── benchmark_adamw_memory.py         # Memory comparison vs standard AdamW
```
