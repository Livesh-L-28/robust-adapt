# Phase 12 Benchmark Limitations

**Document ID:** `DOC-RES-P12-010`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Documented Empirical Limitations

In accordance with Phase 12 governance rules, the following limitations are explicitly noted:

1. **Synthetic Data Focus**:
   All Phase 12 benchmarks utilized controlled synthetic data generators (SEA concepts, rotating hyperplanes, synthetic Gaussian clusters). While synthetic data provides exact mathematical control over drift onset and corruption rates, real-world benchmarks on empirical datasets (e.g., CIFAR-10N, Web-Car, Covertype) will be conducted in downstream release evaluations.
2. **CPU Execution Boundaries**:
   Experiments were conducted on an x86_64 CPU workstation. Quantization overhead in Python loops is higher on CPU than what a dedicated C++/CUDA extension would achieve.
3. **Batch Size Sensitivity in Nearest-Neighbor Scoring**:
   Local density ratio $\delta_k = \rho_k / \bar{\rho}$ relies on batch-level sample density. For micro-batches with fewer than 10 samples, density estimation has higher statistical variance.

