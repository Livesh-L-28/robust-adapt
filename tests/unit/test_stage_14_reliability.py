"""Stage 14 Workstream B — Reliability and Fault Tolerance Test Suite."""

import numpy as np
import pytest

from robust_adapt.ala import ALA30AdaptiveLearner, AdaptiveClassifier
from robust_adapt.rla import RLA30RobustLearner
from robust_adapt.minority import MinorityIntelligence20Learner
from robust_adapt.ulc import UnifiedLearningControllerV5
from robust_adapt.core.exceptions import ValidationError, ConfigurationError


def test_empty_batch_rejection() -> None:
    """Verify that all models explicitly reject empty batches."""
    X0 = np.empty((0, 4))
    y0 = np.empty((0,), dtype=int)

    with pytest.raises(ValidationError, match="cannot be empty"):
        ALA30AdaptiveLearner(n_features=4, n_classes=2).partial_fit(X0, y0)

    with pytest.raises(ValidationError, match="cannot be empty"):
        RLA30RobustLearner(n_features=4, n_classes=2).fit_batch(X0, y0)

    with pytest.raises(ValidationError, match="cannot be empty"):
        MinorityIntelligence20Learner().fit_batch(X0, y0)

    with pytest.raises(ValidationError, match="cannot be empty"):
        UnifiedLearningControllerV5(n_features=4, n_classes=2).step(X0, y0)


def test_single_sample_batch_execution() -> None:
    """Verify that all models handle N=1 single-sample streaming batches."""
    X1 = np.array([[1.0, 2.0, -1.0, 0.5]])
    y1 = np.array([1])

    ala = ALA30AdaptiveLearner(n_features=4, n_classes=2)
    ala.partial_fit(X1, y1)
    assert ala.total_steps == 1

    rla = RLA30RobustLearner(n_features=4, n_classes=2)
    stats = rla.fit_batch(X1, y1)
    assert stats["total_seen"] == 1

    m = MinorityIntelligence20Learner()
    stats = m.fit_batch(X1, y1)
    assert stats["total_samples"] == 1

    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    directive, telemetry = ulc.step(X1, y1)
    assert telemetry["step"] == 1


def test_nan_and_inf_state_isolation() -> None:
    """Verify that invalid floating point values do not corrupt model state."""
    rng = np.random.RandomState(42)
    X_valid = rng.randn(20, 4)
    y_valid = (X_valid[:, 0] > 0).astype(int)

    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    ulc.step(X_valid, y_valid)
    assert ulc.total_steps == 1

    # Attempt to feed NaNs
    X_nan = X_valid.copy()
    X_nan[5, 2] = np.nan
    with pytest.raises(ValidationError, match="contains NaN or Infinite values"):
        ulc.step(X_nan, y_valid)

    # State must not be corrupted
    assert ulc.total_steps == 1
    # Next valid batch must succeed
    ulc.step(X_valid, y_valid)
    assert ulc.total_steps == 2


def test_feature_dimension_mismatch() -> None:
    """Verify that dimension mismatches are rejected cleanly."""
    X_wrong = np.random.randn(20, 3)
    y = np.random.randint(0, 2, size=20)

    with pytest.raises(ValidationError, match="dimension mismatch"):
        ALA30AdaptiveLearner(n_features=4, n_classes=2).partial_fit(X_wrong, y)

    with pytest.raises(ValidationError, match="dimension mismatch"):
        RLA30RobustLearner(n_features=4, n_classes=2).fit_batch(X_wrong, y)

    with pytest.raises(ValidationError, match="dimension mismatch"):
        UnifiedLearningControllerV5(n_features=4, n_classes=2).step(X_wrong, y)


def test_out_of_bounds_and_negative_labels() -> None:
    """Verify that negative or out-of-range class indices are rejected."""
    X = np.random.randn(10, 4)
    y_neg = np.array([-1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    y_oob = np.array([2, 0, 1, 0, 1, 0, 1, 0, 1, 0])

    with pytest.raises(ValidationError, match="negative class labels"):
        UnifiedLearningControllerV5(n_features=4, n_classes=2).step(X, y_neg)

    with pytest.raises(ValidationError, match="exceeds valid range"):
        UnifiedLearningControllerV5(n_features=4, n_classes=2).step(X, y_oob)


def test_repeated_initialization_and_reset() -> None:
    """Verify that models can be reset cleanly without residual state."""
    rng = np.random.RandomState(123)
    X = rng.randn(30, 4)
    y = (X[:, 0] > 0).astype(int)

    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    for _ in range(5):
        ulc.step(X, y)
    assert ulc.total_steps == 5

    ulc.reset()
    assert ulc.total_steps == 0
    assert ulc.total_resets == 0
    assert ulc.total_restores == 0

    # Retrain after reset
    ulc.step(X, y)
    assert ulc.total_steps == 1


def test_single_class_imbalanced_stream() -> None:
    """Verify that streams with all-identical labels do not crash or divide by zero."""
    X = np.random.randn(25, 4)
    y_all_zero = np.zeros(25, dtype=int)

    ala = ALA30AdaptiveLearner(n_features=4, n_classes=2)
    ala.partial_fit(X, y_all_zero)
    assert ala.total_steps == 1

    rla = RLA30RobustLearner(n_features=4, n_classes=2)
    rla.fit_batch(X, y_all_zero)
    assert rla.total_samples_seen == 25

    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    ulc.step(X, y_all_zero)
    assert ulc.total_steps == 1


def test_controlled_recovery_after_failure() -> None:
    """Verify end-to-end recovery: training survives caught exceptions without divergence."""
    rng = np.random.RandomState(456)
    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)

    # Initial good batches
    for _ in range(5):
        X = rng.randn(30, 4)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        ulc.step(X, y)

    # Fault injection: corrupt batch
    X_corrupt = np.full((30, 4), np.inf)
    with pytest.raises(ValidationError):
        ulc.step(X_corrupt, y)

    # Recovery: continue streaming valid data
    for _ in range(10):
        X = rng.randn(30, 4)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        directive, telemetry = ulc.step(X, y)
        assert not np.isnan(telemetry["error_rate"])

    assert ulc.total_steps == 15
