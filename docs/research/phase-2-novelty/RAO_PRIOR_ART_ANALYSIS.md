# AdaptiveML — Pillar 3: RAO Prior-Art Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-004`  
> **Focus**: Resource-Aware Optimization, Memory-Efficient ML, Low-Memory Optimizers, CPU-First Execution

---

## 1. Deep Learning Training Memory Decomposition

To evaluate optimizer prior art accurately, total training memory must be decomposed into its four distinct constituent buffers:

$$\mathcal{M}_{\text{Total}} = \mathcal{M}_{\text{Weights}} + \mathcal{M}_{\text{Gradients}} + \mathcal{M}_{\text{Activations}} + \mathcal{M}_{\text{Optimizer States}}$$

For a neural network with $\Phi$ parameters trained in standard 32-bit single precision:
- **Weights ($\mathcal{M}_{\text{Weights}}$)**: $4\Phi\text{ bytes}$.
- **Gradients ($\mathcal{M}_{\text{Gradients}}$)**: $4\Phi\text{ bytes}$.
- **Activations ($\mathcal{M}_{\text{Activations}}$)**: $O(B \cdot L \cdot H)$ (scales with batch size $B$, sequence length $L$, layers/hidden dimension $H$; reducible via activation checkpointing).
- **Optimizer States ($\mathcal{M}_{\text{Optimizer}}$)**:
  - Standard SGD: $0\text{ bytes}$ (or $4\Phi\text{ bytes}$ with momentum).
  - Standard Adam / AdamW: $8\Phi\text{ bytes}$ ($4\Phi$ for first moment $m_t$ + $4\Phi$ for second moment $v_t$).

> [!IMPORTANT]
> In AdamW training, optimizer states consume **double the memory of the model weights themselves**. In fine-tuning regimes where activations are small, optimizer states represent **50% to 70% of peak runtime memory**.

---

## 2. Comprehensive Prior-Art Optimizer Survey

| Optimizer | Foundational Publication | Memory Complexity | State Buffers per Parameter | Convergence / Stability | Hardware / Platform Bottlenecks |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **SGD + Momentum** | Polyak (1964) | $4\Phi$ bytes | 1 state ($v_t \in \text{fp32}$) | Slower convergence on ill-conditioned loss surfaces | Pure CPU/GPU native; universal baseline |
| **Adam** | Kingma & Ba (ICLR 2015) | $8\Phi$ bytes | 2 states ($m_t, v_t \in \text{fp32}$) | Fast, robust convergence across architectures | Memory heavy; causes OOM on CPU/edge |
| **AdamW** | Loshchilov & Hutter (ICLR 2019) | $8\Phi$ bytes | 2 states ($m_t, v_t \in \text{fp32}$) | Decouples $L_2$ weight decay; standard SOTA baseline | Identical $8\Phi$ memory footprint to Adam |
| **Adafactor** | Shazeer & Stern (ICML 2018) | $O(R+C)$ for $R \times C$ | 0 first moment; factored 2nd moment row/col sums | Prone to stalls and divergence; requires complex warmups | Disables `foreach` vectorization in PyTorch; single-tensor loop CPU overhead |
| **Lion** | Chen et al. (Google 2023) | $4\Phi$ bytes | 1 state ($m_t \in \text{fp32}$) using $\text{sign}(\cdot)$ | Competitive with AdamW on large-scale models | Sensitive to small batch sizes; high gradient noise on tabular models |
| **8-bit Adam** | Dettmers et al. (ICLR 2022) | $2\Phi$ bytes | 2 states quantized to 8-bit non-linear buckets | Matches 32-bit Adam convergence on LLMs | Heavily dependent on CUDA; CPU backend requires AVX-512 and incurs dequantization latency |
| **GaLore** | Zhao et al. (NeurIPS 2024) | $O(2 r \Phi^{1/2})$ | Low-rank projected first and second moments | Theoretical convergence bounds; saves 65%–80% memory | Periodic SVD on CPU creates massive step latency spikes; fp16 SVD causes NaN crashes |

---

## 3. Deep Dive: Memory Compression Mechanisms

### 3.1 Block-wise Dynamic Quantization (bitsandbytes)
- **Mechanism**: Splits parameter tensors into blocks of $B = 2048$ elements. For each block:
  1. Finds absolute maximum: $c = \max(|x_i|)$.
  2. Normalizes: $\tilde{x}_i = x_i / c \in [-1, 1]$.
  3. Maps normalized values into an optimal non-linear 8-bit floating point or quantile codebook $\mathcal{Q}$.
  4. Stores the 8-bit quantized indices and the scalar scale $c \in \text{fp32}$.
- **Memory Footprint**: $1\text{ byte per parameter} + \frac{4}{2048}\text{ bytes overhead} \approx 1.002\Phi\text{ bytes}$ per state (total $2.004\Phi\text{ bytes}$ for AdamW, a **75% reduction** in optimizer state memory).
- **The CPU Gap in Prior Art**:
  - `bitsandbytes` implements custom CUDA kernels written in C++/CUDA.
  - Its CPU fallback relies on AVX2 / AVX-512 intrinsic instructions.
  - On developer laptops without AVX-512, Windows operating systems, or standard ARM64 CPU chips, installation frequently fails with `DLL load failed` or `illegal instruction` errors.

### 3.2 Matrix Factorization (Adafactor)
- **Mechanism**: For a 2D weight matrix $W \in \mathbb{R}^{R \times C}$, instead of storing the full running variance $V \in \mathbb{R}^{R \times C}$, it tracks:
  $$V_R = \frac{1}{C} \sum_{c=1}^C V_{r, c}, \quad V_C = \frac{1}{R} \sum_{r=1}^R V_{r, c}$$
  The reconstructed second moment is approximated as: $\hat{V}_{r, c} = \frac{V_{R, r} V_{C, c}}{\frac{1}{R \cdot C} \sum_{r, c} V_{r, c}}$.
- **Memory Footprint**: Reduces second moment storage from $R \times C$ to $R + C$.
- **Why it Stalls on Small Models**:
  - Drops first-moment momentum entirely ($m_t = 0$) to save an extra $4\Phi\text{ bytes}$.
  - On non-convex surfaces with high gradient curvature (e.g. tabular MLPs, small vision backbones), lack of momentum leads to severe gradient jitter and oscillation around local minima.

---

## 4. Prior-Art Conclusion for RAO

The concepts of optimizer state quantization (8-bit) and low-rank approximation (Adafactor/GaLore) are **established prior art**.

AdaptiveML's target contribution is:
1. **Zero-Compilation Pure Python/NumPy CPU Optimization**:
   Implementing block-wise memory reduction that runs on standard 2D NumPy arrays and PyTorch tensors without requiring C++ compilers, CUDA kernels, or specialized AVX-512 instruction flags.
2. **Momentum-Preserving Compression**:
   Retaining first-moment momentum tracking via compact integer quantization, avoiding the convergence instabilities of Adafactor.
