"""
Workstream F: Performance and Latency Benchmark Script.
Profiles initialization time, prediction latency, update latency, end-to-end latency,
controller decision latency, throughput (samples/sec), and percentiles (P50, P95, P99, Max).
Outputs performance_results.csv and figures/resources/throughput_latency_profile.png.
"""

import csv
import json
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import (
    generate_stream,
    ParamWrapper,
    AdaptiveClassifier,
    LowMemoryAdamW,
    RobustLearningPipeline,
    AdaptiveLearningController,
    ControllerState
)

MODELS = [
    "Static_Baseline",
    "ALA_Only",
    "RLA_Only",
    "RAO_Only",
    "ALA_plus_RLA",
    "ALA_plus_RAO",
    "RLA_plus_RAO",
    "Uncoordinated_Three_Pillars",
    "Full_ULC_v1",
    "Optimized_ULC_v2",
    "MultiObjective_ULC_v3"
]

def run_performance_benchmarks():
    print("================================================================================")
    print("WORKSTREAM F: PERFORMANCE & LATENCY PROFILING")
    print("================================================================================\n")
    
    stream = generate_stream(seed=42, n_batches=100, batch_size=30, n_features=4)
    n_samples_total = 100 * 30
    
    rows = []
    
    for model_name in MODELS:
        print(f"--> Profiling: {model_name:30s} ...", end=" ", flush=True)
        
        # 1. Initialization Time
        t_init_start = time.perf_counter()
        clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=20, enable_drift_detection=True)
        pipeline = RobustLearningPipeline(n_classes=2)
        p_wrapper = ParamWrapper(np.random.randn(4, 2).astype(np.float32) * 0.01)
        opt = LowMemoryAdamW([p_wrapper], lr=0.01)
        controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
        init_time_ms = (time.perf_counter() - t_init_start) * 1000.0
        
        # Warm-up (5 batches)
        for b in range(5):
            X = stream[b]["X"]
            y = stream[b]["y_observed"]
            if "Tree" in model_name or "Static" in model_name or "ALA" in model_name:
                clf.partial_fit(X, y)
            if "RAO" in model_name:
                p_wrapper.grad = np.random.randn(4, 2)
                opt.step()
                
        # 2. Benchmark 100 Batches
        batch_latencies = []
        pred_latencies = []
        update_latencies = []
        controller_latencies = []
        
        for b_idx in range(5, 100):
            X_b = stream[b_idx]["X"]
            y_obs = stream[b_idx]["y_observed"]
            delta = stream[b_idx]["delta"]
            
            t_batch_start = time.perf_counter()
            
            # Predict Phase
            t_pred_start = time.perf_counter()
            if model_name == "Static_Baseline":
                p_pred = clf.predict(X_b)
            elif model_name in ("RAO_Only", "RLA_plus_RAO"):
                logits = X_b @ p_wrapper.data
                p_pred = np.argmax(logits, axis=1)
            elif model_name == "MultiObjective_ULC_v3":
                p_tree = clf.predict_proba(X_b) if clf.samples_seen_ > 0 else np.zeros((len(X_b), 2)) + 0.5
                p_lin = np.exp(X_b @ p_wrapper.data)
                p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                p_pred = np.argmax(0.50 * p_tree + 0.50 * p_lin, axis=1)
            else:
                p_pred = clf.predict(X_b) if clf.samples_seen_ > 0 else np.zeros(len(X_b), dtype=int)
            pred_time_ms = (time.perf_counter() - t_pred_start) * 1000.0
            pred_latencies.append(pred_time_ms)
            
            # Controller Phase (if applicable)
            t_ctrl_start = time.perf_counter()
            if "ULC" in model_name:
                directive, info = controller.step(X_b, y_obs, delta_drift=delta)
                if directive.purge_replay and hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                    clf._replay_buffer.clear()
                if directive.state == ControllerState.CONFIRMED_DRIFT and "v3" in model_name:
                    clf.reset()
                    opt.state.clear()
            ctrl_time_ms = (time.perf_counter() - t_ctrl_start) * 1000.0
            controller_latencies.append(ctrl_time_ms)
            
            # Update Phase
            t_up_start = time.perf_counter()
            if "ALA" in model_name or "Static" in model_name or "ULC" in model_name:
                if model_name != "Static_Baseline":
                    clf.partial_fit(X_b, y_obs)
            if "RAO" in model_name or "Uncoordinated" in model_name or "ULC" in model_name:
                p_wrapper.grad = np.random.randn(4, 2)
                opt.step()
            up_time_ms = (time.perf_counter() - t_up_start) * 1000.0
            update_latencies.append(up_time_ms)
            
            total_b_ms = (time.perf_counter() - t_batch_start) * 1000.0
            batch_latencies.append(total_b_ms)
            
        arr = np.array(batch_latencies)
        mean_lat = float(np.mean(arr))
        p50 = float(np.percentile(arr, 50))
        p95 = float(np.percentile(arr, 95))
        p99 = float(np.percentile(arr, 99))
        p_max = float(np.max(arr))
        p_std = float(np.std(arr, ddof=1))
        
        # Throughput in samples per second
        throughput = (len(arr) * 30.0) / (np.sum(arr) / 1000.0)
        
        mean_pred = float(np.mean(pred_latencies))
        mean_up = float(np.mean(update_latencies))
        mean_ctrl = float(np.mean(controller_latencies)) if "ULC" in model_name else 0.0
        
        rows.append({
            "configuration": model_name,
            "init_time_ms": f"{init_time_ms:.4f}",
            "mean_batch_latency_ms": f"{mean_lat:.4f}",
            "p50_latency_ms": f"{p50:.4f}",
            "p95_latency_ms": f"{p95:.4f}",
            "p99_latency_ms": f"{p99:.4f}",
            "max_latency_ms": f"{p_max:.4f}",
            "std_latency_ms": f"{p_std:.4f}",
            "prediction_latency_ms": f"{mean_pred:.4f}",
            "update_latency_ms": f"{mean_up:.4f}",
            "controller_decision_ms": f"{mean_ctrl:.4f}",
            "throughput_samples_per_sec": f"{throughput:.2f}"
        })
        print(f"Done. Lat: {mean_lat:.3f} ms (P95: {p95:.3f} ms) | Throughput: {throughput:8.1f} samples/s")
        
    out_csv = "experiments/ulc_v3_independent_audit/performance_results.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n[OK] Wrote performance results to {out_csv}")
    
    # Generate Figure
    fig_dir = "experiments/ulc_v3_independent_audit/figures/resources"
    os.makedirs(fig_dir, exist_ok=True)
    
    m_names = [r["configuration"].replace("_", " ") for r in rows]
    throughputs = [float(r["throughput_samples_per_sec"]) for r in rows]
    lat_means = [float(r["mean_batch_latency_ms"]) for r in rows]
    
    fig, ax1 = plt.subplots(figsize=(11, 6))
    
    color = "tab:blue"
    ax1.set_xlabel("System Configuration")
    ax1.set_ylabel("Throughput (Samples/Sec)", color=color)
    bars = ax1.bar(m_names, throughputs, color=color, alpha=0.7, width=0.4, align="edge")
    ax1.tick_params(axis="y", labelcolor=color)
    plt.xticks(rotation=35, ha="right", fontsize=9)
    
    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Batch Latency (ms)", color=color)
    lines = ax2.plot(m_names, lat_means, color=color, marker="o", lw=2, label="Mean Latency (ms)")
    ax2.tick_params(axis="y", labelcolor=color)
    
    plt.title("Streaming Throughput and Batch Latency across 11 Configurations")
    plt.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    plt.savefig(os.path.join(fig_dir, "throughput_latency_profile.png"), dpi=200)
    plt.close()
    print(f"[OK] Wrote throughput_latency_profile.png to {fig_dir}")

if __name__ == "__main__":
    run_performance_benchmarks()

