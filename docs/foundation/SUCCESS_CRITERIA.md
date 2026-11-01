# AdaptiveML: Success Criteria & Evaluation Standards

> **Document Status**: Approved Baseline (Phase 0 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-FDN-003`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Core engineering team, scientific evaluators, peer reviewers, open-source contributors

---

## 1. Principles of Evaluation

To maintain absolute scientific integrity and avoid common pitfalls of AI library claims (such as cherry-picked benchmarks, unverified performance statistics, and synthetic metric manipulation), AdaptiveML enforces the following primary rule:

> [!IMPORTANT]
> **TARGET VS. ACHIEVED RESULT DISTINCTION**  
> Every quantitative performance threshold specified in this document is a **rigorous engineering target**. No metric may be reported or advertised as an "achieved result" until Phase 12 (Research Experiments & Benchmarking) is fully completed, peer-reviewed, and reproduced across multiple independent environments.

---

## 2. Scientific & Algorithmic Success Criteria

### 2.1 Theoretical Correctness & Mathematical Grounding
- **Target SC-SCI-01 (Formulation Rigor)**: Every implemented algorithm must have a formal mathematical specification in `docs/research/` detailing objective functions, gradient expressions, state update formulas, and known convergence boundaries.
- **Target SC-SCI-02 (Convergence Guarantees)**: For optimization routines in RAO, asymptotic convergence guarantees under standard convexity/L-smoothness assumptions must be documented. Where non-convexity precludes theoretical guarantees, empirical stability bounds must be defined.
- **Target SC-SCI-03 (Hypothesis Tracking)**: Research hypotheses must be documented in a central hypotheses registry prior to benchmarking. Post-hoc hypothesis justification ("HARKing") is strictly prohibited.

### 2.2 Standard Baseline Comparisons
Every pillar must be evaluated against established, canonical open-source baselines on standardized public benchmark datasets:

| Pillar | Algorithm Domain | Established Baselines for Comparison | Benchmark Datasets / Environments |
| :--- | :--- | :--- | :--- |
| **ALA** | Concept Drift & Stream Adaptation | - Exponentially Weighted Moving Average (EWMA)<br>- DDM / EDDM drift detectors<br>- Elastic Weight Consolidation (EWC)<br>- Experience Replay / Reservoir Sampling | - Electricity (ELEC2)<br>- Forest CoverType<br>- Synthetic Rotating Hyperplane / SEA<br>- Split-MNIST / Permuted-MNIST |
| **RLA** | Robust Risk & Label Noise Filtering | - Standard ERM (Cross-Entropy / MSE)<br>- Generalized Cross Entropy (Zhang & Sabuncu)<br>- Symmetric Cross Entropy (Wang et al.)<br>- Cleanlab (Confident Learning baseline)<br>- Isolation Forest / Huber Loss | - Noisy CIFAR-10 / CIFAR-100 (symmetric & asymmetric 20%–60%)<br>- Clothing1M / WebVision (real noise)<br>- Corrupted California Housing (regression) |
| **RAO** | Resource-Aware Optimization | - Standard Adam / AdamW ($32\text{-bit}$)<br>- SGD with Momentum ($32\text{-bit}$)<br>- Adafactor<br>- bitsandbytes 8-bit Adam (where CPU-compatible) | - ResNet-18 / MobileNetV3 (image)<br>- Mini-Transformer / GPT-2 small (language)<br>- Large Tabular MLP benchmarks |
| **ULC** | Coordinated Adaptation | - Sequential naive combination of baselines<br>- Uncoordinated greedy pipelines | - Synthetic Non-Stationary Dirty Stream (combined drift + label noise) |

### 2.3 Statistical Rigor & Significance Testing
- **Target SC-SCI-04 (Multi-Seed Replicates)**: Benchmark evaluations must run over a minimum of **5 independent, randomly sampled seeds** (recommended: 10 seeds).
- **Target SC-SCI-05 (Dispersion Reporting)**: Reporting only mean values is forbidden. Every metric must report the mean accompanied by standard deviation, 95% bootstrap confidence intervals, and interquartile range (IQR).
- **Target SC-SCI-06 (Hypothesis Testing)**: Claims of algorithm superiority must be validated using paired two-tailed statistical tests (e.g., Wilcoxon signed-rank test for non-parametric distributions or paired Student's t-test where normality is established) with a significance threshold of $\alpha = 0.01$.
- **Target SC-SCI-07 (Compulsory Negative Results)**: If an algorithm fails to outperform a baseline, degrades on specific data regimes, or experiences instability, this negative result must be formally published in the benchmark report. Hiding or deleting negative results is a violation of research governance.

---

## 3. Engineering & Performance Success Criteria

All performance targets are calibrated for commodity, standard CPU hardware (e.g., 4-core to 8-core modern x86_64 / ARM64 processors with 8 GB to 16 GB RAM).

```
+-------------------------------------------------------------------------------------------------------+
|                                    ENGINEERING PERFORMANCE TARGETS                                    |
+--------------------------+--------------------------------+-------------------------------------------+
| Metric                   | Engineering Target Threshold   | Verification Method                       |
+--------------------------+--------------------------------+-------------------------------------------+
| RAO Memory Reduction     | >= 30% to 50% state reduction  | Memory profiling via memory_profiler and  |
|                          | vs. standard 32-bit Adam       | tracemalloc on standardized model weights |
| ALA Drift Detection Lag  | <= 100 samples detection lag   | Measured step delta on synthetic drift    |
|                          | on abrupt concept drift        | benchmark generators (e.g. SEA concepts)  |
| RLA Noise Resilience     | Maintains >= 85% clean-label   | Test accuracy retained under 30% uniform  |
|                          | accuracy under 30% noise       | symmetric label noise on CIFAR-10/Tabular |
| CPU Step Latency         | <= 1.25x of standard baseline  | Benchmarked step wall-clock time on       |
|                          | compute overhead               | identical CPU runtime                     |
| Core Test Coverage       | >= 90% unit test coverage      | pytest --cov across all core modules      |
| Type Safety              | 100% strict compliance         | mypy --strict passing with zero errors    |
| CI Execution Speed       | <= 10 minutes total            | GitHub Actions standard 2-core CPU runner |
+--------------------------+--------------------------------+-------------------------------------------+
```

---

## 4. Developer Experience (DX) & Ergonomic Criteria

- **Target SC-DX-01 (Frictionless Onboarding)**: A new user must be able to install AdaptiveML, import an estimator or optimizer, train on a sample array, and obtain predictions in $\le 5$ lines of standard Python code:
  ```python
  import adaptiveml as aml
  import numpy as np

  X, y = np.random.randn(100, 10), np.random.randint(0, 2, 100)
  model = aml.rla.RobustClassifier()
  model.fit(X, y)
  predictions = model.predict(X)
  ```
- **Target SC-DX-02 (API Consistency)**:
  - All supervised estimators must implement scikit-learn standard estimator conventions (`fit`, `predict`, `predict_proba`, `score`, and `partial_fit` where streaming is supported).
  - All optimizers intended for neural networks must adhere to standard PyTorch `torch.optim.Optimizer` interface patterns while maintaining standalone fallback execution under pure NumPy.
- **Target SC-DX-03 (Documentation Quality)**:
  - 100% of public classes, methods, and functions must have Google-style docstrings with explicit type signatures, parameter descriptions, return specifications, and mathematical equation references where applicable.
  - Every pillar must provide a minimum of 2 complete, self-contained tutorial notebooks capable of executing entirely on a standard CPU within 3 minutes.
- **Target SC-DX-04 (Zero Mandatory Cloud or Hardware Dependencies)**:
  - The library must install and pass all tests without CUDA, ROCm, MPI, AWS SDKs, GCP SDKs, or network connectivity.

---

## 5. Software Quality & Installation Reliability

- **Target SC-ENG-01 (Installation Reliability)**: Zero installation failures across standard supported platforms:
  - Linux (x86_64, aarch64 / ARM64)
  - macOS (Apple Silicon / M-series and Intel)
  - Windows 10 / 11 (x86_64)
- **Target SC-ENG-02 (Dependency Isolation)**:
  - Mandatory runtime dependency footprint: Python standard library + `numpy >= 1.24.0`.
  - Optional framework integrations (`torch`, `scikit-learn`, `scipy`) must be strictly optional extras (`pip install adaptiveml[torch]`). Importing `adaptiveml` without PyTorch or scikit-learn installed must succeed cleanly without warning or error.
- **Target SC-ENG-03 (Packaging Standards)**:
  - Modern `pyproject.toml` configuration compliant with PEP 517 / PEP 518 / PEP 621.
  - Automated wheel builds and source distribution validation using `build` and `twine check`.

---

## 6. Phase Acceptance Gate Tracking

| Criterion Group | Gate Verification Phase | Mandatory Preconditions for Gate Sign-off |
| :--- | :--- | :--- |
| **Mathematical Formulation** | Phase 6 | Written convergence proofs or analytical formulations vetted by Scientific Review Board. |
| **Algorithmic Implementation** | Phases 8–11 | Modular unit-tested code with 90%+ coverage, strict typing, zero cross-pillar leakage. |
| **Scientific Validation** | Phase 12 | 5+ seeds, baseline comparisons, confidence intervals, negative results registry documented. |
| **Framework Integration** | Phase 13 | scikit-learn estimator tests passing; PyTorch optimizer hooks verified. |
| **Security & Release Audit** | Phase 16 | Legal clearance, trademark review, vulnerability scanning, license dependency audit clean. |
| **PyPI 1.0 General Release** | Phase 18 | All targets validated as achieved results in production environments. |

