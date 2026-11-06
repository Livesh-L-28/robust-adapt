"""
Regression tests for enterprise verification defect remediations (DEF-001, DEF-002, DEF-003).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from robust_adapt.ala.tree import VectorizedHoeffdingTree, _Node
from robust_adapt.core.exceptions import SerializationError, ValidationError
from robust_adapt.core.telemetry import get_process_memory_bytes
from robust_adapt.state.serializer import (
    is_safetensors_available,
    load_state,
    save_state,
)


class TestDEF001SafetensorsIsolation:
    """Regression tests for DEF-001: Safetensors optional dependency isolation."""

    def test_save_state_missing_safetensors_raises_actionable_error(self, tmp_path: Path) -> None:
        """Verify save_state raises SerializationError with install instructions when safetensors missing."""
        with patch("robust_adapt.state.serializer._SAFETENSORS_AVAILABLE", False), patch(
            "robust_adapt.state.serializer.sn", None
        ):
            target = tmp_path / "model_checkpoint"
            tensors = {"weights": np.array([1.0, 2.0, 3.0], dtype=np.float32)}

            with pytest.raises(SerializationError) as exc_info:
                save_state(target, tensors)

            err_msg = str(exc_info.value)
            assert "pip install 'robust-adapt[safetensors]'" in err_msg
            assert "safetensors" in err_msg

    def test_load_state_missing_safetensors_raises_actionable_error(self, tmp_path: Path) -> None:
        """Verify load_state raises SerializationError with install instructions when safetensors missing."""
        with patch("robust_adapt.state.serializer._SAFETENSORS_AVAILABLE", False), patch(
            "robust_adapt.state.serializer.sn", None
        ):
            target = tmp_path / "model_checkpoint.safetensors"

            with pytest.raises(SerializationError) as exc_info:
                load_state(target)

            err_msg = str(exc_info.value)
            assert "pip install 'robust-adapt[safetensors]'" in err_msg
            assert "safetensors" in err_msg

    def test_state_roundtrip_when_safetensors_available(self, tmp_path: Path) -> None:
        """Verify normal save/load roundtrip when safetensors is present."""
        if not is_safetensors_available():
            pytest.skip("safetensors is not installed in this test environment")

        target = tmp_path / "checkpoint_roundtrip"
        tensors = {
            "layer1": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
            "bias": np.array([0.5, -0.5], dtype=np.float32),
        }
        meta = {"step": 42, "accuracy": 0.95}

        save_state(target, tensors, metadata=meta)
        loaded_tensors, loaded_meta = load_state(target)

        assert np.allclose(loaded_tensors["layer1"], tensors["layer1"])
        assert np.allclose(loaded_tensors["bias"], tensors["bias"])
        assert loaded_meta["step"] == 42
        assert loaded_meta["accuracy"] == 0.95

    def test_corrupt_metadata_raises_serialization_error(self, tmp_path: Path) -> None:
        """Verify malformed JSON raises SerializationError instead of raw JSONDecodeError."""
        if not is_safetensors_available():
            pytest.skip("safetensors is not installed in this test environment")

        target = tmp_path / "corrupt_meta"
        tensors = {"w": np.array([1.0], dtype=np.float32)}
        save_state(target, tensors, {"step": 1})

        # Tamper with metadata JSON
        meta_file = tmp_path / "corrupt_meta.meta.json"
        meta_file.write_text("{ unclosed invalid json ...", encoding="utf-8")

        with pytest.raises(SerializationError) as exc_info:
            load_state(target)

        assert "Failed to parse metadata JSON" in str(exc_info.value)


class TestDEF002RuntimeValidation:
    """Regression tests for DEF-002: Explicit runtime validation without assert."""

    def test_attempt_split_uninitialized_edges_raises_validation_error(self) -> None:
        """Verify _attempt_split raises ValidationError when bin_edges is None."""
        tree = VectorizedHoeffdingTree(n_features=4, n_classes=2)
        leaf = tree._create_leaf(depth=0)
        leaf.n_samples = 500.0
        leaf.class_counts = np.array([250.0, 250.0], dtype=np.float64)

        assert tree.bin_edges is None

        with pytest.raises(ValidationError) as exc_info:
            tree._attempt_split(leaf)

        assert "Quantile bin edges must be initialized" in str(exc_info.value)

    def test_route_sample_invalid_node_type_raises_validation_error(self) -> None:
        """Verify _route_sample raises ValidationError if routing lands on a non-leaf non-split node."""
        tree = VectorizedHoeffdingTree(n_features=2, n_classes=2)

        class _BogusNode(_Node):
            pass

        bogus = _BogusNode(node_id=99, depth=1)
        x = np.array([0.5, 0.5])

        with pytest.raises(ValidationError) as exc_info:
            tree._route_sample(x, bogus)

        assert "Tree routing terminated at invalid node type: _BogusNode" in str(exc_info.value)

    def test_validation_works_under_optimized_python(self) -> None:
        """Verify that validation triggers in a separate process executed with -O (assertions stripped)."""
        code = (
            "from robust_adapt.ala.tree import VectorizedHoeffdingTree\n"
            "from robust_adapt.core.exceptions import ValidationError\n"
            "tree = VectorizedHoeffdingTree(n_features=4, n_classes=2)\n"
            "leaf = tree._create_leaf(depth=0)\n"
            "leaf.n_samples = 500.0\n"
            "leaf.class_counts = __import__('numpy').array([250.0, 250.0], dtype='float64')\n"
            "try:\n"
            "    tree._attempt_split(leaf)\n"
            "    print('FAILED_NO_EXCEPTION')\n"
            "except ValidationError:\n"
            "    print('PASSED_VALIDATION_ERROR')\n"
        )

        result = subprocess.run(
            [sys.executable, "-O", "-c", code],
            capture_output=True,
            text=True,
            check=True,
        )

        assert "PASSED_VALIDATION_ERROR" in result.stdout
        assert "FAILED_NO_EXCEPTION" not in result.stdout


class TestDEF003TelemetryExceptionHandling:
    """Regression tests for DEF-003: Narrowed telemetry exception handling."""

    def test_get_process_memory_bytes_returns_positive_int(self) -> None:
        """Verify get_process_memory_bytes returns a valid positive integer on the host."""
        mem = get_process_memory_bytes()
        assert isinstance(mem, int)
        assert mem > 0, f"Expected positive RSS memory bytes, got {mem}"

    def test_psutil_import_error_falls_back_gracefully(self) -> None:
        """Verify that missing psutil triggers fallback without raising unhandled error."""
        with patch.dict(sys.modules, {"psutil": None}):
            mem = get_process_memory_bytes()
            assert isinstance(mem, int)
            assert mem >= 0

    def test_unexpected_exception_is_not_silently_suppressed(self) -> None:
        """Verify that unexpected programming exceptions (e.g. TypeError) in psutil are NOT caught."""
        class MaliciousPsutil:
            @staticmethod
            def Process(*args, **kwargs):
                raise TypeError("Simulated programming bug: invalid type")

        with patch.dict(sys.modules, {"psutil": MaliciousPsutil}):
            with pytest.raises(TypeError) as exc_info:
                get_process_memory_bytes()

            assert "Simulated programming bug" in str(exc_info.value)
