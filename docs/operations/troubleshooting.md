# AdaptiveML Production Operations — Troubleshooting Guide

## 1. Quick Diagnostics Cheat Sheet

When diagnosing unexpected pipeline behavior, inspect the diagnostic log and controller state:
```python
from robust_adapt.core.diagnostics import get_diagnostic_events

# Print last 10 warnings or errors
for event in get_diagnostic_events(min_level="WARNING")[-10:]:
    print(f"[{event['timestamp']}] {event['component'].upper()} {event['level']}: {event['message']}")
```

---

## 2. Common Operational Issues & Remediation

### 2.1 Issue: `ValidationError: X must be a 2-dimensional array`
- **Symptom:** Single streaming sample raises `ValidationError: X must be a 2-dimensional array, got shape (8,)`.
- **Root Cause:** Passing a 1D feature vector directly to `step()`, `predict_proba()`, or `score_reliability()`.
- **Resolution:** Reshape input to 2D before ingestion:
  ```python
  X_sample = x.reshape(1, -1)  # shape becomes (1, D)
  controller.step(X_sample, np.array([y]))
  ```

### 2.2 Issue: `SerializationError: Checkpoint integrity verification failed`
- **Symptom:** Checkpoint loading fails during start-up or container restart.
- **Root Cause:** Bit-rot, truncated file write, or manual edits to `.safetensors` without updating `.meta.json`.
- **Resolution:**
  1. Restore checkpoint from backup or upstream object storage (S3/GCS).
  2. If manually inspecting weights, do not edit binary files with text editors.
  3. If unauthenticated recovery is explicitly required, pass `verify_integrity=False` to `load_state`.

### 2.3 Issue: `SerializationError: State serialization requires the optional 'safetensors' dependency`
- **Symptom:** Calling `save_state` raises `SerializationError`.
- **Root Cause:** Environment was installed with bare `pip install robust-adapt` without the serialization extra.
- **Resolution:** Install the extra:
  ```powershell
  pip install 'robust-adapt[safetensors]'
  ```

### 2.4 Issue: Controller State Stuck in `NOISE_BURST`
- **Symptom:** Telemetry reports `state: NOISE_BURST` for dozens of consecutive batches.
- **Root Cause:** Upstream sensor failure or adversarial stream where $>40\%$ of labels are corrupted.
- **Resolution:**
  1. The controller will automatically escape to `STABLE` after `max_noise_dwell` steps (default: 15).
  2. Check `controller.config.max_noise_dwell`.
  3. Inspect upstream data ingestion quality.
  4. If necessary, call `controller.reset()` to force immediate recovery to `STABLE`.

### 2.5 Issue: `n_retained_samples == 0` Across Consecutive Batches
- **Symptom:** No training updates occur because all incoming samples are filtered out.
- **Root Cause:** Directive `sample_filter_threshold` is higher than the reliability scores assigned by RLA.
- **Resolution:**
  1. Inspect `telemetry['mean_reliability']`. If very low ($<0.20$), labels do not match feature spatial neighborhoods.
  2. Tune `weight_margin` vs `weight_neighbor` in `MultiSignalReliabilityEngine`.
  3. Reset the reliability search index via `engine.clear()`.

### 2.6 Issue: Memory Creep in Custom Integration Scripts
- **Symptom:** Process RSS steadily increases over hours of streaming.
- **Root Cause:** Accumulating references to `telemetry` dicts or tensors in an unbounded Python `list` inside user training loops.
- **Resolution:**
  1. Do not store full `telemetry` dictionaries in unbounded lists.
  2. Use `collections.deque(maxlen=1000)` for application-level metric history.
  3. Delete intermediate PyTorch tensors or detach them from computation graphs (`t.detach().cpu().numpy()`).

### 2.7 Issue: PyTorch Memory Leak During Training
- **Symptom:** GPU/CPU memory climbs during iterative training with `TorchSymmetricCrossEntropyLoss`.
- **Root Cause:** Storing computation graphs across steps by holding references to `loss` rather than `loss.item()`.
- **Resolution:**
  ```python
  # Bad: holds reference to computation graph
  loss_history.append(loss)

  # Good: extracts raw float value
  loss_history.append(loss.item())
  ```
