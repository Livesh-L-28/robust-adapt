"""
Stage 12 — Workstream D: RAO 2.0 Vectorized Neural Benchmark on CoverType.

Evaluates:
1. standard_adamw: PyTorch native C++ AdamW (float32 moments)
2. vectorized_low_memory_adamw: RAO 2.0 Vectorized 8-bit block quantization with selective 1D preservation

Protocol:
- Authentic Forest CoverType features (581,012 samples, 54 features, 7 classes)
- CoverTypeMLP: 4 linear layers, 2 BatchNorm layers, 56,071 parameters
- 5 paired seeds: [42, 101, 202, 303, 404]
- 500 mini-batch training steps (batch_size=128)
- Metrics: State memory (bytes/MB), P50/P95/P99 latency, Throughput, Loss trajectory
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

from experiments.stage_12.rao_2_0.vectorized_adamw import VectorizedLowMemoryAdamW

SEEDS = [42, 101, 202, 303, 404]
BATCH_SIZE = 128
N_STEPS = 500


class CoverTypeMLP(nn.Module):
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


def get_standard_adamw_state_bytes(optimizer) -> int:
    total_bytes = 0
    for state in optimizer.state.values():
        for k, v in state.items():
            if isinstance(v, torch.Tensor):
                total_bytes += v.nelement() * v.element_size()
            elif isinstance(v, (int, float)):
                total_bytes += 8
    return total_bytes


def run_trial(opt_type: str, X_tensor: torch.Tensor, y_tensor: torch.Tensor, seed: int) -> Dict[str, Any]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    gc.collect()

    model = CoverTypeMLP()
    criterion = nn.CrossEntropyLoss()

    if opt_type == "standard_adamw":
        optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    elif opt_type == "vectorized_low_memory_adamw":
        optimizer = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-3, weight_decay=1e-4, block_size=64)
    else:
        raise ValueError(f"Unknown optimizer: {opt_type}")

    param_bytes = sum(p.nelement() * p.element_size() for p in model.parameters())
    step_latencies: List[float] = []
    loss_history: List[float] = []
    n_samples = len(X_tensor)

    tracemalloc.start()
    t_start = time.perf_counter()

    for step in range(N_STEPS):
        idx = np.random.randint(0, n_samples, size=BATCH_SIZE)
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
    _, peak_heap = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if opt_type == "vectorized_low_memory_adamw":
        opt_state_bytes = optimizer.get_state_memory_bytes()
    else:
        opt_state_bytes = get_standard_adamw_state_bytes(optimizer)

    step_latencies_us = np.array(step_latencies) * 1e6

    return {
        "optimizer": opt_type,
        "seed": seed,
        "param_bytes": param_bytes,
        "optimizer_state_bytes": opt_state_bytes,
        "optimizer_state_mb": opt_state_bytes / (1024 ** 2),
        "total_time_sec": t_total,
        "throughput_samples_per_sec": (N_STEPS * BATCH_SIZE) / t_total,
        "p50_latency_us": float(np.percentile(step_latencies_us, 50)),
        "p95_latency_us": float(np.percentile(step_latencies_us, 95)),
        "p99_latency_us": float(np.percentile(step_latencies_us, 99)),
        "initial_loss": float(loss_history[0]),
        "final_loss": float(loss_history[-1]),
        "mean_loss_last_100": float(np.mean(loss_history[-100:])),
        "peak_heap_mb": peak_heap / (1024 ** 2),
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream D — RAO 2.0 Vectorized Benchmark")
    print(f"Seeds: {SEEDS} | Steps: {N_STEPS} | Batch size: {BATCH_SIZE}")
    print("=====================================================================")

    data_file = Path("experiments/stage_11/datasets/covtype.csv.gz")
    df = pd.read_csv(data_file)
    feature_cols = [c for c in df.columns if c not in ["Cover_Type", "target"]]
    X_vals = df[feature_cols].values.astype(np.float32)
    y_vals = df["target"].values.astype(np.int64)

    # Normalize continuous features
    X_vals[:, :10] = (X_vals[:, :10] - np.mean(X_vals[:, :10], axis=0)) / (np.std(X_vals[:, :10], axis=0) + 1e-6)

    X_tensor = torch.from_numpy(X_vals)
    y_tensor = torch.from_numpy(y_vals)

    optimizers = ["standard_adamw", "vectorized_low_memory_adamw"]
    all_results = []

    for opt in optimizers:
        print(f"\nBenchmarking optimizer: {opt}...", flush=True)
        records = []
        for seed in SEEDS:
            res = run_trial(opt, X_tensor, y_tensor, seed)
            records.append(res)
            all_results.append(res)
            print(
                f"  Seed {seed:4d} | Opt State: {res['optimizer_state_mb']:.3f} MB | "
                f"P50: {res['p50_latency_us']:6.1f} us | Loss: {res['final_loss']:.4f} | "
                f"Throughput: {res['throughput_samples_per_sec']:,.0f} s/s",
                flush=True,
            )

        mean_state = np.mean([r["optimizer_state_mb"] for r in records])
        mean_p50 = np.mean([r["p50_latency_us"] for r in records])
        mean_loss = np.mean([r["mean_loss_last_100"] for r in records])
        mean_tput = np.mean([r["throughput_samples_per_sec"] for r in records])
        print(
            f"  --> Mean State: {mean_state:.3f} MB | Mean P50: {mean_p50:.1f} us | "
            f"Mean Loss: {mean_loss:.4f} | Throughput: {mean_tput:,.0f} s/s",
            flush=True,
        )

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "rao_2_0_covertype_results.json"
    out_csv = out_dir / "rao_2_0_covertype_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll RAO 2.0 results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()

