# ROBUST-ADAPT: Robust and Adaptive Learning with Resource-Efficient Optimization

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](community/license.md)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](getting-started/installation.md)
[![Distribution](https://img.shields.io/badge/distribution-robust--adapt-green)](getting-started/installation.md)
[![Typing](https://img.shields.io/badge/typing-PEP_561_compliant-brightgreen)](api/index.md)

**ROBUST-ADAPT** (`robust-adapt`) is an open-source Python machine learning algorithm library designed for robust, continuous, and resource-efficient learning under real-world operational constraints:

1. **Changing Data Distributions**: Continuous statistical shifts, abrupt and gradual concept drift, and recurring operational distributions.
2. **Imperfect and Noisy Feedback**: Mislabeled instances, asymmetric noise transitions, delayed ground-truth arrival, and severe class imbalance.
3. **Resource and Compute Constraints**: Memory-constrained edge devices, CPU-only servers, and low-latency microservice latency budgets ($<1\text{ ms}$).

ROBUST-ADAPT **complements existing ML frameworks** (such as NumPy, Scikit-Learn, and PyTorch)—it does not replace them.

> [!NOTE]
> **OFFICIAL IDENTITY & BACKWARD COMPATIBILITY**<br>
> Formerly developed under the engineering codename AdaptiveML (`aml-core`), this project is officially released under the brand **ROBUST-ADAPT** (distribution: `robust-adapt`, import namespace: `robust_adapt`). For backward compatibility, the historical `adaptive_ml` namespace remains available as a compatibility shim emitting a `FutureWarning`. See the [Migration Guide](migration/ADAPTIVEML_TO_ROBUST_ADAPT.md).

---

## The Five Algorithmic Pillars

```
+-----------------------------------------------------------------------------------+
|                        Unified Learning Controller (ULC-v5)                       |
|        Utility-Calibrated Cross-Pillar Coordination & Anti-Thrashing Backoff      |
+-----------------------------------------+-----------------------------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
        v                                 v                                 v
+-------------------------------+ +-------------------------------+ +-------------------------------+
| Adaptive Learning (ALA 3.0)   | | Robust Learning (RLA 3.0)     | | Resource Optimization (RAO 2.0|
| Fast Hoeffding Tree Induction | | Multi-Signal Reliability      | | Vectorized 8-Bit AdamW        |
| Reliability-Weighted ADWIN    | | Asymmetric Transition Defense | | Selective Quantization (>71%) |
| Recurring Concept Memory      | | Dynamic Noise Filtering       | | Atomic Resilient Checkpoints  |
+-------------------------------+ +-------------------------------+ +-------------------------------+
                                          |
                                          v
                        +-----------------------------------+
                        | Adaptive Minority Intelligence    |
                        | Online Beta-Binomial Prior Tracker|
                        | Dynamic False-Positive Budgets    |
                        +-----------------------------------+
```

- **ALA (Adaptive Learning Algorithms)**: Streaming prequential classification with bounded Hoeffding Tree induction, statistical drift detection (ADWIN), and recurring concept snapshot memory.
- **RLA (Robust Learning Algorithms)**: Multi-signal sample reliability estimation combining prediction margins, spatial $k$-NN consistency, and temporal stability to insulate learners against noisy feedback.
- **Adaptive Minority Intelligence**: Online Beta-Binomial prior tracking and dynamic false-positive budget thresholding for severe class imbalance ($<1\%$ minority).
- **RAO (Resource-Aware Optimization)**: CPU-first block-quantized optimizer (`VectorizedLowMemoryAdamW`) achieving $>71\%$ optimizer state RAM savings without C++ extensions or CUDA dependencies.
- **ULC (Unified Learning Controller)**: Hierarchical five-tier intervention arbitration (NOOP, Parameter Damping, Concept Restoration, Soft Replay Reset, Hard Reset) governed by calibrated expected utility scoring.

---

## Key Product Principles

- **Local-First & CPU-First**: Executes efficiently on standard CPUs ($5\ \mu\text{s}$ inference, $>23,000\text{ samples/sec}$ streaming throughput). No GPUs or cloud services required.
- **Modular & Decoupled**: Core algorithms require strictly `numpy>=1.24.0`. PyTorch, Scikit-Learn, and Pandas are purely optional extras.
- **Lightweight Footprint**: Sub-$110\text{ ms}$ cold import latency, $<37\text{ MB}$ resident memory, and strict $O(1)$ memory consumption ($<50\text{ MB}$ across $100,000+$ streaming samples).
- **Secure by Default**: Absolute **zero-pickle architecture**; state persistence utilizes binary SafeTensors with HMAC-SHA256 constant-time verification.
- **Zero Unprompted Telemetry**: Emits zero network traffic. Diagnostics use bounded in-memory ring buffers and standard Python logging with `NullHandler`.

---

## 30-Second Quickstart

```python
import numpy as np
from robust_adapt import AdaptiveClassifier, ReliabilityWeightedADWIN

# Initialize streaming adaptive classifier and drift detector
clf = AdaptiveClassifier(n_features=4, n_classes=2)
detector = ReliabilityWeightedADWIN(delta=0.002)

# Stream incoming data prequentially
X_stream = np.random.randn(100, 4)
y_stream = (X_stream[:, 0] + X_stream[:, 1] > 0).astype(int)

for i in range(len(X_stream)):
    x_i, y_i = X_stream[i : i + 1], y_stream[i : i + 1]

    # 1. Predict before learning (Prequential Evaluation)
    prob = clf.predict_proba(x_i)
    pred = int(np.argmax(prob))

    # 2. Track prediction error in drift detector
    is_error = float(pred != y_i[0])
    if detector.update(is_error):
        print(f"Concept drift detected at sample {i}!")

    # 3. Incrementally update classifier weights
    clf.partial_fit(x_i, y_i)
```

---

## Documentation Navigation

- [Installation Guide](getting-started/installation.md) — Pip instructions and optional framework extras.
- [5-Minute Quickstart](getting-started/quickstart.md) — Hands-on walkthrough for your first streaming pipeline.
- [Migration Guide](migration/ADAPTIVEML_TO_ROBUST_ADAPT.md) — Migrating from legacy AdaptiveML (`aml-core`) to ROBUST-ADAPT (`robust-adapt`).
- [Core Concepts](concepts/concept-drift.md) — Deep dive into drift, noisy labels, and minority preservation.
- [Algorithmic Guides](algorithms/ala/overview.md) — Technical specifications for ALA, RLA, RAO, Minority Intelligence, and ULC.
- [Public API Reference](api/index.md) — Complete signature documentation and type contracts.
- [Framework Integrations](integrations/index.md) — How to use ROBUST-ADAPT with PyTorch, Scikit-Learn, and Pandas.
- [Troubleshooting & FAQ](troubleshooting/index.md) — Diagnostic guides and common questions.

---

## Governance & Brand Notice

> [!NOTE]
> **ROBUST-ADAPT** is the official registered brand and project identity. The official distribution package identifier registered for installation is `robust-adapt`. This project is an independent open-source library distributed under the Apache License 2.0. See [License & Trademark Notice](community/license.md) for details.
