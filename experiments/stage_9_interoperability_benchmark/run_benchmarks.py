"""
Stage 9 Framework Interoperability Performance & Overhead Micro-benchmarks.

Measures:
1. Data conversion latency & memory (NumPy <-> Pandas <-> Polars <-> PyTorch).
2. PyTorch Training Loop Overhead: Standard nn.CrossEntropyLoss vs TorchSymmetricCrossEntropyLoss + TorchTrainingBudgetHook.
3. scikit-learn Pipeline Overhead: StandardScaler + LogisticRegression vs StandardScaler + SklearnAdaptiveClassifier + SklearnDriftDetectorTransformer.
4. Checkpoint Serialization & Deserialization: torch.save vs TorchCheckpointAdapter (SafeTensors + JSON metadata).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
import numpy as np

# AdaptiveML imports
from adaptive_ml.integrations.data import to_numpy, to_tensor, inspect_dataset_contract
from adaptive_ml.integrations.sklearn import (
    SklearnAdaptiveClassifier,
    SklearnDriftDetectorTransformer,
    SklearnReliabilityFilter,
)
from adaptive_ml.integrations.torch_module import TorchSymmetricCrossEntropyLoss
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.integrations.torch_callback import TorchTrainingBudgetHook, TorchCheckpointAdapter

# Optional libraries
import pandas as pd
import polars as pl
import torch
import torch.nn as nn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier


def benchmark_data_conversion(n_samples: int = 50_000, n_features: int = 20, iterations: int = 50):
    print(f"--- 1. Data Conversion Micro-benchmarks ({n_samples:,} rows x {n_features} cols, {iterations} iterations) ---")
    rng = np.random.default_rng(42)
    raw_np = rng.standard_normal((n_samples, n_features), dtype=np.float32)
    raw_df_pandas = pd.DataFrame(raw_np, columns=[f"feat_{i}" for i in range(n_features)])
    raw_df_polars = pl.DataFrame(raw_df_pandas)
    raw_tensor = torch.from_numpy(raw_np)

    # 1.1 Pandas -> NumPy
    times_pd_to_np = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        arr = to_numpy(raw_df_pandas)
        times_pd_to_np.append(time.perf_counter() - t0)
    pd_to_np_ms = np.median(times_pd_to_np) * 1000.0

    # 1.2 Polars -> NumPy
    times_pl_to_np = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        arr = to_numpy(raw_df_polars)
        times_pl_to_np.append(time.perf_counter() - t0)
    pl_to_np_ms = np.median(times_pl_to_np) * 1000.0

    # 1.3 Torch -> NumPy
    times_torch_to_np = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        arr = to_numpy(raw_tensor)
        times_torch_to_np.append(time.perf_counter() - t0)
    torch_to_np_ms = np.median(times_torch_to_np) * 1000.0

    # 1.4 NumPy -> Torch Tensor
    times_np_to_torch = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        t = to_tensor(raw_np)
        times_np_to_torch.append(time.perf_counter() - t0)
    np_to_torch_ms = np.median(times_np_to_torch) * 1000.0

    # 1.5 Pandas -> Torch Tensor
    times_pd_to_torch = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        t = to_tensor(raw_df_pandas)
        times_pd_to_torch.append(time.perf_counter() - t0)
    pd_to_torch_ms = np.median(times_pd_to_torch) * 1000.0

    # 1.6 Polars -> Torch Tensor
    times_pl_to_torch = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        t = to_tensor(raw_df_polars)
        times_pl_to_torch.append(time.perf_counter() - t0)
    pl_to_torch_ms = np.median(times_pl_to_torch) * 1000.0

    # 1.7 Dataset Contract Inspection
    times_contract = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        contract = inspect_dataset_contract(raw_df_pandas)
        times_contract.append(time.perf_counter() - t0)
    contract_ms = np.median(times_contract) * 1000.0

    print(f"  Pandas DataFrame -> NumPy:   {pd_to_np_ms:.3f} ms")
    print(f"  Polars DataFrame -> NumPy:   {pl_to_np_ms:.3f} ms")
    print(f"  PyTorch Tensor   -> NumPy:   {torch_to_np_ms:.3f} ms")
    print(f"  NumPy Array     -> Tensor:   {np_to_torch_ms:.3f} ms")
    print(f"  Pandas DataFrame -> Tensor:  {pd_to_torch_ms:.3f} ms")
    print(f"  Polars DataFrame -> Tensor:  {pl_to_torch_ms:.3f} ms")
    print(f"  Dataset Contract Inspection: {contract_ms:.3f} ms")

    return {
        "pandas_to_numpy_ms": pd_to_np_ms,
        "polars_to_numpy_ms": pl_to_np_ms,
        "torch_to_numpy_ms": torch_to_np_ms,
        "numpy_to_torch_ms": np_to_torch_ms,
        "pandas_to_torch_ms": pd_to_torch_ms,
        "polars_to_torch_ms": pl_to_torch_ms,
        "contract_inspection_ms": contract_ms,
    }


def benchmark_pytorch_training(n_steps: int = 500, batch_size: int = 64, n_features: int = 32, n_classes: int = 4):
    print(f"\n--- 2. PyTorch Training Loop Overhead ({n_steps} steps, batch_size={batch_size}) ---")
    torch.manual_seed(42)

    # Synthetic batches
    batches = [
        (torch.randn(batch_size, n_features), torch.randint(0, n_classes, (batch_size,)))
        for _ in range(n_steps)
    ]

    # Baseline: Vanilla PyTorch with nn.CrossEntropyLoss and torch.optim.AdamW
    baseline_model = nn.Sequential(
        nn.Linear(n_features, 64),
        nn.ReLU(),
        nn.Linear(64, n_classes)
    )
    baseline_criterion = nn.CrossEntropyLoss()
    baseline_optimizer = torch.optim.AdamW(baseline_model.parameters(), lr=1e-3)

    t0 = time.perf_counter()
    for x, y in batches:
        baseline_optimizer.zero_grad()
        out = baseline_model(x)
        loss = baseline_criterion(out, y)
        loss.backward()
        baseline_optimizer.step()
    baseline_sec = time.perf_counter() - t0
    baseline_step_ms = (baseline_sec / n_steps) * 1000.0

    # AdaptiveML: PyTorch with TorchSymmetricCrossEntropyLoss + TorchTrainingBudgetHook + create_torch_low_memory_adamw
    aml_model = nn.Sequential(
        nn.Linear(n_features, 64),
        nn.ReLU(),
        nn.Linear(64, n_classes)
    )
    aml_criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.5)
    aml_optimizer = create_torch_low_memory_adamw(aml_model.parameters(), lr=1e-3)
    budget_mgr = DynamicResourceBudgetManager(max_memory_mb=4096.0)
    budget_hook = TorchTrainingBudgetHook(budget_mgr)

    t0 = time.perf_counter()
    for x, y in batches:
        budget_hook.on_step_begin()
        aml_optimizer.zero_grad()
        out = aml_model(x)
        loss = aml_criterion(out, y)
        loss.backward()
        aml_optimizer.step()
        budget_hook.on_step_end()
    aml_sec = time.perf_counter() - t0
    aml_step_ms = (aml_sec / n_steps) * 1000.0
    overhead_pct = ((aml_sec - baseline_sec) / baseline_sec) * 100.0

    print(f"  Baseline PyTorch:   {baseline_sec*1000:.2f} ms total ({baseline_step_ms:.3f} ms/step)")
    print(f"  AdaptiveML PyTorch: {aml_sec*1000:.2f} ms total ({aml_step_ms:.3f} ms/step)")
    print(f"  Relative Overhead:  {overhead_pct:+.2f}%")

    return {
        "baseline_total_ms": baseline_sec * 1000.0,
        "baseline_step_ms": baseline_step_ms,
        "adaptive_ml_total_ms": aml_sec * 1000.0,
        "adaptive_ml_step_ms": aml_step_ms,
        "relative_overhead_pct": overhead_pct,
    }


def benchmark_sklearn_pipeline(n_samples: int = 10_000, n_features: int = 16, n_classes: int = 2):
    print(f"\n--- 3. scikit-learn Pipeline Overhead ({n_samples:,} samples, {n_features} features) ---")
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_samples, n_features), dtype=np.float32)
    y = (X[:, 0] + X[:, 1] > 0).astype(np.int64)

    # 3.1 Standard Scikit-learn Pipeline with SGDClassifier
    standard_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SGDClassifier(loss="log_loss", random_state=42))
    ])

    t0 = time.perf_counter()
    standard_pipe.fit(X, y)
    t_std_fit = time.perf_counter() - t0

    t0 = time.perf_counter()
    std_preds = standard_pipe.predict(X)
    t_std_pred = time.perf_counter() - t0

    # 3.2 AdaptiveML Pipeline with SklearnDriftDetectorTransformer and SklearnAdaptiveClassifier
    aml_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("drift_monitor", SklearnDriftDetectorTransformer(delta=1e-4, monitored_feature_index=0)),
        ("clf", SklearnAdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=50, random_state=42))
    ])

    t0 = time.perf_counter()
    aml_pipe.fit(X, y)
    t_aml_fit = time.perf_counter() - t0

    t0 = time.perf_counter()
    aml_preds = aml_pipe.predict(X)
    t_aml_pred = time.perf_counter() - t0

    # Incremental update overhead: partial_fit over 20 batches of 500 samples
    batch_size = 500
    n_batches = n_samples // batch_size

    t0 = time.perf_counter()
    for b in range(n_batches):
        xb = X[b*batch_size : (b+1)*batch_size]
        yb = y[b*batch_size : (b+1)*batch_size]
        standard_pipe.named_steps["clf"].partial_fit(xb, yb, classes=[0, 1])
    t_std_partial = time.perf_counter() - t0

    t0 = time.perf_counter()
    for b in range(n_batches):
        xb = X[b*batch_size : (b+1)*batch_size]
        yb = y[b*batch_size : (b+1)*batch_size]
        aml_pipe.named_steps["clf"].partial_fit(xb, yb, classes=[0, 1])
    t_aml_partial = time.perf_counter() - t0

    print(f"  Standard fit:     {t_std_fit*1000:.2f} ms | AML fit:     {t_aml_fit*1000:.2f} ms")
    print(f"  Standard predict: {t_std_pred*1000:.2f} ms | AML predict: {t_aml_pred*1000:.2f} ms")
    print(f"  Standard partial: {t_std_partial*1000:.2f} ms | AML partial: {t_aml_partial*1000:.2f} ms")

    return {
        "standard_fit_ms": t_std_fit * 1000.0,
        "aml_fit_ms": t_aml_fit * 1000.0,
        "standard_predict_ms": t_std_pred * 1000.0,
        "aml_predict_ms": t_aml_pred * 1000.0,
        "standard_partial_fit_ms": t_std_partial * 1000.0,
        "aml_partial_fit_ms": t_aml_partial * 1000.0,
    }


def benchmark_checkpoint_interoperability(out_dir: Path, iterations: int = 10):
    print(f"\n--- 4. Checkpoint Serialization & Deserialization Benchmark ({iterations} iterations) ---")
    out_dir.mkdir(parents=True, exist_ok=True)
    model = nn.Sequential(
        nn.Linear(128, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 10)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    adapter = TorchCheckpointAdapter()

    torch_ckpt_path = out_dir / "standard_torch.pt"
    aml_ckpt_path = out_dir / "aml_checkpoint.safetensors"

    # 4.1 PyTorch Native (torch.save / torch.load)
    save_times_native = []
    load_times_native = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        torch.save({"model": model.state_dict(), "opt": optimizer.state_dict()}, torch_ckpt_path)
        save_times_native.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        loaded = torch.load(torch_ckpt_path, weights_only=True)
        load_times_native.append(time.perf_counter() - t0)

    native_save_ms = np.median(save_times_native) * 1000.0
    native_load_ms = np.median(load_times_native) * 1000.0
    native_size_kb = torch_ckpt_path.stat().st_size / 1024.0

    # 4.2 AdaptiveML TorchCheckpointAdapter (SafeTensors + JSON metadata)
    save_times_aml = []
    load_times_aml = []
    actual_aml_path = None
    for _ in range(iterations):
        t0 = time.perf_counter()
        actual_aml_path = adapter.save_hybrid_checkpoint(model, optimizer, None, aml_ckpt_path)
        save_times_aml.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        adapter.load_hybrid_checkpoint(model, optimizer, None, actual_aml_path)
        load_times_aml.append(time.perf_counter() - t0)

    aml_save_ms = np.median(save_times_aml) * 1000.0
    aml_load_ms = np.median(load_times_aml) * 1000.0
    aml_size_kb = actual_aml_path.stat().st_size / 1024.0 if (actual_aml_path and actual_aml_path.exists()) else 0.0

    meta_path = Path(str(actual_aml_path).replace(".safetensors", ".meta.json"))
    if meta_path.exists():
        aml_total_size_kb = (actual_aml_path.stat().st_size + meta_path.stat().st_size) / 1024.0
    else:
        aml_total_size_kb = aml_size_kb

    print(f"  torch.save():                  Save: {native_save_ms:.2f} ms | Load: {native_load_ms:.2f} ms | Size: {native_size_kb:.2f} KB")
    print(f"  TorchCheckpointAdapter:        Save: {aml_save_ms:.2f} ms | Load: {aml_load_ms:.2f} ms | Size: {aml_total_size_kb:.2f} KB")

    # Cleanup temp checkpoint files
    if torch_ckpt_path.exists():
        torch_ckpt_path.unlink()
    if actual_aml_path and actual_aml_path.exists():
        actual_aml_path.unlink()
    if meta_path.exists():
        meta_path.unlink()

    return {
        "native_save_ms": native_save_ms,
        "native_load_ms": native_load_ms,
        "native_size_kb": native_size_kb,
        "aml_save_ms": aml_save_ms,
        "aml_load_ms": aml_load_ms,
        "aml_size_kb": aml_total_size_kb,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 9 — Interoperability Micro-benchmark Suite")
    print(f"Python: {sys.version.split()[0]} on {sys.platform}")
    print("=====================================================================")

    out_dir = Path("experiments/stage_9_interoperability_benchmark")
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["data_conversion"] = benchmark_data_conversion()
    results["pytorch_training"] = benchmark_pytorch_training()
    results["sklearn_pipeline"] = benchmark_sklearn_pipeline()
    results["checkpoints"] = benchmark_checkpoint_interoperability(out_dir)

    results_file = out_dir / "benchmark_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAll benchmark results successfully recorded to: {results_file}")


if __name__ == "__main__":
    main()
