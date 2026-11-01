# RAO Known Limitations

**Document ID:** `RAO-LIM-001`  
**Phase:** Phase 10 — Resource-Aware Optimization Module (RAO)  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.rao`

---

## 1. Known Architectural & Numerical Limitations

### 1.1 Quantization Latency Overhead on Small Models
- For tiny parameter counts ($P < 1,000$), the compute overhead of quantizing and dequantizing momentum blocks on every step can outweigh memory bandwidth savings.
- **Guideline**: `LowMemoryAdamW` provides the greatest throughput and memory benefits for parameter counts $P \ge 10,000$.

### 1.2 Block Alignment & Padding
- Input parameter vectors whose lengths are not divisible by block size $B$ (default $64$) require padding during block quantization.
- While dynamically handled with zero memory leak, parameter flattening and slicing incurs minor index bookkeeping.

### 1.3 Non-Convex Splay in Highly Sparse Gradients
- When parameter gradients are extremely sparse (e.g., rare embedding lookups), block-level scaling factor calculation can dilute non-zero gradient moments across zero-valued neighbors in the same block.
- **Mitigation**: Future releases will introduce sparse embedding state exclusions or block grouping strategies.

### 1.4 Native PyTorch Compilation (TorchScript / `torch.compile`)
- `LowMemoryAdamW` currently performs CPU-vectorized NumPy operations during the dequantization update step. While fully compatible with standard PyTorch eager execution and autograd, it does not currently generate pure TorchScript IR or Triton kernels for `torch.compile`.

