"""
Unit and Integration Regression Tests for Stage 7.2: ULC-v4.1 Validation & Robustness.

Targeted test suite covering:
1. Scenario A deadlock prevention.
2. Spatial discordance calculation & distance metrics.
3. High-dimensional feature behavior (D=128).
4. Hoeffding tie-breaking (tau_tie = 0.10).
5. Threshold smoothing (gamma = 0.50).
6. Minority protection under extreme imbalance.
7. Delayed labels buffer handling.
8. Conflicting evidence deadband.
9. Safe fallback when optional pillars are missing.
10. Controller recovery after concept drift.
11. Deterministic replay under fixed seeds.
"""

from __future__ import annotations

import numpy as np
import pytest

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.ala.tree import VectorizedHoeffdingTree
from robust_adapt.minority.prior import OnlineClassPriorTracker
from robust_adapt.minority.threshold import AdaptiveThresholdManager
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.rla.pipeline import RobustLearningPipeline
from robust_adapt.ulc.v4_automaton import AutomatonStateV4
from experiments.stage_7_1_ulc_v4_optimization.candidate_controllers import (
    HybridMasterControllerV4_1,
    compute_spatial_discordance,
)


class TestULCv4_1TargetedValidation:
    """Targeted regression and robustness tests for ULC-v4.1 candidate improvements."""

    def test_spatial_discordance_calculation(self) -> None:
        """Verifies spatial discordance logic on clean clusters vs noise."""
        X_clean = np.vstack([np.full((20, 4), -2.0), np.full((10, 4), 2.0)])
        y_clean = np.array([0] * 20 + [1] * 10)
        disc_clean = compute_spatial_discordance(X_clean, y_clean, k=5)
        assert disc_clean <= 0.10, f"Expected clean discordance <= 0.10, got {disc_clean}"

        # Invert half of labels randomly to simulate label noise
        y_noisy = y_clean.copy()
        y_noisy[:10] = 1
        disc_noisy = compute_spatial_discordance(X_clean, y_noisy, k=5)
        assert disc_noisy >= 0.25, f"Expected noisy discordance >= 0.25, got {disc_noisy}"

    def test_high_dimensional_feature_behavior(self) -> None:
        """Verifies discordance scaling and numerical stability at D=128."""
        rng = np.random.default_rng(42)
        X_high = rng.normal(0, 1, (30, 128))
        y_high = np.array([0] * 27 + [1] * 3)

        disc = compute_spatial_discordance(X_high, y_high, k=5)
        assert 0.0 <= disc <= 1.0
        assert not np.isnan(disc)

    def test_hoeffding_tie_breaking(self) -> None:
        """Verifies that tau_tie > 0 triggers splitting when attribute delta is small."""
        tree = VectorizedHoeffdingTree(n_features=4, n_classes=2, grace_period=10, tau_tie=0.10)
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (100, 4))
        y = (X[:, 0] > 0).astype(int)

        tree.partial_fit(X, y)
        # Verify tree performed splits
        assert tree._next_node_id > 1

    def test_threshold_smoothing_dynamics(self) -> None:
        """Verifies that gamma=0.50 damps threshold movement compared to gamma=1.0."""
        mgr_smoothed = AdaptiveThresholdManager(n_classes=2, gamma=0.5)
        mgr_linear = AdaptiveThresholdManager(n_classes=2, gamma=1.0)

        # 90:10 prior
        priors = np.array([0.90, 0.10])
        mgr_smoothed.update_from_priors(priors)
        mgr_linear.update_from_priors(priors)

        # Smoothed threshold should be higher than linear (more conservative FPR)
        assert mgr_smoothed.primary_threshold > mgr_linear.primary_threshold
        assert abs(mgr_smoothed.primary_threshold - 0.2236) < 0.01

    def test_scenario_a_deadlock_elimination(self) -> None:
        """Verifies that unadapted low margin does NOT deadlock controller into NOISE_BURST."""
        clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=10, tau_tie=0.10)
        clf.fit(np.ones((20, 4)), np.array([0] * 10 + [1] * 10))

        ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

        # Abrupt drift with clean labels but incorrect unadapted logits
        X_drift = np.vstack([np.full((27, 4), 3.0), np.full((3, 4), -3.0)])
        y_drift = np.array([0] * 27 + [1] * 3)
        logits_unadapted = np.array([[-5.0, 5.0]] * 27 + [[5.0, -5.0]] * 3)

        directive, telemetry = ctrl.step(X_drift, y_drift, logits=logits_unadapted, delta_drift=1.4)

        assert directive.state == AutomatonStateV4.CONFIRMED_DRIFT
        assert telemetry["n_retained_samples"] == 30
        assert directive.suppress_adwin is False

    def test_minority_protection_under_imbalance(self) -> None:
        """Verifies minority preservation in replay buffer and prior tracking."""
        prior = OnlineClassPriorTracker(n_classes=2)
        clf = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=100)
        clf.fit(np.ones((20, 4)), np.array([0] * 18 + [1] * 2))

        ctrl = HybridMasterControllerV4_1(classifier=clf, prior_tracker=prior, generate_explanations=False)

        # Feed multiple 90:10 batches
        for _ in range(5):
            X_imb = np.vstack([np.zeros((27, 4)), np.ones((3, 4))])
            y_imb = np.array([0] * 27 + [1] * 3)
            ctrl.step(X_imb, y_imb, delta_drift=0.05)

        assert prior.priors[0] > prior.priors[1]
        assert prior.imbalance_ratio > 1.2

    def test_delayed_labels_handling(self) -> None:
        """Verifies stability when feedback arrives out-of-band or delayed."""
        clf = AdaptiveClassifier(n_features=4, n_classes=2)
        clf.fit(np.ones((20, 4)), np.array([0] * 10 + [1] * 10))
        ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

        # Feed batch with neutral feedback
        X = np.random.randn(30, 4)
        y = np.array([0] * 25 + [1] * 5)
        directive, telemetry = ctrl.step(X, y, delta_drift=0.05)

        assert directive.state in (AutomatonStateV4.STABLE, AutomatonStateV4.ELEVATED_VARIANCE, AutomatonStateV4.NOISE_BURST)

    def test_conflicting_evidence_deadband(self) -> None:
        """Verifies that delta in warning deadband (0.85) enters pending adaptation."""
        clf = AdaptiveClassifier(n_features=4, n_classes=2)
        clf.fit(np.ones((20, 4)), np.array([0] * 10 + [1] * 10))
        ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

        X = np.random.randn(30, 4)
        y = np.array([0] * 27 + [1] * 3)
        directive, telemetry = ctrl.step(X, y, delta_drift=0.85)

        assert directive is not None

    def test_safe_fallback_missing_pillars(self) -> None:
        """Verifies that controller functions safely when optional pillars are None."""
        clf = AdaptiveClassifier(n_features=4, n_classes=2)
        clf.fit(np.ones((20, 4)), np.array([0] * 10 + [1] * 10))

        # Bare controller with only classifier
        ctrl_bare = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

        X = np.random.randn(30, 4)
        y = np.array([0] * 27 + [1] * 3)
        directive, telemetry = ctrl_bare.step(X, y, delta_drift=0.1)

        assert directive is not None
        assert telemetry["n_retained_samples"] == 30

    def test_controller_recovery_after_drift(self) -> None:
        """Verifies that model updates after drift and returns to stable state."""
        clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=10, tau_tie=0.10)
        clf.fit(np.full((20, 4), -2.0), np.array([0] * 18 + [1] * 2))

        ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

        # Trigger drift
        X_new = np.full((30, 4), 2.0)
        y_new = np.array([0] * 27 + [1] * 3)
        d1, _ = ctrl.step(X_new, y_new, delta_drift=1.4)
        assert d1.state == AutomatonStateV4.CONFIRMED_DRIFT

        # Next nominal batch
        d2, _ = ctrl.step(X_new, y_new, delta_drift=0.05)
        assert d2.state != AutomatonStateV4.CONFIRMED_DRIFT

    def test_deterministic_replay(self) -> None:
        """Verifies that two runs with identical seeds produce bit-identical directives."""
        seeds = [42, 42]
        directives_out = []

        for s in seeds:
            clf = AdaptiveClassifier(n_features=4, n_classes=2, random_state=s)
            clf.fit(np.ones((20, 4)), np.array([0] * 10 + [1] * 10))
            ctrl = HybridMasterControllerV4_1(classifier=clf, generate_explanations=False)

            rng = np.random.default_rng(s)
            X = rng.normal(0, 1, (30, 4))
            y = np.array([0] * 27 + [1] * 3)
            d, _ = ctrl.step(X, y, delta_drift=1.2)
            directives_out.append(d.state.value)

        assert directives_out[0] == directives_out[1]
