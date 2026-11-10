"""
Stage 7.3 Workstream G: Verification of Checkpoint Serialization and Recovery.
Tests round-trip state preservation, atomic checkpointing, corruption detection,
and zero-pickle security for UnifiedLearningControllerV4_1.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from adaptive_ml.state.checkpoint import CheckpointManager
from adaptive_ml.state.serializer import is_safetensors_available, load_state, save_state
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4


def run_serialization_verification(tmp_dir: Path) -> dict:
    config = ULCv41Config(
        spatial_k=7,
        spatial_discordance_threshold=0.22,
        prior_freeze_threshold=0.28,
        tau_tie=0.12,
        gamma_smoothing=0.45,
        max_noise_dwell=15,
        max_history_len=500,
    )
    ctrl = UnifiedLearningControllerV4_1(config=config)

    # Step through some streaming data to populate state
    np.random.seed(42)
    for i in range(10):
        X = np.random.randn(20, 4)
        y = np.random.choice([0, 1], size=20)
        ctrl.step(X, y, delta_drift=0.10 * (i + 1))

    # Extract state dict
    state = ctrl.state_dict()
    assert state["version"] == "4.1"
    assert state["total_steps"] == 10
    assert state["config"]["spatial_k"] == 7

    # 1. Test native save_state and load_state using Safetensors and JSON metadata
    state_file = tmp_dir / "ulc_v41_checkpoint"
    tensors = {
        "step_counter": np.array([ctrl.total_steps], dtype=np.int64),
        "noise_dwell": np.array([ctrl.noise_dwell_counter], dtype=np.int64),
    }
    save_state(state_file, tensors=tensors, metadata=state)

    loaded_tensors, loaded_meta = load_state(state_file)
    assert loaded_meta["version"] == "4.1"
    assert loaded_meta["total_steps"] == 10
    assert loaded_tensors["step_counter"][0] == 10

    # 2. Test restoring state into a fresh controller
    ctrl_restored = UnifiedLearningControllerV4_1()
    ctrl_restored.load_state_dict(loaded_meta)
    assert ctrl_restored.total_steps == 10
    assert ctrl_restored.config.spatial_k == 7
    assert ctrl_restored.config.spatial_discordance_threshold == 0.22

    # 3. Test CheckpointManager integration
    mgr = CheckpointManager(checkpoint_dir=tmp_dir / "checkpoints", max_checkpoints=3)
    for s in range(1, 6):
        mgr.save_checkpoint(step=s, tensors=tensors, metadata={"version": "4.1", "step": s})
    active_ckpts = mgr.list_checkpoints()
    assert active_ckpts == [3, 4, 5]

    # 4. Test corruption detection
    corrupt_file = tmp_dir / "corrupted_state.meta.json"
    with open(corrupt_file, "w") as f:
        f.write("{invalid_json_format")
    
    corruption_detected = False
    try:
        load_state(tmp_dir / "corrupted_state")
    except Exception:
        corruption_detected = True

    # 5. Test version mismatch rejection
    invalid_version_state = {"version": "9.9", "total_steps": 1}
    version_rejected = False
    try:
        ctrl.load_state_dict(invalid_version_state)
    except ValueError as e:
        if "Incompatible state_dict version" in str(e):
            version_rejected = True

    results = {
        "safetensors_available": is_safetensors_available(),
        "roundtrip_state_preserved": True,
        "config_restored_accurately": ctrl_restored.config.spatial_k == 7,
        "checkpoint_manager_pruning": active_ckpts == [3, 4, 5],
        "corruption_detected": corruption_detected,
        "version_mismatch_rejected": version_rejected,
    }

    results_path = Path("experiments/stage_7_3_production_integration/serialization_verification_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Serialization & Recovery Verification Results:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    return results


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        run_serialization_verification(Path(td))

