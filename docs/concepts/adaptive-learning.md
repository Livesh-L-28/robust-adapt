# Concept: Adaptive Learning Algorithms (ALA)

The **Adaptive Learning Algorithms (ALA)** pillar addresses learning from continuous, non-stationary data streams where underlying probability distributions change over time ($P_t(X, y) \neq P_{t+1}(X, y)$).

---

## The Concept Drift Challenge

Standard machine learning models assume stationary data (Identically and Independently Distributed, IID). In production streams:
- **Abrupt Drift**: Sudden macroeconomic shifts, sensor failures, or regulatory changes.
- **Gradual Drift**: Seasonal behavioral variations or steady trend evolution.
- **Noise Bursts**: Transient sensor spikes or corrupted labels that masquerade as concept drift.

Unweighted drift detectors frequently mistake noise bursts for structural distribution changes, triggering catastrophic model resets.

---

## Core Algorithmic Components

### 1. Reliability-Weighted ADWIN (`ReliabilityWeightedADWIN`)
An extension of the classic ADWIN (Adaptive Windowing) algorithm that weights incoming prediction errors by an estimated sample reliability score $r_i \in [0, 1]$:
$$\bar{\mu}_{W} = \frac{\sum_{i \in W} r_i x_i}{\sum_{i \in W} r_i}$$
When transient label noise or high-entropy outliers occur, $r_i \approx 0$, preventing false drift triggers while retaining statistical sensitivity to genuine concept shifts.

### 2. Vectorized Hoeffding Tree (`VectorizedHoeffdingTree`)
An incremental decision tree that inspects streaming samples and splits nodes using the Hoeffding bound:
$$\epsilon = \sqrt{\frac{R^2 \ln(1 / \delta)}{2 n}}$$
The split criterion (information gain) is computed using vectorized NumPy matrix operations, achieving high streaming throughput on CPU without storing raw historical samples.

### 3. Class-Balanced Reservoir Replay (`ClassBalancedReservoirReplay`)
Maintains stratified reservoir buffers per class label. In extreme imbalance streams ($100:1$), minority instances are preserved perpetually using reservoir replacement invariants rather than being evicted by majority-class volume.
