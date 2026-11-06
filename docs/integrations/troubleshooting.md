# Framework Integrations Troubleshooting & Diagnostics Guide

Common diagnostic procedures, error messages, and remediation steps when interfacing AdaptiveML with third-party frameworks.

---

## 1. Missing Optional Dependency Errors

AdaptiveML keeps its core lightweight and requires optional dependency extras to be installed explicitly.

### Error: `scikit-learn is required for SklearnAdaptiveClassifier`
**Cause:** `sklearn` is not installed in the active Python environment.<br>
**Solution:**
```bash
pip install "robust-adapt[sklearn]"
```

### Error: `PyTorch is required for TorchSymmetricCrossEntropyLoss`
**Cause:** `torch` is not installed in the active Python environment.<br>
**Solution:**
```bash
pip install "robust-adapt[torch]"
```

### Error: `safetensors is required for fast zero-copy state loading`
**Cause:** HuggingFace `safetensors` package is missing.<br>
**Solution:**
```bash
pip install "robust-adapt[safetensors]"
```

### Error: `pandas or polars is required for DataFrame conversion`
**Cause:** Tabular data extras have not been installed.<br>
**Solution:**
```bash
pip install "robust-adapt[dataframe]"
```

---

## 2. Data Validation & Dimensionality Errors

### Error: `ValidationError: X contains non-finite values (NaN or Inf)`
**Cause:** AdaptiveML decision trees and online drift detectors require valid finite real numbers.<br>
**Solution:**
- For scikit-learn pipelines, insert `SimpleImputer(strategy='mean')` prior to the classifier:
  ```python
  from sklearn.impute import SimpleImputer
  from sklearn.pipeline import Pipeline

  pipe = Pipeline([
      ("imputer", SimpleImputer(strategy="mean")),
      ("clf", SklearnAdaptiveClassifier(n_features=10, n_classes=2)),
  ])
  ```
- In pandas/Polars, clean data using `.fillna()` or `.drop_nulls()` before passing to `to_numpy()`.

### Error: `ValidationError: y must be a 1D vector, got 2D shape (N, 2)`
**Cause:** Target label vectors must have shape `(N,)` or single-column `(N, 1)`. Multi-column one-hot encoded targets are not accepted directly by decision trees.<br>
**Solution:**
- Convert one-hot vectors to class index integers using `np.argmax(y_onehot, axis=1)`.

---

## 3. Resource Budget & Memory Pressure Warnings

### State: `PRESSURE_WARNING` or `THROTTLED`
**Symptom:** `TorchTrainingBudgetHook` reports throttled state or decreases recommended batch size.<br>
**Cause:** Process RSS memory footprint exceeded `warning_threshold` (default 80%) of `max_memory_mb`, or per-step latency exceeded `max_step_time_ms`.<br>
**Remediation:**
1. Dynamically read `budget_hook.recommended_batch_size` in the training loop:
   ```python
   batch_size = budget_hook.recommended_batch_size
   ```
2. Enable 8-bit block-quantized optimizer via `create_torch_low_memory_adamw` to cut optimizer state memory by $75\%$.
3. Increase memory budget if host RAM permits:
   ```python
   budget_mgr = DynamicResourceBudgetManager(max_memory_mb=8192.0)
   ```

---

## 4. Checkpoint Loading Errors

### Error: `SerializationError: Checkpoint file not found: ...`
**Cause:** Checkpoint file path does not exist, or the `.meta.json` companion file is missing.<br>
**Remediation:**
Ensure both the binary tensor file (`<name>.safetensors`) and the metadata JSON file (`<name>.meta.json`) are located in the same directory.
