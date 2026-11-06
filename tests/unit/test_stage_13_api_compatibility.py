"""Unit tests for Stage 13 Public API & Compatibility."""

import inspect
import pytest
import robust_adapt
from robust_adapt.ala import (
    ALA30AdaptiveLearner,
    AdaptiveClassifier,
    ConceptFingerprinter,
    ConceptSnapshot,
    RecurringConceptMemory,
)
from robust_adapt.rla import (
    AsymmetricTransitionDetector,
    ClassConditionalReliabilityEstimator,
    RLA30RobustLearner,
    RobustLearningPipeline,
)
from robust_adapt.minority import (
    BetaBinomialPriorTracker,
    DynamicFPBudgetThresholdManager,
    MinorityIntelligence20Learner,
    compute_sublinear_cost_weights,
)
from robust_adapt.rao import LowMemoryAdamW
from robust_adapt.ulc import (
    InterventionTier,
    ULCv5Config,
    ULCv5Directive,
    UnifiedLearningControllerV4_1,
    UnifiedLearningControllerV5,
    UtilityScorer,
)


def test_top_level_exports() -> None:
    """Verify that all symbols declared in __all__ are accessible at top-level."""
    for symbol in robust_adapt.__all__:
        assert hasattr(robust_adapt, symbol), f"Top-level export missing: {symbol}"


def test_subpackage_exports() -> None:
    """Verify subpackage exports match Stage 13 architectural specifications."""
    # ALA 3.0
    assert inspect.isclass(ALA30AdaptiveLearner)
    assert hasattr(robust_adapt.ala, "RecurringConceptMemory")
    assert hasattr(robust_adapt.ala, "ConceptFingerprinter")

    # RLA 3.0
    assert inspect.isclass(RLA30RobustLearner)
    assert hasattr(robust_adapt.rla, "AsymmetricTransitionDetector")
    assert hasattr(robust_adapt.rla, "ClassConditionalReliabilityEstimator")

    # Minority 2.0
    assert hasattr(robust_adapt.minority, "BetaBinomialPriorTracker")
    assert hasattr(robust_adapt.minority, "DynamicFPBudgetThresholdManager")
    assert hasattr(robust_adapt.minority, "compute_sublinear_cost_weights")
    assert hasattr(robust_adapt.minority, "MinorityIntelligence20Learner")

    # RAO 2.0
    assert hasattr(robust_adapt.rao, "LowMemoryAdamW")
    if hasattr(robust_adapt.rao, "VectorizedLowMemoryAdamW"):
        assert inspect.isclass(robust_adapt.rao.VectorizedLowMemoryAdamW)

    # ULC-v5
    assert inspect.isclass(UnifiedLearningControllerV5)
    assert inspect.isclass(ULCv5Config)
    assert inspect.isclass(UtilityScorer)
    assert issubclass(InterventionTier, str)


def test_estimator_interface_compliance() -> None:
    """Verify that all new learner classes implement partial_fit, predict, predict_proba, and score."""
    learners = [
        ALA30AdaptiveLearner(n_features=2, n_classes=2),
        RLA30RobustLearner(n_features=2, n_classes=2),
        MinorityIntelligence20Learner(),
    ]

    for model in learners:
        assert hasattr(model, "partial_fit")
        assert callable(model.partial_fit)
        assert hasattr(model, "predict")
        assert callable(model.predict)
        assert hasattr(model, "predict_proba")
        assert callable(model.predict_proba)
        assert hasattr(model, "score")
        assert callable(model.score)
