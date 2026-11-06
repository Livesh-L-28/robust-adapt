"""Stage 13 Security, Reliability, Error Handling and State Management Tests."""

import os
import tempfile
import numpy as np
import pytest

from robust_adapt.core.exceptions import SerializationError, ValidationError, ConfigurationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d
from robust_adapt.rao.recovery import ResilientCheckpointManager
from robust_adapt.ala.concept_memory import RecurringConceptMemory, ConceptSnapshot
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.ulc.v5_controller import UnifiedLearningControllerV5


def test_checkpoint_integrity_sha256() -> None:
    """Verify atomic checkpoint persistence and SHA-256 checksum verification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = ResilientCheckpointManager(checkpoint_dir=tmp_dir, max_to_keep=2)
        state = {"weights": [0.1, 0.2, 0.3], "step": 100}

        path = mgr.save_checkpoint(step=100, state_dict=state)
        assert os.path.exists(path)

        # Restore
        res = mgr.load_latest_checkpoint()
        assert res is not None
        step, restored = res
        assert step == 100
        assert restored["step"] == 100
        assert restored["weights"] == [0.1, 0.2, 0.3]


def test_tampering_and_bit_rot_detection() -> None:
    """Verify that tampering or bit rot is detected via SHA-256 digest verification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = ResilientCheckpointManager(checkpoint_dir=tmp_dir, max_to_keep=3)
        state_1 = {"weights": [1.0, 2.0], "step": 50}
        state_2 = {"weights": [3.0, 4.0], "step": 100}

        mgr.save_checkpoint(step=50, state_dict=state_1)
        path_2 = mgr.save_checkpoint(step=100, state_dict=state_2)

        # Inject bit rot / tampering into latest checkpoint
        with open(path_2, "r+b") as fp:
            data = bytearray(fp.read())
            data[len(data) // 2] ^= 0xFF  # Flip bits
            fp.seek(0)
            fp.write(data)

        # Manager should detect corruption and gracefully roll back to step 50
        res = mgr.load_latest_checkpoint()
        assert res is not None
        step, restored = res
        assert step == 50
        assert restored["weights"] == [1.0, 2.0]


def test_input_validation_nans_and_infs() -> None:
    """Verify that NaN and Inf floating-point inputs are strictly rejected."""
    nan_array = np.array([[1.0, np.nan], [0.5, 0.2]])
    with pytest.raises(ValidationError, match="contains NaN or Infinite values"):
        check_array_2d(nan_array, name="test_nan")

    inf_array = np.array([[1.0, np.inf], [0.5, 0.2]])
    with pytest.raises(ValidationError, match="contains NaN or Infinite values"):
        check_array_2d(inf_array, name="test_inf")


def test_label_validation_bounds() -> None:
    """Verify that invalid discrete target labels are strictly rejected."""
    y_invalid_negative = np.array([-1, 0, 1])
    with pytest.raises(ValidationError, match="contains negative class labels"):
        check_labels_1d(y_invalid_negative, expected_len=3, n_classes=2, name="y_neg")

    y_out_of_bounds = np.array([0, 1, 2])
    with pytest.raises(ValidationError, match="exceeds valid range"):
        check_labels_1d(y_out_of_bounds, expected_len=3, n_classes=2, name="y_oob")


def test_ulc_v5_resilient_checkpointing() -> None:
    """Verify end-to-end ULC-v5 serialization, checksumming, and state restoration."""
    rng = np.random.RandomState(42)
    ulc = UnifiedLearningControllerV5(n_features=3, n_classes=2)

    for _ in range(10):
        X = rng.randn(20, 3)
        y = (X[:, 0] > 0).astype(int)
        ulc.step(X, y)

    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = ResilientCheckpointManager(checkpoint_dir=tmp_dir, max_to_keep=2)
        state = ulc.state_dict()
        mgr.save_checkpoint(step=ulc.total_steps, state_dict=state)

        res = mgr.load_latest_checkpoint()
        assert res is not None
        step, loaded_state = res
        assert step == 10
        assert loaded_state["total_steps"] == 10

        ulc_restored = UnifiedLearningControllerV5(n_features=3, n_classes=2)
        ulc_restored.load_state_dict(loaded_state)
        assert ulc_restored.total_steps == 10
        assert ulc_restored.total_resets == ulc.total_resets


def test_memory_and_buffer_capacity_bounding() -> None:
    """Verify strict bounded memory capacity enforcement across recurring memory and reservoir replay."""
    # 1. Reservoir replay capacity bounds
    replay = ClassBalancedReservoirReplay(capacity=50, n_classes=2)
    rng = np.random.RandomState(99)
    for _ in range(10):
        X = rng.randn(20, 2)
        y = rng.randint(0, 2, size=20)
        replay.add(X, y)

    assert replay.total_stored <= 50

    # 2. Recurring concept memory capacity bounds
    memory = RecurringConceptMemory(max_concepts=3, similarity_threshold=0.80)
    for i in range(10):
        fp = rng.randn(10)
        memory.store_concept(fingerprint=fp, model_state=None, step=i)

    assert memory.n_stored <= 3
