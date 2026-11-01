# AdaptiveML — Phase 5: RAO Research Gap Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-004`  
> **Focus Pillar**: Pillar 3 — RAO (Resource-Aware Optimization)

---

## 1. Candidate Research Gaps in RAO

```
+-------------------------------------------------------------------------------------------------------+
|                                    RAO RESEARCH GAP INVENTORY                                         |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| Gap ID  | Candidate Gap Title               | Failure Mode       | Priority Rank    | Classification  |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| **RAO-G1**| The CPU Quantization Latency/Trap | Compilation failure| **P0 (Critical)**| Systems / Eng   |
| **RAO-G2**| Adafactor Momentum-Drop Collapse  | Convergence stall  | **P1 (High)**    | Mathematical    |
| **RAO-G3**| Dynamic Memory-Budget Adaptation  | OOM on RAM spike   | **P2 (Medium)**  | Systems         |
| **RAO-G4**| GaLore SVD CPU Latency Spikes     | Step latency stall | **P2 (Medium)**  | Algorithmic     |
+---------+-----------------------------------+--------------------+------------------+-----------------+
```

---

## 2. In-Depth Analysis: GAP RAO-G1 (The CPU Quantization Barrier)

### 2.1 The Platform Barrier in Existing Low-Memory Optimizers
- **The Reality**: Standard AdamW consumes $8\text{ bytes per parameter}$ in state memory. To avoid OOM crashes during local training, practitioners attempt to use 8-bit optimizers like `bitsandbytes.optim.AdamW8bit`.
- **The Breakdown**: `bitsandbytes` is architected for CUDA GPUs. Its CPU backend is implemented in C++ and explicitly requires **AVX2 or AVX-512 instruction sets**.
  - On standard developer laptops lacking AVX-512, Windows machines without specific MSVC runtime DLLs, or ARM64 development boards (Raspberry Pi, Apple Silicon), `bitsandbytes` crashes with `Illegal Instruction` or dynamic link loader failures.
- **Target Gap**: Formulating **`LowMemoryAdamW`** — a pure Python/NumPy/PyTorch optimizer state compression mechanism utilizing block-wise dynamic scaling and symmetric integer mapping:
  $$\tilde{m}_i = \text{round}\left( \frac{m_i}{\text{scale}_B} \cdot 127 \right) \in \text{int8}$$
  executed entirely via vectorized tensor operations without requiring external C/C++ compilation.

---

## 3. In-Depth Analysis: GAP RAO-G2 (Adafactor Momentum-Drop Collapse)

### 3.1 The Breakdown in Momentum-Free Optimization
- Adafactor achieves sublinear second-moment memory ($O(R+C)$) by factoring row and column variance. However, to maximize memory savings, it **drops the first moment entirely ($\beta_1 = 0$)**.
- On non-convex surfaces with high stochastic gradient variance (common in deep neural networks and tabular MLPs), the lack of momentum causes the optimization path to oscillate erratically, frequently stalling in sharp local plateaus.
- **Target Gap**: Investigating whether retaining a **quantized 8-bit first moment ($m_t \in \text{int8}$)** restores full AdamW-level convergence trajectories while still saving 50% of optimizer state memory relative to standard 32-bit AdamW.
