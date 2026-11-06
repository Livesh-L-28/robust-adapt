"""Unit tests for Stage 3: Adaptive Minority Intelligence.

Verifies OnlineClassPriorTracker, AdaptiveThresholdManager, MinorityAwareReplayBuffer,
and ClassAwareCalibrator under extreme class imbalance and non-stationary distribution shifts.
"""

import numpy as np
import pytest

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.minority.calibration import ClassAwareCalibrator
from robust_adapt.minority.prior import OnlineClassPriorTracker
from robust_adapt.minority.replay import MinorityAwareReplayBuffer
from robust_adapt.minority.threshold import AdaptiveThresholdManager


class TestOnlineClassPriorTracker:
    """Verifies online prior tracking, Laplace smoothing, and emerging class detection."""

    def test_initialization_and_validation(self) -> None:
        tracker = OnlineClassPriorTracker(n_classes=3)
        assert tracker.n_classes == 3
        np.testing.assert_allclose(tracker.priors, [1/3, 1/3, 1/3])

        with pytest.raises(ConfigurationError):
            OnlineClassPriorTracker(n_classes=1)

        with pytest.raises(ConfigurationError):
            OnlineClassPriorTracker(alpha=-0.1)

    def test_imbalanced_stream_convergence(self) -> None:
        # Stream 95% class 0 and 5% class 1
        tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.1)
        rng = np.random.default_rng(42)

        for _ in range(30):
            batch_y = rng.choice([0, 1], size=100, p=[0.95, 0.05])
            tracker.update(batch_y)

        priors = tracker.priors
        assert priors[0] > 0.90
        assert priors[1] < 0.10
        assert tracker.imbalance_ratio > 9.0
        assert tracker.minority_classes == [1]
        assert tracker.majority_class == 0

    def test_emerging_class_detection(self) -> None:
        tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.1)
        # Stream initial binary data for 20 batches
        for _ in range(20):
            tracker.update(np.zeros(50, dtype=int))

        assert not tracker.is_emerging(0)
        assert not tracker.is_emerging(1)

        # Class 2 suddenly emerges
        batch_new = np.array([2] * 10 + [0] * 40)
        tracker.update(batch_new)

        assert tracker.n_classes == 3
        assert tracker.is_emerging(2)

    def test_state_serialization(self) -> None:
        tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.08)
        tracker.update(np.array([0] * 80 + [1] * 20))
        state = tracker.state_dict()

        tracker2 = OnlineClassPriorTracker(n_classes=2)
        tracker2.load_state_dict(state)
        np.testing.assert_allclose(tracker.priors, tracker2.priors)
        assert tracker.total_samples_seen == tracker2.total_samples_seen


class TestAdaptiveThresholdManager:
    """Verifies decision threshold adaptation, cost-sensitivity, and validation tuning."""

    def test_dynamic_threshold_shifts_with_prior(self) -> None:
        mgr = AdaptiveThresholdManager(n_classes=2, mode="dynamic", base_threshold=0.5, gamma=0.5)

        # Balanced priors -> threshold = 0.5
        mgr.update_from_priors(np.array([0.5, 0.5]))
        assert mgr.primary_threshold == pytest.approx(0.5)

        # Minority prior drops to 0.05 -> threshold should decrease to boost recall
        mgr.update_from_priors(np.array([0.95, 0.05]))
        assert mgr.primary_threshold < 0.30

    def test_cost_sensitive_threshold(self) -> None:
        # C[0, 1] = 1 (FP cost), C[1, 0] = 9 (FN cost, missing fraud is 9x worse)
        cost_mat = np.array([[0.0, 1.0], [9.0, 0.0]])
        mgr = AdaptiveThresholdManager(n_classes=2, mode="cost_sensitive", cost_matrix=cost_mat)
        # Bayes optimal: 1 / (1 + 9) = 0.1
        assert mgr.primary_threshold == pytest.approx(0.1)

    def test_optimize_on_validation_window(self) -> None:
        mgr = AdaptiveThresholdManager(n_classes=2, mode="pr_constrained")
        rng = np.random.default_rng(42)

        # Generate synthetic validation probabilities and labels
        val_labels = np.array([0] * 90 + [1] * 10)
        # Class 1 probabilities concentrated around 0.35, Class 0 around 0.15
        val_probs = np.where(val_labels == 1, rng.uniform(0.3, 0.6, size=100), rng.uniform(0.05, 0.25, size=100))

        best_tau = mgr.optimize_on_validation(val_probs, val_labels, metric="f1")
        assert 0.20 <= best_tau <= 0.35

        # Predictions with optimal threshold should have high F1
        preds = mgr.predict(val_probs)
        tp = np.sum((preds == 1) & (val_labels == 1))
        assert tp >= 8  # Catches vast majority of minority instances

    def test_threshold_rollback(self) -> None:
        mgr = AdaptiveThresholdManager(n_classes=2, mode="dynamic", base_threshold=0.5)
        mgr.update_from_priors(np.array([0.5, 0.5]))
        tau_init = mgr.primary_threshold

        mgr.update_from_priors(np.array([0.99, 0.01]))
        assert mgr.primary_threshold != tau_init

        mgr.rollback()
        assert mgr.primary_threshold == pytest.approx(tau_init)


class TestMinorityAwareReplayBuffer:
    """Verifies memory preservation under extreme 1000:1 stream imbalance."""

    def test_extreme_imbalance_retention(self) -> None:
        buf = MinorityAwareReplayBuffer(
            capacity=500,
            n_classes=2,
            min_minority_fraction=0.40,
            random_state=42,
        )
        rng = np.random.default_rng(42)

        # Ingest 10 minority samples (class 1)
        X_min = rng.normal(size=(10, 4))
        y_min = np.ones(10, dtype=int)
        buf.add(X_min, y_min)

        # Flood with 2000 majority samples (class 0) - ratio 200:1
        for _ in range(20):
            X_maj = rng.normal(size=(100, 4))
            y_maj = np.zeros(100, dtype=int)
            buf.add(X_maj, y_maj)

        # All 10 minority instances MUST be strictly preserved in buffer!
        assert buf.class_counts[1] == 10
        assert buf.class_counts[0] <= 300  # Majority strictly bounded by capacity quota

    def test_reliability_noise_filtering(self) -> None:
        buf = MinorityAwareReplayBuffer(capacity=100, n_classes=2, min_reliability=0.5)
        X = np.random.randn(10, 4)
        y = np.ones(10, dtype=int)
        # All low reliability (noise)
        w = np.full(10, 0.2)

        ingested = buf.add(X, y, sample_weight=w)
        assert ingested == 0
        assert buf.total_stored == 0

    def test_sample_balanced_stratification(self) -> None:
        buf = MinorityAwareReplayBuffer(capacity=200, n_classes=2, min_minority_fraction=0.4, random_state=42)
        X0 = np.random.randn(80, 4)
        y0 = np.zeros(80, dtype=int)
        X1 = np.random.randn(20, 4)
        y1 = np.ones(20, dtype=int)
        buf.add(X0, y0)
        buf.add(X1, y1)

        X_rep, y_rep = buf.sample_balanced(n_samples=20, target_minority_ratio=0.5)
        assert X_rep.shape[0] == 20
        # Exactly or approximately 50% minority samples
        assert np.sum(y_rep == 1) >= 8

    def test_purge_selective_protects_minority(self) -> None:
        buf = MinorityAwareReplayBuffer(capacity=200, n_classes=2, random_state=42)
        X0 = np.random.randn(60, 4)
        y0 = np.zeros(60, dtype=int)
        w0 = np.array([0.3] * 30 + [0.8] * 30)

        X1 = np.random.randn(15, 4)
        y1 = np.ones(15, dtype=int)
        w1 = np.full(15, 0.3)  # low reliability minority

        buf.add(X0, y0, sample_weight=w0)
        buf.add(X1, y1, sample_weight=w1)

        purged = buf.purge(policy="selective", min_reliability=0.5, keep_minority=True)
        assert buf.class_counts[1] == 15  # 100% minority preserved
        assert buf.class_counts[0] == 30  # Low-reliability majority purged
        assert purged == 30


class TestClassAwareCalibrator:
    """Verifies temperature scaling, calibration error reduction, and Brier scoring."""

    def test_temperature_scaling_reduces_ece(self) -> None:
        calibrator = ClassAwareCalibrator(n_classes=2, lr=0.1, max_iter=80)
        rng = np.random.default_rng(42)

        # Overconfident uncalibrated logits
        # Model is 95% confident on average, but true accuracy is only 75%
        labels = rng.choice([0, 1], size=200, p=[0.7, 0.3])
        # True positive logits biased, but exaggerated
        logits = np.zeros((200, 2))
        for i in range(200):
            correct = rng.random() < 0.75
            pred = labels[i] if correct else (1 - labels[i])
            logits[i, pred] = 4.0
            logits[i, 1 - pred] = -4.0

        ece_before = calibrator.compute_ece(calibrator.calibrate(logits, is_logit=True), labels)

        # Fit temperatures on validation window
        calibrator.fit_validation(logits, labels, is_logit=True)
        # Temperatures should have increased (> 1.0) to soften overconfident logits
        assert np.all(calibrator.temperatures > 1.2)

        calibrated_probs = calibrator.calibrate(logits, is_logit=True)
        ece_after = calibrator.compute_ece(calibrated_probs, labels)

        # Calibration error must be significantly reduced
        assert ece_after < ece_before
        assert ece_after < 0.15

    def test_brier_score_computation(self) -> None:
        calibrator = ClassAwareCalibrator(n_classes=2)
        # Perfect predictions
        probs = np.array([[1.0, 0.0], [0.0, 1.0]])
        labels = np.array([0, 1])
        brier = calibrator.compute_brier_score(probs, labels)
        assert brier == pytest.approx(0.0)

        # Totally wrong predictions
        probs_wrong = np.array([[0.0, 1.0], [1.0, 0.0]])
        brier_wrong = calibrator.compute_brier_score(probs_wrong, labels)
        assert brier_wrong == pytest.approx(2.0)
