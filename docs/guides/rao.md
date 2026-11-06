# Resource-Aware Optimization (RAO) User Guide

This guide covers memory-efficient optimizer state quantization, micro-batch scheduling, and CPU performance tuning.

---

## 1. LowMemoryAdamW Usage

`LowMemoryAdamW` drops optimizer state RAM by $73.44\%$ across NumPy and PyTorch models:

```python
import numpy as np
from robust_adapt.rao import LowMemoryAdamW

# Optimize parameters
weights = np.random.randn(1000).astype(np.float32)

class Wrapper:
    def __init__(self, arr):
        self.arr = arr
        self.grad = np.zeros_like(arr)
    @property
    def data(self):
        return self.arr

p = Wrapper(weights)
optimizer = LowMemoryAdamW([p], lr=0.01, block_size=64)

# Training step
p.grad = 0.1 * p.arr
optimizer.step()
```

---

## 2. Resource Budget Management

```python
from robust_adapt.rao.memory import ResourceBudget

# Set budget: max 256MB RAM and 20ms per step
budget = ResourceBudget(max_rss_mb=256.0, max_step_time_ms=20.0)

with budget.track_step():
    # Execute batch training operation
    pass

metrics = budget.get_telemetry()
print(f"Current Process RSS: {metrics['current_rss_mb']:.1f} MB")
```

---

## 3. Hardware Requirements, CPU Quantization Behavior & Measured Limitations

### 3.1 Supported CPU Architecture & Hardware Requirements
`LowMemoryAdamW` and `BlockQuantizer` are designed for pure-CPU, zero-dependency deployment:
- **Processor Architectures:** Standard 64-bit CPU architectures (x86_64, aarch64 / Apple Silicon).
- **Instruction Set Support:** Does not require AVX-512 or specialized vector extensions. NumPy SIMD acceleration (via OpenBLAS or MKL) is utilized automatically when present.
- **Memory Ceiling:** Functional in resource-constrained environments with as little as $512\text{ MB}$ total system RAM.
- **Mandatory Dependencies:** Python $\ge 3.10$ and NumPy $\ge 1.24.0$. Zero GPU or custom C++ compiler toolchains required.

### 3.2 Measured Execution Characteristics & Scaling Profile
Independent profiling on standard CPU hardware (x86_64, 32 logical cores, OpenBLAS) recorded the following sustained metrics across block size $B_q = 64$:

| Parameter Count ($P$) | Quantize + Dequantize Latency | Sustained Throughput | Optimizer State RAM (LowMemoryAdamW) | RAM Reduction vs FP32 |
| :--- | :--- | :--- | :--- | :--- |
| **$1,024$** ($1\text{K}$) | $0.118\text{ ms}$ | $8.68\text{ MParams/s}$ | $2,176\text{ Bytes}$ ($2.125\text{ B/param}$) | **$73.44\%$** |
| **$10,240$** ($10\text{K}$) | $1.039\text{ ms}$ | $9.86\text{ MParams/s}$ | $21,760\text{ Bytes}$ ($2.125\text{ B/param}$) | **$73.44\%$** |
| **$102,400$** ($100\text{K}$) | $10.362\text{ ms}$ | $9.88\text{ MParams/s}$ | $217,600\text{ Bytes}$ ($2.125\text{ B/param}$) | **$73.44\%$** |
| **$1,048,576$** ($1\text{M}$) | $107.736\text{ ms}$ | $9.73\text{ MParams/s}$ | $2,228,224\text{ Bytes}$ ($2.125\text{ B/param}$) | **$73.44\%$** |

### 3.3 Known Large-Model Limitations & Architectural Guidance
- **CPU Throughput Plateau:** Vectorized NumPy quantization sustains $\approx 9.7 - 9.9\text{ MParams/second}$ on CPU. For models under $1\text{M}$ parameters, quantization step latency is negligible ($<100\text{ ms}$).
- **Large-Model Limitation ($>5\text{M}$ Parameters):** For deep architectures exceeding $5\text{M}$ to $10\text{M}$ parameters, pure-CPU block quantization introduces non-negligible step latency ($>500\text{ ms}$ per step), creating a computational bottleneck during intensive iterative training.
- **When to Use PyTorch Integration:** For deep neural networks with large parameter counts trained on CUDA-capable accelerators, users should pair AdaptiveML with GPU-native 8-bit optimizers (such as `bitsandbytes` CUDA kernels) via the PyTorch integration adapter (`adaptive_ml.integrations.torch_optim`), rather than relying on pure-CPU NumPy quantization. `LowMemoryAdamW` remains optimal for CPU-first streaming, embedded inference, edge micro-servers, and tabular models where GPU acceleration is unavailable.
