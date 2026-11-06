"""Unit tests for Stage 2 Defect Remediation and Architecture Hardening.

Verifies DEF-006 (canonical replay buffer purge contract) and DEF-007 (canonical
optimizer momentum reset and learning rate scaling interface) across ALA, RAO, and ULC.
"""

from typing import List
import numpy as np
import pytest

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.core.exceptions import ValidationError
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.ulc.automaton import ArbitrationAutomaton
from robust_adapt.ulc.controller import AdaptiveLearningController
from robust_adapt.ulc.directives import ControllerDirective, ControllerState
from robust_adapt.ulc.evidence import EvidenceVector


class TestDEF006ReplayBufferContract:
    """Verifies DEF-006 canonical replay buffer interface and safe purge semantics."""

    def test_classifier_replay_buffer_property(self) -> None:
        clf = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=500)
        assert clf.replay_buffer is not None
        assert isinstance(clf.replay_buffer, ClassBalancedReservoirReplay)

        clf_no_replay = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=0)
        assert clf_no_replay.replay_buffer is None

    def test_replay_buffer_purge_full(self) -> None:
        buf = ClassBalancedReservoirReplay(capacity=100, n_classes=2, random_state=42)
        X = np.random.randn(20, 4)
        y = np.array([0] * 10 + [1] * 10)
        buf.add(X, y)
        assert buf.total_stored == 20

        purged = buf.purge(policy="full")
        assert purged == 20
        assert buf.total_stored == 0

    def test_replay_buffer_purge_selective_preserves_minority(self) -> None:
        buf = ClassBalancedReservoirReplay(capacity=200, n_classes=2, random_state=42)
        # 40 majority samples (class 0) with mixed reliability, 5 minority samples (class 1)
        X0 = np.random.randn(40, 4)
        y0 = np.zeros(40, dtype=int)
        w0 = np.array([0.2] * 20 + [0.9] * 20)  # half low reliability, half high

        X1 = np.random.randn(5, 4)
        y1 = np.ones(5, dtype=int)
        w1 = np.array([0.1] * 5)  # all low reliability, but minority class!

        buf.add(X0, y0, sample_weight=w0)
        buf.add(X1, y1, sample_weight=w1)

        assert buf.class_counts[0] == 40
        assert buf.class_counts[1] == 5

        # Selective purge with min_reliability=0.5 and keep_minority=True
        purged = buf.purge(policy="selective", min_reliability=0.5, keep_minority=True)

        # Class 1 (minority) must be 100% preserved
        assert buf.class_counts[1] == 5
        # Class 0 low-reliability samples should be purged
        assert buf.class_counts[0] == 20
        assert purged == 20

    def test_replay_buffer_purge_partial(self) -> None:
        buf = ClassBalancedReservoirReplay(capacity=200, n_classes=2, random_state=42)
        X0 = np.random.randn(30, 4)
        y0 = np.zeros(30, dtype=int)
        X1 = np.random.randn(4, 4)
        y1 = np.ones(4, dtype=int)

        buf.add(X0, y0)
        buf.add(X1, y1)

        purged = buf.purge(policy="partial", keep_minority=True)
        assert buf.class_counts[1] == 4  # minority preserved
        assert buf.class_counts[0] == 15  # majority trimmed by half
        assert purged == 15

    def test_classifier_purge_replay_method(self) -> None:
        clf = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=200)
        X = np.random.randn(20, 4)
        y = np.array([0] * 18 + [1] * 2)
        clf.partial_fit(X, y)

        assert clf.replay_buffer is not None
        assert clf.replay_buffer.total_stored > 0

        purged = clf.purge_replay(policy="selective", keep_minority=True)
        assert isinstance(purged, int)
        assert clf.replay_buffer.class_counts[1] == 2  # minority untouched

    def test_invalid_purge_policy_raises_validation_error(self) -> None:
        buf = ClassBalancedReservoirReplay(capacity=50, n_classes=2)
        with pytest.raises(ValidationError, match="policy must be one of"):
            buf.purge(policy="invalid_policy")


class TestDEF007OptimizerContract:
    """Verifies DEF-007 canonical optimizer momentum reset and LR scaling interface."""

    def test_low_memory_adamw_reset_momenta_numpy(self) -> None:
        param = np.ones((5, 5), dtype=np.float32)
        grad = np.full((5, 5), 0.5, dtype=np.float32)
        param_obj = type("Param", (), {"data": param, "grad": grad})()
        opt = LowMemoryAdamW([param_obj], lr=1e-3)

        # Perform 3 optimization steps to build non-zero momentum
        for _ in range(3):
            opt.step()

        p_key = id(param_obj.data)
        state = opt.state[p_key]
        assert state["step"] == 3
        assert np.any(state["q_m"] != 0)
        assert np.any(state["scale_m"] > 0)

        # Execute momentum reset
        opt.reset_momenta()

        assert state["step"] == 0
        assert np.all(state["q_m"] == 0)
        assert np.all(state["scale_m"] == 0.0)

    def test_low_memory_adamw_scale_learning_rate(self) -> None:
        param = np.zeros(10, dtype=np.float32)
        opt = LowMemoryAdamW([param], lr=0.01)

        assert opt.param_groups[0]["lr"] == pytest.approx(0.01)
        opt.scale_learning_rate(2.5)
        assert opt.param_groups[0]["lr"] == pytest.approx(0.025)

        opt.scale_learning_rate(0.4)
        assert opt.param_groups[0]["lr"] == pytest.approx(0.01)

        with pytest.raises(ValidationError, match="must be positive"):
            opt.scale_learning_rate(-1.0)

        with pytest.raises(ValidationError, match="must be positive"):
            opt.scale_learning_rate(0.0)


class TestStage2CrossPillarCoordination:
    """Verifies integrated ULC coordination with DEF-006 and DEF-007 active."""

    def test_ulc_confirmed_drift_triggers_safe_purge_and_momentum_reset(self) -> None:
        clf = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=100)
        param = np.random.randn(8, 4).astype(np.float32)
        grad = np.random.randn(8, 4).astype(np.float32)
        p_obj = type("Param", (), {"data": param, "grad": grad})()
        opt = LowMemoryAdamW([p_obj], lr=0.01)

        controller = AdaptiveLearningController(classifier=clf, optimizer=opt)

        # Pre-populate classifier and optimizer state
        X_init = np.random.randn(20, 4)
        y_init = np.array([0] * 18 + [1] * 2)
        clf.partial_fit(X_init, y_init)
        opt.step()

        assert clf.replay_buffer.class_counts[1] == 2
        p_key = id(p_obj.data)
        assert opt.state[p_key]["step"] == 1

        # Trigger concept drift with incoming majority batch
        X_drift = np.random.randn(10, 4)
        y_drift = np.zeros(10, dtype=int)
        directive, info = controller.step(X_drift, y_drift, delta_drift=1.5)

        assert directive.state == ControllerState.CONFIRMED_DRIFT
        assert directive.reset_momentum is True
        assert directive.purge_replay is True
        assert directive.learning_rate_scale == 2.5

        # Check optimizer state: momenta was reset and LR was scaled
        assert opt.state[p_key]["step"] == 0
        assert np.all(opt.state[p_key]["q_m"] == 0)
        assert opt.param_groups[0]["lr"] == pytest.approx(0.025)

        # Check replay buffer: minority class (class 1) was preserved
        assert clf.replay_buffer.class_counts[1] == 2
