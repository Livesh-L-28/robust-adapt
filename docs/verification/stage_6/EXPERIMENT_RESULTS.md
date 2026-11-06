# Stage 6: Empirical Experiment Results
## RAO 2.0 (Advanced Resource-Aware Optimization)

**Document Identifier:** `VERIF-STAGE-6-006`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Target Script:** [`experiments/stage_6_rao_v2/run_stage6_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_6_rao_v2/run_stage6_experiment.py)<br>
**Raw Evidence:** [`stage6_rao_results.json`](file:///c:/projects/AdaptiveML/experiments/stage_6_rao_v2/stage6_rao_results.json), [`stage6_rao_results.csv`](file:///c:/projects/AdaptiveML/experiments/stage_6_rao_v2/stage6_rao_results.csv)<br>
**Status:** `EMPIRICALLY VERIFIED`

---

## 1. Quantitative Benchmark Results

### 1.1 Dynamic Resource Budget Manager Throttling & Batch Scaling

The experiment injected a 3-step latency spike ($52 - 60\text{ ms}$, exceeding target ceiling of $40.0\text{ ms}$):

| Execution Phase | Injected Latency | Budget State | Active Batch Size | Operation Shedding |
| :--- | :--- | :--- | :--- | :--- |
| **Steps 1–5 (Normal)** | $14.0 - 16.0\text{ ms}$ | `NORMAL` | $512$ | Disabled |
| **Step 6 (Lag Spike 1)** | $55.0\text{ ms}$ | `CRITICAL` | $256$ (Halved) | **Active** |
| **Step 7 (Lag Spike 2)** | $60.0\text{ ms}$ | `CRITICAL` | $128$ (Halved) | **Active** |
| **Step 8 (Lag Spike 3)** | $52.0\text{ ms}$ | `CRITICAL` | $64$ (Halved) | **Active** |
| **Steps 9–10 (Recovery)** | $20.0\text{ ms}$ | `NORMAL` | $77$ (Recovering) | Disabled |

---

### 1.2 Execution Profiler Step Telemetry across 100 Optimizer Steps

| Telemetry Metric | Measured Value | Unit |
| :--- | :--- | :--- |
| **Profiled Steps** | 100 | steps |
| **Mean EMA Latency** | **$0.2550$** | ms / step |
| **Minimum Latency** | $0.1980$ | ms / step |
| **Maximum Latency** | $0.5800$ | ms / step |
| **Peak Resident RAM** | $207.72$ | MB |
| **Predictive Breach Alert Functional** | **True** | Triggers before hard SLA violation |

---

### 1.3 Hardware Acceleration Profile Detection

| Hardware Attribute | Detected System Property |
| :--- | :--- |
| **Host Operating System** | Windows |
| **Machine Architecture** | AMD64 |
| **Processor Type** | Intel64 Family 6 Model 183 Stepping 1, GenuineIntel |
| **Logical CPU Cores** | 32 cores |
| **CUDA Accelerator Present** | False (Graceful fallback) |
| **Apple MPS Present** | False |
| **Recommended Execution Backend** | `numpy_cpu` (Optimal pure-vectorized execution) |

---

### 1.4 Resilient Checkpoint Manager Corruption Recovery

| Event | Step Number | Checkpoint File Integrity | Recovery Action | Restored State Step |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Checkpoint** | 100 | Intact SHA-256 | Saved | — |
| **New Checkpoint** | 200 | **Truncated JSON Injected** | Corruption Caught | — |
| **Crash Recovery Execution** | — | Evaluated descending | **Rolled back to prior step** | **Step 100** |
