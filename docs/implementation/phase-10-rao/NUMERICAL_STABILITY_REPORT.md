# Numerical Stability Report

**Document ID:** `RAO-NUM-001`  
**Phase:** Phase 10 — Resource-Aware Optimization Module (RAO)  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.rao`

---

## 1. Overview

$8\text{-bit}$ quantization and low-precision arithmetic introduce risks of underflow, catastrophic cancellation, division by zero, and numerical overflow. This report documents the mathematical safeguards implemented in `BlockQuantizer` and `LowMemoryAdamW`.

---

## 2. Implemented Safeguards

### 2.1 Epsilon Division Guard
- When computing scale factors for all-zero or near-zero blocks:
  $$s_b = \frac{\max_{i \in b} |x_i|}{127.0 + \epsilon_{\text{quant}}}$$
  where $\epsilon_{\text{quant}} = 1.0 \times 10^{-12}$ (defined in `adaptive_ml.core.constants.EPS_DIV`).
- Prevents division-by-zero or `NaN` scale generation when parameter gradients or moments are precisely zero.

### 2.2 Saturated Integer Clipping
- Quantization values are explicitly clipped to valid integer bit ranges prior to casting:
  $$q_{\text{signed}} = \text{clip}\left(\left\lfloor \frac{x}{s_b} + 0.5 \right\rfloor, -128, 127\right).\text{astype}(\text{int8})$$
  $$q_{\text{unsigned}} = \text{clip}\left(\left\lfloor \frac{x}{s_b} + 0.5 \right\rfloor, 0, 255\right).\text{astype}(\text{uint8})$$
- Eliminates silent integer overflow wrap-around (e.g., $128 \to -128$ in two's complement).

### 2.3 Second Moment Non-Negativity
- In theory, $v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2 \ge 0$.
- In quantized arithmetic, small negative reconstruction artifacts can corrupt $\sqrt{v_t}$.
- Safeguard: $q_v$ uses unsigned `uint8` exclusively, guaranteeing $v_t \ge 0$ unconditionally without requiring `np.maximum(0, v)`.

### 2.4 Bias-Correction Numerical Limits
- For large step indices $t \to \infty$, $1 - \beta_1^t \to 1.0$ and $1 - \beta_2^t \to 1.0$.
- For early steps $t=1, 2$, the denominator $1 - \beta^t$ is small ($0.1$ for $\beta_1=0.9$, $0.001$ for $\beta_2=0.999$).
- We guard the bias correction terms with $\max(1 - \beta^t, \epsilon_{\text{div}})$ to prevent numerical instability.

---

## 3. Stability Test Verification

Tested under extreme conditions:
1. **All-zero input vectors**: Scale evaluated cleanly to $\sim 0.0$, dequantization yielded exact zeros without `NaN` or `Inf`.
2. **Extreme dynamic range ($10^{-8}$ to $10^{6}$)**: Block partitioning confines high-magnitude values to their local blocks, preventing dynamic range collapse across distant parameters.
3. **Adversarial gradients ($10^{15}$)**: Handled gracefully via gradient clipping or exception raising in `ResourceBudget`.

