# Resource-Aware Optimization (RAO)

Resource-Aware Optimization (RAO) focuses on maximizing computational throughput and minimizing RAM/VRAM consumption in continuous streaming and deep learning environments.

---

## 1. The Optimizer State Bottleneck

When training neural networks with standard AdamW, the memory consumed by the optimizer often far exceeds the model parameters:

```
[ Model Parameters: float32 ] ---> 4 bytes / parameter
[ First Moment m_t: float32 ] ---> 4 bytes / parameter
[ Second Moment v_t: float32 ] --> 4 bytes / parameter
-------------------------------------------------------
Total Memory per Parameter    ---> 12 bytes / parameter
Optimizer Overhead            ---> 8 bytes / parameter (66.7% of total!)
```

For a 100-million parameter model:
- Model weights: $400\text{ MB}$
- Optimizer state: **$800\text{ MB}$**
- Combined footprint: **$1.2\text{ GB}$**

On edge devices, microservice pods, or constrained CPU instances, this optimizer state overhead frequently causes fatal Out-Of-Memory (OOM) failures.

---

## 2. 8-Bit Dynamic Block Quantization

AdaptiveML's `VectorizedLowMemoryAdamW` compresses optimizer moments into signed 8-bit integers (`int8`) and unsigned 8-bit integers (`uint8`) across contiguous blocks of size $B_q = 64$:

```
Continuous Parameter Tensor (2D+ Dense Weights)
[================================================================]
         |
         v Split into Blocks of size B_q = 64
[ Block 0 ] [ Block 1 ] [ Block 2 ] ... [ Block N ]
    |
    +---> Compute local max absolute value: s_m = max(|m|) / 127
    +---> Quantize: q_m = round(m / s_m) in [-127, 127] (int8)
    +---> Compute local max value: s_v = max(v) / 255
    +---> Quantize: q_v = round(v / s_v) in [0, 255] (uint8)
```

### Memory Footprint Comparison
| State Component | Standard 32-bit AdamW | VectorizedLowMemoryAdamW |
| :--- | :--- | :--- |
| First Moment $m$ | $4.00\text{ bytes}$ | $1.0625\text{ bytes}$ (`int8` + scale) |
| Second Moment $v$ | $4.00\text{ bytes}$ | $1.0625\text{ bytes}$ (`uint8` + scale) |
| **Total Optimizer RAM** | **$8.00\text{ bytes/param}$** | **$2.125\text{ bytes/param}$** |
| **Savings** | **Baseline** | **$>73.4\%$ Reduction** |

---

## 3. Selective Quantization

Not all parameters can tolerate 8-bit quantization without precision degradation:
- **2D+ Matrices (Linear weights, Conv kernels)**: Block-quantized to 8-bit. They contain thousands of weights, which dominate total RAM ($>99\%$) and exhibit high spatial redundancy.
- **1D Tensors (Biases, LayerNorm, BatchNorm)**: Maintained in full **32-bit floating point precision (`float32`)**. They represent $<1\%$ of total parameters but are hypersensitive to numeric rounding errors.

This selective policy delivers $>71\%$ total memory savings while preserving convergence curves matching uncompressed 32-bit AdamW.
