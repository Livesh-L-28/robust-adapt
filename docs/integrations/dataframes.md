# Tabular DataFrames Integration: Pandas & Polars

AdaptiveML provides high-performance data conversion utilities in `adaptive_ml.integrations` designed for zero-copy views, memory alignment, and robust numerical validation across Pandas and Polars DataFrames.

---

## 1. Supported DataFrame Ecosystems

| Source Framework | Type | `to_numpy()` Path | Performance Characteristics |
|:---|:---|:---|:---|
| **Pandas** | `pd.DataFrame`, `pd.Series` | Direct buffer access via `.to_numpy()` | Zero-copy view if homogeneous float64/float32; contiguous buffer conversion. |
| **Polars** | `pl.DataFrame`, `pl.Series` | Apache Arrow memory slice via `.to_numpy()` | Columnar-to-row layout conversion with strict SIMD alignment. |

---

## 2. Ingesting Pandas DataFrames

Pandas DataFrames can be passed directly to `to_numpy()` or to `DatasetContract` inspection:

```python
import pandas as pd
import numpy as np
from robust_adapt.integrations import to_numpy, inspect_dataset_contract
from robust_adapt.ala import ALA30AdaptiveLearner

# Construct sample DataFrame
df = pd.DataFrame({
    "feature_0": np.random.randn(100),
    "feature_1": np.random.randn(100),
    "target": np.random.randint(0, 2, size=100)
})

# Inspect contract
contract = inspect_dataset_contract(df[["feature_0", "feature_1"]])
print(f"Detected framework: {contract.source_framework}, shape: ({contract.n_samples}, {contract.n_features})")

# Convert to validated numpy array
X = to_numpy(df[["feature_0", "feature_1"]], ensure_2d=True, dtype=np.float64)
y = to_numpy(df["target"], ensure_1d=True, dtype=np.int64)

# Stream to AdaptiveML learner
learner = ALA30AdaptiveLearner(n_features=2, n_classes=2)
res = learner.fit_batch(X, y)
print(f"Accuracy: {res['accuracy'] * 100:.2f}%")
```

---

## 3. Ingesting Polars DataFrames

Polars provides high-speed columnar data processing. AdaptiveML converts Polars Arrow chunks into C-contiguous NumPy arrays without intermediary Python objects:

```python
import polars as pl
import numpy as np
from robust_adapt.integrations import to_numpy, inspect_dataset_contract

# Construct sample Polars DataFrame
pldf = pl.DataFrame({
    "x0": np.random.randn(100).tolist(),
    "x1": np.random.randn(100).tolist(),
})

contract = inspect_dataset_contract(pldf)
print(f"Polars Contract: samples={contract.n_samples}, features={contract.n_features}")

X_polars = to_numpy(pldf, ensure_2d=True, dtype=np.float64)
print(f"Converted shape: {X_polars.shape}, is_contiguous: {X_polars.flags['C_CONTIGUOUS']}")
```

---

## 4. Automatic Non-Finite & Dimension Validation

When converting DataFrames, `to_numpy` automatically performs safety checks:
- **`NaN` / `Inf` Detection**: Floating-point matrices with missing or non-finite values raise a typed `ValidationError` with informative diagnostic messages.
- **Dimensionality Enforcement**: Single-column Series/DataFrames can be forced to 1D (`ensure_1d=True`) or 2D (`ensure_2d=True`).
- **Contiguity Guarantee**: Ensures arrays are memory-contiguous for optimal SIMD and cache locality during Hoeffding tree updates and block quantization.
