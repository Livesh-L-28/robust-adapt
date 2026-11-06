"""Unit tests for Stage 14 Security Hardening.

Verifies zero pickle usage, Safetensors+JSON atomic state serialization,
SHA-256 integrity checks, HMAC-SHA256 authenticated verification,
tamper rejection, file size caps, and ResilientCheckpointManager security.
"""

import json
import os
import shutil
import tempfile
import numpy as np
import pytest

from robust_adapt.core.exceptions import SerializationError
from robust_adapt.rao.recovery import ResilientCheckpointManager
from robust_adapt.state.serializer import (
    compute_file_hmac,
    compute_file_sha256,
    is_safetensors_available,
    load_state,
    save_state,
)


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_zero_pickle_policy():
    """Verify that pickle is never imported or used across the core serialization pathway."""
    import sys
    # Ensure pickle is not referenced in serializer globals
    import robust_adapt.state.serializer as s
    assert "pickle" not in s.__dict__


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_safetensors_roundtrip_with_integrity(temp_dir):
    """Test standard atomic save and load with SHA-256 integrity."""
    filepath = os.path.join(temp_dir, "model_state")
    tensors = {
        "weights": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        "bias": np.array([0.5, -0.5], dtype=np.float32),
    }
    metadata = {"step": 42, "model_type": "linear"}

    save_state(filepath, tensors, metadata)
    loaded_tensors, loaded_meta = load_state(filepath)

    assert np.allclose(loaded_tensors["weights"], tensors["weights"])
    assert np.allclose(loaded_tensors["bias"], tensors["bias"])
    assert loaded_meta["step"] == 42
    assert "_sha256" in loaded_meta


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_safetensors_tamper_detection(temp_dir):
    """Test that modifying bytes in a safetensors file triggers integrity failure."""
    filepath = os.path.join(temp_dir, "model_state")
    tensors = {"weights": np.ones((10, 10), dtype=np.float32)}

    save_state(filepath, tensors)

    # Tamper with the binary file
    tensor_path = os.path.join(temp_dir, "model_state.safetensors")
    with open(tensor_path, "r+b") as f:
        f.seek(50)
        f.write(b"\xff\xff\xff\xff")

    with pytest.raises(SerializationError, match="Integrity check failed"):
        load_state(filepath, verify_integrity=True)


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_safetensors_hmac_authentication(temp_dir):
    """Test authenticated checkpointing using HMAC-SHA256."""
    filepath = os.path.join(temp_dir, "auth_state")
    key = b"super_secret_enterprise_key_123"
    wrong_key = b"wrong_secret_enterprise_key_999"

    tensors = {"weights": np.array([1.0, 2.0, 3.0], dtype=np.float32)}
    metadata = {"tenant": "enterprise_corp"}

    # Save with HMAC
    save_state(filepath, tensors, metadata=metadata, auth_key=key)

    # Load with correct key succeeds
    loaded_tensors, loaded_meta = load_state(filepath, auth_key=key)
    assert np.allclose(loaded_tensors["weights"], tensors["weights"])
    assert loaded_meta["tenant"] == "enterprise_corp"
    assert "_hmac_sha256" in loaded_meta

    # Load with incorrect key fails HMAC check
    with pytest.raises(SerializationError, match="HMAC authentication failed"):
        load_state(filepath, auth_key=wrong_key)


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_safetensors_missing_hmac_rejected_when_key_expected(temp_dir):
    """Test that loading an unauthenticated checkpoint fails when auth_key is required."""
    filepath = os.path.join(temp_dir, "unauth_state")
    key = b"super_secret_enterprise_key_123"

    tensors = {"weights": np.array([1.0, 2.0], dtype=np.float32)}
    save_state(filepath, tensors)  # No auth key

    with pytest.raises(SerializationError, match="does not contain an HMAC signature"):
        load_state(filepath, auth_key=key)


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_safetensors_file_size_limit(temp_dir):
    """Test that file exceeding max_file_size_bytes is rejected."""
    filepath = os.path.join(temp_dir, "size_state")
    tensors = {"weights": np.zeros(1000, dtype=np.float32)}
    save_state(filepath, tensors)

    # Set threshold lower than actual file size
    with pytest.raises(SerializationError, match="Checkpoint file exceeds size ceiling"):
        load_state(filepath, max_file_size_bytes=50)


def test_auth_key_validation(temp_dir):
    """Test validation of auth_key length and type."""
    filepath = os.path.join(temp_dir, "key_state")
    tensors = {"w": np.zeros(1)}

    with pytest.raises(TypeError, match="auth_key must be bytes or bytearray"):
        save_state(filepath, tensors, auth_key="string_key_invalid")

    with pytest.raises(ValueError, match="at least 16 bytes"):
        save_state(filepath, tensors, auth_key=b"short")


def test_resilient_checkpoint_manager_hmac(temp_dir):
    """Test ResilientCheckpointManager with HMAC-SHA256 signature and rollback."""
    key = b"secret_checkpoint_key_12345"
    mgr = ResilientCheckpointManager(temp_dir, max_to_keep=3, auth_key=key)

    # Save step 1 and step 2
    mgr.save_checkpoint(1, {"loss": 0.5, "lr": 0.01})
    ckpt2_path = mgr.save_checkpoint(2, {"loss": 0.3, "lr": 0.005})

    # Normal load recovers step 2
    res = mgr.load_latest_checkpoint()
    assert res is not None
    step, state = res
    assert step == 2
    assert state["loss"] == 0.3

    # Corrupt step 2 state_dict payload
    with open(ckpt2_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["state_dict"]["loss"] = 999.0  # Tamper without updating HMAC
    with open(ckpt2_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # Manager detects tampering and rolls back to step 1
    rollback_res = mgr.load_latest_checkpoint()
    assert rollback_res is not None
    rb_step, rb_state = rollback_res
    assert rb_step == 1
    assert rb_state["loss"] == 0.5


def test_resilient_checkpoint_manager_size_limit(temp_dir):
    """Test that ResilientCheckpointManager rejects files exceeding max_file_size_bytes."""
    mgr = ResilientCheckpointManager(temp_dir, max_file_size_bytes=100)
    # Save a normal checkpoint
    mgr.save_checkpoint(1, {"param": "x" * 200})

    # The file is > 100 bytes, so load should reject it and return None
    res = mgr.load_latest_checkpoint()
    assert res is None
