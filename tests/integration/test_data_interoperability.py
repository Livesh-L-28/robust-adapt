"""
Comprehensive integration tests for ROBUST-ADAPT data interoperability.

Tests to_numpy(), to_tensor(), and inspect_dataset_contract() across
NumPy, PyTorch, pandas, and Polars.
"""

from __future__ import annotations

import numpy as np
import pytest

from robust_adapt.core.exceptions import ValidationError
from robust_adapt.integrations.data import (
    DatasetContract,
    inspect_dataset_contract,
    to_numpy,
    to_tensor,
)

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

try:
    import polars as pl
    _POLARS_AVAILABLE = True
except ImportError:
    _POLARS_AVAILABLE = False


class TestDataInteroperability:
    """Test suite for cross-framework data conversions."""

    def test_to_numpy_from_numpy(self) -> None:
        """Verify standard NumPy arrays pass through cleanly or with requested casting."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        out = to_numpy(arr)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.float32
        assert np.array_equal(out, arr)

        # Cast to float64
        out64 = to_numpy(arr, dtype=np.float64)
        assert out64.dtype == np.float64

    def test_to_numpy_dimensions_enforcement(self) -> None:
        """Verify ensure_1d and ensure_2d shape enforcement."""
        v = np.array([1.0, 2.0, 3.0])

        # 1D enforced
        v1 = to_numpy(v, ensure_1d=True)
        assert v1.ndim == 1
        assert v1.shape == (3,)

        # Reshaped to 2D
        v2 = to_numpy(v, ensure_2d=True)
        assert v2.ndim == 2
        assert v2.shape == (3, 1)

        # 2D to 1D flattening if single column
        v_col = np.array([[10.0], [20.0], [30.0]])
        v_flat = to_numpy(v_col, ensure_1d=True)
        assert v_flat.ndim == 1
        assert v_flat.shape == (3,)

        # Invalid multi-column to 1D
        m = np.ones((3, 2))
        with pytest.raises(ValidationError, match="must be a 1D vector"):
            to_numpy(m, ensure_1d=True)

    def test_to_numpy_rejects_nan_and_inf(self) -> None:
        """Verify non-finite values are caught and raise ValidationError."""
        arr_nan = np.array([1.0, np.nan, 3.0])
        with pytest.raises(ValidationError, match="contains non-finite values"):
            to_numpy(arr_nan)

        arr_inf = np.array([1.0, np.inf, 3.0])
        with pytest.raises(ValidationError, match="contains non-finite values"):
            to_numpy(arr_inf)

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch is required")
    def test_to_numpy_from_torch(self) -> None:
        """Verify conversion from PyTorch tensors (with autograd detached)."""
        tensor = torch.tensor([[1.5, 2.5], [3.5, 4.5]], requires_grad=True)
        out = to_numpy(tensor)
        assert isinstance(out, np.ndarray)
        assert out.shape == (2, 2)
        assert np.isclose(out[0, 0], 1.5)

    @pytest.mark.skipif(not _PANDAS_AVAILABLE, reason="pandas is required")
    def test_to_numpy_from_pandas(self) -> None:
        """Verify conversion from pandas DataFrame and Series."""
        df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        out_df = to_numpy(df, ensure_2d=True)
        assert isinstance(out_df, np.ndarray)
        assert out_df.shape == (2, 2)

        s = pd.Series([10.0, 20.0, 30.0], name="target")
        out_s = to_numpy(s, ensure_1d=True)
        assert isinstance(out_s, np.ndarray)
        assert out_s.shape == (3,)

    @pytest.mark.skipif(not _POLARS_AVAILABLE, reason="Polars is required")
    def test_to_numpy_from_polars(self) -> None:
        """Verify conversion from Polars DataFrame and Series."""
        pldf = pl.DataFrame({"x": [10.0, 20.0], "y": [30.0, 40.0]})
        out_pldf = to_numpy(pldf, ensure_2d=True)
        assert isinstance(out_pldf, np.ndarray)
        assert out_pldf.shape == (2, 2)

        pls = pl.Series("label", [0, 1, 0, 1])
        out_pls = to_numpy(pls, ensure_1d=True)
        assert isinstance(out_pls, np.ndarray)
        assert out_pls.shape == (4,)

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch is required")
    def test_to_tensor_conversions(self) -> None:
        """Verify to_tensor from NumPy, pandas, and Polars."""
        np_data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        t_from_np = to_tensor(np_data)
        assert isinstance(t_from_np, torch.Tensor)
        assert t_from_np.dtype == torch.float32
        assert t_from_np.shape == (2, 2)

        if _PANDAS_AVAILABLE:
            df = pd.DataFrame({"f0": [1.0, 2.0], "f1": [3.0, 4.0]})
            t_from_pd = to_tensor(df)
            assert isinstance(t_from_pd, torch.Tensor)
            assert t_from_pd.shape == (2, 2)

        if _POLARS_AVAILABLE:
            pldf = pl.DataFrame({"f0": [1.0, 2.0], "f1": [3.0, 4.0]})
            t_from_pl = to_tensor(pldf)
            assert isinstance(t_from_pl, torch.Tensor)
            assert t_from_pl.shape == (2, 2)

    def test_inspect_dataset_contract(self) -> None:
        """Verify dataset contract extraction across frameworks."""
        raw = np.zeros((25, 4), dtype=np.float32)
        contract = inspect_dataset_contract(raw)
        assert isinstance(contract, DatasetContract)
        assert contract.n_samples == 25
        assert contract.n_features == 4
        assert contract.dtype == np.float32
        assert contract.source_framework == "numpy"
        assert contract.is_contiguous is True

        if _PANDAS_AVAILABLE:
            df = pd.DataFrame({"colA": [1.0, 2.0], "colB": [3.0, 4.0]})
            df_contract = inspect_dataset_contract(df)
            assert df_contract.source_framework == "pandas"
            assert df_contract.feature_names == ("colA", "colB")
            assert df_contract.n_samples == 2
            assert df_contract.n_features == 2

        if _POLARS_AVAILABLE:
            pldf = pl.DataFrame({"feature_0": [10.0], "feature_1": [20.0]})
            pl_contract = inspect_dataset_contract(pldf)
            assert pl_contract.source_framework == "polars"
            assert pl_contract.feature_names == ("feature_0", "feature_1")
            assert pl_contract.n_samples == 1
            assert pl_contract.n_features == 2
