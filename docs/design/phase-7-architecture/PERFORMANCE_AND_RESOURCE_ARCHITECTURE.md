# AdaptiveML — Performance & Resource Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-008`  
> **Last Updated**: 2026-11-01  
> **Scope**: CPU SIMD execution, cache alignment, zero-copy buffer reuse, and memory ceiling enforcement  
> **Target Audience**: Performance Engineers, Systems Programmers

---

## 1. CPU SIMD Optimization & Cache Alignment

AdaptiveML achieves performance comparable to compiled C++ libraries by structuring all numeric computation around modern CPU memory hierarchies:

### 1.1 Contiguous C-Order Layout
Every multi-dimensional array in AdaptiveML is strictly created with C-contiguous layout (`order='C'`). This guarantees that row-wise iterations traverse adjacent memory addresses:
- Minimizes CPU cache line misses (64-byte L1 data cache lines are saturated by 16 single-precision floats).
- Enables automatic compiler auto-vectorization across x86-64 (AVX-256, AVX-512) and ARM64 (NEON).

### 1.2 Block-Aligned Slicing ($B_q = 256$)
In `LowMemoryAdamW`, blocks of 256 elements align with exactly $256 \times 4\text{ bytes} = 1024\text{ bytes}$ (1 KB) of memory.
- A 1 KB block fits completely inside the smallest CPU L1 data cache (typically 32 KB to 48 KB per core).
- All element-wise operations (dequantization, EMA, square, clamp, requantization) complete within L1 cache before the block is written back to host RAM, eliminating main memory bus stalls.

---

## 2. Zero-Copy Buffer Reuse & Scratch Memory

To prevent high-frequency heap allocations and garbage collection thrashing in high-throughput streaming pipelines:

1. **Pre-Allocated Leaf Scratch Buffers**:
   - In `VectorizedHoeffdingTree`, temporary evaluation arrays (`left_counts`, `right_counts`, `gini_split`) are allocated once per tree instance in a reusable `_ScratchPad` struct rather than allocated dynamically inside split check loops.
2. **Quantization Strided Views**:
   - PyTorch parameters are flattened via `.view(-1)` and sliced via `.narrow()`, creating sub-views that share underlying storage without memory copies.
3. **In-Place Histogram Accumulation**:
   - Uses `np.add.at(target, indices, values)` for scatter accumulation directly into target tensors.

---

## 3. Host Memory Ceiling & Telemetry Architecture

To guarantee execution on low-memory edge devices or shared CPU workers without triggering OS OOM-killer termination:

```
+─────────────────────────────────────────────────────────────────────────────+
|                         MEMORY BUDGET ENFORCEMENT LOOP                      |
+─────────────────────────────────────────────────────────────────────────────+

                           Streaming Batch Arrival
                                      │
                         Check Host Virtual Memory
                                      │
                     Is Used RAM >= 0.85 * M_budget?
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼ (Yes)                               ▼ (No)
        ┌───────────────────────┐             ┌───────────────────────┐
        │  Dynamic Mitigation   │             │   Standard Execution  │
        │  1. Halve Batch Size  │             │   Run normal batch    │
        │  2. Double Accum Step │             │   update cycle        │
        │  3. Prune Old Replay  │             └───────────────────────┘
        └───────────────────────┘
```

1. **Memory Polling**: `adaptive_ml.core.telemetry` samples process Resident Set Size (RSS) via lightweight OS primitives (`GetProcessMemoryInfo` on Windows, `/proc/self/statm` on Linux) without external dependency overhead.
2. **Adaptive Replay Buffer Truncation**: Under severe memory pressure, the reservoir buffer capacity $M_{\text{buf}}$ is temporarily contracted by dropping samples from over-represented classes.

