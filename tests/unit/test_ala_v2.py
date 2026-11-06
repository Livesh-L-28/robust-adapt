"""Unit tests for Stage 4: ALA 2.0 (Advanced Adaptive Learning Algorithms).

Verifies CUSUM, Page-Hinkley, MultiDetectorConsensus, DriftClassifier taxonomy & attribution,
ConceptMemory recurring restoration, and DelayedLabelQueue.
"""

import numpy as np
import pytest

from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.ala.delayed_labels import DelayedLabelQueue
from robust_adapt.ala.detector import CUSUMDetector, MultiDetectorConsensus, PageHinkleyDetector
from robust_adapt.ala.drift_classifier import DriftClassifier, DriftNature, DriftType


class TestMultiDetectors:
    """Verifies CUSUM, Page-Hinkley, and MultiDetectorConsensus behavior."""

    def test_cusum_stationary_and_drift(self) -> None:
        det = CUSUMDetector(target_mean=0.1, delta=0.01, threshold=3.0)
        rng = np.random.default_rng(42)

        # Stationary: mean 0.10
        stationary_drift = False
        for _ in range(50):
            val = float(rng.normal(0.10, 0.02))
            if det.update(val):
                stationary_drift = True
        assert not stationary_drift

        # Sudden shift: mean jumps to 0.50
        drift_found = False
        for _ in range(30):
            val = float(rng.normal(0.50, 0.05))
            if det.update(val):
                drift_found = True
                break
        assert drift_found

    def test_page_hinkley_drift_detection(self) -> None:
        det = PageHinkleyDetector(threshold=5.0)
        rng = np.random.default_rng(42)

        # Baseline
        for _ in range(40):
            det.update(float(rng.normal(0.0, 0.1)))

        # Mean shift
        drift_detected = False
        for _ in range(30):
            if det.update(float(rng.normal(2.0, 0.2))):
                drift_detected = True
                break
        assert drift_detected

    def test_multi_detector_consensus_majority(self) -> None:
        consensus = MultiDetectorConsensus(voting_strategy="majority")
        rng = np.random.default_rng(42)

        # Baseline stationary stream
        for _ in range(50):
            flag, conf, votes = consensus.update(float(rng.normal(0.05, 0.01)), reliability=1.0)
            assert not flag

        # Shift
        detected = False
        for _ in range(40):
            flag, conf, votes = consensus.update(float(rng.normal(0.80, 0.05)), reliability=1.0)
            if flag:
                detected = True
                assert conf >= 0.5
                assert isinstance(votes, dict)
                break
        assert detected


class TestDriftClassifier:
    """Verifies drift taxonomy classification and feature attribution."""

    def test_abrupt_concept_drift_classification(self) -> None:
        classifier = DriftClassifier(n_features=4, window_size=50, reference_window_size=100)
        rng = np.random.default_rng(42)

        # Reference stationary window (mean 0, error 0.05)
        for _ in range(10):
            X_ref = rng.normal(0.0, 1.0, size=(10, 4))
            y_ref = np.zeros(10, dtype=int)
            err_ref = np.full(10, 0.05)
            classifier.update(X_ref, y_ref, errors=err_ref)

        res_stat = classifier.analyze()
        assert res_stat.drift_type == DriftType.STATIONARY

        # Abrupt jump: feature 2 shifts by +4.0 and error surges to 0.75
        X_drift = rng.normal(0.0, 1.0, size=(50, 4))
        X_drift[:, 2] += 4.0  # Feature 2 causes major drift
        y_drift = np.ones(50, dtype=int)
        err_drift = np.full(50, 0.75)
        classifier.update(X_drift, y_drift, errors=err_drift)

        res_drift = classifier.analyze()
        assert res_drift.drift_type == DriftType.ABRUPT
        assert res_drift.drift_nature in (DriftNature.DUAL_DRIFT, DriftNature.CONCEPT_DRIFT)
        assert res_drift.severity >= 0.70
        # Feature 2 must be identified as the top contributor
        top_idx, top_score = res_drift.top_features[0]
        assert top_idx == 2
        assert top_score > 2.0


class TestConceptMemory:
    """Verifies signature matching and recurring concept restoration."""

    def test_store_and_query_recurring_concept(self) -> None:
        memory = ConceptMemory(max_concepts=5, similarity_threshold=0.75)
        rng = np.random.default_rng(42)

        # Concept A: Gaussian centered at -3.0
        X_A = rng.normal(-3.0, 0.5, size=(100, 4))
        state_A = {"model_name": "Model_A", "weights": np.array([1.0, -1.0])}
        memory.store_concept("concept_A", state_A, X_A)

        # Concept B: Gaussian centered at +3.0
        X_B = rng.normal(3.0, 0.5, size=(100, 4))
        state_B = {"model_name": "Model_B", "weights": np.array([-2.0, 2.0])}
        memory.store_concept("concept_B", state_B, X_B)

        assert memory.n_stored == 2

        # Candidate Stream matches Concept A distribution
        X_query_A = rng.normal(-3.0, 0.5, size=(50, 4))
        match_A = memory.query_recurring(X_query_A)
        assert match_A is not None
        c_id, restored_state, sim = match_A
        assert c_id == "concept_A"
        assert restored_state["model_name"] == "Model_A"
        assert sim > 0.85

        # Novel unseen concept centered at +10.0
        X_novel = rng.normal(10.0, 0.5, size=(50, 4))
        match_novel = memory.query_recurring(X_novel)
        assert match_novel is None  # Does not trigger false recurring match


class TestDelayedLabelQueue:
    """Verifies delayed feedback streaming and timestamp synchronization."""

    def test_enqueue_and_delayed_matching(self) -> None:
        queue = DelayedLabelQueue(max_queue_size=100)
        X1 = np.array([1.0, 2.0, 3.0])
        X2 = np.array([4.0, 5.0, 6.0])

        # Enqueue 2 predictions at t=10.0
        queue.enqueue("sample_1", X1, prediction=0, timestamp=10.0)
        queue.enqueue("sample_2", X2, prediction=1, timestamp=10.0)

        assert queue.pending_count == 2
        assert queue.ready_count == 0

        # Ground truth label for sample_1 arrives at t=15.0 (delay = 5.0)
        matched1 = queue.provide_label("sample_1", label=0, arrival_timestamp=15.0)
        assert matched1
        assert queue.pending_count == 1
        assert queue.ready_count == 1

        # Ground truth label for sample_2 arrives at t=18.0 (delay = 8.0)
        matched2 = queue.provide_label("sample_2", label=1, arrival_timestamp=18.0)
        assert matched2
        assert queue.pending_count == 0
        assert queue.ready_count == 2

        # Extract ready training batch
        X_batch, y_batch, w_batch, delays = queue.extract_ready_batch()
        assert X_batch.shape == (2, 3)
        np.testing.assert_array_equal(y_batch, [0, 1])
        np.testing.assert_allclose(delays, [5.0, 8.0])
        assert queue.ready_count == 0

    def test_timeout_pruning(self) -> None:
        queue = DelayedLabelQueue(max_queue_size=50, max_wait_time=10.0)
        queue.enqueue("expired_sample", np.zeros(2), timestamp=5.0)
        queue.enqueue("fresh_sample", np.ones(2), timestamp=14.0)

        # Current stream time is 18.0 -> expired_sample elapsed 13.0 > 10.0
        pruned = queue.prune_timeouts(current_time=18.0)
        assert pruned == 1
        assert queue.pending_count == 1
        # Label arrival for timed-out sample returns False
        assert not queue.provide_label("expired_sample", label=0, arrival_timestamp=19.0)
