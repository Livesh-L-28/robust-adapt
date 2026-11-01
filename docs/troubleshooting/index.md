# Troubleshooting Guide

Common issues and solutions when working with AdaptiveML (`aml-core`).

---

## 1. Installation Issues

### `ModuleNotFoundError: No module named 'torch'` or `'sklearn'`
- **Cause**: Core package installs strictly with NumPy. Optional framework adapters require their respective extras.
- **Solution**: Install the required extra:
  ```bash
  pip install "aml-core[torch]"
  # or
  pip install "aml-core[sklearn]"
  ```

---

## 2. Numerical Stability

### Loss exploding with SymmetricCrossEntropyLoss
- **Cause**: The Reverse Cross-Entropy (RCE) term $\beta \sum p_k \ln q_k$ can scale gradients when $\beta$ is set excessively high or when learning rate $\eta > 0.01$.
- **Solution**: Set $\beta \le 0.1$ and use standard AdamW learning rate ($\eta \approx 10^{-3}$).

### Quantizer block size error
- **Cause**: `block_size` in `LowMemoryAdamW` must be a power of two (e.g., 32, 64, 128, 256).
- **Solution**: Ensure `block_size` satisfies `(b & (b - 1)) == 0`.
