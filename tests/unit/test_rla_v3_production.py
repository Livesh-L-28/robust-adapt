"""
Stage 13 — Production Unit Tests for RLA 3.0 Asymmetric Noise Intelligence.

Validates:
1. AsymmetricTransitionDetector (directional discordance, ratio calculation, threshold alerting)
2. ClassConditionalReliabilityEstimator (density modeling, MAD normalization, minority protection)
3. RLA30RobustLearner (training loop, security modes, selective abstention, telemetry, error handling)
"""

import numpy as np
import pytest

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.rla import (
    AsymmetricTransitionDetector,
    ClassConditionalReliabilityEstimator,
    RLA30RobustLearner,
)


def test_asymmetric_transition_detector():
    detector = AsymmetricTransitionDetector(n_classes=2, window_size=50)

    # Clean / symmetric predictions
    y_pred_sym = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    y_true_sym = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    detector.update(y_pred_sym, y_true_sym)
    assert detector.get_asymmetry_ratio() == 1.0
    assert not detector.is_asymmetric(threshold=1.5)

    # Asymmetric directional evasion: true 1 (spam) predicted as 0 (ham)
    y_pred_asym = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    y_true_asym = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    detector.update(y_pred_asym, y_true_asym)

    ratio = detector.get_asymmetry_ratio()
    assert ratio > 2.0
    assert detector.is_asymmetric(threshold=1.5)


def test_asymmetric_transition_detector_validation():
    with pytest.raises(ConfigurationError):
        AsymmetricTransitionDetector(n_classes=1)
    with pytest.raises(ConfigurationError):
        AsymmetricTransitionDetector(n_classes=2, window_size=5)


def test_class_conditional_reliability_estimator():
    estimator = ClassConditionalReliabilityEstimator(
        n_features=3,
        n_classes=2,
        buffer_per_class=50,
        minority_protection=True,
        min_minority_prior=0.30,
    )

    # Populate class 0 (majority, 90 samples) and class 1 (minority, 10 samples)
    X_maj = np.random.normal(loc=0.0, scale=1.0, size=(90, 3))
    y_maj = np.zeros(90, dtype=int)
    X_min = np.random.normal(loc=5.0, scale=1.0, size=(10, 3))
    y_min = np.ones(10, dtype=int)

    estimator.update(X_maj, y_maj)
    estimator.update(X_min, y_min)

    # Test sample fitting class 0 closely
    test_maj = np.array([[0.1, -0.1, 0.0]])
    rel_maj = estimator.compute_reliability(test_maj, np.array([0]))
    assert rel_maj[0] > 0.70

    # Test minority sample: minority protection floor must guarantee >= 0.70
    test_min = np.array([[5.5, 4.8, 5.2]])
    rel_min = estimator.compute_reliability(test_min, np.array([1]))
    assert rel_min[0] >= 0.70


def test_class_conditional_reliability_validation():
    with pytest.raises(ConfigurationError):
        ClassConditionalReliabilityEstimator(n_features=0)
    with pytest.raises(ConfigurationError):
        ClassConditionalReliabilityEstimator(n_features=2, n_classes=1)

    estimator = ClassConditionalReliabilityEstimator(n_features=2, n_classes=2)
    with pytest.raises(ValidationError):
        estimator.compute_reliability(np.random.randn(5, 3), np.zeros(5, dtype=int))


def test_rla30_robust_learner_standard_mode():
    np.random.seed(42)
    learner = RLA30RobustLearner(n_features=4, n_classes=2, security_mode="standard")

    X = np.random.randn(100, 4)
    y = (X[:, 0] > 0).astype(int)

    # Initial batch warm-up
    res1 = learner.fit_batch(X[:50], y[:50])
    assert res1["retained"] == 50
    assert learner.is_fitted is True

    # Second batch update
    res2 = learner.fit_batch(X[50:], y[50:])
    assert res2["retained"] > 0
    assert "mean_reliability" in res2

    preds = learner.predict(X[:10])
    assert preds.shape == (10,)
    probas = learner.predict_proba(X[:10])
    assert probas.shape == (10, 2)
    assert np.allclose(np.sum(probas, axis=1), 1.0)


def test_rla30_robust_learner_high_security_evasion_mode():
    np.random.seed(42)
    learner = RLA30RobustLearner(
        n_features=3,
        n_classes=2,
        security_mode="high_security_evasion",
        minority_class=1,
    )

    # Train initial clean batch
    X_tr = np.random.randn(60, 3)
    y_tr = (X_tr[:, 0] > 0.5).astype(int)
    learner.fit_batch(X_tr, y_tr)

    # Feed batch with asymmetric noise (spam flipped to ham)
    X_noise = np.random.randn(40, 3)
    y_noise = np.zeros(40, dtype=int)  # All labeled as ham
    res = learner.fit_batch(X_noise, y_noise)

    assert "asymmetry_ratio" in res
    assert learner.total_samples_seen == 100


def test_rla30_robust_learner_conservative_abstain_mode():
    learner = RLA30RobustLearner(n_features=2, n_classes=2, security_mode="conservative_abstain")
    X = np.random.randn(50, 2)
    y = np.random.randint(0, 2, size=50)
    learner.fit_batch(X, y)

    res = learner.fit_batch(X, y)
    assert "abstained" in res


def test_rla30_robust_learner_validation():
    with pytest.raises(ConfigurationError):
        RLA30RobustLearner(n_features=0)
    with pytest.raises(ConfigurationError):
        RLA30RobustLearner(n_features=2, n_classes=1)
    with pytest.raises(ConfigurationError):
        RLA30RobustLearner(n_features=2, security_mode="invincible_shield")
    with pytest.raises(ConfigurationError):
        RLA30RobustLearner(n_features=2, reliability_threshold=1.5)
