"""
Unit tests for Phase 11 — Unified Learning Controller (ULC).
"""

from __future__ import annotations

import numpy as np
import pytest

from adaptive_ml.core.config import ULCConfig
from adaptive_ml.ulc.automaton import ArbitrationAutomaton
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.evidence import EvidenceSynthesizer, EvidenceVector


class TestEvidenceSynthesizer:
    def test_predictive_entropy_bounds(self) -> None:
        synth = EvidenceSynthesizer()

        # One-hot confident predictions -> entropy ~ 0.0
        one_hot = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
        h_low = synth.compute_predictive_entropy(one_hot)
        assert 0.0 <= h_low < 0.05

        # Completely uniform predictions -> maximum entropy = 1.0
        uniform = np.full((10, 3), 1.0 / 3.0, dtype=np.float64)
        h_high = synth.compute_predictive_entropy(uniform)
        assert pytest.approx(1.0, abs=1e-3) == h_high

    def test_loss_trend_tracking(self) -> None:
        synth = EvidenceSynthesizer(ema_alpha=0.5, slope_gain=2.0)

        # First observation -> neutral 0.5
        t0 = synth.update_loss_trend(1.0)
        assert pytest.approx(0.5, abs=1e-3) == t0

        # Loss surges to 3.0 -> trend > 0.5
        t_high = synth.update_loss_trend(3.0)
        assert t_high > 0.8

        # Loss plunges to 0.1 -> trend < 0.5
        t_low = synth.update_loss_trend(0.1)
        assert t_low < 0.3


class TestArbitrationAutomaton:
    def test_drift_without_noise_transition(self) -> None:
        config = ULCConfig(tau_R=0.65, recovery_steps=5, hysteresis_band=0.15)
        automaton = ArbitrationAutomaton(config=config)

        assert automaton.state == ControllerState.STABLE

        # High drift divergence delta >= 1.0 AND high sample reliability rel >= 0.65
        ev = EvidenceVector(delta_drift=1.2, mean_reliability=0.85, predictive_entropy=0.7, loss_trend=0.8)
        directive = automaton.transition(ev)

        assert directive.state == ControllerState.CONFIRMED_DRIFT
        assert directive.learning_rate_scale == 2.5
        assert directive.reset_momentum is True
        assert directive.purge_replay is True
        assert directive.split_immediate is True

        # Next step should automatically enter RECOVERY mode
        ev_recovery = EvidenceVector(delta_drift=0.3, mean_reliability=0.85, predictive_entropy=0.5, loss_trend=0.5)
        directive2 = automaton.transition(ev_recovery)

        assert directive2.state == ControllerState.RECOVERY
        assert directive2.learning_rate_scale > 1.0
        assert directive2.dwell_remaining == 5

    def test_noise_burst_without_drift_transition(self) -> None:
        config = ULCConfig(tau_R=0.65, recovery_steps=5)
        automaton = ArbitrationAutomaton(config=config)

        # High divergence delta >= 1.0 BUT low reliability rel < 0.65 (noise burst)
        ev_noise = EvidenceVector(delta_drift=1.4, mean_reliability=0.25, predictive_entropy=0.3, loss_trend=0.9)
        directive = automaton.transition(ev_noise)

        assert directive.state == ControllerState.NOISE_BURST
        assert directive.suppress_adwin is True
        assert directive.freeze_buffer is True
        assert directive.sample_filter_threshold == 0.65
        assert directive.gradient_clip_factor == 0.5

        # Remains in NOISE_BURST while rel is low
        directive_still_noise = automaton.transition(ev_noise)
        assert directive_still_noise.state == ControllerState.NOISE_BURST

        # Clean batch arrives (rel >= 0.65, delta < 0.5) -> restores STABLE
        ev_clean = EvidenceVector(delta_drift=0.2, mean_reliability=0.90, predictive_entropy=0.2, loss_trend=0.5)
        directive_clean = automaton.transition(ev_clean)
        assert directive_clean.state == ControllerState.STABLE

    def test_warning_state_and_hysteresis_deadband(self) -> None:
        config = ULCConfig(tau_R=0.65, hysteresis_band=0.15)
        automaton = ArbitrationAutomaton(config=config)

        # 0.5 <= delta < 1.0 -> WARNING state
        ev_warn = EvidenceVector(delta_drift=0.65, mean_reliability=0.8, predictive_entropy=0.5, loss_trend=0.5)
        dir1 = automaton.transition(ev_warn)
        assert dir1.state == ControllerState.WARNING

        # Delta dips to 0.40: within hysteresis deadband [0.35, 0.50), should remain in WARNING
        ev_deadband = EvidenceVector(delta_drift=0.40, mean_reliability=0.8, predictive_entropy=0.5, loss_trend=0.5)
        dir2 = automaton.transition(ev_deadband)
        assert dir2.state == ControllerState.WARNING

        # Delta drops below 0.35 (0.5 - 0.15) -> returns to STABLE
        ev_stable = EvidenceVector(delta_drift=0.25, mean_reliability=0.8, predictive_entropy=0.5, loss_trend=0.5)
        dir3 = automaton.transition(ev_stable)
        assert dir3.state == ControllerState.STABLE


class TestAdaptiveLearningController:
    def test_controller_step_isolated_no_submodules(self) -> None:
        """ULC operates cleanly even if no pillars are connected."""
        controller = AdaptiveLearningController()
        X = np.random.randn(20, 4)
        y = np.random.choice([0, 1], size=20)

        directive, info = controller.step(X, y)
        assert directive.state == ControllerState.STABLE
        assert info["n_input_samples"] == 20
        assert info["n_retained_samples"] == 20
        assert info["mean_reliability"] == 1.0

    def test_controller_noise_burst_filtering_with_rla(self) -> None:
        from adaptive_ml.rla.pipeline import RobustLearningPipeline

        pipeline = RobustLearningPipeline(n_classes=2)
        controller = AdaptiveLearningController(pipeline=pipeline)

        # Incoming batch has inverted corrupt labels with model predicting class 0
        X_corrupt = np.random.normal(loc=-3.0, size=(10, 2))
        y_corrupt = np.array([1] * 10)  # corrupt labels
        # Model strongly predicts class 0
        logits = np.tile([5.0, -5.0], (10, 1))

        # Forcing high delta_drift to trigger arbitration
        directive, info = controller.step(X_corrupt, y_corrupt, logits=logits, delta_drift=1.5)

        assert directive.state == ControllerState.NOISE_BURST
        assert directive.suppress_adwin is True
        assert directive.sample_filter_threshold > 0.0
        # Corrupt samples should have low reliability
        assert info["mean_reliability"] < 0.65

    def test_controller_with_classifier_and_optimizer_under_drift(self) -> None:
        from adaptive_ml.ala.classifier import AdaptiveClassifier
        from adaptive_ml.rao.adamw import LowMemoryAdamW

        clf = AdaptiveClassifier(n_features=4, n_classes=2)
        params = [np.random.randn(10, 4)]
        opt = LowMemoryAdamW(params, lr=0.01)

        controller = AdaptiveLearningController(classifier=clf, optimizer=opt)

        X = np.random.randn(20, 4)
        y = np.random.choice([0, 1], size=20)

        # Trigger drift with clean reliability
        directive, info = controller.step(X, y, delta_drift=1.2)

        assert directive.state == ControllerState.CONFIRMED_DRIFT
        assert directive.learning_rate_scale == 2.5
        assert directive.reset_momentum is True
        assert directive.split_immediate is True
        assert directive.purge_replay is True
        assert clf.samples_seen_ > 0

        # Next step transitions into RECOVERY
        dir2, info2 = controller.step(X, y, delta_drift=0.2)
        assert dir2.state == ControllerState.RECOVERY
        assert dir2.dwell_remaining > 0
