# API Reference: Framework Integrations (`adaptive_ml.integrations`)

The `adaptive_ml.integrations` module provides native interoperability adapters, dataset contract validators, and specialized wrappers for Scikit-Learn and PyTorch.

---

## 1. Data Contracts & Ingestion

### `DatasetContract`
```python
@dataclass(frozen=True)
class DatasetContract:
    n_samples: int
    n_features: int
    dtype: np.dtype
    source_framework: str
    feature_names: Optional[Tuple[str, ...]] = None
    is_contiguous: bool = True
```

Immutable metadata contract describing ingested data containers (NumPy arrays, PyTorch Tensors, Pandas/Polars DataFrames).

### `inspect_dataset_contract`
```python
def inspect_dataset_contract(data: Any) -> DatasetContract
```
Inspects an arbitrary dataset object without mutating or deeply copying it, returning a standardized `DatasetContract`.

### `to_numpy`
```python
def to_numpy(
    data: Any,
    dtype: Optional[Union[np.dtype, type]] = None,
    ensure_2d: bool = False,
    ensure_1d: bool = False,
    copy: bool = False,
    name: str = "data",
) -> np.ndarray
```
Converts incoming data structures (PyTorch Tensors, Pandas Series/DataFrames, Polars DataFrames/Series, Python lists) into validated C-contiguous NumPy arrays.

### `to_tensor`
```python
def to_tensor(
    data: Any,
    dtype: Optional[Any] = None,
    device: Optional[Union[str, Any]] = None,
    copy: bool = False,
    name: str = "data",
) -> Any
```
Converts incoming data structures into PyTorch Tensors on the designated target device.

---

## 2. Scikit-Learn Estimator & Pipeline Adapters

### `SklearnAdaptiveClassifier`
```python
class SklearnAdaptiveClassifier(
    n_features: int = 10,
    n_classes: int = 2,
    grace_period: int = 200,
    delta: float = 1e-05,
    tau_tie: float = 0.05,
    enable_drift_detection: bool = True,
    replay_capacity: int = 5000,
    replay_ratio: float = 0.2,
    n_estimators: int = 1,
    random_state: Optional[int] = None,
) -> None
```

Scikit-learn compliant streaming classifier wrapping ALA Hoeffding Tree adaptive learning. Implements standard `BaseEstimator` and `ClassifierMixin` interfaces.

#### Methods
- **`fit(X, y)`**: Fits the estimator incrementally on initial batch.
- **`partial_fit(X, y, classes=None)`**: Streams batch updates with drift detection.
- **`predict(X) -> np.ndarray`**: Predicts target labels.
- **`predict_proba(X) -> np.ndarray`**: Predicts class posterior probabilities.
- **`score(X, y) -> float`**: Evaluates mean accuracy on validation data.

---

### `SklearnDriftDetectorTransformer`
```python
class SklearnDriftDetectorTransformer(
    delta: float = 0.002,
    monitored_feature_index: int = 0,
) -> None
```

Scikit-learn `TransformerMixin` monitoring continuous feature streams or residuals for statistical drift. Pass-through transformer emitting drift events without mutating input feature columns.

---

### `SklearnReliabilityFilter`
```python
class SklearnReliabilityFilter(
    n_classes: int = 2,
    min_reliability: float = 0.35,
) -> None
```

Scikit-learn pipeline transformer filtering out low-reliability noisy training instances prior to downstream model fitting.

---

## 3. PyTorch Deep Learning Utilities

### `VectorizedLowMemoryAdamW`
```python
class VectorizedLowMemoryAdamW(
    params: Iterable[Any],
    lr: float = 0.001,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 0.0001,
    weight_decay: float = 0.01,
    block_size: int = 64,
    max_grad_norm: Optional[float] = 1.0,
) -> None
```

High-performance CPU vectorized 8-bit dynamic block-quantized optimizer.
- Achieves $>73.4\%$ optimizer state RAM reduction over standard `torch.optim.AdamW`.
- Supports parameter groups, gradient clipping (`max_grad_norm`), and standard PyTorch learning rate schedulers (`torch.optim.lr_scheduler`).

#### Methods
- **`step(closure=None) -> Optional[float]`**: Executes vectorized block-quantized parameter update.
- **`get_state_memory_bytes() -> int`**: Returns exact memory consumed by quantized momentum and variance states.

---

### `TorchSymmetricCrossEntropyLoss`
```python
class TorchSymmetricCrossEntropyLoss(
    alpha: float = 1.0,
    beta: float = 0.5,
    eps: float = 1e-07,
) -> None
```

PyTorch `nn.Module` computing noise-robust Symmetric Cross Entropy:
$$\mathcal{L}_{\text{SCE}} = \alpha \, \mathcal{L}_{\text{CE}} + \beta \, \mathcal{L}_{\text{RCE}}$$

---

### `TorchGeneralizedCrossEntropyLoss`
```python
class TorchGeneralizedCrossEntropyLoss(
    q: float = 0.7,
    eps: float = 1e-07,
) -> None
```

PyTorch `nn.Module` computing Generalized Cross Entropy (GCE) loss for extreme asymmetric noise scenarios ($q \in (0, 1]$).

---

### `TorchTrainingBudgetHook`
```python
class TorchTrainingBudgetHook(
    budget_manager: DynamicResourceBudgetManager,
    max_history_len: int = 10000,
) -> None
```

PyTorch training step hook monitoring execution latency and memory usage per batch, signaling throttling directives when resource ceilings are breached.

---

### `TorchCheckpointAdapter`
```python
class TorchCheckpointAdapter
```

Utility adapter facilitating zero-copy conversion between PyTorch `state_dict` structures and SafeTensors serialized checkpoints.
