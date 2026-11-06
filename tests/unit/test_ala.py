"""Unit tests for Phase 8 ALA (Adaptive Learning Algorithms)."""

import pytest
import numpy as np
from robust_adapt.ala.tree import VectorizedHoeffdingTree
from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.ala.ensemble import StreamingEnsemble
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.core.exceptions import ValidationError


class TestVectorizedHoeffdingTree:
    """Tests for VectorizedHoeffdingTree."""

    def test_initialization_and_validation(self) -> None:
        tree = VectorizedHoeffdingTree(n_features=4, n_classes=3, grace_period=50)
        assert tree.n_features == 4
        assert tree.n_classes == 3

        with pytest.raises(ValidationError):
            VectorizedHoeffdingTree(n_features=0, n_classes=2)
        with pytest.raises(ValidationError):
            VectorizedHoeffdingTree(n_features=4, n_classes=1)

    def test_partial_fit_and_prediction(self) -> None:
        rng = np.random.default_rng(42)
        tree = VectorizedHoeffdingTree(
            n_features=2,
            n_classes=2,
            grace_period=40,
            delta=1e-3,
            tau_tie=0.1,
        )

        # Linearly separable clusters
        X0 = rng.normal(loc=[-2.0, -2.0], scale=0.5, size=(100, 2))
        y0 = np.zeros(100, dtype=np.int64)
        X1 = rng.normal(loc=[2.0, 2.0], scale=0.5, size=(100, 2))
        y1 = np.ones(100, dtype=np.int64)

        X = np.vstack([X0, X1])
        y = np.concatenate([y0, y1])

        # Shuffle
        perm = rng.permutation(200)
        X = X[perm]
        y = y[perm]

        # Ingest in mini-batches
        for b in range(0, 200, 50):
            tree.partial_fit(X[b : b + 50], y[b : b + 50])

        assert tree.total_samples_seen == 200

        # Test predictions
        probs = tree.predict_proba(X)
        assert probs.shape == (200, 2)
        assert np.allclose(np.sum(probs, axis=1), 1.0)

        preds = tree.predict(X)
        accuracy = np.mean(preds == y)
        assert accuracy > 0.85

    def test_state_serialization(self) -> None:
        rng = np.random.default_rng(123)
        tree = VectorizedHoeffdingTree(n_features=3, n_classes=2, grace_period=50)
        X = rng.normal(size=(120, 3))
        y = rng.integers(0, 2, size=120)
        tree.partial_fit(X, y)

        state = tree.state_dict()
        tree2 = VectorizedHoeffdingTree(n_features=3, n_classes=2)
        tree2.load_state_dict(state)

        p1 = tree.predict_proba(X)
        p2 = tree2.predict_proba(X)
        assert np.allclose(p1, p2)


class TestReliabilityWeightedADWIN:
    """Tests for ReliabilityWeightedADWIN."""

    def test_stationary_stream_no_false_alarm(self) -> None:
        rng = np.random.default_rng(42)
        adwin = ReliabilityWeightedADWIN(delta=0.01)

        drifts = 0
        for _ in range(300):
            val = float(rng.normal(loc=0.3, scale=0.05))
            val = float(np.clip(val, 0.0, 1.0))
            if adwin.update(val, reliability=1.0):
                drifts += 1

        assert drifts == 0
        assert adwin.total_samples == 300

    def test_abrupt_drift_detection(self) -> None:
        adwin = ReliabilityWeightedADWIN(delta=0.01)

        # Phase 1: mean 0.1
        for _ in range(150):
            adwin.update(0.1, reliability=1.0)

        # Phase 2: abrupt shift to mean 0.9
        detected = False
        for step in range(150):
            if adwin.update(0.9, reliability=1.0):
                detected = True
                break

        assert detected, "Abrupt concept drift should be detected"

    def test_noise_burst_suppression_via_reliability(self) -> None:
        """Theorem 1 verification: low-reliability noise burst suppresses false drift alarm."""
        adwin = ReliabilityWeightedADWIN(delta=0.01)

        # Clean stationary stream: mean 0.1
        for _ in range(100):
            adwin.update(0.1, reliability=1.0)

        # Burst of 10 noisy corruptions with high error (1.0), but flagged with low reliability (0.01)
        detected = False
        for _ in range(10):
            if adwin.update(1.0, reliability=0.01):
                detected = True
                break

        assert not detected, "Low reliability noise burst should NOT trigger concept drift alarm"


class TestClassBalancedReservoirReplay:
    """Tests for ClassBalancedReservoirReplay."""

    def test_extreme_imbalance_retention(self) -> None:
        rng = np.random.default_rng(999)
        replay = ClassBalancedReservoirReplay(capacity=100, n_classes=2)

        # 1000 instances of majority class 0, 10 instances of minority class 1 (100:1 ratio)
        X_maj = rng.normal(size=(1000, 4))
        y_maj = np.zeros(1000, dtype=np.int64)

        X_min = rng.normal(size=(10, 4))
        y_min = np.ones(10, dtype=np.int64)

        replay.add(X_maj, y_maj)
        replay.add(X_min, y_min)

        counts = replay.class_counts
        # Total stored bounded by capacity (<= 100)
        assert replay.total_stored <= 100
        # Minority class 1 MUST retain all its 10 samples rather than being purged
        assert counts[1] == 10
        assert counts[0] == 50  # Majority capped at bucket capacity 50

    def test_stratified_sample(self) -> None:
        rng = np.random.default_rng(42)
        replay = ClassBalancedReservoirReplay(capacity=60, n_classes=3)
        for c in range(3):
            X_c = rng.normal(size=(50, 2))
            y_c = np.full(50, c, dtype=np.int64)
            replay.add(X_c, y_c)

        X_s, y_s = replay.sample(n_samples=15)
        assert X_s.shape == (15, 2)
        # Should have samples from all 3 classes
        assert set(np.unique(y_s)) == {0, 1, 2}


class TestAdaptiveClassifier:
    """Tests for AdaptiveClassifier."""

    def test_fit_and_partial_fit(self) -> None:
        rng = np.random.default_rng(42)
        clf = AdaptiveClassifier(
            n_features=3,
            n_classes=2,
            grace_period=30,
            enable_drift_detection=True,
            replay_capacity=100,
        )

        X = rng.normal(size=(150, 3))
        y = (X[:, 0] + X[:, 1] > 0).astype(np.int64)

        clf.partial_fit(X[:100], y[:100])
        assert clf.samples_seen_ == 100

        clf.partial_fit(X[100:], y[100:])
        assert clf.samples_seen_ == 150

        acc = clf.score(X, y)
        assert 0.0 <= acc <= 1.0

    def test_ensemble_mode(self) -> None:
        rng = np.random.default_rng(42)
        clf = AdaptiveClassifier(
            n_features=2,
            n_classes=2,
            n_estimators=3,
            grace_period=20,
        )

        X = rng.normal(size=(100, 2))
        y = (X[:, 0] > 0).astype(np.int64)

        clf.fit(X, y)
        probs = clf.predict_proba(X)
        assert probs.shape == (100, 2)
        assert np.allclose(np.sum(probs, axis=1), 1.0)
