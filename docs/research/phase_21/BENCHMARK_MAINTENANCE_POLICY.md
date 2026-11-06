# PHASE 21 DELIVERABLE 03 — BENCHMARK MAINTENANCE POLICY
## Repeatable Benchmark Suites, Versioned Streaming Datasets, Evaluation Metrics, and Anti-Drift Audit

**Document Identifier:** `docs/research/phase_21/BENCHMARK_MAINTENANCE_POLICY.md`<br>
**Phase:** 21 — Continuous R&D<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Benchmark Infrastructure Lead & Metric Integrity Officer<br>

---

## 1. Benchmark Integrity Policy & Anti-Drift Rule

> [!WARNING]
> **IMMUTABLE BENCHMARK POLICY:**<br>
> 1. **Zero Silent Benchmark Alterations:** Benchmark generator parameters, dataset splits, and random seed sequences are immutable.<br>
> 2. No benchmark definition shall be modified to artificially inflate performance metrics of a proposed algorithm.
> 3. New benchmarks must be introduced as additive suites with separate version identifiers (e.g. `BENCHMARK_V2`).

---

## 2. Standard Evaluation Metrics Suite

Every benchmark run must log the standard 15-dimensional evaluation vector:

```
+---------------------------------------------------------------------------------------------------------+
|                                    15-DIMENSIONAL BENCHMARK METRIC VECTOR                               |
+-------------------+-----------------------------------+-------------------------------------------------+
| Metric Category   | Individual Metric Name            | Mathematical Definition / Measurement Unit      |
+-------------------+-----------------------------------+-------------------------------------------------+
| Classification    | 1. Prequential Accuracy           | Running mean classification accuracy (%)        |
|                   | 2. Balanced Accuracy              | Macro-averaged recall across all classes        |
|                   | 3. Minority Precision             | Precision on class k=1 (Imbalance streams)      |
|                   | 4. Minority Recall                | Recall on class k=1 (Target: >= 70%)            |
|                   | 5. Macro F1-Score                 | Harmonic mean of precision and recall           |
|                   | 6. False Positive Rate            | FPR on negative instances under noise           |
+-------------------+-----------------------------------+-------------------------------------------------+
| Drift Dynamics    | 7. Drift Recovery Steps           | Prequential steps to return to >=95% baseline   |
|                   | 8. False Drift Alarm Rate         | Alarms per 1,000 steps in stationary stream     |
|                   | 9. Recurring Concept Speed        | Steps to restore historical concept state       |
+-------------------+-----------------------------------+-------------------------------------------------+
| Systems Efficiency| 10. Per-Sample Latency            | Mean step execution duration (microseconds)     |
|                   | 11. Streaming Throughput          | Samples processed per second on 1 CPU core      |
|                   | 12. Peak Process RSS Memory       | Maximum resident set size (Megabytes)           |
|                   | 13. Optimizer Buffer Memory       | Explicit tensor momentum buffer allocation      |
|                   | 14. Checkpoint Serialization Time | Time to serialize state dict via safetensors    |
|                   | 15. Checkpoint File Size          | Stored bytes on disk                            |
+-------------------+-----------------------------------+-------------------------------------------------+
```

---

## 3. Dataset Versioning & Storage Strategy

- **Synthetic Streams:** Standardized generators (`AgrawalStream`, `SeaStream`, `HyperplaneStream`) are seeded and parameterized in code to guarantee $100\%$ mathematical determinism across platforms.
- **Authentic Benchmark Datasets:** Real-world benchmark arrays (Credit Card Fraud, Forest Covertype) are checksummed via SHA-256 and hosted in immutable release archives with strict provenance manifests.
- **Result Archival:** All automated benchmark runs write raw JSON telemetry to `benchmarks/telemetry/run_{timestamp}_{git_hash}.json`.
