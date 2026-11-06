# AdaptiveML Production Operations — Checkpoint and Recovery Guide

## 1. Overview and Invariants

AdaptiveML provides enterprise-grade, cryptographically verified checkpoint serialization and disaster recovery for both streaming algorithms and deep learning models.

Key invariants:
1. **Zero-Bytecode Serialization:** Uses the HuggingFace `safetensors` standard. Pickling of executable Python code is strictly prohibited.
2. **Atomic Two-Phase Commits:** Checkpoint files are written to staging files (`.<name>.tmp.safetensors`) and verified before atomic OS-level file replacement (`os.replace`).
3. **Cryptographic SHA-256 Verification:** Checkpoints calculate a cryptographic SHA-256 hash on write, stored in `<name>.meta.json`. On load, the file digest is recomputed and compared before memory allocation.
4. **File Size Hard Limits:** Defaults to a maximum checkpoint file size of $5\text{ GB}$ to prevent memory exhaustion attacks.

---

## 2. Checkpointing Streaming Controllers

The [`UnifiedLearningControllerV4_1`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) supports full state persistence and restoration:

```python
from robust_adapt.state.serializer import save_state, load_state

# 1. Export controller state dictionary
state = controller.state_dict()

# 2. Persist with atomic write and SHA-256 checksum
save_state(
    "checkpoints/production_ulc.safetensors",
    state,
    metadata={"version": "1.0", "step": controller.total_steps},
)

# 3. Reload state with integrity verification
restored_state, metadata = load_state("checkpoints/production_ulc.safetensors")
controller.load_state_dict(restored_state)
```

---

## 3. Checkpointing PyTorch Integration Models

For PyTorch models running within AdaptiveML pipelines, use [`TorchCheckpointAdapter`](file:///c:/projects/AdaptiveML/adaptive_ml/integrations/torch_module.py):

```python
from robust_adapt.integrations import TorchCheckpointAdapter

adapter = TorchCheckpointAdapter(
    checkpoint_dir="checkpoints/torch_model",
    save_best_only=True,
    monitor="val_loss",
    mode="min",
)

# Save checkpoint
adapter.save(model, optimizer=optimizer, epoch=10, metrics={"val_loss": 0.245})

# Restore best checkpoint
checkpoint_info = adapter.load_best(model, optimizer=optimizer)
```

---

## 4. Disaster Recovery & Failure Triage

### 4.1 Checkpoint Integrity Verification Failure
If `load_state` raises:
```
SerializationError: Checkpoint integrity verification failed for ...: computed SHA-256 does not match metadata digest
```
**Cause:** The `.safetensors` binary file has experienced bit-rot, incomplete network transfer, or unauthorized file alteration.
**Action:**
1. Do not load corrupted state into running pipelines.
2. Revert to the previous verified checkpoint (e.g. `<name>_prev.safetensors`).
3. If using distributed storage, re-download the checkpoint from primary storage.

### 4.2 Missing Metadata File
If `load_state` finds `.safetensors` but the `.meta.json` file is missing:
- A `SerializationWarning` is emitted to the diagnostic registry.
- Loading proceeds only if `verify_integrity=False` is explicitly passed; otherwise `load_state` rejects unauthenticated checkpoints.

### 4.3 In-Flight Process Termination During Save
Because writes are staged to temporary files (`.model.tmp.safetensors`) and replaced atomically, a process crash during `save_state` leaves the previous valid checkpoint completely intact.
