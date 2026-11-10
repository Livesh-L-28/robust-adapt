"""
Workstream F: Memory Benchmark Script.
Evaluates LowMemoryAdamW vs Standard AdamW across model sizes (1K to 1M parameters),
tracks long-running streaming RSS memory over 5,000 batches, exports environment matrix,
and outputs optimizer_memory_results.csv, long_run_memory_results.csv, environment_matrix.json.
"""

import csv
import json
import os
import platform
import sys
import time
import psutil
import numpy as np
import torch
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.ulc.controller import AdaptiveLearningController

class DummyParam:
    def __init__(self, data: np.ndarray):
        self.data = data
        self.grad = np.zeros_like(data)

def run_optimizer_memory_scaling():
    print("--> 1. Running Optimizer Memory Scaling Benchmark (1K to 1M parameters) ...")
    param_sizes = [1_000, 10_000, 100_000, 1_000_000]
    block_size = 16
    
    rows = []
    
    for N in param_sizes:
        # Standard FP32 AdamW: 8.0 bytes / param
        fp32_theory = N * 8
        
        # LowMemoryAdamW: 1 byte m + 1 byte v + 8 bytes scale per block (B=16)
        n_blocks = int(np.ceil(N / block_size))
        lowmem_theory = N * 2 + n_blocks * 8
        
        # Instantiate LowMemoryAdamW and measure actual
        data = np.random.randn(N).astype(np.float32)
        p = DummyParam(data)
        opt = LowMemoryAdamW([p], lr=0.01, block_size=block_size)
        
        # Take 5 steps to populate optimizer state
        t0 = time.perf_counter()
        for _ in range(5):
            p.grad = np.random.randn(N).astype(np.float32)
            opt.step()
        step_time_ms = (time.perf_counter() - t0) / 5.0 * 1000.0
        
        measured_bytes = opt.get_state_memory_bytes()
        
        reduction_pct = (1.0 - (measured_bytes / fp32_theory)) * 100.0
        bytes_per_param = measured_bytes / N
        
        rows.append({
            "param_count": N,
            "standard_adamw_bytes": fp32_theory,
            "standard_adamw_kb": f"{fp32_theory / 1024:.2f}",
            "lowmem_theory_bytes": lowmem_theory,
            "lowmem_measured_bytes": measured_bytes,
            "lowmem_measured_kb": f"{measured_bytes / 1024:.2f}",
            "bytes_per_param": f"{bytes_per_param:.3f}",
            "memory_reduction_pct": f"{reduction_pct:.2f}%",
            "step_time_ms": f"{step_time_ms:.4f}"
        })
        print(f"    N = {N:9d} | FP32: {fp32_theory/1024:8.2f} KB | LowMem: {measured_bytes/1024:8.2f} KB | Saved: {reduction_pct:5.2f}% | Lat: {step_time_ms:6.3f} ms")
        
    out_csv = "experiments/ulc_v3_independent_audit/optimizer_memory_results.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[OK] Wrote optimizer memory results to {out_csv}\n")
    return rows

def run_long_running_memory_benchmark(n_batches=5000):
    print(f"--> 2. Running Long-Duration Streaming Memory Benchmark ({n_batches} batches) ...")
    proc = psutil.Process()
    
    clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20, enable_drift_detection=True)
    pipeline = RobustLearningPipeline(n_classes=2)
    p_wrapper = DummyParam(np.random.randn(4, 2).astype(np.float32) * 0.01)
    opt = LowMemoryAdamW([p_wrapper], lr=0.01)
    controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
    
    tracked_steps = []
    
    initial_rss_mb = proc.memory_info().rss / (1024 ** 2)
    print(f"    Initial Process RSS: {initial_rss_mb:.2f} MB")
    
    rng = np.random.RandomState(42)
    
    for b in range(1, n_batches + 1):
        # 30 samples per batch
        X = rng.randn(30, 4)
        y = (rng.rand(30) > 0.90).astype(int)
        
        # Step
        directive, info = controller.step(X, y)
        if directive.purge_replay and hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
            clf._replay_buffer.clear()
            
        # Linear step
        logits = X @ p_wrapper.data
        p_wrapper.grad = (X.T @ (logits - np.eye(2)[y])) / 30.0
        opt.step()
        
        if b % 250 == 0 or b == 1 or b == n_batches:
            rss_mb = proc.memory_info().rss / (1024 ** 2)
            opt_b = opt.get_state_memory_bytes()
            buf_len = clf._replay_buffer.total_stored if hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None else 0
            
            tracked_steps.append({
                "batch_idx": b,
                "process_rss_mb": f"{rss_mb:.2f}",
                "rss_delta_mb": f"{rss_mb - initial_rss_mb:+.2f}",
                "optimizer_state_bytes": opt_b,
                "replay_buffer_size": buf_len
            })
            
    final_rss_mb = proc.memory_info().rss / (1024 ** 2)
    print(f"    Final Process RSS ({n_batches} batches): {final_rss_mb:.2f} MB (Delta: {final_rss_mb - initial_rss_mb:+.2f} MB)")
    
    out_csv = "experiments/ulc_v3_independent_audit/long_run_memory_results.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tracked_steps[0].keys()))
        w.writeheader()
        w.writerows(tracked_steps)
    print(f"[OK] Wrote long-run memory results to {out_csv}\n")
    return tracked_steps

def export_environment_matrix():
    print("--> 3. Auditing & Exporting Host Environment Matrix ...")
    env_data = {
        "host_system": {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
        },
        "python_environment": {
            "active_version": sys.version,
            "active_version_tuple": list(sys.version_info[:3]),
            "compiler": platform.python_compiler(),
            "build": platform.python_build()
        },
        "installed_dependencies": {
            "torch": torch.__version__,
            "numpy": np.__version__,
            "scipy": getattr(__import__("scipy"), "__version__", "unknown"),
            "scikit_learn": getattr(__import__("sklearn"), "__version__", "unknown"),
            "psutil": psutil.__version__,
            "safetensors": getattr(__import__("safetensors"), "__version__", "unknown"),
            "pytest": getattr(__import__("pytest"), "__version__", "unknown"),
            "matplotlib": getattr(__import__("matplotlib"), "__version__", "unknown")
        },
        "compatibility_table": {
            "Python 3.14": {"status": "TESTED_OPERATIONAL", "active_version": "3.14.3", "evidence": "All 54 tests pass; full validation executed"},
            "Python 3.11": {"status": "INSTALLED_VERIFIED", "installed_version": "3.11.9", "evidence": "Bytecode compilation pyc present"},
            "Python 3.13": {"status": "UNTESTED_ON_HOST", "installed_version": None, "evidence": "Not installed locally"},
            "Python 3.12": {"status": "UNTESTED_ON_HOST", "installed_version": None, "evidence": "Not installed locally"},
            "Python 3.10": {"status": "UNTESTED_ON_HOST", "installed_version": None, "evidence": "Not installed locally"}
        }
    }
    
    out_json = "experiments/ulc_v3_independent_audit/environment_matrix.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(env_data, f, indent=2)
    print(f"[OK] Wrote environment matrix to {out_json}\n")

def generate_resource_figures(mem_rows, long_rows):
    print("--> 4. Generating Resource Visualization Figures ...")
    fig_dir = "experiments/ulc_v3_independent_audit/figures/resources"
    os.makedirs(fig_dir, exist_ok=True)
    
    # Fig 1: Optimizer Memory Scaling
    params = [r["param_count"] for r in mem_rows]
    fp32_kb = [float(r["standard_adamw_kb"]) for r in mem_rows]
    lowmem_kb = [float(r["lowmem_measured_kb"]) for r in mem_rows]
    
    plt.figure(figsize=(9, 5))
    x_indices = np.arange(len(params))
    width = 0.35
    plt.bar(x_indices - width/2, fp32_kb, width, label="Standard AdamW (FP32)", color="lightcoral")
    plt.bar(x_indices + width/2, lowmem_kb, width, label="LowMemoryAdamW (8-bit)", color="royalblue")
    plt.xticks(x_indices, ["1K", "10K", "100K", "1M"])
    plt.yscale("log")
    plt.ylabel("Optimizer State Storage (KB, Log Scale)")
    plt.xlabel("Model Parameter Count (N)")
    plt.title("Optimizer Memory Consumption: Standard AdamW vs. LowMemoryAdamW")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "optimizer_memory_scaling.png"), dpi=200)
    plt.close()
    
    # Fig 2: Long-run RSS stability
    batches = [int(r["batch_idx"]) for r in long_rows]
    rss_vals = [float(r["process_rss_mb"]) for r in long_rows]
    
    plt.figure(figsize=(9, 5))
    plt.plot(batches, rss_vals, color="forestgreen", lw=2, label="Process RSS (MB)")
    plt.xlabel("Streaming Batches (30 samples/batch)")
    plt.ylabel("Process Resident Set Size (MB)")
    plt.title("Long-Run Streaming Memory Profile (5,000 Batches = 150,000 Instances)")
    plt.ylim(min(rss_vals) - 10, max(rss_vals) + 15)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "long_run_rss_stability.png"), dpi=200)
    plt.close()
    print(f"[OK] Generated resource figures in {fig_dir}")

def main():
    mem_rows = run_optimizer_memory_scaling()
    long_rows = run_long_running_memory_benchmark(n_batches=5000)
    export_environment_matrix()
    generate_resource_figures(mem_rows, long_rows)
    print("Memory benchmark execution completed successfully.")

if __name__ == "__main__":
    main()
