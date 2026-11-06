# ALA 3.0: Adaptive Learning Algorithms Overview

**ALA (Adaptive Learning Algorithms)** provides continuous, online streaming classification algorithms capable of learning incrementally from infinite data streams while dynamically detecting and adapting to concept drift.

---

## 1. Key Capabilities

- **Streaming Hoeffding Trees (`AdaptiveClassifier`)**: Incremental decision tree induction that splits nodes based on mathematically proven statistical confidence bounds without retraining from scratch.
- **Statistical Drift Detection (`ReliabilityWeightedADWIN`)**: Adaptive windowing that dynamically sizes its window based on variance changes, detecting distribution shifts with bounded false positive rates.
- **Recurring Concept Retention (`RecurringConceptMemory`)**: Extracts statistical concept fingerprints (centroids, feature variances, class priors) and restores historical model checkpoints upon recurring distribution shifts.
- **Class-Stratified Replay (`ClassBalancedReservoirReplay`)**: Bounded memory buffer guaranteeing proportional retention across rare and frequent classes regardless of arrival sequence.

---

## 2. When to Use ALA

- Data arrives sequentially in unbounded data streams (e.g. sensor telemetry, clickstreams, log events).
- The underlying relationships between features and target labels shift over time.
- Periodic or seasonal operational patterns repeat (e.g. daily, weekly, or market cycles).
- Compute and memory are constrained, precluding periodic batch retraining from scratch.
