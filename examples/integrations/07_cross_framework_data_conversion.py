"""
Example 07: Cross-Framework Data Ingestion and Contract Inspection.

Demonstrates seamless zero-copy data conversion across Pandas, Polars,
PyTorch, and NumPy into standard ROBUST-ADAPT classifiers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import torch

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.integrations.data import (
    inspect_dataset_contract,
    to_numpy,
    to_tensor,
)


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 07: Cross-Framework Data Interoperability")
    print("=====================================================================")

    # 1. Ingestion from Pandas DataFrame
    print("\n--- 1. Pandas DataFrame Ingestion ---")
    df_pandas = pd.DataFrame({
        "sensor_temp": [22.4, 23.1, 24.5, 23.8, 25.0],
        "sensor_pressure": [101.3, 101.5, 101.2, 100.9, 101.4],
        "sensor_humidity": [45.2, 46.1, 48.0, 47.5, 49.2],
    })
    contract_pd = inspect_dataset_contract(df_pandas)
    print(f"Contract: {contract_pd.n_samples} samples x {contract_pd.n_features} features, Source: '{contract_pd.source_framework}'")
    print(f"Features: {contract_pd.feature_names}")
    np_from_pd = to_numpy(df_pandas)
    print(f"NumPy Array Shape: {np_from_pd.shape}, dtype: {np_from_pd.dtype}")

    # 2. Ingestion from Polars DataFrame
    print("\n--- 2. Polars DataFrame Ingestion ---")
    df_polars = pl.DataFrame({
        "signal_alpha": [0.12, 0.45, 0.88, 0.34, 0.72],
        "signal_beta": [1.45, 1.82, 0.99, 1.15, 1.30],
        "signal_gamma": [0.05, 0.08, 0.02, 0.04, 0.06],
    })
    contract_pl = inspect_dataset_contract(df_polars)
    print(f"Contract: {contract_pl.n_samples} samples x {contract_pl.n_features} features, Source: '{contract_pl.source_framework}'")
    print(f"Features: {contract_pl.feature_names}")
    np_from_pl = to_numpy(df_polars)
    print(f"NumPy Array Shape: {np_from_pl.shape}, dtype: {np_from_pl.dtype}")

    # 3. Ingestion from PyTorch Tensors
    print("\n--- 3. PyTorch Tensor Ingestion ---")
    tensor_torch = torch.randn(5, 3)
    contract_torch = inspect_dataset_contract(tensor_torch)
    print(f"Contract: {contract_torch.n_samples} samples x {contract_torch.n_features} features, Source: '{contract_torch.source_framework}'")
    np_from_torch = to_numpy(tensor_torch)
    print(f"NumPy Array Shape: {np_from_torch.shape}")

    # 4. Bidirectional Tensor Conversion
    print("\n--- 4. Conversion to PyTorch Tensor ---")
    tensor_from_pd = to_tensor(df_pandas)
    tensor_from_pl = to_tensor(df_polars)
    print(f"Tensor from Pandas: type={type(tensor_from_pd)}, shape={tensor_from_pd.shape}, device={tensor_from_pd.device}")
    print(f"Tensor from Polars: type={type(tensor_from_pl)}, shape={tensor_from_pl.shape}, device={tensor_from_pl.device}")

    # 5. Direct Feed into AdaptiveClassifier
    print("\n--- 5. Feeding Tabular Data Directly into AdaptiveClassifier ---")
    rng = np.random.default_rng(42)
    n_train = 500
    train_df = pd.DataFrame(rng.standard_normal((n_train, 4)), columns=[f"f_{i}" for i in range(4)])
    train_labels = (train_df["f_0"] + train_df["f_1"] > 0).astype(int).to_numpy()

    clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20)
    # Pass pandas DataFrame directly to fit
    X_train_np = to_numpy(train_df)
    clf.fit(X_train_np, train_labels)

    test_polars = pl.DataFrame(rng.standard_normal((100, 4)), schema=[f"f_{i}" for i in range(4)])
    test_labels = (test_polars["f_0"] + test_polars["f_1"] > 0).cast(pl.Int64).to_numpy()

    # Pass Polars DataFrame directly to predict
    X_test_np = to_numpy(test_polars)
    preds = clf.predict(X_test_np)
    acc = np.mean(preds == test_labels)

    print(f"Fitted AdaptiveClassifier with Pandas DataFrame ({n_train} samples).")
    print(f"Evaluated predictions on Polars DataFrame (100 samples) -> Accuracy: {acc * 100:.2f}%")


if __name__ == "__main__":
    main()
