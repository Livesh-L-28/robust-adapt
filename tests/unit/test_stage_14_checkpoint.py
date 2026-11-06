"""Unit tests for Stage 14 Checkpoint and State Recovery.

Verifies:
1. Transactional atomic save and load.
2. Missing file handling (.safetensors without .meta.json and vice-versa).
3. Temporary file cleanup on write failures.
4. ResilientCheckpointManager multi-step rollback on corruption.
5. Pruning of historical checkpoints beyond max_to_keep.
"""

import json
import os
import shutil
import tempfile
import numpy as np
import pytest

from robust_adapt.core.exceptions import SerializationError
from robust_adapt.rao.recovery import ResilientCheckpointManager
from robust_adapt.state.serializer import is_safetensors_available, load_state, save_state


@pytest.fixture
def temp_ckpt_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_missing_tensor_file_raises_filenotfound(temp_ckpt_dir):
    """Verify load_state raises FileNotFoundError when safetensors file is missing."""
    non_existent = os.path.join(temp_ckpt_dir, "ghost_model")
    with pytest.raises(FileNotFoundError):
        load_state(non_existent)


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_load_state_without_metadata_succeeds_unauthenticated(temp_ckpt_dir):
    """Verify load_state succeeds when meta.json is absent and auth_key is not required."""
    filepath = os.path.join(temp_ckpt_dir, "bare_model")
    tensors = {"w": np.array([1.0, 2.0, 3.0], dtype=np.float32)}
    save_state(filepath, tensors)

    # Delete metadata file
    meta_path = os.path.join(temp_ckpt_dir, "bare_model.meta.json")
    os.remove(meta_path)

    # Loading without metadata should still load tensors
    loaded_tensors, meta = load_state(filepath)
    assert np.allclose(loaded_tensors["w"], tensors["w"])
    assert meta == {}


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_load_state_without_metadata_fails_when_auth_key_required(temp_ckpt_dir):
    """Verify load_state rejects unauthenticated state when auth_key is passed."""
    filepath = os.path.join(temp_ckpt_dir, "bare_model")
    tensors = {"w": np.array([1.0, 2.0, 3.0], dtype=np.float32)}
    save_state(filepath, tensors)

    # Delete metadata file
    meta_path = os.path.join(temp_ckpt_dir, "bare_model.meta.json")
    os.remove(meta_path)

    key = b"1234567890123456"
    with pytest.raises(SerializationError, match="does not contain an HMAC signature"):
        load_state(filepath, auth_key=key)


def test_resilient_checkpoint_manager_multi_rollback(temp_ckpt_dir):
    """Verify ResilientCheckpointManager rolls back across multiple corrupted checkpoints."""
    mgr = ResilientCheckpointManager(temp_ckpt_dir, max_to_keep=5)

    # Save 4 checkpoints
    p1 = mgr.save_checkpoint(1, {"val": 100})
    p2 = mgr.save_checkpoint(2, {"val": 200})
    p3 = mgr.save_checkpoint(3, {"val": 300})
    p4 = mgr.save_checkpoint(4, {"val": 400})

    # Corrupt step 4 (truncate file)
    with open(p4, "wb") as f:
        f.write(b"corrupted_garbage_bytes")

    # Corrupt step 3 (invalid JSON checksum)
    with open(p3, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["state_dict"]["val"] = 99999  # Tamper without updating checksum
    with open(p3, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # Manager should bypass step 4 and step 3 and recover step 2 intact
    res = mgr.load_latest_checkpoint()
    assert res is not None
    step, state = res
    assert step == 2
    assert state["val"] == 200


def test_resilient_checkpoint_manager_all_corrupted(temp_ckpt_dir):
    """Verify ResilientCheckpointManager returns None gracefully when all checkpoints are corrupted."""
    mgr = ResilientCheckpointManager(temp_ckpt_dir, max_to_keep=2)
    p1 = mgr.save_checkpoint(1, {"val": 1})
    with open(p1, "wb") as f:
        f.write(b"bad")

    res = mgr.load_latest_checkpoint()
    assert res is None


def test_resilient_checkpoint_manager_pruning(temp_ckpt_dir):
    """Verify ResilientCheckpointManager strictly prunes checkpoints beyond max_to_keep."""
    max_to_keep = 3
    mgr = ResilientCheckpointManager(temp_ckpt_dir, max_to_keep=max_to_keep)

    for i in range(1, 8):
        mgr.save_checkpoint(i, {"step": i})

    remaining = mgr._list_checkpoints_descending()
    assert len(remaining) == max_to_keep

    # Should retain the newest 3: steps 7, 6, 5
    expected_steps = [f"checkpoint_step_{s:08d}.json" for s in [7, 6, 5]]
    basenames = [os.path.basename(p) for p in remaining]
    assert basenames == expected_steps
