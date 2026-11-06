# AdaptiveML Stage 9 — Adapter Interface Specification

**Document Identifier**: `STAGE-9-SPEC-001`<br>
**Distribution Name**: `aml-core`<br>
**Namespace**: `adaptive_ml`<br>
**Version**: `0.1.0.dev0`<br>
**Status**: SPECIFICATION COMPLETE<br>
**Date**: November 6, 2026<br>
**Governance**: DEF-004 Remains Open (Phase 17 & Phase 18 locked)

---

## 1. Overview & Scope

This document specifies the exact programming interfaces, method signatures, parameter types, error handling behaviors, and invariants for AdaptiveML's framework adapters.

Adapters act as the bridge between external framework ecosystems (scikit-learn, PyTorch, DataFrames) and AdaptiveML's internal four-pillar learning architecture.

---

## 2. Data Interoperability Interfaces (`adaptive_ml.integrations.data`)

### 2.1 Function: `to_numpy`
Converts arbitrary input representations (NumPy arrays, PyTorch tensors, pandas DataFrames/Series, Polars DataFrames/Series, Python nested lists) into standardized 1D or 2D NumPy arrays.

```python
def to_numpy(
    data: Any,
    dtype: Optional[np.dtype] = None,
    ensure_2d: bool = False,
    ensure_1d: bool = False,
    copy: bool = False,
    name: str = "data",
) -> np.ndarray
```

#### Contracts & Invariants:
1. **PyTorch Tensors**: Calls `.detach().cpu().numpy()`. If `copy=True`, executes `.copy()`.
2. **pandas DataFrame / Series**: Calls `.to_numpy(dtype=dtype, copy=copy)`. Missing values (`NaN`, `None`) raise [`ValidationError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py).
3. **Polars DataFrame / Series**: Calls `.to_numpy()`.
4. **Zero Unintended Mutation**: Never mutates the caller's input object in-place.
5. **Dimensionality Checks**: If `ensure_2d=True`, verifies `ndim == 2` (or reshapes `(N,)` to `(N, 1)` if single-feature). If `ensure_1d=True`, verifies or flattens to 1D vector of length $N$.

### 2.2 Function: `to_tensor`
Converts arbitrary input representations into a PyTorch Tensor with explicit device and dtype placement.

```python
def to_tensor(
    data: Any,
    dtype: Optional["torch.dtype"] = None,
    device: Optional[Union[str, "torch.device"]] = None,
    copy: bool = False,
    name: str = "data",
) -> "torch.Tensor"
```

#### Contracts & Invariants:
1. When input is already a PyTorch Tensor, avoids memory reallocation unless `copy=True` or `device`/`dtype` conversion is requested.
2. When input is a NumPy array of matching dtype, uses zero-copy `torch.from_numpy(arr)` if contiguous.
3. If PyTorch is not installed, raises an explicit `ImportError` explaining how to install `aml-core[torch]`.

---

## 3. Scikit-Learn Adapter Specifications (`adaptive_ml.integrations.sklearn`)

### 3.1 Class: `SklearnAdaptiveClassifier`
```python
class SklearnAdaptiveClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        n_features: int = 10,
        n_classes: int = 2,
        grace_period: int = 200,
        delta: float = 1e-5,
        tau_tie: float = 0.05,
        enable_drift_detection: bool = True,
        replay_capacity: int = 5000,
        replay_ratio: float = 0.2,
        n_estimators: int = 1,
        random_state: Optional[int] = None,
    )
```

#### Invariants & Scikit-Learn Contracts:
1. **`get_params(deep=True)` & `set_params(**params)`**: Implements pure estimator cloning compatibility. Calling `sklearn.base.clone(clf)` creates a pristine, un-fitted instance with identical hyperparameters and `_estimator = None`.
2. **`classes_` Attribute**: Set to `np.arange(self.n_classes)` upon the first `fit()` or `partial_fit()` call.
3. **`n_features_in_` Attribute**: Verified and recorded on first fit.
4. **`partial_fit(X, y, classes=None, sample_weight=None)`**: Fully incremental streaming update. Supports `classes` parameter as required by scikit-learn streaming estimators.
5. **`predict_proba(X)`**: Returns valid posterior probability matrix of shape $(N, K)$ where row sums equal $1.0 \pm 10^{-6}$.
6. **`score(X, y)`**: Evaluates mean accuracy on $(X, y)$.

### 3.2 Class: `SklearnDriftDetectorTransformer`
```python
class SklearnDriftDetectorTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, delta: float = 0.002, feature_indices: Optional[Sequence[int]] = None)
```
A transformer that can be embedded in a scikit-learn pipeline to monitor streaming feature distribution drift while passing data through transparently.

---

## 4. PyTorch Adapter Specifications (`adaptive_ml.integrations.torch_*`)

### 4.1 Class: `TorchSymmetricCrossEntropyLoss` (`torch_module.py`)
```python
class TorchSymmetricCrossEntropyLoss(nn.Module):
    def __init__(self, alpha: float = 1.0, beta: float = 0.5, eps: float = 1e-7)
    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        sample_weights: Optional[torch.Tensor] = None,
    ) -> torch.Tensor
```
- Ingests unnormalized logits $(N, K)$ and integer targets $(N,)$.
- Differentiable with respect to `logits`.
- Provides bounded gradients against corrupt targets via Reverse Cross Entropy.

### 4.2 Class: `TorchGeneralizedCrossEntropyLoss` (`torch_module.py`)
```python
class TorchGeneralizedCrossEntropyLoss(nn.Module):
    def __init__(self, q: float = 0.7, eps: float = 1e-7)
    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor
```
- Computes Box-Cox loss $\mathcal{L}_{\text{GCE}} = \frac{1 - p_y^q}{q}$.

### 4.3 Function: `create_torch_low_memory_adamw` (`torch_optim.py`)
```python
def create_torch_low_memory_adamw(
    params: Iterable[Any],
    lr: float = 1e-3,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    weight_decay: float = 1e-2,
    block_size: int = 256,
) -> LowMemoryAdamW
```
- Instantiates `LowMemoryAdamW` wrapping PyTorch tensor parameters with 8-bit dynamic quantization.

### 4.4 Class: `TorchTrainingBudgetHook` (`torch_callback.py`)
```python
class TorchTrainingBudgetHook:
    def __init__(self, budget_manager: DynamicResourceBudgetManager)
    def on_step_begin(self) -> None
    def on_step_end(self) -> BudgetState
```
- Tracks execution step timing and RSS memory in PyTorch training loops, throttling micro-batch sizes automatically.
