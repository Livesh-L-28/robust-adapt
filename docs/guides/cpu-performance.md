# CPU Performance & Optimization Guide

AdaptiveML is designed from the ground up to achieve state-of-the-art streaming throughput on commodity multicore CPUs without requiring GPUs or distributed clusters.

---

## 1. Principles of CPU-First Streaming Performance

1. **Hardware-Efficient Micro-Batching:** Processing streams in small vectorized batches ($B \in [16, 64]$) provides $4\times$ to $12\times$ higher throughput than naive sample-by-sample loops by saturating CPU SIMD vector lanes (AVX2 / AVX-512).
2. **Contiguous Memory Alignment:** Core algorithms operate exclusively on C-contiguous NumPy float64 and float32 arrays, maximizing L1/L2 cache line hits and eliminating memory stride penalties.
3. **8-Bit State Compression:** By compressing optimizer momentum and variance vectors into 8-bit dynamic blocks, optimizer memory traffic through the CPU memory bus is reduced by $>73\%$.

---

## 2. Optimizing Streaming Tree Induction

When using Hoeffding Trees in high-throughput environments, choose vectorized tree variants and tune split evaluation frequencies:

```python
from robust_adapt.ala import VectorizedHoeffdingTree
import numpy as np

# Configure tree for maximum CPU throughput
tree = VectorizedHoeffdingTree(
    grace_period=200,      # Evaluate splits every 200 samples to amortize calculation
    delta=1e-5,            # Statistically conservative Hoeffding bound
    tau_tie=0.05,          # Tie-breaking margin
)

# Stream data in contiguous chunks
X_stream = np.random.randn(1000, 16).astype(np.float64, order="C")
y_stream = np.random.randint(0, 2, size=1000)

for i in range(0, 1000, 50):
    tree.update(X_stream[i : i + 50], y_stream[i : i + 50])
```

---

## 3. High-Throughput Neural Optimization (`VectorizedLowMemoryAdamW`)

In PyTorch streaming neural pipelines, `VectorizedLowMemoryAdamW` eliminates unrolled loop overhead by performing block quantization across flattened tensor contiguous memory:

```python
import torch
import torch.nn as nn
from robust_adapt.integrations import VectorizedLowMemoryAdamW

model = nn.Sequential(
    nn.Linear(32, 128),
    nn.ReLU(),
    nn.Linear(128, 2),
)

# Use block size of 64 or 256 for optimal CPU L1 cache fit
optimizer = VectorizedLowMemoryAdamW(
    model.parameters(),
    lr=1e-3,
    block_size=64,
    max_grad_norm=1.0,
)
```

---

## 4. Multi-Threading & Thread Affinity Configuration

For maximum deterministic latency on modern multicore CPUs:

```python
import os
import torch

# 1. Limit OpenMP / BLAS threads to physical cores to avoid context-switching thrash
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"

# 2. Configure PyTorch CPU intra-op threads
torch.set_num_threads(4)
torch.set_num_interop_threads(2)
```

---

## 5. Latency vs. Throughput Tuning Checklist

| Setting | Recommended Value | Impact |
| :--- | :--- | :--- |
| **Micro-batch size** | $16 \le B \le 64$ | Balances sub-10ms latency with SIMD vectorization. |
| **Data Memory Order** | `np.ascontiguousarray(X, dtype=np.float64)` | Guarantees sequential memory reads in C-order. |
| **Hoeffding `grace_period`** | $100 \le N_g \le 500$ | Reduces expensive entropy/information gain recomputations. |
| **Quantization `block_size`**| $64 \le b \le 256$ | Fits cleanly inside 32KB CPU L1 data cache. |
| **ADWIN `delta`** | $0.001 \le \delta \le 0.01$ | Prevents false-alarm variance resets while maintaining swift drift response. |
