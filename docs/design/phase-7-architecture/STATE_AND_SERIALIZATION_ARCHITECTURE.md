# AdaptiveML — State Lifecycle & Serialization Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-006`  
> **Last Updated**: 2026-11-01  
> **Scope**: State persistence, checkpoint formats, memory snapshots, and safe deserialization  
> **Security Posture**: Zero Python `pickle` on untrusted input; safe binary + JSON serialization

---

## 1. State Lifecycle Architecture

AdaptiveML components maintain well-defined internal state lifecycles:

```
+─────────────────────────────────────────────────────────────────────────────+
|                            STATE LIFECYCLE PHASES                           |
+─────────────────────────────────────────────────────────────────────────────+

   1. UNINITIALIZED  ──►  2. INITIALIZED  ──►  3. ACTIVE_STREAMING
                                                     │         ▲
                                                     ▼         │
                                               4. CHECKPOINTED
                                                     │
                                                     ▼
                                               5. TERMINATED
```

1. **Uninitialized**: Configuration passed to `__init__`; buffers not yet allocated.
2. **Initialized**: Memory buffers allocated upon first call to `partial_fit` or `step` when feature dimensions ($d, C, p$) are verified.
3. **Active Streaming**: Dynamic state updates occur in-place during stream ingestion.
4. **Checkpointed**: State serialized to disk or snapshot buffer for fault recovery.
5. **Terminated**: Resources released; memory buffers deallocated.

---

## 2. Safe Serialization vs Pickle Prohibition

### 2.1 The Vulnerability of Python `pickle`
Standard Python serialization (`pickle`, `joblib`, `dill`) allows arbitrary object instantiation and is vulnerable to Remote Code Execution (RCE) via malicious payloads embedded in model files. Because AdaptiveML is designed for production streaming pipelines ingesting untrusted external data, **unvalidated pickle serialization is strictly prohibited**.

### 2.2 Dual-File Safe Storage Format
AdaptiveML serializes model state into a paired directory or zip bundle containing two safe files:

1. **`metadata.json` (Plain Text JSON)**:
   - Schema version (`"format_version": "1.0.0"`).
   - Component class identifier (`"component": "AdaptiveClassifier"`).
   - Hyperparameter configuration dictionary.
   - Symbolic tree structure (node IDs, split features, threshold values, child pointers).
   - Controller state and dwell counters.
2. **`tensors.safetensors` (or raw binary `.bin`)**:
   - Stores all multidimensional numeric arrays (leaf sufficient statistics $\mathbf{S}_u$, reservoir feature arrays $\mathbf{X}_{\text{buf}}$, quantized optimizer states $\tilde{\mathbf{m}}, \tilde{\mathbf{v}}$, and scales).
   - Header is strictly bounded JSON with byte offsets; data payload is pure raw contiguous C-order binary memory.
   - Zero code execution during deserialization.

---

## 3. Serialization Schema Specification

```json
{
  "format_version": "1.0.0",
  "library_version": "0.1.0.dev0",
  "created_at_utc": "2026-11-01T21:00:00Z",
  "component": "adaptive_ml.ala.AdaptiveClassifier",
  "hyperparameters": {
    "n_features": 64,
    "n_classes": 10,
    "grace_period": 200,
    "delta": 1e-5,
    "tau_tie": 0.05
  },
  "tree_topology": {
    "root_id": 0,
    "nodes": [
      {
        "id": 0,
        "is_leaf": false,
        "split_feature": 12,
        "split_threshold": 0.452,
        "left_child": 1,
        "right_child": 2
      },
      {
        "id": 1,
        "is_leaf": true,
        "n_samples": 412,
        "tensor_key": "leaf_stats_1"
      },
      {
        "id": 2,
        "is_leaf": true,
        "n_samples": 588,
        "tensor_key": "leaf_stats_2"
      }
    ]
  },
  "controller_state": {
    "current_state": "STABLE",
    "dwell_counter": 0
  }
}
```

---

## 4. Checkpoint, Rollback & Fault Recovery Mechanics

For online streaming systems where a sudden burst of corrupt data may temporarily degrade model quality before detection:
1. **Periodic Micro-Snapshots**: In-memory circular buffer retains the model state of $K_{\text{history}} = 3$ prior checkpoint intervals.
2. **Rollback Trigger**: If the ULC transition kernel detects a confirmed adversarial noise burst, the application can issue `controller.rollback()` to restore the last verified clean state prior to the anomaly.
3. **Atomic File Write**: Disk checkpoints are written to temporary files (`model.safetensors.tmp`) and renamed atomically (`os.replace`) to prevent corruption during unexpected process termination.

