# AdaptiveML: Developer Problem Register

> **Document Status**: Authoritative Baseline (Phase 1 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-RES-003`  
> **Last Updated**: 2026-11-01  
> **Confidence Rating**: High (Directly evidenced across multiple GitHub issues/discussions) | Medium (Documented in research papers / engineering blogs) | Low (Single-instance developer report)

---

## 1. Problem Classification Matrix

| Problem ID | Pillar | Concise Problem Statement | Observed Frequency | Severity | Confidence | Existing Workaround | Core Unresolved Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PRB-ALA-001** | ALA | **Drift False Positives on Noisy Data**: ADWIN and statistical detectors fire false drift alarms when exposed to transient outliers or noisy samples. | Recurring (Multiple issues across River/Menelaus/Frouros) | High | **High** | Manually tuning detection sensitivity ($\delta$) down to extreme values ($10^{-5}$). | Causes unacceptable detection lag on genuine gradual concept drift; requires manual trial-and-error per dataset. |
| **PRB-ALA-002** | ALA | **Interpreter Bottleneck on Numerical Streams**: Dict-based streaming (`learn_one(x)`) incurs massive Python loop overhead when processing large numeric feature matrices. | Common (Discussed frequently in River GitHub discussions) | High | **High** | Batching using `pandas.DataFrame` via `learn_many` or converting to Cython/Rust custom loops. | Pandas introduces heavy memory allocations; standard 2D NumPy array matrix batching (`partial_fit`) is not natively first-class. |
| **PRB-ALA-003** | ALA | **Catastrophic Forgetting in Streaming Updates**: Incrementally updating a deployed model on new data causes it to catastrophically forget baseline patterns. | Ubiquitous (Core challenge in continual learning literature) | Critical | **High** | Retraining periodically from scratch on accumulated historical data; storing unbounded replay buffers. | Retraining is computationally expensive; unbounded replay buffers exhaust host RAM on edge devices. |
| **PRB-RLA-001** | RLA | **Minority-Class Pruning by Noise Filters**: Small-loss sample selection algorithms (Cleanlab / Confident Learning / MentorNet) discard legitimate minority-class samples as "label noise". | Recurring (Documented in ACL 2023 i-LNL paper & Cleanlab issues) | Critical | **High** | Manual human-in-the-loop inspection of flagged errors; manually re-adding high-loss minority instances. | Completely defeats automated data cleaning; impossible in real-time or large-scale pipelines. |
| **PRB-RLA-002** | RLA | **Inability to Filter Label Noise in Real-Time Streams**: Existing label curation frameworks require multi-pass out-of-fold cross-validation. | Ubiquitous (Cleanlab API limitation) | High | **High** | Accumulating large batches of data, training offline shadow models, and filtering data before offline retraining. | Incompatible with continuous learning; high compute cost; cannot protect an online model during training. |
| **PRB-RLA-003** | RLA | **Robust Loss Hyperparameter Brittleness**: Generalized Cross Entropy (GCE) and symmetric losses are highly sensitive to curvature parameters ($q$, $A, B$), collapsing training if misconfigured. | Common (Reported across academic benchmarks and PyTorch forums) | High | **Medium** | Extensive grid searches across noise parameters for each individual dataset. | Users cannot deploy robust losses in production without knowing the exact ground-truth noise rate in advance. |
| **PRB-RAO-001** | RAO | **Optimizer State Memory Bloat on CPU / Laptop Training**: Standard Adam maintains two 32-bit float accumulators per parameter, doubling or tripling memory consumption and causing OOM crashes. | Ubiquitous (Standard deep learning bottleneck) | Critical | **High** | Dropping down to SGD with momentum (sacrificing convergence speed) or using smaller batch sizes. | SGD fails on complex architectures; small batch sizes degrade gradient quality and throughput. |
| **PRB-RAO-002** | RAO | **Hardware Instruction Traps in 8-bit CPU Optimizers**: `bitsandbytes` CPU kernels fail to execute on systems without AVX2/AVX-512 instructions or on non-CUDA platforms. | Common (Persistent issues on bitsandbytes GitHub repo) | High | **High** | Compiling custom C++ binaries from source or abandoning low-memory optimizers on CPU. | High developer friction; breaks standard `pip install` on developer laptops and edge appliances. |
| **PRB-RAO-003** | RAO | **Adafactor Convergence Instability**: Adafactor reduces memory by dropping first-moment momentum and factoring second moments, but frequently exhibits unstable training or stalls. | Common (PyTorch forum discussions & Hugging Face issues) | High | **High** | Implementing complex learning rate warmups and aggressive update clipping thresholds. | Fails to match AdamW accuracy on small and medium models; requires manual tuning per architecture. |
| **PRB-ULC-001** | ULC | **Uncoordinated Drift vs. Noise Conflict**: When non-stationary data streams contain noisy labels, drift detectors interpret label noise as concept drift, triggering catastrophic retraining on corrupted data. | Observed Pattern (Reported in stream mining literature) | Critical | **High** | Writing ad-hoc custom heuristic scripts combining drift alerts with loss thresholding. | Fragile, error-prone glue code; no standardized, reusable algorithmic controller exists. |
| **PRB-ULC-002** | ULC | **Memory Exhaustion During Drift Retraining**: Triggering model retraining or expanding memory buffers in response to drift causes unexpected host RAM exhaustion on constrained nodes. | Observed Pattern (Edge ML and IoT deployments) | High | **Medium** | Setting hard arbitrary replay buffer limits; discarding data indiscriminately. | Indiscriminate buffer pruning discards critical anchor samples, accelerating catastrophic forgetting. |

---

## 2. Deep-Dive Analysis of Critical Tension Points

### 2.1 The Noise-vs-Imbalance Dilemma (PRB-RLA-001)
- **Mechanism**: In deep learning and gradient boosted models, sample loss $L(x_i, y_i)$ is used as a proxy for sample difficulty. Confident Learning and small-loss selection heuristics hypothesize:
  $$\text{If } L(x_i, y_i) > \tau \implies (x_i, y_i) \text{ is mislabeled or corrupt.}$$
- **The Failure Mode**: Minority-class samples located in sparse regions of the feature space naturally generate high initial training losses because the model has seen fewer supporting instances. 
- **The Consequence**: Applying naive noise filtering systematically deletes the tail distribution. In medical diagnosis or fraud detection, this results in catastrophic drops in minority-class recall.
- **AdaptiveML Opportunity**: Design an RLA density-aware sample reliability metric that computes margin confidence relative to local feature density, ensuring rare samples are protected from noise deletion.

### 2.2 The Drift-Noise Collision in Streams (PRB-ULC-001)
- **Mechanism**: Standard drift detectors (such as ADWIN) monitor the classification error rate $e_t \in \{0, 1\}$ over a dynamic window $W$.
- **The Failure Mode**: When a batch of noisy labels arrives, the error rate spikes temporarily:
  $$\Delta e = |\mu_{W_0} - \mu_{W_1}| > \epsilon_{\text{cut}} \implies \text{Drift Alert Triggered!}$$
- **The Consequence**: The detector alerts the system that a concept drift has occurred, prompting the model to reset its weights or aggressively adapt to the corrupted batch. The model overfits to corrupted noise, permanently destroying previously calibrated representations.
- **AdaptiveML Opportunity**: The Unified Learning Controller (ULC) must gate drift alerts with RLA sample reliability scores. If a sudden spike in error is driven by samples flagged as low-confidence noise, the ULC suppresses model resetting.
