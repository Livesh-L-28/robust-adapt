"""
Stage 11 — Workstream F: RAO Resource Efficiency Validation on CoverType Features.

Compares Standard PyTorch AdamW vs AdaptiveML LowMemoryAdamW (64-block 8-bit dynamic quantization)
on a genuine multi-layer neural network trained on real CoverType features (54 features, 7 classes).

Metrics measured:
1. Exact optimizer-state memory consumption (bytes and MB)
2. Model parameter and gradient memory footprint
3. Step latency distribution (Mean, Median, P50, P95, P99)
4. Training throughput (samples/sec)
5. Numerical stability and loss convergence trajectories across 1,000 batches
6. Peak heap and physical RSS allocations
"""

from __future__ import annotations

import gc
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW

# AdaptiveML imports
from adaptive_ml.integrations import create_torch_low_memory_adamw
from adaptive_ml.core.telemetry import get_process_memory_bytes


SEEDS = [42, 101, 202, 303, 404]
BATCH_SIZE = 128
N_STEPS = 1000


class CoverTypeMLP(nn.Module):
    """Multi-layer perceptron for 54-dimensional CoverType classification."""
    def __init__(self, in_features: int = 54, n_classes: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def get_optimizer_state_size_bytes(optimizer) -> int:
    """Calculates total memory occupied by optimizer state buffers."""
    total_bytes = 0
    for state in optimizer.state.values():
        for k, v in state.items():
            if isinstance(v, torch.Tensor):
                total_bytes += v.nelement() * v.element_size()
            elif isinstance(v, np.ndarray):
                total_bytes += v.nbytes
            elif isinstance(v, (int, float)):
                total_bytes += 8
    return total_bytes


def run_optimizer_trial(
    opt_type: str,
    X_tensor: torch.Tensor,
    y_tensor: torch.Tensor,
    seed: int,
    n_steps: int = N_STEPS,
    batch_size: int = BATCH_SIZE,
) -> Dict[str, Any]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    gc.collect()

    model = CoverTypeMLP()
    criterion = nn.CrossEntropyLoss()

    if opt_type == "standard_adamw":
        optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    elif opt_type == "adaptive_ml_low_memory_adamw":
        optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, weight_decay=1e-4, block_size=64)
    else:
        raise ValueError(f"Unknown optimizer: {opt_type}")

    # Count parameters
    param_bytes = sum(p.nelement() * p.element_size() for p in model.parameters())

    step_latencies = []
    loss_history = []
    n_total_samples = len(X_tensor)

    tracemalloc.start()
    rss_start = get_process_memory_bytes() / (1024 ** 2)
    t_start = time.perf_counter()

    for step in range(n_steps):
        # Sample mini-batch
        idx = np.random.randint(0, n_total_samples, size=batch_size)
        x_b = X_tensor[idx]
        y_b = y_tensor[idx]

        t0 = time.perf_counter()
        optimizer.zero_grad()
        out = model(x_b)
        loss = criterion(out, y_b)
        loss.backward()
        optimizer.step()
        t1 = time.perf_counter()

        step_latencies.append(t1 - t0)
        loss_history.append(float(loss.item()))

    t_total = time.perf_counter() - t_start
    rss_end = get_process_memory_bytes() / (1024 ** 2)
    current_heap, peak_heap = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    opt_state_bytes = get_optimizer_state_size_bytes(optimizer)
    step_latencies_us = np.array(step_latencies) * 1e6

    return {
        "optimizer": opt_type,
        "seed": seed,
        "param_bytes": param_bytes,
        "optimizer_state_bytes": opt_state_bytes,
        "optimizer_state_mb": opt_state_bytes / (1024 ** 2),
        "total_time_sec": t_total,
        "throughput_samples_per_sec": (n_steps * batch_size) / t_total,
        "p50_latency_us": float(np.percentile(step_latencies_us, 50)),
        "p95_latency_us": float(np.percentile(step_latencies_us, 95)),
        "p99_latency_us": float(np.percentile(step_latencies_us, 99)),
        "initial_loss": float(loss_history[0]),
        "final_loss": float(loss_history[-1]),
        "mean_loss_last_100": float(np.mean(loss_history[-100:])),
        "peak_heap_mb": peak_heap / (1024 ** 2),
        "rss_delta_mb": rss_end - rss_start,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Workstream F — RAO Real-World Neural Benchmark")
    print(f"Seeds: {SEEDS} | Steps: {N_STEPS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/covtype.csv.gz")
    if not data_file.exists():
        raise FileNotFoundError(f"CoverType dataset {data_file} not found.")

    print("Loading CoverType features...")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["Cover_Type", "target"]]
    X_vals = df[feature_cols].values.astype(np.float32)
    y_vals = df["target"].values.astype(np.int64)

    # Normalize continuous features (first 10)
    X_vals[:, :10] = (X_vals[:, :10] - np.mean(X_vals[:, :10], axis=0)) / (np.std(X_vals[:, :10], axis=0) + 1e-6)

    X_tensor = torch.from_numpy(X_vals)
    y_tensor = torch.from_numpy(y_vals)
    print(f"Loaded {len(X_tensor):,} tensors with {X_tensor.shape[1]} features.")

    optimizers = ["standard_adamw", "adaptive_ml_low_memory_adamw"]
    all_results = []

    for opt in optimizers:
        print(f"\nBenchmarking optimizer: {opt}...")
        opt_records = []
        for seed in SEEDS:
            res = run_optimizer_trial(opt, X_tensor, y_tensor, seed=seed)
            opt_records.append(res)
            all_results.append(res)
            print(f"  Seed {seed:4d} | Opt State: {res['optimizer_state_mb']:.2f} MB | P50: {res['p50_latency_us']:6.1f} us | Loss: {res['final_loss']:.4f} | Throughput: {res['throughput_samples_per_sec']:,.0f} s/s")

        mean_state = np.mean([r["optimizer_state_mb"] for r in opt_records])
        mean_p50 = np.mean([r["p50_latency_us"] for r in opt_records])
        mean_loss = np.mean([r["mean_loss_last_100"] for r in opt_records])
        mean_tput = np.mean([r["throughput_samples_per_sec"] for r in opt_records])
        print(f"  --> Mean State: {mean_state:.3f} MB | Mean P50: {mean_p50:.1f} us | Mean Loss: {mean_loss:.4f} | Throughput: {mean_tput:,.0f} s/s")

    out_dir = Path("experiments/stage_11/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "rao_resource_results.json"
    out_csv = out_dir / "rao_resource_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll RAO results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

