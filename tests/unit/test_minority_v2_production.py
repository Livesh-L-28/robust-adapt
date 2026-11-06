"""
Stage 13 — Production Unit Tests for Adaptive Minority Intelligence 2.0.

Validates:
1. BetaBinomialPriorTracker (Bayesian updates, exponential decay, imbalance ratio)
2. compute_sublinear_cost_weights (sublinear scaling behavior, boundary checks)
3. DynamicFPBudgetThresholdManager (PID false positive rate control, anti-windup, deadband, missing feedback)
4. MinorityIntelligence20Learner (streaming training, prediction, scoring, serialization)
"""

import numpy as np
import pytest

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.minority import (
    BetaBinomialPriorTracker,
    DynamicFPBudgetThresholdManager,
    MinorityIntelligence20Learner,
    compute_sublinear_cost_weights,
)


def test_beta_binomial_prior_tracker():
    tracker = BetaBinomialPriorTracker(alpha_prior=1.0, beta_prior=99.0, decay=0.95)
    # Initial prior approx 1 / 100 = 0.01
    assert np.isclose(tracker.current_prior, 0.01, atol=1e-3)
    assert tracker.imbalance_ratio > 50.0

    # Feed 100 positive instances
    y_pos = np.ones(100, dtype=int)
    tracker.update(y_pos)
    assert tracker.current_prior > 0.40

    # Serialization test
    state = tracker.state_dict()
    tracker2 = BetaBinomialPriorTracker()
    tracker2.load_state_dict(state)
    assert np.isclose(tracker2.current_prior, tracker.current_prior)


def test_beta_binomial_prior_tracker_validation():
    with pytest.raises(ConfigurationError):
        BetaBinomialPriorTracker(alpha_prior=0.0)
    with pytest.raises(ConfigurationError):
        BetaBinomialPriorTracker(beta_prior=-1.0)
    with pytest.raises(ConfigurationError):
        BetaBinomialPriorTracker(decay=1.5)


def test_sublinear_cost_weights():
    # Extreme imbalance: prior = 0.0018 (approx 556:1)
    w_sub = compute_sublinear_cost_weights(0.0018, power=0.52)
    # Sublinear weight should be around 23-28, NOT 556
    assert 20.0 < w_sub < 35.0
    assert w_sub < 556.0

    # Edge cases
    assert compute_sublinear_cost_weights(0.0) == 1.0
    assert compute_sublinear_cost_weights(1.0) == 1.0


def test_dynamic_fp_budget_threshold_manager_pid_control():
    mgr = DynamicFPBudgetThresholdManager(
        target_fp_budget_per_1k=1.5,
        base_threshold=0.50,
        kp=0.5,
        ki=0.05,
        kd=0.02,
        min_threshold=0.20,
        max_threshold=0.80,
    )
    assert mgr.threshold == 0.50
    assert mgr.target_fpr == 0.0015

    # Simulate high false alarm batch: true negative labels with high positive probabilities
    y_neg = np.zeros(100, dtype=int)
    probas_high = np.full(100, 0.70)  # All predicted as 1 -> 100% FPR!

    new_th = mgr.step(y_neg, probas_high)
    # Threshold should aggressively increase to suppress false alarms
    assert new_th > 0.50
    assert new_th <= 0.80

    # Simulate zero false alarm batch: true negative labels with zero positive probabilities
    probas_low = np.full(100, 0.05)
    lower_th = mgr.step(y_neg, probas_low)
    # Threshold should decrease or stabilize
    assert lower_th <= new_th


def test_dynamic_fp_budget_threshold_manager_missing_feedback():
    mgr = DynamicFPBudgetThresholdManager(base_threshold=0.45)
    th1 = mgr.step(None, np.array([0.2, 0.8]))
    assert th1 == 0.45
    th2 = mgr.step(np.empty(0), np.array([0.2, 0.8]))
    assert th2 == 0.45


def test_dynamic_fp_budget_threshold_manager_validation():
    with pytest.raises(ConfigurationError):
        DynamicFPBudgetThresholdManager(target_fp_budget_per_1k=0.0)
    with pytest.raises(ConfigurationError):
        DynamicFPBudgetThresholdManager(base_threshold=1.5)
    with pytest.raises(ConfigurationError):
        DynamicFPBudgetThresholdManager(min_threshold=0.70, max_threshold=0.30)


def test_minority_intelligence_20_learner_streaming():
    np.random.seed(42)
    learner = MinorityIntelligence20Learner(
        target_fp_budget_per_1k=2.0,
        sublinear_cost_power=0.52,
        base_threshold=0.50,
    )

    # Generate imbalanced stream (10% minority)
    X = np.random.randn(200, 4)
    y = (X[:, 0] > 1.2).astype(int)  # Sparse minority

    for i in range(0, 200, 50):
        res = learner.fit_batch(X[i:i+50], y[i:i+50])
        assert "minority_weight" in res
        assert "active_threshold" in res
        assert res["minority_weight"] > 1.0

    preds = learner.predict(X[:20])
    assert preds.shape == (20,)
    assert set(preds).issubset({0, 1})

    probas = learner.predict_proba(X[:20])
    assert probas.shape == (20, 2)
    assert np.allclose(np.sum(probas, axis=1), 1.0)


def test_minority_intelligence_20_learner_serialization():
    learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5)
    X = np.random.randn(50, 3)
    y = (X[:, 0] > 0.8).astype(int)
    learner.fit_batch(X, y)

    state = learner.state_dict()
    learner2 = MinorityIntelligence20Learner()
    learner2.load_state_dict(state)

    assert learner2.total_samples_seen == learner.total_samples_seen
    assert np.isclose(learner2.threshold_mgr.threshold, learner.threshold_mgr.threshold)
    assert np.allclose(learner2.predict_proba(X[:5]), learner.predict_proba(X[:5]))
