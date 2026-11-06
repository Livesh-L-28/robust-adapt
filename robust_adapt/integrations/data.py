"""Data interoperability layer supporting conversions between NumPy, pandas, Polars, and PyTorch.

Provides copy-conscious, device-aware, and validation-guarded data conversions
without coupling the core AdaptiveML algorithms to any external framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ValidationError

# Optional framework detection
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore[assignment]
    _PANDAS_AVAILABLE = False

try:
    import polars as pl
    _POLARS_AVAILABLE = True
except ImportError:
    pl = None  # type: ignore[assignment]
    _POLARS_AVAILABLE = False

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


@dataclass(frozen=True)
class DatasetContract:
    """Metadata specification describing an ingested dataset or streaming batch."""
    n_samples: int
    n_features: int
    dtype: np.dtype
    source_framework: str
    feature_names: Optional[Tuple[str, ...]] = None
    is_contiguous: bool = True


def to_numpy(
    data: Any,
    dtype: Optional[Union[np.dtype, type]] = None,
    ensure_2d: bool = False,
    ensure_1d: bool = False,
    copy: bool = False,
    name: str = "data",
) -> np.ndarray:
    """Convert arbitrary input representations into a validated NumPy array.

    Supported input types:
    - NumPy ndarray
    - PyTorch Tensor (CPU / CUDA / MPS)
    - pandas DataFrame / Series
    - Polars DataFrame / Series
    - Python lists / tuples

    Parameters
    ----------
    data : Any
        Input dataset or vector to convert.
    dtype : Optional[np.dtype], default=None
        Target NumPy data type. If None, preserves source numerical precision.
    ensure_2d : bool, default=False
        If True, ensures the returned array has shape (N, D). If 1D, reshapes to (N, 1).
    ensure_1d : bool, default=False
        If True, ensures the returned array is a 1D vector of shape (N,).
    copy : bool, default=False
        Whether to force a memory copy even when zero-copy views are possible.
    name : str, default="data"
        Identifier for error reporting.

    Returns
    -------
    np.ndarray
        Standardized NumPy array.

    Raises
    ------
    ValidationError
        If data contains NaN/Inf values, has invalid dimensionality, or is unsupported.
    """
    if data is None:
        raise ValidationError(f"{name} cannot be None.")

    out: np.ndarray

    # 1. PyTorch Tensor
    if _TORCH_AVAILABLE and isinstance(data, torch.Tensor):
        detached = data.detach().cpu()
        out = detached.numpy()
        if copy:
            out = out.copy()

    # 2. pandas DataFrame / Series
    elif _PANDAS_AVAILABLE and isinstance(data, (pd.DataFrame, pd.Series)):
        if data.isna().any().any() if isinstance(data, pd.DataFrame) else data.isna().any():
            raise ValidationError(f"{name} contains missing (NaN/None) values which are not supported.")
        out = data.to_numpy(dtype=dtype, copy=copy)

    # 3. Polars DataFrame / Series
    elif _POLARS_AVAILABLE and isinstance(data, (pl.DataFrame, pl.Series)):
        if data.null_count() > 0 if isinstance(data, pl.Series) else any(data.null_count().row(0)):
            raise ValidationError(f"{name} contains null values which are not supported.")
        out = data.to_numpy()
        if copy:
            out = out.copy()

    # 4. Standard NumPy ndarray
    elif isinstance(data, np.ndarray):
        out = data.copy() if copy else data

    # 5. Generic Python sequence
    elif isinstance(data, (list, tuple)):
        out = np.asarray(data)
        if copy:
            out = out.copy()

    else:
        raise ValidationError(
            f"Unsupported data type for {name}: {type(data).__name__}. "
            f"Expected numpy.ndarray, torch.Tensor, pandas.DataFrame, or polars.DataFrame."
        )

    # Apply target dtype if requested
    if dtype is not None and out.dtype != dtype:
        out = out.astype(dtype, copy=copy)

    # Validate non-finite numbers
    if np.issubdtype(out.dtype, np.floating) and not np.all(np.isfinite(out)):
        raise ValidationError(f"{name} contains non-finite values (NaN or Inf).")

    # Dimensionality enforcement
    if ensure_2d:
        if out.ndim == 1:
            out = out.reshape(-1, 1)
        elif out.ndim != 2:
            raise ValidationError(f"{name} must be a 2D array, got {out.ndim}D shape {out.shape}.")

    if ensure_1d:
        if out.ndim == 2 and out.shape[1] == 1:
            out = out.ravel()
        elif out.ndim != 1:
            raise ValidationError(f"{name} must be a 1D vector, got {out.ndim}D shape {out.shape}.")

    return out


def to_tensor(
    data: Any,
    dtype: Optional[Any] = None,
    device: Optional[Union[str, Any]] = None,
    copy: bool = False,
    name: str = "data",
) -> Any:
    """Convert arbitrary input representations into a PyTorch Tensor.

    Parameters
    ----------
    data : Any
        Input dataset to convert.
    dtype : Optional[torch.dtype], default=None
        Target PyTorch tensor dtype.
    device : Optional[torch.device], default=None
        Target compute device ('cpu', 'cuda', 'mps').
    copy : bool, default=False
        Whether to enforce a memory copy.
    name : str, default="data"
        Identifier for error reporting.

    Returns
    -------
    torch.Tensor
        Standardized PyTorch tensor.

    Raises
    ------
    ImportError
        If PyTorch is not installed in the active environment.
    ValidationError
        If input data is invalid.
    """
    if not _TORCH_AVAILABLE:
        raise ImportError(
            f"PyTorch is required to convert {name} to a torch.Tensor. "
            f"Install optional torch extras via: pip install 'robust-adapt[torch]'"
        )

    if isinstance(data, torch.Tensor):
        t = data
        if copy:
            t = t.clone()
        if dtype is not None and t.dtype != dtype:
            t = t.to(dtype=dtype)
        if device is not None and t.device != torch.device(device):
            t = t.to(device=device)
        return t

    # Convert to numpy first, then wrap into tensor
    np_arr = to_numpy(data, copy=copy, name=name)

    # Zero-copy conversion when contiguous and matching memory layout
    if not np_arr.flags.c_contiguous and not np_arr.flags.f_contiguous:
        np_arr = np.ascontiguousarray(np_arr)
    if not np_arr.flags.writeable:
        np_arr = np.copy(np_arr)

    tensor = torch.from_numpy(np_arr)
    if dtype is not None and tensor.dtype != dtype:
        tensor = tensor.to(dtype=dtype)
    if device is not None:
        tensor = tensor.to(device=device)

    return tensor


def inspect_dataset_contract(data: Any) -> DatasetContract:
    """Analyze input dataset and extract structural contract metadata."""
    source_framework = "numpy"
    feature_names: Optional[Tuple[str, ...]] = None

    if _TORCH_AVAILABLE and isinstance(data, torch.Tensor):
        source_framework = "torch"
    elif _PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
        source_framework = "pandas"
        feature_names = tuple(str(c) for c in data.columns)
    elif _POLARS_AVAILABLE and isinstance(data, pl.DataFrame):
        source_framework = "polars"
        feature_names = tuple(data.columns)

    arr = to_numpy(data, ensure_2d=True)
    return DatasetContract(
        n_samples=arr.shape[0],
        n_features=arr.shape[1],
        dtype=arr.dtype,
        source_framework=source_framework,
        feature_names=feature_names,
        is_contiguous=bool(arr.flags.c_contiguous or arr.flags.f_contiguous),
    )
