"""
Unit tests for safe state serialization and checkpoint manager.
"""

from pathlib import Path
import numpy as np
import pytest

from adaptive_ml.state.checkpoint import CheckpointManager
from adaptive_ml.state.serializer import load_state, save_state


def test_safetensors_save_and_load(tmp_path: Path) -> None:
    filepath = tmp_path / "model_state"

    tensors = {
        "weight": np.random.randn(10, 5).astype(np.float32),
        "bias": np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32),
        "step_count": np.array([42], dtype=np.int64),
    }
    meta = {"model_name": "AdaptiveClassifier", "version": "0.1.0"}

    save_state(filepath, tensors, metadata=meta)

    loaded_tensors, loaded_meta = load_state(filepath)

    assert loaded_meta["model_name"] == "AdaptiveClassifier"
    assert loaded_meta["version"] == "0.1.0"
    for k in tensors:
        np.testing.assert_allclose(loaded_tensors[k], tensors[k])


def test_checkpoint_manager_atomic_and_pruning(tmp_path: Path) -> None:
    manager = CheckpointManager(checkpoint_dir=tmp_path, max_checkpoints=3)

    tensors = {"w": np.ones((4, 4), dtype=np.float32)}

    # Save 5 checkpoints
    for step in range(1, 6):
        manager.save_checkpoint(step=step, tensors=tensors, metadata={"metric": step * 10})

    # Only the last 3 checkpoints should be retained: [3, 4, 5]
    available_steps = manager.list_checkpoints()
    assert available_steps == [3, 4, 5]

    # Load latest (step 5)
    latest_tensors, latest_meta = manager.load_latest()
    assert latest_meta["step"] == 5
    assert latest_meta["metric"] == 50
    np.testing.assert_allclose(latest_tensors["w"], tensors["w"])

    # Load specific step (step 3)
    step3_tensors, step3_meta = manager.load_step(3)
    assert step3_meta["step"] == 3
    assert step3_meta["metric"] == 30
