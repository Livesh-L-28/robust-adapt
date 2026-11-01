# AdaptiveML

> **Adaptive, Robust, and Resource-Efficient Learning for Python**  
> *A modular, CPU-first, local-first Python algorithm library for non-stationary, noisy, and resource-constrained machine learning.*

---

## What is AdaptiveML?

**AdaptiveML** (`aml-core`) is an open-source algorithmic library developed in Python to complement existing machine learning and deep learning frameworks (such as NumPy, scikit-learn, and PyTorch).

Conventional machine learning assumes pristine, static datasets and high-memory cloud infrastructure. Real-world continuous deployments, edge devices, and resource-constrained environments frequently experience:

1. **Changing Data Distributions**: Concept drift degrades static models over time.
2. **Corrupted or Noisy Annotations**: Label errors undermine standard Empirical Risk Minimization (ERM).
3. **Severe Resource Constraints**: Large optimizer state footprints and heavy frameworks overwhelm commodity CPUs.

AdaptiveML delivers modular, mathematically grounded components engineered specifically for **local-first** and **CPU-first** execution.

---

## Core Product Pillars

AdaptiveML is structured around three autonomous, unbundled algorithm pillars and an optional dynamic coordination layer:

```
+-------------------------------------------------------------------------------+
|                       ULC: Unified Learning Controller                         |
|   (Optional coordination layer; balances drift, noise, and memory dynamics)   |
+-----------------------+-------------------------------+-----------------------+
                        |                               |
        +---------------+---------------+               |
        v                               v               v
+-------------------------------+ +-------------------+ +-----------------------+
|  ALA: Adaptive Learning       | |  RLA: Robust      | |  RAO: Resource-Aware  |
|  Algorithms                   | |  Learning         | |  Optimization         |
|  ---------------------------  | |  ---------------  | |  -------------------  |
|  - Reliability-Weighted ADWIN | |  - Margin Scorer  | |  - Block Quantized    |
|  - Incremental Updates        | |  - Robust Losses  | |    AdamW (int8/uint8) |
|  - Hoeffding Trees            | |  - Minority Class | |  - State RAM: -73.4%  |
|  - Balanced Replay Buffer     | |    Preservation   | |  - Gradient Acc.      |
+-------------------------------+ +-------------------+ +-----------------------+
```

1. **ALA — Adaptive Learning Algorithms**:
   Online concept drift detection and incremental learning. Features `ReliabilityWeightedADWIN` which filters false alarms during transient noise bursts, and `ClassBalancedReservoirReplay` ensuring extreme imbalance retention.
2. **RLA — Robust Learning Algorithms**:
   Robust learning under label noise and extreme class imbalance. Features `DensityAwareMarginScorer` which proves **Theorem 2** (preserving minority instances while filtering label noise), and bounded `SymmetricCrossEntropyLoss`.
3. **RAO — Resource-Aware Optimization**:
   High-efficiency training on commodity CPUs. Features `LowMemoryAdamW` achieving an exact **$73.44\%$ optimizer state memory reduction** ($2.125\text{ B/param}$ vs. $8.00\text{ B/param}$) via 8-bit dynamic block quantization.
4. **ULC — Unified Learning Controller**:
   Optional coordination engine resolving the drift vs. noise dilemma. Eliminates catastrophic model wipes under corrupting noise bursts through dual predictive-entropy arbitration.

Each pillar is completely decoupled and can be used independently.

---

## Installation

AdaptiveML requires **Python 3.10 or higher** and depends strictly on **NumPy**:

```bash
# Core installation from source or wheel
pip install aml-core

# With PyTorch support
pip install "aml-core[torch]"

# With scikit-learn support
pip install "aml-core[sklearn]"

# Complete installation with all optional adapters
pip install "aml-core[all]"
```

---

## 5-Minute Quickstart

```python
import numpy as np
from adaptive_ml.ala import AdaptiveClassifier

# Initialize incremental adaptive classifier
clf = AdaptiveClassifier(max_depth=5, grace_period=20)

# Simulate streaming batches with concept drift
X_batch = np.random.randn(50, 10).astype(np.float32)
y_batch = (X_batch[:, 0] > 0.0).astype(np.int64)

# Incremental update
metrics = clf.partial_fit(X_batch, y_batch)
print(f"Ingested {metrics['n_samples']} samples | Accuracy: {metrics['accuracy']:.1%}")

# Real-time inference
preds = clf.predict(X_batch[:5])
print("Predictions:", preds)
```

---

## Key Measured Results

All performance results are empirically grounded in multi-seed benchmarks recorded in [Phase 12 Benchmark Reports](docs/research/phase-12-benchmarking/BENCHMARK_REPORT.md):
- **Minority Recall Preserved**: On $100:1$ extreme imbalance with $20\%$ label noise, standard Cross-Entropy collapsed with $0.0\%$ minority recall. AdaptiveML achieved **$60.0\%$ minority recall** ($+60.0\%$) and elevated Macro $F_1$ from $0.659 \rightarrow 0.821$.
- **State Memory Reduced**: `LowMemoryAdamW` uses strictly **$2.125\text{ bytes/parameter}$** ($73.44\%$ memory reduction) with zero loss in convex convergence ($L_2 = 0.033$).
- **Zero False Wipes**: Under an $85\%$ noise burst, ULC prevented catastrophic model reset (0 wipes vs. 10 wipes in uncoordinated baselines) while filtering $83.2\%$ of corrupted samples.

---

## Documentation Navigation

- [Installation Guide](getting-started/installation.md)
- [Quickstart Guide](getting-started/quickstart.md)
- [Pillars & Concepts](concepts/adaptive-learning.md)
- [Interactive Tutorials](tutorials/01_your_first_workflow.md)
- [Benchmark Reports](docs/research/phase-12-benchmarking/BENCHMARK_REPORT.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [License (Apache-2.0)](LICENSE)
