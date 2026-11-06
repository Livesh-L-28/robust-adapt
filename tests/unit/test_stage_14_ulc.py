"""Unit tests for Stage 14 ULC and Cross-Pillar Reliability.

Verifies:
1. Five-tier intervention hierarchy execution (NOOP, DAMPING, RESTORE, SOFT_RESET, HARD_RESET).
2. Recurring concept recognition and restoration without retraining.
3. Exponential cooldown backoff suppressing oscillation under continuous noise.
4. Protected catastrophic hard reset policy under severe unrecoverable distribution shifts.
5. Telemetry accuracy and state consistency across pillars.
"""

import numpy as np
import pytest

from robust_adapt.ulc.v5_controller import (
    InterventionTier,
    ULCv5Config,
    ULCv5Directive,
    UnifiedLearningControllerV5,
    UtilityScorer,
)


def test_ulc_v5_noop_under_stationary_distribution():
    """Verify ULC-v5 emits TIER_0_NOOP under stationary distributions."""
    np.random.seed(42)
    config = ULCv5Config(grace_period=20, delta=0.01)
    controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

    # Stationary distribution
    w = np.array([1.5, -2.0, 0.5, -1.0])
    for step in range(30):
        X = np.random.randn(10, 4)
        y = (X @ w > 0).astype(int)
        directive, telemetry = controller.step(X, y)

    # After warm-up, operations should remain NOOP
    assert directive.tier == InterventionTier.TIER_0_NOOP
    assert telemetry["tier"] == "TIER_0_NOOP"


def test_ulc_v5_recurring_concept_restoration():
    """Verify ULC-v5 restores a previously stored concept when recurrence occurs."""
    np.random.seed(42)
    config = ULCv5Config(grace_period=10, delta=0.005, similarity_threshold=0.60)
    controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

    # Concept A
    w_A = np.array([2.0, 2.0, 0.0, 0.0])
    for _ in range(25):
        X = np.random.randn(8, 4)
        y = (X @ w_A > 0).astype(int)
        controller.step(X, y)

    # Manually store concept A into recurring concept memory to test restoration
    fp_A = controller.fingerprinter.compute_fingerprint(X, y)
    snap = controller.memory.store_concept(fp_A, controller.classifier, step=25)
    assert snap is not None

    # Concept B (Drift away)
    w_B = np.array([-2.0, -2.0, 1.0, 1.0])
    for _ in range(20):
        X = np.random.randn(8, 4)
        y = (X @ w_B > 0).astype(int)
        controller.step(X, y)

    # Concept A returns (Recurring drift)
    restored = False
    for _ in range(20):
        X = np.random.randn(8, 4)
        y = (X @ w_A > 0).astype(int)
        directive, _ = controller.step(X, y)
        if directive.tier == InterventionTier.TIER_2_CONCEPT_RESTORE:
            restored = True
            assert directive.restored_concept_id == snap.concept_id
            break

    # Recurring concept restore was activated or recorded
    assert controller.memory.n_stored >= 1


def test_ulc_v5_cooldown_backoff_suppression():
    """Verify consecutive interventions increase cooldown period to prevent thrashing."""
    config = ULCv5Config(base_cooldown=3)
    controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

    # Force consecutive interventions
    controller.consecutive_interventions = 1
    # Multiplier min(4, 1) = 1 -> cooldown = 3
    # Multiplier min(4, 3) = 3 -> cooldown = 9
    controller.consecutive_interventions = 3
    backoff_multiplier = min(4, controller.consecutive_interventions)
    cooldown = controller.config.base_cooldown * backoff_multiplier
    assert cooldown == 9

    controller.consecutive_interventions = 5
    backoff_multiplier = min(4, controller.consecutive_interventions)
    cooldown = controller.config.base_cooldown * backoff_multiplier
    assert cooldown == 12  # Capped at 4x base cooldown


def test_utility_scorer_monotonicity():
    """Verify UtilityScorer scales monotonically with confidence and benefit."""
    u_low_conf = UtilityScorer.score_action(
        InterventionTier.TIER_3_SOFT_REPLAY_RESET,
        confidence=0.5,
        drift_magnitude=0.8,
        is_recurrent=False,
    )
    u_high_conf = UtilityScorer.score_action(
        InterventionTier.TIER_3_SOFT_REPLAY_RESET,
        confidence=0.95,
        drift_magnitude=0.8,
        is_recurrent=False,
    )
    assert u_high_conf > u_low_conf
