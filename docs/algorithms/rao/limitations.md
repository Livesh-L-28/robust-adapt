# RAO 2.0: Known Limitations & Numerical Trade-offs

---

## 1. Sparse Gradients

- **Behavior**: `VectorizedLowMemoryAdamW` operates on dense block tensor memory layouts. Sparse gradient tensors (e.g. from `nn.Embedding` with `sparse=True`) are not supported.
- **Handling**: If a sparse gradient is encountered, `VectorizedLowMemoryAdamW` raises an explicit `ConfigurationError`.
- **Workaround**: Use dense embeddings (`sparse=False`).

## 2. Extremely Small Block Sizes ($B_q < 16$)

- **Behavior**: Choosing $B_q < 16$ increases the number of float32 scale factors ($2 \times \frac{4}{B_q}\text{ bytes/param}$), reducing memory savings.
- **Recommendation**: Use the default $B_q = 64$ for the optimal balance between quantization fidelity and memory savings ($>73\%$).

## 3. Microsecond-Sensitive Micro-Inference

- **Behavior**: Quantization and dequantization introduce a slight computational overhead ($\approx 15-25\%$ longer optimizer step execution).
- **Guidance**: When optimizer state memory is not constrained (e.g. models $<10,000$ parameters on large GPU clusters), native C++ `torch.optim.AdamW` may execute marginally faster.
