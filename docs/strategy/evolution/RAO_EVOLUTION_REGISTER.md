# Resource-Aware Optimization (RAO) — Evolution Register v2.0

**Document Identifier:** `DOC-STRAT-EVO-RAO-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Target Module:** [`adaptive_ml.rao`](file:///c:/projects/AdaptiveML/adaptive_ml/rao)<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Approved Strategic Architecture<br>

---

## 1. Pillar Mission & Architectural Scope

The **Resource-Aware Optimization (RAO)** pillar provides high-efficiency first-order optimization routines and memory management primitives designed for local-first, commodity CPU hardware execution.

In strict compliance with **Non-Functional Requirement NFR-PLAT-001 (CPU-First Execution)**, RAO routines execute natively on standard x86_64 and ARM64 processors without requiring CUDA compilers, specialized GPU drivers, or proprietary accelerators. In compliance with **Research Governance Rule 7 (Pillar Independence)**, RAO operates as a decoupled module in pure Python/NumPy, maintaining zero mandatory dependencies on ALA, RLA, or ULC.

---

## 2. Baseline Capabilities Grounded in Verified Source Evidence

The verified implementation of RAO in `aml-core==0.1.0.dev0` comprises four core modules in [`adaptive_ml/rao`](file:///c:/projects/AdaptiveML/adaptive_ml/rao):

```
adaptive_ml/rao/
├── __init__.py           # Exports BlockQuantizer, LowMemoryAdamW,
│                         # AdaptiveGradientAccumulator, ResourceBudget
├── quantizer.py          # BlockQuantizer (8-bit signed/unsigned block quantization)
├── adamw.py              # LowMemoryAdamW (Compressed optimizer state with decoupled weight decay)
├── accumulator.py        # AdaptiveGradientAccumulator (Dynamic step aggregation under memory budgets)
└── memory.py             # ResourceBudget (RAM profiling, RSS thresholds, budget manager)
```

### 2.1 Verified Capabilities Inventory

| Component | Source File & Class | Mathematical Formulation / Implementation | Verified Invariants |
| :--- | :--- | :--- | :--- |
| **Block Quantizer** | [`BlockQuantizer`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/quantizer.py#L22) in [`quantizer.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/quantizer.py) | Divides array into blocks of $B=64$ elements; computes local scale $s_b = \frac{\max \vert x_b \vert}{127}$; quantizes to `int8` with zero division protection via [`EPS_QUANT`](file:///c:/projects/AdaptiveML/adaptive_ml/core/constants.py) | Max quantization error bounded: $\| x - \hat{x} \|_\infty \le \frac{s_b}{2}$; exact dequantization in pure NumPy |
| **Low-Memory AdamW** | [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py#L26) in [`adamw.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) | Compresses first moment $m_t$ to `int8` and second moment $v_t$ to `uint8` with dynamic scaling; updates parameter vector: $\theta_{t+1} = \theta_t - \eta_t (\frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} + \lambda \theta_t)$ | Memory reduction: $50\%$ to $60\%$ vs standard 32-bit AdamW ($4\text{ bytes}$ state vs $8\text{ bytes}$ state per param); verified convergence on synthetic regression/classification |
| **Gradient Accumulator** | [`AdaptiveGradientAccumulator`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/accumulator.py#L20) in [`accumulator.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/accumulator.py) | Dynamic accumulation steps $K_t$ based on available system memory headroom; prevents OOM during micro-batching | Quantized gradient buffering; automatic flush when buffer reaches memory budget |
| **Resource Budget** | [`ResourceBudget`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/memory.py#L20) in [`memory.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/memory.py) | Monitors RSS memory via [`get_process_memory_bytes()`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py); enforces soft and hard memory ceilings | Native Win32 `psapi` x64 typed fallback without `psutil` (DEF-003 remediation); cross-platform Linux `/proc/self/statm` support |

---

## 3. Current Limitations

Based on empirical profiling from Phase 12 benchmarks and DEF-005 documentation findings:

1. **CPU Memory Bandwidth Bottlenecks:** On x86_64 commodity CPUs, [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) achieves an empirical throughput of $\approx 9.7 - 9.9\text{ MParams/s}$. Step execution latency scales linearly with parameter dimension:
   - $10\text{K}$ parameters ($40\text{ KB}$): $\approx 0.168\text{ ms}$
   - $100\text{K}$ parameters ($400\text{ KB}$): $\approx 1.25\text{ ms}$
   - $1\text{M}$ parameters ($4\text{ MB}$): $\approx 10.2\text{ ms}$
2. **L3 Cache Saturation on Large Models ($>5\text{M}$ parameters):** Models with $d > 5,000,000$ parameters ($>20\text{ MB}$ state) exceed CPU L3 cache capacities, incurring memory bus latency penalties ($\approx 50 - 75\text{ ms/step}$). Large deep learning models must be delegated to PyTorch GPU adapters.
3. **8-bit Linear Quantization Floor:** State storage is currently bounded at 8-bit integers ($1\text{ byte}$ per moment). Sub-8-bit formats (e.g., 4-bit NormalFloat NF4) have not been implemented in CPU-native NumPy.
4. **Unfactored Second Moments:** Second moments $v_t$ are stored per-parameter. Matrix parameters $W \in \mathbb{R}^{d_1 \times d_2}$ do not exploit row/column rank-1 factorizations (Adafactor style), which could reduce state from $\mathcal{O}(d_1 d_2)$ to $\mathcal{O}(d_1 + d_2)$.

---

## 4. RAO Evolution Itemized Register

| Identifier | Priority | Classification | Original Phase Mapping | Complexity | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-RAO-001** | **P1** | Proposed Enhancement | Phase 10 (RAO Development) | Medium | Low | Pure NumPy |
| **EVO-RAO-002** | **P1** | New Research | Phase 10 & Phase 12 | High | Medium | Phase 12 Benchmarks |
| **EVO-RAO-003** | **P2** | Proposed Enhancement | Phase 10 (RAO Development) | Medium | Low | [`adaptive_ml.rao.adamw`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) |
| **EVO-RAO-004** | **P2** | New Engineering | Phase 10 & Phase 13 | Medium | Low | PyTorch Adapter |
| **EVO-RAO-005** | **P3** | New Research | Phase 10 & Phase 21 | High | Medium | Mathematical Design |
| **EVO-RAO-006** | **P4** | Deferred Opportunity | Phase 21 (Continuous R&D) | Very High | High | Custom C/SIMD Extensions |

---

### Detailed Specification of Evolution Items

#### EVO-RAO-001: Factored Second-Moment Matrix Optimization (NumPy Adafactor)
- **Classification:** Proposed Enhancement
- **Priority:** P1
- **Phase Mapping:** Phase 10 (RAO Development)
- **Problem Statement:** For 2D weight matrices (e.g., transformer linear projections, large tabular MLPs), storing full second moments $V \in \mathbb{R}^{d_1 \times d_2}$ requires $d_1 \cdot d_2$ elements. For $d_1 = 4096, d_2 = 4096$, this consumes $16\text{ MB}$ per matrix in 8-bit quantization.
- **Mathematical Design Requirements:** Implement rank-1 factorization of second moments in pure NumPy:
  $$R_{i} = \frac{1}{d_2} \sum_{j=1}^{d_2} V_{i, j}, \quad C_{j} = \frac{1}{d_1} \sum_{i=1}^{d_1} V_{i, j}$$
  $$\widehat{V}_{i, j} = \frac{R_i C_j}{\frac{1}{d_1} \sum_k R_k}$$
  reducing memory complexity from $\mathcal{O}(d_1 d_2)$ to $\mathcal{O}(d_1 + d_2)$.
- **Implementation Dependencies:** Pure NumPy, [`adaptive_ml.rao.adamw`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py).
- **Validation Requirements:** Verify numerical stability and convergence on MLP and Mini-Transformer benchmark models.
- **Acceptance Criteria:** Second-moment memory consumption for 2D weights reduced by $\ge 80\%$; final convergence loss within $1.5\%$ of standard 32-bit AdamW.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RAO-002: CPU-Native 4-bit NormalFloat (NF4) State Quantization
- **Classification:** New Research
- **Priority:** P1
- **Phase Mapping:** Phase 10 (RAO Development) & Phase 12 (Benchmarking)
- **Problem Statement:** Existing 8-bit block quantization leaves state storage at 8 bits per moment. 4-bit quantization on GPU relies on specialized CUDA lookup tables not available on standard CPUs.
- **Research Hypothesis:** Formulating an information-theoretically optimal 4-bit quantile grid for standard normal distributions $\mathcal{N}(0, 1)$ combined with uint8 bit-packing in NumPy allows 4-bit optimizer states on CPU with minimal dequantization latency:
  $$q_i = \frac{1}{2} \left( Q_X\left(\frac{i}{2^k}\right) + Q_X\left(\frac{i+1}{2^k}\right) \right)$$
  packing two 4-bit state indices into a single `uint8` byte.
- **Relevant Prior Art:**
  - Dettmers et al. (2023): *QLoRA: Efficient Finetuning of Quantized LLMs* (NeurIPS).
  - Banner et al. (2019): *Post-Training 4-bit Quantization of Convolutional Networks for Rapid-Deployment*.
- **Validation Requirements:** Benchmarked on ResNet-18 weights ($11.7\text{M}$ parameters) on CPU.
- **Acceptance Criteria:** State memory reduced by $75\%$ compared to standard 32-bit AdamW ($2\text{ bytes}$ total state per param vs $8\text{ bytes}$); throughput $\ge 6.5\text{ MParams/s}$ on modern x86_64 CPU.
- **Estimated Complexity:** High.
- **Risk:** Medium (NumPy bit-shifting overhead on CPU without compiled C extensions).

---

#### EVO-RAO-003: Volatility-Gated Parameter Update Sparsification
- **Classification:** Proposed Enhancement
- **Priority:** P2
- **Phase Mapping:** Phase 10 (RAO Development)
- **Problem Statement:** In large parameter vectors, a substantial fraction of parameters experience negligible gradient magnitude ($\vert g_{t, j} \vert < \tau$) at any given step, yet are updated through full dequantization, vector math, and requantization.
- **Mathematical Design Requirements:** Implement dynamic top-$k$ or magnitude-thresholded update skipping:
  $$\Delta \theta_{t, j} = \begin{cases} -\eta_t u_{t, j} & \text{if } \vert g_{t, j} \vert \ge \tau_t \\ 0 & \text{otherwise} \end{cases}$$
  accumulating skipped gradients locally in low-precision buffers until threshold is breached.
- **Implementation Dependencies:** [`adaptive_ml.rao.adamw`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py).
- **Validation Requirements:** Test step wall-clock speedup across 10,000 steps on synthetic and real tabular workloads.
- **Acceptance Criteria:** Step execution latency reduced by $\ge 30\%$ when update sparsity $\ge 50\%$; final test error degradation $\le 0.3\%$.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RAO-004: In-Place Zero-Copy PyTorch Tensor Buffer Sharing
- **Classification:** New Engineering
- **Priority:** P2
- **Phase Mapping:** Phase 10 & Phase 13 (Framework Integrations)
- **Problem Statement:** In [`adaptive_ml/integrations/torch_optim.py`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_optim.py), converting PyTorch tensor parameters to NumPy arrays for optimizer step evaluation introduces array copying overhead when parameters are non-contiguous.
- **Mathematical Design Requirements:** Implement strict zero-copy array sharing using `from_numpy()` and `param.data.numpy()` memory views with guaranteed contiguous layout validation:
  $$\text{assert } \text{param.data.is_contiguous}()$$
- **Implementation Dependencies:** [`adaptive_ml.integrations.torch_optim`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_optim.py), PyTorch $\ge 2.0.0$.
- **Validation Requirements:** Profile step latency with `tracemalloc` and verify zero transient heap allocations during `step()`.
- **Acceptance Criteria:** Interoperability step overhead reduced by $\ge 20\%$; zero additional memory allocation per step.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-RAO-005: Stochastic Rounding with Unbiased Low-Precision Accumulators
- **Classification:** New Research
- **Priority:** P3
- **Phase Mapping:** Phase 10 & Phase 21 (Continuous R&D)
- **Problem Statement:** Deterministic rounding in sub-8-bit quantization introduces directional gradient bias, causing optimization to stall ("gradient vanishing in quantization") when gradient magnitudes fall below the quantization grid spacing $\Delta$.
- **Research Hypothesis:** Implementing hardware-efficient stochastic rounding guarantees mathematical unbiasedness $\mathbb{E}[\text{SR}(x)] = x$:
  $$\text{SR}(x) = \begin{cases} \lfloor x \rfloor & \text{with probability } 1 - \frac{x - \lfloor x \rfloor}{\Delta} \\ \lfloor x \rfloor + \Delta & \text{with probability } \frac{x - \lfloor x \rfloor}{\Delta} \end{cases}$$
  enabling steady convergence even under extreme 4-bit state compression.
- **Relevant Prior Art:**
  - Connolly et al. (2021): *Stochastic Rounding and Its Numerical Properties*.
  - Gupta et al. (2015): *Deep Learning with Limited Numerical Precision* (ICML).
- **Validation Requirements:** Mathematical proof of asymptotic convergence in `docs/research/` and empirical validation on convex quadratic objectives.
- **Acceptance Criteria:** Eliminates optimization stall under small learning rates ($\eta \le 10^{-5}$); provably zero first-order quantization bias.
- **Estimated Complexity:** High.
- **Risk:** Medium (pseudo-random number generation throughput overhead on CPU).

---

#### EVO-RAO-006: Hardware-Accelerated Vector Kernels (Optional C/SIMD Extensions)
- **Classification:** Deferred Opportunity
- **Priority:** P4
- **Phase Mapping:** Phase 21 (Continuous R&D)
- **Problem Statement:** Pure Python/NumPy block quantization is bounded by interpreted loop overhead and NumPy C-API call dispatch.
- **Proposed Exploration:** Explore optional standalone C / Cython / CFFI SIMD extension (AVX-512 / ARM Neon) compiled as optional wheel extras, preserving pure Python/NumPy as the authoritative fallback.
- **Acceptance Criteria:** Throughput on CPU increased to $\ge 35\text{ MParams/s}$; 100% test passing on machines without C extensions.
- **Estimated Complexity:** Very High.
- **Risk:** High (packaging and wheel compilation matrix complexity across platforms).
