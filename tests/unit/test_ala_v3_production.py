"""
Stage 13 — Production Unit Tests for ALA 3.0 Recurring-Concept Intelligence.

Validates:
1. ConceptFingerprinter (dimension, normalization, validation)
2. RecurringConceptMemory (bounded capacity, similarity matching, eviction, serialization)
3. ALA30AdaptiveLearner (prequential updates, drift resets, concept restorations)
4. AdaptiveClassifier backward compatibility and concept memory extension
"""

import numpy as np
import pytest

from robust_adapt.ala import (
    AdaptiveClassifier,
    ALA30AdaptiveLearner,
    ConceptFingerprinter,
    ConceptSnapshot,
    RecurringConceptMemory,
)
from robust_adapt.core.exceptions import ConfigurationError, ValidationError


def test_concept_fingerprinter_dimensions_and_normalization():
    fp_gen = ConceptFingerprinter(n_features=5, n_classes=2)
    X = np.random.randn(20, 5)
    y = np.random.randint(0, 2, size=20)

    fp = fp_gen.compute_fingerprint(X, y)
    # Expected length: 5 means + 5 stds + 2 priors = 12
    assert fp.shape == (12,)
    # Norm must be 1.0 (unit hypersphere projection)
    assert np.isclose(np.linalg.norm(fp), 1.0, atol=1e-5)


def test_concept_fingerprinter_validation_errors():
    with pytest.raises(ConfigurationError):
        ConceptFingerprinter(n_features=0)
    with pytest.raises(ConfigurationError):
        ConceptFingerprinter(n_features=5, n_classes=0)

    fp_gen = ConceptFingerprinter(n_features=5, n_classes=2)
    with pytest.raises(ValidationError):
        fp_gen.compute_fingerprint(np.empty((0, 5)))


def test_recurring_concept_memory_bounded_capacity_and_eviction():
    mem = RecurringConceptMemory(max_concepts=3, similarity_threshold=0.85)
    assert mem.max_concepts == 3
    assert mem.n_stored == 0

    # Store 3 distinct orthogonal concepts
    fp1 = np.array([1.0, 0.0, 0.0, 0.0])
    fp2 = np.array([0.0, 1.0, 0.0, 0.0])
    fp3 = np.array([0.0, 0.0, 1.0, 0.0])

    s1 = mem.store_concept(fp1, {"w": 1}, step=10)
    s2 = mem.store_concept(fp2, {"w": 2}, step=20)
    s3 = mem.store_concept(fp3, {"w": 3}, step=30)
    assert mem.n_stored == 3

    # Access s1 to boost its usage and last_used_step
    mem.update_concept(s1.concept_id, fp1, {"w": 1.1}, step=40)

    # Store a 4th concept - s2 should be evicted (lowest usage & earliest last_used_step)
    fp4 = np.array([0.0, 0.0, 0.0, 1.0])
    s4 = mem.store_concept(fp4, {"w": 4}, step=50)

    assert mem.n_stored == 3
    assert s2.concept_id not in mem.concepts
    assert s1.concept_id in mem.concepts
    assert s3.concept_id in mem.concepts
    assert s4.concept_id in mem.concepts


def test_recurring_concept_memory_similarity_matching_and_rejection():
    mem = RecurringConceptMemory(max_concepts=5, similarity_threshold=0.85)

    base_fp = np.array([0.8, 0.6, 0.0, 0.0])
    base_fp /= np.linalg.norm(base_fp)
    snap = mem.store_concept(base_fp, "model_A", step=1)

    # Query with a highly similar fingerprint (cos_sim > 0.95)
    query_similar = np.array([0.82, 0.58, 0.0, 0.0])
    query_similar /= np.linalg.norm(query_similar)
    match, sim = mem.find_matching_concept(query_similar)
    assert match is not None
    assert match.concept_id == snap.concept_id
    assert sim >= 0.85

    # Query with a distinct/dissimilar fingerprint (cos_sim < 0.85)
    query_dissimilar = np.array([0.0, 0.0, 1.0, 0.0])
    match_fail, sim_fail = mem.find_matching_concept(query_dissimilar)
    assert match_fail is None
    assert sim_fail < 0.85


def test_recurring_concept_memory_serialization():
    mem = RecurringConceptMemory(max_concepts=5, similarity_threshold=0.80)
    fp = np.array([0.5, 0.5, 0.5, 0.5])
    mem.store_concept(fp, {"weights": [1, 2]}, step=15, metadata={"domain": "power"})

    data = mem.to_dict()
    assert data["max_concepts"] == 5
    assert len(data["concepts"]) == 1

    restored = RecurringConceptMemory.from_dict(data)
    assert restored.max_concepts == 5
    assert restored.similarity_threshold == 0.80
    assert restored.n_stored == 1
    c_id = next(iter(restored.concepts))
    assert restored.concepts[c_id].metadata["domain"] == "power"


def test_ala30_adaptive_learner_prequential_updates():
    np.random.seed(42)
    learner = ALA30AdaptiveLearner(
        n_features=4,
        n_classes=2,
        grace_period=20,
        delta=0.01,
        similarity_threshold=0.80,
        cooldown_steps=2,
        max_concepts=3,
    )

    # Generate synthetic stationary concept
    X_stationary = np.random.randn(200, 4)
    y_stationary = (X_stationary[:, 0] > 0).astype(int)

    for i in range(0, 200, 20):
        X_b, y_b = X_stationary[i:i+20], y_stationary[i:i+20]
        res = learner.update(X_b, y_b)
        assert "action" in res
        assert "batch_acc" in res
        assert 0.0 <= res["batch_acc"] <= 1.0

    assert learner.total_steps == 10
    assert learner.predict(X_stationary[:10]).shape == (10,)
    assert learner.predict_proba(X_stationary[:10]).shape == (10, 2)


def test_ala30_state_dict_roundtrip():
    learner = ALA30AdaptiveLearner(n_features=3, n_classes=2, max_concepts=2)
    X = np.random.randn(50, 3)
    y = np.random.randint(0, 2, size=50)
    learner.update(X, y)

    state = learner.state_dict()
    new_learner = ALA30AdaptiveLearner(n_features=3, n_classes=2, max_concepts=2)
    new_learner.load_state_dict(state)

    assert new_learner.total_steps == learner.total_steps
    assert new_learner.drift_resets == learner.drift_resets
    assert new_learner.recurring_restorations == learner.recurring_restorations


def test_adaptive_classifier_concept_memory_extension():
    # Backward compatible default (enable_concept_memory=False)
    clf_default = AdaptiveClassifier(n_features=4, n_classes=2)
    assert clf_default.enable_concept_memory is False
    assert clf_default._concept_memory is None

    # Extended ALA 3.0 mode (enable_concept_memory=True)
    clf_ala3 = AdaptiveClassifier(
        n_features=4,
        n_classes=2,
        enable_concept_memory=True,
        concept_memory_capacity=5,
        concept_similarity_threshold=0.82,
    )
    assert clf_ala3.enable_concept_memory is True
    assert clf_ala3._concept_memory is not None
    assert clf_ala3._concept_memory.max_concepts == 5

    # Incremental update check
    X = np.random.randn(40, 4)
    y = np.random.randint(0, 2, size=40)
    clf_ala3.partial_fit(X, y)
    assert clf_ala3.samples_seen_ == 40
