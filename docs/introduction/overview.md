# Product Overview & Mission

## What is AdaptiveML?

**AdaptiveML** (distribution package: `aml-core`) is a production-grade Python library providing algorithms for **Adaptive, Robust, and Resource-Efficient Learning**.

Modern machine learning systems deployed in production environments operate in fundamentally non-stationary conditions. While traditional machine learning assumes identically and independently distributed (i.i.d.) data drawn from a static distribution, real-world data pipelines face:
- Shifts in user behavior, market regimes, or seasonal trends (concept drift).
- Imperfect human annotations, sensor degradation, and delayed labels (noisy data).
- Stringent memory ceilings on edge gateways or microservice pods (computational constraints).

AdaptiveML provides native streaming algorithms, statistical drift detectors, label reliability estimators, memory-quantized optimizers, and unified controllers to address these challenges.

---

## Complement, Not Replace

AdaptiveML is designed to **complement existing industry frameworks**:
- **NumPy**: AdaptiveML uses pure NumPy arrays as its primary data structure. Core algorithms execute without external overhead.
- **Scikit-Learn**: AdaptiveML estimators (`AdaptiveClassifier`, etc.) implement standard Scikit-Learn protocols (`fit`, `partial_fit`, `predict`, `predict_proba`, `get_params`, `set_params`) and integrate into Scikit-Learn pipelines.
- **PyTorch**: For deep neural architectures, AdaptiveML provides `VectorizedLowMemoryAdamW` (reducing optimizer state memory by $>71\%$) and custom loss functions (`TorchFocalLoss`, `TorchGeneralizedCrossEntropyLoss`).

AdaptiveML does not replace Scikit-Learn or PyTorch; it extends them into continuous, resource-constrained streaming domains.

---

## When to Use AdaptiveML

| Scenario | Suitable? | Recommended Approach |
| :--- | :--- | :--- |
| **Continuous Streaming Pipelines** | **Yes** | Use `AdaptiveClassifier` with `ReliabilityWeightedADWIN` or `UnifiedLearningControllerV5`. |
| **Severe Label Noise & Adversarial Inputs** | **Yes** | Use `MultiSignalReliabilityEngine` or `RLA30RobustLearner` to filter/downweight corrupt labels. |
| **Extreme Class Imbalance (<1% minority)** | **Yes** | Use `MinorityIntelligence20Learner` with dynamic false-positive budget thresholding. |
| **Large Neural Network Optimizer Memory Bottlenecks** | **Yes** | Replace `torch.optim.AdamW` with `VectorizedLowMemoryAdamW` for 73% RAM reduction. |
| **Static Offline Training on Clean Datasets** | *No* | Standard Scikit-Learn or PyTorch is simpler and fully sufficient. |
| **Distributed Multi-GPU Clusters (Megatron/FSDP)** | *No* | AdaptiveML is CPU-first and local-first; use specialized distributed frameworks. |
