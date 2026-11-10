"""Unit tests for Phase 17.7 Alpha usability defect remediations.

Covers:
- ALPHA-DEF-001: DelayedLabelQueue max_delay alias and property
- ALPHA-DEF-002: ConceptMemory.store_concept signature flexibility
- ALPHA-DEF-003: BlockQuantizer generic quantize and dequantize methods
- ALPHA-DEF-004: Scikit-learn integration canonical aliases and top-level export
- ALPHA-DEF-005: MultiSignalReliabilityEngine logits support and stable softmax
- ALPHA-DEF-006: MinorityIntelligence20Learner upfront feature and class configuration
"""

import numpy as np
import pytest

from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.ala.delayed_labels import DelayedLabelQueue
from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.minority.learner import MinorityIntelligence20Learner
from robust_adapt.rao.quantizer import BlockQuantizer
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine, _stable_softmax


# ---------------------------------------------------------------------------
# ALPHA-DEF-001: DelayedLabelQueue max_delay alias
# ---------------------------------------------------------------------------

def test_delayed_label_queue_max_delay_alias():
    """Verify max_delay alias and property behavior."""
    # Test initialization with max_delay alias
    queue = DelayedLabelQueue(max_delay=120.0, max_queue_size=100)
    assert queue.max_wait_time == 120.0
    assert queue.max_delay == 120.0

    # Test initialization with canonical max_wait_time
    queue2 = DelayedLabelQueue(max_wait_time=90.0)
    assert queue2.max_wait_time == 90.0
    assert queue2.max_delay == 90.0

    # Test initialization with both set consistently
    queue3 = DelayedLabelQueue(max_wait_time=45.0, max_delay=45.0)
    assert queue3.max_wait_time == 45.0
    assert queue3.max_delay == 45.0

    # Test conflicting arguments raise ValidationError
    with pytest.raises(ValidationError, match="Conflicting"):
        DelayedLabelQueue(max_wait_time=30.0, max_delay=60.0)


# ---------------------------------------------------------------------------
# ALPHA-DEF-002: ConceptMemory.store_concept signature flexibility
# ---------------------------------------------------------------------------

def test_concept_memory_store_concept_signatures():
    """Verify ConceptMemory.store_concept supports both legacy and intuitive ordering."""
    mem = ConceptMemory(max_concepts=5, similarity_threshold=0.8)
    rng = np.random.RandomState(42)
    X1 = rng.randn(20, 4)
    y1 = rng.randint(0, 2, size=20)
    state1 = {"weights": [1.0, 2.0]}

    # Legacy signature: (concept_id, model_state, X, y)
    sig1 = mem.store_concept("concept_legacy", state1, X1, y1)
    assert sig1.concept_id == "concept_legacy"
    assert mem.get_model("concept_legacy") == state1

    # Intuitive signature: (concept_id, X, y, model_state)
    X2 = rng.randn(20, 4)
    y2 = rng.randint(0, 2, size=20)
    state2 = {"weights": [3.0, 4.0]}
    sig2 = mem.store_concept("concept_intuitive", X2, y2, state2)
    assert sig2.concept_id == "concept_intuitive"
    assert mem.get_model("concept_intuitive") == state2

    # Intuitive signature without y: (concept_id, X, model_state)
    X3 = rng.randn(20, 4)
    state3 = {"weights": [5.0, 6.0]}
    sig3 = mem.store_concept("concept_no_y", X3, state3)
    assert sig3.concept_id == "concept_no_y"
    assert mem.get_model("concept_no_y") == state3

    # Keyword arguments: (concept_id=..., X=..., y=..., model_state=...)
    X4 = rng.randn(20, 4)
    y4 = rng.randint(0, 2, size=20)
    state4 = {"weights": [7.0, 8.0]}
    sig4 = mem.store_concept(concept_id="concept_kw", X=X4, y=y4, model_state=state4)
    assert sig4.concept_id == "concept_kw"
    assert mem.get_model("concept_kw") == state4


# ---------------------------------------------------------------------------
# ALPHA-DEF-003: BlockQuantizer generic quantize & dequantize
# ---------------------------------------------------------------------------

def test_block_quantizer_generic_methods():
    """Verify quantize and dequantize dispatch correctly for signed and unsigned modes."""
    bq = BlockQuantizer(block_size=64)
    rng = np.random.RandomState(42)

    # Signed test
    signed_data = rng.randn(256).astype(np.float32)
    q_signed, scales_signed = bq.quantize(signed_data, signed=True)
    assert q_signed.dtype == np.int8
    assert len(scales_signed) == 4
    recon_signed = bq.dequantize(q_signed, scales_signed, signed=True)
    assert recon_signed.shape == signed_data.shape
    mse_signed = float(np.mean((signed_data - recon_signed) ** 2))
    assert mse_signed < 1e-3

    # Unsigned test
    unsigned_data = np.abs(rng.randn(256)).astype(np.float32)
    q_unsigned, scales_unsigned = bq.quantize(unsigned_data, signed=False)
    assert q_unsigned.dtype == np.uint8
    assert len(scales_unsigned) == 4
    recon_unsigned = bq.dequantize(q_unsigned, scales_unsigned, signed=False)
    assert recon_unsigned.shape == unsigned_data.shape
    mse_unsigned = float(np.mean((unsigned_data - recon_unsigned) ** 2))
    assert mse_unsigned < 1e-3


# ---------------------------------------------------------------------------
# ALPHA-DEF-004: Scikit-learn integration canonical aliases and top-level export
# ---------------------------------------------------------------------------

def test_sklearn_canonical_aliases():
    """Verify ScikitLearn* aliases exist and export consistently."""
    from robust_adapt.integrations.sklearn import (
        ScikitLearnAdaptiveClassifier,
        ScikitLearnDriftDetectorTransformer,
        ScikitLearnReliabilityFilter,
        SklearnAdaptiveClassifier,
        SklearnDriftDetectorTransformer,
        SklearnReliabilityFilter,
    )
    assert ScikitLearnAdaptiveClassifier is SklearnAdaptiveClassifier
    assert ScikitLearnDriftDetectorTransformer is SklearnDriftDetectorTransformer
    assert ScikitLearnReliabilityFilter is SklearnReliabilityFilter

    # Top-level dynamic import
    import robust_adapt
    assert hasattr(robust_adapt, "ScikitLearnAdaptiveClassifier")
    assert hasattr(robust_adapt, "SklearnAdaptiveClassifier")
    assert robust_adapt.ScikitLearnAdaptiveClassifier is SklearnAdaptiveClassifier


# ---------------------------------------------------------------------------
# ALPHA-DEF-005: MultiSignalReliabilityEngine logits support
# ---------------------------------------------------------------------------

def test_reliability_engine_logits_support():
    """Verify logits support with stable softmax produces equivalent reliability."""
    engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=3, buffer_size=50)
    rng = np.random.RandomState(42)

    X = rng.randn(15, 4)
    y = rng.randint(0, 2, size=15)
    logits = rng.randn(15, 2)

    # Compute expected probabilities using stable softmax
    probs = _stable_softmax(logits)

    engine.clear()
    rel_probs = engine.compute_reliability(X, y, probs, input_type="probabilities")

    engine.clear()
    rel_logits_param = engine.compute_reliability(X, y, logits, input_type="logits")

    engine.clear()
    rel_from_logits = engine.compute_reliability_from_logits(X, y, logits)

    # Verify identical output across all three methods
    np.testing.assert_allclose(rel_probs, rel_logits_param, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(rel_probs, rel_from_logits, rtol=1e-5, atol=1e-5)

    # Verify invalid input_type raises ValidationError
    with pytest.raises(ValidationError, match="input_type must be"):
        engine.compute_reliability(X, y, probs, input_type="invalid_type")


# ---------------------------------------------------------------------------
# ALPHA-DEF-006: MinorityIntelligence20Learner upfront configuration
# ---------------------------------------------------------------------------

def test_minority_learner_upfront_configuration():
    """Verify n_features and n_classes configuration upfront."""
    # Test upfront initialization with n_features
    learner = MinorityIntelligence20Learner(n_features=8, n_classes=2, random_state=42)
    assert learner.weights is not None
    assert learner.weights.shape == (8,)
    assert learner.n_classes == 2

    # Fit a batch matching n_features
    rng = np.random.RandomState(42)
    X = rng.randn(20, 8)
    y = rng.binomial(1, 0.1, size=20)
    info = learner.fit_batch(X, y)
    assert info["total_samples"] == 20
    assert learner.weights.shape == (8,)

    # Dimension mismatch in subsequent batch raises ValidationError
    X_bad = rng.randn(10, 5)
    y_bad = rng.binomial(1, 0.1, size=10)
    with pytest.raises(ValidationError, match="Feature dimension mismatch"):
        learner.fit_batch(X_bad, y_bad)

    # Test invalid n_classes raises ConfigurationError
    with pytest.raises(ConfigurationError, match="binary classification"):
        MinorityIntelligence20Learner(n_classes=3)

    # Test invalid n_features raises ConfigurationError
    with pytest.raises(ConfigurationError, match="n_features must be positive"):
        MinorityIntelligence20Learner(n_features=0)

    # Test lazy initialization still works (backward compatibility)
    lazy_learner = MinorityIntelligence20Learner()
    assert lazy_learner.weights is None
    lazy_info = lazy_learner.fit_batch(X, y)
    assert lazy_learner.weights is not None
    assert lazy_learner.weights.shape == (8,)
    assert lazy_info["total_samples"] == 20
