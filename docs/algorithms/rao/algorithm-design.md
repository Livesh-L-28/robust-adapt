# RAO 2.0: Algorithm Design & Mathematical Formulation

RAO 2.0 replaces standard 32-bit optimizer state representation with dynamic block quantization.

---

## 1. Dynamic Block Quantization Formulation

For each 2D+ parameter tensor $\theta$, elements are partitioned into contiguous blocks $b$ of size $B_q$ (default $B_q = 64$):

### First-Order Moment Quantization ($m_t$)
1. Compute the local maximum absolute value across block $b$:
   $$s_m^{(b)} = \frac{\max_{i \in b} |m_i|}{127} + \epsilon_{\text{quant}}$$
2. Quantize into signed 8-bit integers:
   $$q_m^{(b)} = \text{clip}\left(\left\lfloor \frac{m^{(b)}}{s_m^{(b)}} \right\rceil, -127, 127\right) \in \text{int8}$$

### Second-Order Moment Quantization ($v_t$)
Since second-order moments are strictly non-negative ($v_t \ge 0$):
1. Compute the local maximum across block $b$:
   $$s_v^{(b)} = \frac{\max_{i \in b} v_i}{255} + \epsilon_{\text{quant}}$$
2. Quantize into unsigned 8-bit integers:
   $$q_v^{(b)} = \text{clip}\left(\left\lfloor \frac{v^{(b)}}{s_v^{(b)}} \right\rceil, 0, 255\right) \in \text{uint8}$$

---

## 2. Parallel Tensor Update Equations

During `step()`, all block operations are executed using vectorized tensor math:

1. **Parallel Dequantization**:
   $$\tilde{m} = q_m \cdot s_m, \quad \tilde{v} = q_v \cdot s_v$$
2. **Standard Bias-Corrected Updates**:
   $$\tilde{m}_t = \beta_1 \tilde{m}_{t-1} + (1 - \beta_1) g_t$$
   $$\tilde{v}_t = \beta_2 \tilde{v}_{t-1} + (1 - \beta_2) g_t^2$$
   $$\hat{m}_t = \frac{\tilde{m}_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{\tilde{v}_t}{1 - \beta_2^t}$$
3. **Decoupled Weight Decay & Step**:
   $$\theta_t = \theta_{t-1} (1 - \eta \lambda) - \eta \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$
4. **Re-Quantization & State Preservation**:
   New scales $s_m, s_v$ are calculated in a single tensor reduction, and new integer states $q_m, q_v$ are copied back into place.
