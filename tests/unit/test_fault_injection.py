"""
Stage 10 Comprehensive Fault-Injection and Failure Recovery Test Suite.

Verifies 20 distinct failure modes and recovery behaviors across ROBUST-ADAPT.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from robust_adapt.core.exceptions import (
    AdaptiveMLError,
    ConfigurationError,
    SerializationError,
    ValidationError,
)
from robust_adapt.core.validation import (
    check_array_2d,
    check_labels_1d,
    check_probabilities,
    check_sample_weights,
)
from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.rla.losses import GeneralizedCrossEntropyLoss, SymmetricCrossEntropyLoss
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from robust_adapt.ulc.v4_automaton import AutomatonStateV4
from robust_adapt.state.serializer import load_state, save_state
from robust_adapt.integrations.data import to_numpy, to_tensor


class TestFaultInjectionAndRecovery:
    """20 fault-injection test cases verifying failure isolation and graceful recovery."""

    # Scenario 1: Missing optional dependency message clarity
    def test_01_missing_dependency_actionable_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify calling to_tensor without PyTorch raises an actionable ImportError."""
        import robust_adapt.integrations.data as data_mod
        monkeypatch.setattr(data_mod, "_TORCH_AVAILABLE", False)
        with pytest.raises(ImportError, match="pip install 'robust-adapt\\[torch\\]'"):
            to_tensor(np.array([1.0, 2.0]))

    # Scenario 2: Invalid dataset type
    def test_02_invalid_dataset_type_rejected(self) -> None:
        """Verify passing unsupported objects raises ValidationError."""
        with pytest.raises(ValidationError, match="Unsupported data type"):
            to_numpy({"a": 1, "b": 2})

    # Scenario 3: Unexpected tensor shape (3D array to check_array_2d)
    def test_03_unexpected_3d_shape_rejected(self) -> None:
        """Verify 3D array raises ValidationError."""
        arr_3d = np.ones((10, 5, 2))
        with pytest.raises(ValidationError, match="must be a 2D array"):
            check_array_2d(arr_3d)

    # Scenario 4: NaN input in features
    def test_04_nan_input_rejected(self) -> None:
        """Verify array containing NaN raises ValidationError."""
        arr = np.array([[1.0, 2.0], [np.nan, 4.0]])
        with pytest.raises(ValidationError, match="contains NaN or Infinite"):
            check_array_2d(arr)

    # Scenario 5: Infinity input in features
    def test_05_infinity_input_rejected(self) -> None:
        """Verify array containing Inf raises ValidationError."""
        arr = np.array([[1.0, np.inf], [3.0, 4.0]])
        with pytest.raises(ValidationError, match="contains NaN or Infinite"):
            check_array_2d(arr)

    # Scenario 6: Empty batch (0 samples)
    def test_06_empty_batch_rejected(self) -> None:
        """Verify 0-row array raises ValidationError."""
        arr = np.empty((0, 4))
        with pytest.raises(ValidationError, match="cannot be empty"):
            check_array_2d(arr)

    # Scenario 7: Oversized batch dimension mismatch
    def test_07_feature_dimension_mismatch_rejected(self) -> None:
        """Verify unexpected column count raises ValidationError."""
        arr = np.ones((10, 8))
        with pytest.raises(ValidationError, match="feature dimension mismatch"):
            check_array_2d(arr, expected_dim=4)

    # Scenario 8: Corrupted checkpoint (tampered bytes)
    def test_08_corrupted_checkpoint_integrity_failure(self, tmp_path: Path) -> None:
        """Verify tampered checkpoint file fails cryptographic checksum validation."""
        ckpt_path = tmp_path / "model.safetensors"
        tensors = {"weights": np.ones((5, 5), dtype=np.float32)}
        meta = {"model_name": "test_net"}

        save_state(ckpt_path, tensors=tensors, metadata=meta)
        assert ckpt_path.exists()

        # Tamper with the binary file
        with open(ckpt_path, "r+b") as f:
            f.seek(10)
            f.write(b"\xFF\xFF\xFF\xFF")

        with pytest.raises(SerializationError, match="Integrity check failed"):
            load_state(ckpt_path, verify_integrity=True)

    # Scenario 9: Incompatible configuration bounds
    def test_09_incompatible_configuration_rejected(self) -> None:
        """Verify negative or invalid budget values raise ConfigurationError."""
        with pytest.raises(ConfigurationError, match="max_step_time_ms must be positive"):
            DynamicResourceBudgetManager(max_step_time_ms=-10.0)

        with pytest.raises(ConfigurationError, match="max_memory_mb must be positive"):
            DynamicResourceBudgetManager(max_memory_mb=0.0)

    # Scenario 10: ADWIN invalid delta parameter
    def test_10_adwin_invalid_delta_rejected(self) -> None:
        """Verify ADWIN rejects delta outside (0, 1)."""
        with pytest.raises(ValidationError, match="delta must be in"):
            ReliabilityWeightedADWIN(delta=0.0)

        with pytest.raises(ValidationError, match="delta must be in"):
            ReliabilityWeightedADWIN(delta=1.5)

    # Scenario 11: Drift detector NaN loss rejected
    def test_11_adwin_nan_loss_rejected(self) -> None:
        """Verify ADWIN rejects NaN error observations."""
        adwin = ReliabilityWeightedADWIN(delta=0.01)
        with pytest.raises(ValidationError, match="Loss must be finite"):
            adwin.update(float("nan"))

    # Scenario 12: Replay buffer sample weight mismatch
    def test_12_replay_buffer_weight_mismatch_rejected(self) -> None:
        """Verify replay buffer rejects weights array with mismatched length."""
        buf = ClassBalancedReservoirReplay(capacity=100, n_classes=2)
        X = np.ones((5, 2))
        y = np.array([0, 1, 0, 1, 0])
        w = np.array([1.0, 1.0])  # Length 2 instead of 5

        with pytest.raises(ValidationError, match="sample_weight length"):
            buf.add(X, y, sample_weight=w)

    # Scenario 13: Optional pillar missing in ULC-v4.1
    def test_13_controller_runs_without_optional_pillars(self) -> None:
        """Verify ULC-v4.1 operates cleanly when all optional submodules are None."""
        ctrl = UnifiedLearningControllerV4_1(
            classifier=None,
            optimizer=None,
            adwin=None,
            pipeline=None,
            budget_manager=None,
        )
        X = np.random.randn(20, 4)
        y = np.random.randint(0, 2, (20,))

        directive, telemetry = ctrl.step(X, y)
        assert directive is not None
        assert "state" in telemetry
        assert telemetry["step"] == 1

    # Scenario 14: Invalid probability distribution
    def test_14_invalid_probability_distribution_rejected(self) -> None:
        """Verify non-simplex probabilities raise ValidationError."""
        probs = np.array([[0.8, 0.8], [0.1, 0.2]])  # Rows do not sum to 1.0
        with pytest.raises(ValidationError, match="probability simplex"):
            check_probabilities(probs)

    # Scenario 15: Corrupted metadata JSON in checkpoint
    def test_15_corrupted_json_metadata_rejected(self, tmp_path: Path) -> None:
        """Verify malformed JSON metadata raises SerializationError."""
        ckpt_path = tmp_path / "model.safetensors"
        meta_path = tmp_path / "model.meta.json"
        save_state(ckpt_path, tensors={"w": np.ones((2, 2))})

        # Overwrite JSON with garbage syntax
        meta_path.write_text("{ unclosed bad json", encoding="utf-8")

        with pytest.raises(SerializationError, match="Failed to parse metadata JSON"):
            load_state(ckpt_path)

    # Scenario 16: Dynamic budget manager negative step time rejected
    def test_16_budget_manager_negative_step_time_rejected(self) -> None:
        """Verify budget manager rejects negative step latency."""
        mgr = DynamicResourceBudgetManager(max_step_time_ms=50.0)
        with pytest.raises(ValidationError, match="step_time_ms must be a non-negative finite float"):
            mgr.evaluate_step(-1.0)

    # Scenario 17: Generalized cross entropy invalid q
    def test_17_gce_invalid_q_rejected(self) -> None:
        """Verify GeneralizedCrossEntropyLoss rejects q <= 0 or q > 1."""
        with pytest.raises(ValidationError, match="q must be in"):
            GeneralizedCrossEntropyLoss(q=0.0)

        with pytest.raises(ValidationError, match="q must be in"):
            GeneralizedCrossEntropyLoss(q=1.2)

    # Scenario 18: Idempotent controller reset
    def test_18_idempotent_controller_reset(self) -> None:
        """Verify multiple consecutive resets leave the controller clean."""
        ctrl = UnifiedLearningControllerV4_1()
        X = np.random.randn(10, 4)
        y = np.random.randint(0, 2, (10,))
        ctrl.step(X, y)
        assert ctrl.total_steps == 1

        ctrl.reset()
        assert ctrl.total_steps == 0
        assert len(ctrl.history_) == 0

        ctrl.reset()  # Second reset should be completely safe
        assert ctrl.total_steps == 0

    # Scenario 19: Checkpoint file size ceiling enforcement
    def test_19_checkpoint_file_size_ceiling_enforced(self, tmp_path: Path) -> None:
        """Verify load_state rejects files exceeding the specified max_file_size_bytes."""
        ckpt_path = tmp_path / "small.safetensors"
        save_state(ckpt_path, tensors={"w": np.ones((10, 10))})

        # Set max ceiling to 5 bytes
        with pytest.raises(SerializationError, match="exceeds size ceiling"):
            load_state(ckpt_path, max_file_size_bytes=5)

    # Scenario 20: Recovery after drift and noise (Scenario A deadlock avoidance)
    def test_20_recovery_after_drift_and_noise_burst(self) -> None:
        """Verify controller successfully recovers and does not deadlock."""
        ctrl = UnifiedLearningControllerV4_1()
        rng = np.random.default_rng(42)

        # 5 steps clean
        for _ in range(5):
            X = rng.normal(0.0, 1.0, (20, 4))
            y = (X[:, 0] > 0).astype(int)
            ctrl.step(X, y)

        # 3 steps noise
        for _ in range(3):
            X = rng.normal(0.0, 1.0, (20, 4))
            y = rng.integers(0, 2, (20,))
            ctrl.step(X, y)

        # Recovery clean
        for _ in range(5):
            X = rng.normal(0.0, 1.0, (20, 4))
            y = (X[:, 0] > 0).astype(int)
            d, _ = ctrl.step(X, y)

        assert ctrl.total_steps == 13
        assert ctrl.automaton.state != AutomatonStateV4.NOISE_BURST
        assert d is not None
