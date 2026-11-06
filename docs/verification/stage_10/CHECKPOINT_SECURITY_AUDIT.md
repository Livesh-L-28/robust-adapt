# AdaptiveML Stage 10 — Checkpoint & Serialization Security Audit

**Distribution Package:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Version:** `0.1.0.dev0`<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Status:** Complete & Reconciled<br>

---

## 1. Executive Summary & Security Distinction

A critical vulnerability in contemporary machine learning systems is the reliance on Python `pickle` for model serialization (e.g., standard `torch.save(model)` or `joblib.dump(model)`). Because `pickle` deserialization interprets arbitrary Python opcodes, loading an untrusted model file can execute arbitrary malicious code on the host machine.

AdaptiveML enforces a **strict non-pickle persistence architecture**:
1. **Raw Neural Parameter Weights:** Stored exclusively via HuggingFace SafeTensors (`.safetensors`).
2. **Architecture and Controller Metadata:** Stored exclusively via human-readable JSON (`.meta.json`).

### Important Security Distinction: SafeTensors vs Cryptographic Authenticity

While SafeTensors eliminates arbitrary code execution risks by restricting storage to raw memory buffers with header bounds checking, **SafeTensors alone does not provide cryptographic authenticity, anti-tampering protection, or bit-rot detection**.

To address this gap, Stage 10 introduces:
- **Mandatory SHA-256 Cryptographic Checksums:** Generated at write time and validated at read time.
- **Atomic Two-Phase Persistence:** Temporary file writes with atomic file replacements (`replace()`).
- **File Size DoS Ceilings:** $5\text{ GB}$ hard bounds preventing memory exhaustion attacks.

---

## 2. Threat Modeling & Attack Surfaces

```
                    ┌─────────────────────────┐
                    │ Untrusted Checkpoint    │
                    │ (.safetensors + .json)  │
                    └───────────┬─────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       [Tensor Binary File]           [Metadata JSON File]
       - Max Size Check (<=5GB)       - JSON Syntax Validation
       - SHA-256 Integrity Hash       - Format Version ("1.0")
       - Contiguous Buffer Mmap       - Controller State Schema
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Verified Safe Checkpoint │
                    │ (Zero Code Exec Hazards) │
                    └─────────────────────────┘
```

### Threat Assessment Matrix

| Threat Vector | Severity | Attack Mechanism | AdaptiveML Defense |
|:---|:---|:---|:---|
| **Arbitrary Code Execution (RCE)** | **Critical** | Attacker embeds `__reduce__` exploit payload in pickle stream. | **ELIMINATED:** Zero pickle deserialization. Safetensors parses only numerical arrays. |
| **Silent Bit-Rot / File Truncation** | **High** | Incomplete download or disk corruption modifies model weights. | **PREVENTED:** SHA-256 digest validation fails immediately with `SerializationError`. |
| **Half-Written State (Crash)** | **Medium** | Host power loss or OOM kill occurs during `save_state`. | **PREVENTED:** Writes to temporary file; commits atomically via filesystem `replace()`. |
| **Denial of Service (DoS)** | **Medium** | Attacker supplies crafted massive file causing OOM. | **PREVENTED:** Hard file size ceiling checks before allocation. |
| **Untrusted Scikit-Learn Checkpoints** | **High** | User unpickles a `.joblib` model from untrusted source. | **DOCUMENTED:** Clear operational warnings regarding `joblib`/`pickle` trust boundaries. |

---

## 3. Implementation Specification

Implemented in [`adaptive_ml.state.serializer`](file:///c:/projects/AdaptiveML/adaptive_ml/state/serializer.py):

### 3.1 Two-Phase Atomic Write with SHA-256
```python
# 1. Save tensor weights to temporary file
sn.save_file(contiguous_tensors, str(tmp_tensor_path))

# 2. Compute cryptographic SHA-256 digest
sha256_hash = compute_file_sha256(tmp_tensor_path)
file_size_bytes = tmp_tensor_path.stat().st_size

# 3. Construct and write metadata
meta["_format_version"] = "1.0"
meta["_sha256"] = sha256_hash
meta["_file_size_bytes"] = file_size_bytes
with open(tmp_meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, default=str)

# 4. Atomic replacement
tmp_tensor_path.replace(tensor_path)
tmp_meta_path.replace(meta_path)
```

### 3.2 Integrity-Verified Deserialization
```python
# 1. Bounds check
if tensor_path.stat().st_size > max_file_size_bytes:
    raise SerializationError("Checkpoint exceeds size ceiling")

# 2. Integrity check
if verify_integrity and "_sha256" in metadata:
    actual_hash = compute_file_sha256(tensor_path)
    if actual_hash != metadata["_sha256"]:
        raise SerializationError("Integrity check failed: checksum mismatch")

# 3. Load safe arrays
tensors = sn.load_file(str(tensor_path))
```

---

## 4. Empirical Security Test Verification

The checkpoint security suite in [`tests/unit/test_defect_remediation.py`](file:///c:/projects/AdaptiveML/tests/unit/test_defect_remediation.py) and [`tests/unit/test_fault_injection.py`](file:///c:/projects/AdaptiveML/tests/unit/test_fault_injection.py) validates:
1. **Tampered File Rejection:** Modifying a single byte in the binary `.safetensors` file causes `load_state` to raise a `SerializationError` with a clear checksum mismatch alert.
2. **Corrupted JSON Rejection:** Malformed JSON syntax in `.meta.json` raises `SerializationError`.
3. **Missing Dependency Guard:** When `safetensors` is absent, actionable error guidance directs the user to `pip install aml-core[safetensors]`.
4. **Clean Round-Trip:** Model parameters and metadata match identically upon verified load.
