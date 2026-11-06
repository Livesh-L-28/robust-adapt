# Optional Integrations & Extras

ROBUST-ADAPT isolates optional frameworks using Python dependency extras. If an optional feature is accessed when the required dependency is not installed, ROBUST-ADAPT raises a clear `ConfigurationError` explaining how to install the extra.

---

## 1. PyTorch Integration (`[torch]`)

Enables tensor-quantized optimizers and PyTorch loss functions.

```bash
pip install "robust-adapt[torch]"
```

Provides:
- `VectorizedLowMemoryAdamW`: 8-bit block-quantized AdamW for PyTorch parameters.
- `TorchFocalLoss` & `TorchGeneralizedCrossEntropyLoss`: Robust loss functions for noisy-label neural training.
- `TorchCheckpointAdapter`: Safe checkpoint conversion to PyTorch `state_dict`.

---

## 2. Scikit-Learn Integration (`[sklearn]`)

Enables integration into Scikit-Learn pipelines and transformers.

```bash
pip install "robust-adapt[sklearn]"
```

Provides:
- `SklearnAdaptiveClassifier`: Wrapper implementing `BaseEstimator` and `ClassifierMixin`.
- `SklearnDriftDetectorTransformer`: Transformer tracking stream drift inside a pipeline.
- `SklearnReliabilityFilter`: Sample-weighting filter for noisy data streams.

---

## 3. SafeTensors Persistence (`[safetensors]`)

Enables fast, zero-copy, zero-pickle binary tensor persistence.

```bash
pip install "robust-adapt[safetensors]"
```

Provides:
- `save_state(filepath, tensors, metadata, auth_key)`: Atomic twin-file serialization (`.safetensors` + `.meta.json`).
- `load_state(filepath, verify_integrity, auth_key)`: Verified loading with SHA-256 integrity and HMAC-SHA256 signatures.

---

## 4. Tabular DataFrames (`[dataframe]`)

Enables zero-copy and batch conversions between Pandas/Polars DataFrames and NumPy arrays.

```bash
pip install "robust-adapt[dataframe]"
```

Provides:
- Direct ingestion of Pandas `DataFrame` and Polars `DataFrame` into `DatasetContract`.
- Automatic column type validation and NumPy array conversion.
