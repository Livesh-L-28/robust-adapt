# AdaptiveML Stage 10 — Architecture Risk Register

**Distribution Package:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Version:** `0.1.0.dev0`<br>
**Git Baseline:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Status:** Complete & Reconciled<br>

---

## 1. Risk Register Summary

| Risk ID | Component | Risk Description | Severity | Likelihood | Pre-Stage 10 Status | Stage 10 Remediation Status |
|:---|:---|:---|:---|:---|:---|:---|
| **ARCH-001** | `TorchTrainingBudgetHook` | Unbounded `step_latencies` list in long-running training loops could cause linear heap memory growth over millions of steps. | **Medium** | High | Unbounded list | **RESOLVED:** Bounded ring buffer with `max_history_len` (default 10,000) implemented. |
| **ARCH-002** | `state.serializer` | SafeTensors eliminates pickle arbitrary code execution, but raw files lack cryptographic integrity verification against bit-rot or file tampering. | **Medium** | Low | Unchecked binary load | **RESOLVED:** SHA-256 integrity hash verification and file size checks added to checkpoint engine. |
| **ARCH-003** | `state.serializer` | Non-atomic write operations: directly writing checkpoint files risks file corruption if process terminates or crashes mid-write. | **Medium** | Low | Direct in-place write | **RESOLVED:** Atomic write via temporary file creation and atomic replacement (`replace()`). |
| **ARCH-004** | `rao.budget` | Unchecked non-positive or NaN execution latencies could corrupt moving averages under timing clock anomalies. | **Low** | Low | Permissive float input | **RESOLVED:** Strict numerical validation guards added to `evaluate_step()`. |
| **ARCH-005** | `ala.classifier` | Scikit-learn base classes imported eagerly when scikit-learn is present in global site-packages, pulling in pandas. | **Low** | High | Eager try/except | **RESOLVED:** Strict core-only execution paths preserved and verified via automated isolation tests. |

---

## 2. Detailed Risk Analysis & Remediation Strategy

### ARCH-001: Bounding Callback History in `TorchTrainingBudgetHook`
- **Root Cause:** `self.step_latencies.append(elapsed_ms)` grew monotonically with every forward-backward step. In training runs exceeding 1,000,000 steps, this retains megabytes of heap data unnecessarily.
- **Remediation:** Introduce `max_history_len: int = 10000`. When length reaches capacity, evict oldest items (`self.step_latencies.pop(0)` or bounded slice). Retain property access so tests and users access full history without breaking backward compatibility.

### ARCH-002: Cryptographic Checkpoint Integrity Verification
- **Root Cause:** SafeTensors validates tensor headers and shapes, but does not verify whether the binary buffer on disk has been corrupted by disk errors, partial downloads, or unauthorized modifications.
- **Remediation:** On `save_state`, compute the SHA-256 digest of the `.safetensors` binary file and record it in `metadata["_sha256"]`. On `load_state`, verify the computed SHA-256 digest against `metadata["_sha256"]` before returning tensor dictionaries, raising a typed `SerializationError` if a mismatch occurs.

### ARCH-003: Atomic Checkpoint Persistence
- **Root Cause:** Writing directly to the target file path risks leaving an invalid zero-byte or truncated file if the process is killed by an OOM killer or host shutdown mid-write.
- **Remediation:** Save tensors and metadata to temporary files in the same directory (`.<name>.tmp.safetensors`, `.<name>.tmp.meta.json`). Once both writes complete successfully, execute an atomic rename (`replace()`), guaranteeing that the checkpoint file is never in a half-written state.

### ARCH-004: Timing Guard in Dynamic Budget Manager
- **Root Cause:** System clock jumps or virtual machine time adjustments can yield negative or infinite step latency floats.
- **Remediation:** Explicitly check `if step_time_ms < 0.0 or math.isnan(step_time_ms) or math.isinf(step_time_ms): raise ValidationError(...)`.

### ARCH-005: Optional Dependency Import Isolation
- **Root Cause:** `import sklearn.base` in `adaptive_ml.ala.classifier` attempts an import at module load time. If scikit-learn is installed, it loads `sklearn` into `sys.modules`.
- **Remediation:** Document this behavior in the API stability policy. Ensure pure core components (`VectorizedHoeffdingTree`, `ReliabilityWeightedADWIN`, `ParetoArbitrator`) have zero optional imports, and verify that missing dependencies gracefully degrade.
