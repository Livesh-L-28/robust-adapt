# Frequently Asked Questions (FAQ)

---

## 1. General & Architecture

### What is ROBUST-ADAPT?
**ROBUST-ADAPT** (`robust-adapt`) is an open-source Python machine-learning library dedicated to **robust and adaptive learning with resource-efficient optimization**. It solves the challenges of non-stationary streams: concept drift, noisy/flipped labels, extreme class imbalance, and strict hardware memory bounds.

### Does ROBUST-ADAPT replace PyTorch or Scikit-Learn?
**No.** ROBUST-ADAPT is an algorithmic complement, not a framework replacement. It provides native estimator adapters for Scikit-Learn pipelines (`SklearnAdaptiveClassifier`), robust autograd losses and 8-bit optimizers for PyTorch (`VectorizedLowMemoryAdamW`), and high-speed array bridges for Pandas and Polars.

### Can ROBUST-ADAPT run on GPUs?
ROBUST-ADAPT is engineered **CPU-first and local-first**. While PyTorch integrations can optimize GPU-resident tensors, all core streaming decision trees, drift detectors, prior trackers, and quantizers run with maximum throughput on standard multi-core CPUs without requiring CUDA or GPU hardware.

---

## 2. Algorithms & Capabilities

### What are the "Five Pillars" of ROBUST-ADAPT?
1. **ALA (Adaptive Learning Algorithms):** Streaming Hoeffding tree induction, Reliability-Weighted ADWIN drift detection, and Recurring Concept Memory.
2. **RLA (Robust Learning Algorithms):** Multi-signal sample reliability scoring ($r_i$), asymmetric transition detection, and noise-tolerant losses ($\mathcal{L}_{\text{SCE}}, \mathcal{L}_{\text{GCE}}$).
3. **Minority Intelligence:** Online Beta-Binomial Bayesian prior tracking, sublinear cost scaling, and dynamic PID false-positive budget thresholding.
4. **RAO (Resource-Aware Optimization):** 8-bit dynamic block-quantized AdamW achieving $>73\%$ state RAM reduction and dynamic batch budget management.
5. **ULC (Unified Learning Controller):** Master multi-tier arbitration automaton evaluating expected utility $U = \text{Confidence} \times \text{Benefit} - \text{Cost}$ to disambiguate drift from noise.

### How does ROBUST-ADAPT handle recurring concept drift?
Unlike traditional streaming libraries that blindly reset the model whenever a drift is detected, **ALA 3.0** computes a statistical concept fingerprint. When a recurring regime returns (e.g. seasonal demand), it restores the historical tree snapshot from `RecurringConceptMemory`, avoiding the transient accuracy penalty of re-learning.

### How does ROBUST-ADAPT avoid catastrophic forgetting under label noise?
Under sudden noise bursts (e.g., sensor glitched and inverted labels), standard drift detectors falsely perceive a concept shift and destroy good model weights. The **ULC-v5 controller** uses **Spatial Discordance Gating** ($\mathcal{D}_s$) to verify whether prediction errors are topologically localized (true drift) or scattered/incoherent (noise burst), triggering sample abstention rather than model reset.

---

## 3. Performance & Memory

### How does `LowMemoryAdamW` achieve $>73\%$ RAM reduction?
Standard AdamW maintains two 32-bit float moments ($m_t, v_t$) per parameter, requiring 8 bytes per parameter. `LowMemoryAdamW` dynamically quantizes momentum into signed 8-bit integers (`int8`) and variance into unsigned 8-bit integers (`uint8`), grouped into small blocks of 64 or 256 parameters with per-block float32 scale factors.

### Is dynamic block quantization lossy?
While 8-bit quantization is numerically lossy, dynamic per-block scale normalization bounds quantization error. On standard deep learning benchmarks, models trained with `LowMemoryAdamW` achieve convergence accuracy identical to full 32-bit AdamW within standard seed variance.

---

## 4. Security, State & Checkpoints

### Why is Python's `pickle` banned in ROBUST-ADAPT?
Python's standard `pickle` deserialization executes arbitrary code bytecodes, creating severe remote code execution vulnerabilities (CWE-502) when loading weights from shared or untrusted storage. ROBUST-ADAPT exclusively uses the **HuggingFace SafeTensors** format: raw binary arrays indexed by immutable JSON headers.

### Can checkpoints be tampered with?
Not when using `auth_key`. ROBUST-ADAPT allows providing a 32-byte secret key during `save_state` and `load_state`. The system verifies an **HMAC-SHA256** signature in constant time (`hmac.compare_digest`). Any byte alteration triggers an immediate `SerializationError`.

### Does ROBUST-ADAPT log or transmit user data?
**Never.** ROBUST-ADAPT maintains a strict **zero-PII policy**. Telemetry logs only aggregate mathematical scalars (loss, latency, accuracy, step counts). Furthermore, ROBUST-ADAPT makes **zero outbound network connections**; it is $100\%$ air-gapped and offline ready.

---

## 5. Governance & Branding

### What is the relationship between ROBUST-ADAPT and AdaptiveML?
The project originated under the research working title **AdaptiveML** (with fallback identifier `aml-core`). To achieve complete trademark freedom and eliminate brand collision with commercial entities (*Adaptive ML, Inc.*), the project was permanently rebranded to **ROBUST-ADAPT**. The canonical distribution is **`robust-adapt`** and the primary import namespace is **`robust_adapt`**. Complete backward compatibility is maintained for the historical `adaptive_ml` namespace.

### What license applies to ROBUST-ADAPT?
ROBUST-ADAPT is licensed under the permissive **Apache License, Version 2.0**.
