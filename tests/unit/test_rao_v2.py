"""Unit tests for Stage 6: RAO 2.0 (Advanced Resource-Aware Optimization).

Verifies DynamicResourceBudgetManager, ExecutionProfiler, DeviceCapabilityDetector,
and ResilientCheckpointManager with corruption rollback.
"""

import os
import tempfile
import time
import numpy as np
import pytest

from robust_adapt.rao.budget import BudgetState, DynamicResourceBudgetManager
from robust_adapt.rao.device import DeviceCapabilityDetector, DeviceProfile
from robust_adapt.rao.profiler import ExecutionProfiler
from robust_adapt.rao.recovery import ResilientCheckpointManager


class TestDynamicResourceBudgetManager:
    """Verifies multi-dimensional budget constraints, operation shedding, and throttling."""

    def test_normal_and_throttling_transitions(self) -> None:
        mgr = DynamicResourceBudgetManager(
            max_step_time_ms=50.0,
            max_memory_mb=4096.0,
            min_batch_size=10,
            max_batch_size=100,
        )

        assert mgr.state == BudgetState.NORMAL
        assert mgr.current_batch_size == 100
        assert not mgr.should_skip_expensive_ops()

        # Step time = 20ms (< 50ms ceiling) -> remains NORMAL
        state = mgr.evaluate_step(step_time_ms=20.0)
        assert state == BudgetState.NORMAL
        assert not mgr.should_skip_expensive_ops()

        # Step time = 65ms (> 50ms ceiling) -> transitions to CRITICAL and reduces batch size
        state_crit = mgr.evaluate_step(step_time_ms=65.0)
        assert state_crit == BudgetState.CRITICAL
        assert mgr.should_skip_expensive_ops()
        assert mgr.current_batch_size == 50  # Cut by half

    def test_replay_ratio_scaling_under_pressure(self) -> None:
        mgr = DynamicResourceBudgetManager(max_step_time_ms=50.0)
        # Normal
        assert mgr.recommended_replay_ratio(base_ratio=0.20) == 0.20

        # Trigger critical
        mgr.evaluate_step(step_time_ms=80.0)
        assert mgr.recommended_replay_ratio(base_ratio=0.20) == 0.05


class TestExecutionProfiler:
    """Verifies execution profiling, EMA latency smoothing, and predictive breach alerts."""

    def test_profiler_measure_step(self) -> None:
        profiler = ExecutionProfiler(alpha=0.20)

        with profiler.measure_step() as info:
            # Simulated lightweight computation
            _ = np.linalg.norm(np.ones(1000))

        assert profiler.step_count == 1
        assert profiler.last_latency_ms > 0.0
        assert profiler.peak_memory_bytes > 0
        assert "elapsed_ms" in info

        summ = profiler.summary()
        assert summ["total_steps"] == 1
        assert summ["ema_latency_ms"] > 0.0

    def test_predictive_breach_detection(self) -> None:
        profiler = ExecutionProfiler(alpha=0.50)

        # Record 4 steps with ~40ms simulated latency
        for _ in range(4):
            with profiler.measure_step() as info:
                time.sleep(0.035)

        # If ceiling is 45ms, and EMA is ~35ms: 35 * 1.35 = 47.25 >= 45 -> breach predicted!
        breach = profiler.is_breach_predicted(target_latency_ms=45.0, safety_margin=1.35)
        assert breach


class TestDeviceCapabilityDetector:
    """Verifies safe hardware capability detection without external crashes."""

    def test_detect_hardware_profile(self) -> None:
        profile = DeviceCapabilityDetector.detect()
        assert isinstance(profile, DeviceProfile)
        assert profile.cpu_cores >= 1
        assert profile.platform in ("Windows", "Linux", "Darwin")
        assert profile.recommended_backend in ("cuda", "mps", "numpy_cpu")


class TestResilientCheckpointManager:
    """Verifies atomic checkpointing, checksum validation, and corruption rollback."""

    def test_checkpoint_save_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResilientCheckpointManager(checkpoint_dir=tmpdir, max_to_keep=2)

            state1 = {"model_weights": [1.0, 2.0, 3.0], "lr": 0.01}
            manager.save_checkpoint(step=10, state_dict=state1)

            state2 = {"model_weights": [4.0, 5.0, 6.0], "lr": 0.005}
            manager.save_checkpoint(step=20, state_dict=state2)

            # Latest checkpoint should restore step 20
            res = manager.load_latest_checkpoint()
            assert res is not None
            step, loaded_state = res
            assert step == 20
            assert loaded_state["lr"] == 0.005

    def test_corruption_rollback_to_prior_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResilientCheckpointManager(checkpoint_dir=tmpdir, max_to_keep=3)

            state1 = {"weights": [1.0], "version": 1}
            manager.save_checkpoint(step=100, state_dict=state1)

            state2 = {"weights": [2.0], "version": 2}
            ckpt2_path = manager.save_checkpoint(step=200, state_dict=state2)

            # Corrupt checkpoint 200 payload by overwriting with invalid truncated bytes
            with open(ckpt2_path, "wb") as f:
                f.write(b'{"step": 200, "checksum": "deadbeef", "state_dict": {"truncated":')

            # Manager should catch corruption and roll back to step 100
            res = manager.load_latest_checkpoint()
            assert res is not None
            step, loaded_state = res
            assert step == 100
            assert loaded_state["version"] == 1
