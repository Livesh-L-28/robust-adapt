# Troubleshooting & Diagnostics Guide

This guide provides practical diagnoses and resolutions for common runtime errors, configuration issues, and edge cases encountered when running AdaptiveML (`aml-core`).

---

## 1. Installation & Dependency Issues

### `SerializationError: State serialization requires the optional 'safetensors' dependency`
- **Root Cause:** Attempted to invoke `save_state` or `load_state` without installing the HuggingFace `safetensors` binary package.
- **Resolution:** Install the `safetensors` extra:
  ```bash
  pip install "robust-adapt[safetensors]"
  ```

### `ModuleNotFoundError: No module named 'torch'` or `'sklearn'`
- **Root Cause:** Attempted to use PyTorch modules (`TorchSymmetricCrossEntropyLoss`, `VectorizedLowMemoryAdamW`) or Scikit-Learn estimators (`SklearnAdaptiveClassifier`) in an environment where only core dependencies (`numpy`) are installed.
- **Resolution:** Install the appropriate framework extra:
  ```bash
  pip install "robust-adapt[torch]"     # For PyTorch components
  pip install "robust-adapt[sklearn]"   # For Scikit-learn pipelines
  pip install "robust-adapt[all]"       # For all optional integrations
  ```

---

## 2. Input Validation & Data Contracts

### `ValidationError: Expected 2D array, got 1D vector of shape (N,)`
- **Root Cause:** A 1D array was passed to an algorithm or prequential method expecting a 2D feature matrix $(N, D)$.
- **Resolution:** Use `adaptive_ml.integrations.to_numpy(data, ensure_2d=True)` or reshape using `data.reshape(-1, 1)`:
  ```python
  from robust_adapt.integrations import to_numpy
  X_clean = to_numpy(X_raw, ensure_2d=True)
  ```

### `ValidationError: Input matrix contains non-finite values (NaN or Inf)`
- **Root Cause:** Feature ingestion encountered missing data, divisions by zero, or numerical overflows before entering the model.
- **Resolution:** Impute missing values (e.g. via `SimpleImputer` in Scikit-Learn) before streaming to AdaptiveML. AdaptiveML strictly rejects `NaN` to prevent silent model poisoning.

---

## 3. Streaming Drift Adaptation & False Alarms

### The model triggers excessive drift resets during noisy stream phases
- **Root Cause:** ADWIN confidence parameter $\delta$ is set too aggressively (e.g., $\delta > 0.05$), or raw error rates fluctuate due to random label corruption rather than true concept drift.
- **Resolution:**
  1. Increase confidence parameter $\delta$ to a more conservative threshold: $\delta \in [0.001, 0.005]$.
  2. Increase Hoeffding tree `grace_period` (e.g., $100 \le N_g \le 500$) to allow sufficient statistics per leaf.
  3. Switch to `UnifiedLearningControllerV5` which utilizes **Spatial Discordance Gating** to distinguish true drift from noisy label spikes.

### The model experiences catastrophic forgetting on recurring patterns
- **Root Cause:** Standard drift detectors reset model parameters to zero upon drift, forgetting historical regimes.
- **Resolution:** Use `ALA30AdaptiveLearner` with `RecurringConceptMemory`. Ensure `similarity_threshold` is calibrated (recommended: $0.80 \le \tau_s \le 0.85$) to allow cosine matching against historical concept snapshots.

---

## 4. State Persistence & Checkpoint Errors

### `SerializationError: HMAC authentication failed for checkpoint`
- **Root Cause:** The secret `auth_key` provided to `load_state` does not match the key used during `save_state`, or the underlying binary file was altered in transit.
- **Resolution:** Ensure the identical 32-byte secret key is provided. If loading from untrusted storage, treat this exception as an active indicator of file corruption or tampering.

### `SerializationError: Checkpoint file exceeds size ceiling`
- **Root Cause:** The tensor file exceeds the $5\text{ GB}$ denial-of-service ceiling, or the `.meta.json` file exceeds $64\text{ MB}$.
- **Resolution:** If legitimately persisting an exceptionally large model, adjust the safety ceiling explicitly:
  ```python
  load_state("path/to/checkpoint", max_file_size_bytes=10 * 1024 * 1024 * 1024)  # 10 GB
  ```

---

## 5. Memory Optimization & RAO

### `LowMemoryAdamW` raises error on block size
- **Root Cause:** Dynamic block quantization requires power-of-two block sizes for SIMD alignment.
- **Resolution:** Set `block_size` to one of `[32, 64, 128, 256]`. The recommended default is `64` for optimal CPU L1 cache fit.

### Memory usage does not decrease when instantiating `LowMemoryAdamW`
- **Root Cause:** In PyTorch, optimizer states ($m_t, v_t$) are lazily allocated on the first `step()` call, not in `__init__`.
- **Resolution:** Measure memory usage *after* performing at least one forward pass, backward pass, and `optimizer.step()`. Use `optimizer.get_state_memory_bytes()` to inspect exact allocated state bytes.
