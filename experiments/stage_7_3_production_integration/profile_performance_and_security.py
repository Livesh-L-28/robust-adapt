"""
Stage 7.3 Workstream J: Detailed Profiling of Performance, Latency, Memory, and Security.
========================================================================================
Measures component latencies, memory footprint over long streams, and validates
security controls against malformed inputs, NaNs, infinities, and corrupted states.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
import numpy as np

from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.telemetry import get_process_memory_bytes
from adaptive_ml.state.serializer import load_state, save_state
from adaptive_ml.ulc.spatial import compute_spatial_discordance
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4
from adaptive_ml.ulc.v4_evidence import EvidenceSynthesizerV4


def run_profiling_and_security_suite() -> dict:
    np.random.seed(42)

    # =========================================================================
    # 1. Component Latency Profiling (1,000 iterations per component)
    # =========================================================================
    N_ITERS = 1000
    X_sample = np.random.randn(50, 4)
    y_sample = np.random.choice([0, 1], size=50)

    # 1.1. Spatial Discordance
    t0 = time.perf_counter()
    for _ in range(N_ITERS):
        compute_spatial_discordance(X_sample, y_sample, k=5)
    spatial_lat_ms = ((time.perf_counter() - t0) / N_ITERS) * 1000.0

    # 1.2. Evidence Generation
    synth = EvidenceSynthesizerV4()
    probas_sample = np.random.uniform(0.1, 0.9, size=(50, 2))
    probas_sample /= np.sum(probas_sample, axis=1, keepdims=True)
    t0 = time.perf_counter()
    for _ in range(N_ITERS):
        synth.synthesize(delta_drift=0.5, probas=probas_sample)
    evidence_lat_ms = ((time.perf_counter() - t0) / N_ITERS) * 1000.0

    # 1.3. Controller Initialization
    t0 = time.perf_counter()
    for _ in range(N_ITERS):
        ctrl = UnifiedLearningControllerV4_1()
    init_lat_ms = ((time.perf_counter() - t0) / N_ITERS) * 1000.0

    # 1.4. Controller Step (Full lifecycle, without explanation)
    ctrl = UnifiedLearningControllerV4_1()
    step_latencies = []
    for _ in range(N_ITERS):
        t_start = time.perf_counter()
        ctrl.step(X_sample, y_sample, delta_drift=0.1)
        step_latencies.append((time.perf_counter() - t_start) * 1000.0)

    # 1.5. On-Demand Explanation Latency
    t0 = time.perf_counter()
    for _ in range(100):
        ctrl.explain()
    explain_lat_ms = ((time.perf_counter() - t0) / 100) * 1000.0

    # 1.6. Checkpoint Serialization & Recovery
    tmp_path = Path("experiments/stage_7_3_production_integration/profile_ckpt")
    t0 = time.perf_counter()
    sd = ctrl.state_dict()
    save_state(tmp_path, tensors={"step": np.array([ctrl.total_steps])}, metadata=sd)
    ckpt_save_lat_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    loaded_tensors, loaded_meta = load_state(tmp_path)
    ctrl.load_state_dict(loaded_meta)
    ckpt_load_lat_ms = (time.perf_counter() - t0) * 1000.0

    # Measure Checkpoint file sizes
    safetensors_size = (tmp_path.with_suffix(".safetensors")).stat().st_size
    meta_json_size = (tmp_path.with_suffix(".meta.json")).stat().st_size

    # Clean up temp checkpoint
    try:
        tmp_path.with_suffix(".safetensors").unlink(missing_ok=True)
        tmp_path.with_suffix(".meta.json").unlink(missing_ok=True)
    except Exception:
        pass

    # =========================================================================
    # 2. Long-Running Stream Memory & Ring Buffer Boundedness (5,000 steps)
    # =========================================================================
    LONG_STEPS = 5000
    ctrl_long = UnifiedLearningControllerV4_1(config=ULCv41Config(max_history_len=1000))
    initial_rss = get_process_memory_bytes() / (1024**2)

    rss_samples = []
    for step in range(LONG_STEPS):
        ctrl_long.step(X_sample, y_sample, delta_drift=0.1)
        if step % 1000 == 0:
            rss_samples.append(get_process_memory_bytes() / (1024**2))

    final_rss = get_process_memory_bytes() / (1024**2)
    history_bounded = len(ctrl_long.history_) <= 1000
    intervention_history_bounded = len(ctrl_long.intervention_history_) <= 1000

    # =========================================================================
    # 3. Security & Input Validation Tests
    # =========================================================================
    security_results = {}

    # 3.1. NaN in features
    X_nan = np.copy(X_sample)
    X_nan[0, 0] = np.nan
    try:
        ctrl.step(X_nan, y_sample)
        security_results["nan_features_rejected"] = False
    except (ValueError, ValidationError):
        security_results["nan_features_rejected"] = True

    # 3.2. Infinity in features
    X_inf = np.copy(X_sample)
    X_inf[0, 0] = np.inf
    try:
        ctrl.step(X_inf, y_sample)
        security_results["inf_features_rejected"] = False
    except (ValueError, ValidationError):
        security_results["inf_features_rejected"] = True

    # 3.3. Dimension mismatch between X and y
    try:
        ctrl.step(X_sample, y_sample[:10])
        security_results["shape_mismatch_rejected"] = False
    except (ValueError, ValidationError):
        security_results["shape_mismatch_rejected"] = True

    # 3.4. Invalid 1D feature array
    try:
        ctrl.step(np.ones(50), y_sample)
        security_results["1d_feature_array_rejected"] = False
    except (ValueError, ValidationError):
        security_results["1d_feature_array_rejected"] = True

    # 3.5. Invalid config bounds
    try:
        ULCv41Config(spatial_discordance_threshold=-0.5)
        security_results["invalid_config_rejected"] = False
    except ValueError:
        security_results["invalid_config_rejected"] = True

    # 3.6. Checkpoint version mismatch
    try:
        ctrl.load_state_dict({"version": "3.0", "total_steps": 10})
        security_results["version_mismatch_rejected"] = False
    except ValueError:
        security_results["version_mismatch_rejected"] = True

    # Compile results
    lat_arr = np.array(step_latencies)
    results = {
        "component_latency_ms": {
            "spatial_discordance": float(spatial_lat_ms),
            "evidence_synthesis": float(evidence_lat_ms),
            "controller_init": float(init_lat_ms),
            "controller_step_mean": float(np.mean(lat_arr)),
            "controller_step_p50": float(np.percentile(lat_arr, 50)),
            "controller_step_p95": float(np.percentile(lat_arr, 95)),
            "controller_step_p99": float(np.percentile(lat_arr, 99)),
            "on_demand_explain": float(explain_lat_ms),
            "checkpoint_save": float(ckpt_save_lat_ms),
            "checkpoint_load": float(ckpt_load_lat_ms),
        },
        "memory_and_resources": {
            "initial_rss_mb": float(initial_rss),
            "final_rss_mb": float(final_rss),
            "rss_delta_mb": float(final_rss - initial_rss),
            "history_length_at_5000_steps": len(ctrl_long.history_),
            "history_strictly_bounded": history_bounded,
            "intervention_history_strictly_bounded": intervention_history_bounded,
            "safetensors_bytes": int(safetensors_size),
            "meta_json_bytes": int(meta_json_size),
        },
        "security_controls": security_results,
    }

    out_file = Path("experiments/stage_7_3_production_integration/performance_and_security_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("Performance & Security Profile Summary:")
    print(f"  Step Latency Mean: {results['component_latency_ms']['controller_step_mean']:.3f}ms")
    print(f"  Step Latency P99:  {results['component_latency_ms']['controller_step_p99']:.3f}ms")
    print(f"  Spatial Discordance Latency: {results['component_latency_ms']['spatial_discordance']:.3f}ms")
    print(f"  Memory Delta (5000 steps): {results['memory_and_resources']['rss_delta_mb']:.2f} MB")
    print(f"  History Ring Buffer Bounded: {history_bounded} (len={len(ctrl_long.history_)})")
    print(f"  Security Controls Passed: {all(security_results.values())} ({security_results})")

    return results


if __name__ == "__main__":
    run_profiling_and_security_suite()

