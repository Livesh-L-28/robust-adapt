# AdaptiveML Production Operations — Security Guide

## 1. Threat Model & Security Posture

Streaming ML pipelines operate in production environments exposed to untrusted user input, external network streams, and remote distributed storage. AdaptiveML enforces a comprehensive defensive security posture addressing four primary threat vectors:

1. **Arbitrary Code Execution via Deserialization:** Standard Python serialization (`pickle`) allows arbitrary remote code execution via object reduction payloads. AdaptiveML **prohibits** `pickle` in favor of SafeTensors.
2. **Checkpoint Tampering and Bit-Rot:** Binary weights stored in distributed object stores (S3, GCS) or shared filesystems can be maliciously modified or corrupted during transit.
3. **Denial-of-Service via Resource Exhaustion:** Maliciously oversized checkpoint payloads or unvalidated infinite input dimensions can trigger out-of-memory (OOM) crashes.
4. **Adversarial Label Poisoning:** Coordinated label inversion attacks attempt to degrade model accuracy and force controller state trapping.

---

## 2. Checkpoint Serialization Security

### 2.1 SafeTensors-First Format
All model parameters and arrays are serialized using the HuggingFace `safetensors` standard:
- **No executable bytecode:** SafeTensors files contain only a JSON header with tensor shapes/dtypes and raw contiguous binary buffer slices.
- **Zero-copy memory mapping:** Tensors can be memory-mapped directly without running arbitrary Python deserialization code.

### 2.2 SHA-256 Cryptographic Digest Verification
Every checkpoint saved through `save_state` generates a cryptographic SHA-256 digest stored in an adjacent `.meta.json` file:
```python
from robust_adapt.state.serializer import save_state, load_state

# Saves: model.safetensors and model.meta.json (containing _sha256 digest)
save_state("checkpoints/model.safetensors", state_dict)

# Validates: computes SHA-256 on load, raises SerializationError on bit mismatch
loaded_state, metadata = load_state("checkpoints/model.safetensors")
```
If an adversary or bit-rot alters even a single byte of `model.safetensors`, `load_state` immediately rejects the file with:
```
SerializationError: Checkpoint integrity verification failed for ...: computed SHA-256 does not match metadata digest
```

### 2.3 Atomic Two-Phase Commits
To prevent corrupt checkpoints resulting from power failure, SIGKILL, or network disconnection mid-write:
1. Files are written to hidden temporary files: `.<name>.tmp.safetensors` and `.<name>.tmp.meta.json`.
2. Both files are flushed and synced to disk.
3. Files are atomically renamed into place using OS-level atomic filesystem primitives (`os.replace`).

### 2.4 File Size Ceiling Limits
To guard against disk exhaustion and memory ballooning attacks, `load_state` strictly enforces a maximum file size limit (default: $5\text{ GB}$):
```python
if file_size > max_file_size_bytes:
    raise SerializationError(f"Checkpoint file size ({file_size} bytes) exceeds safety limit")
```

---

## 3. Input Validation Boundaries

All public entrypoints in AdaptiveML validate external inputs using defensive utilities in [`adaptive_ml/core/validation.py`](file:///c:/projects/AdaptiveML/adaptive_ml/core/validation.py):

| Function | Validation Enforced | Exception Raised |
| :--- | :--- | :--- |
| `check_array_2d` | Ensures 2D NumPy array, converts from array-like, rejects `NaN` / `Inf`, checks minimum rows | `ValidationError` |
| `check_labels_1d` | Ensures 1D integer labels, validates range $0 \le y_i < K$, checks length match | `ValidationError` |
| `check_probabilities` | Ensures valid probability range $[0, 1]$, validates row sums equal $1.0 \pm 10^{-3}$ | `ValidationError` |
| `check_non_negative_finite`| Enforces finite real numbers $\ge 0$ for time/memory budgets | `ValidationError` |

---

## 4. Supply Chain & Dependency Invariants

- Core library depends **only on `numpy>=1.24.0`**.
- Zero mandatory network access, zero outbound telemetry, zero background phone-home threads.
- All optional dependencies (PyTorch, scikit-learn, SafeTensors, pandas, Polars) use permissive open-source licenses (Apache-2.0, BSD-3-Clause, MIT).
- Automated dependency vulnerability scanning is integrated via `pip check`.
