"""Robust Learning Algorithms (RLA) module.

Provides multi-signal sample reliability scoring, noise taxonomy classification,
outlier vs rare pattern discrimination, robust loss functions, and evidence-based label correction.
"""

from robust_adapt.rla.label_correction import (
    CorrectionAuditRecord,
    EvidenceBasedLabelCorrector,
)
from robust_adapt.rla.losses import (
    FocalLoss,
    GeneralizedCrossEntropyLoss,
    ReliabilityWeightedLoss,
    SymmetricCrossEntropyLoss,
)
from robust_adapt.rla.noise_classifier import (
    NoiseTaxonomyClassifier,
    NoiseType,
    PatternType,
)
from robust_adapt.rla.pipeline import RLA30RobustLearner, RobustLearningPipeline
from robust_adapt.rla.reliability import (
    AsymmetricTransitionDetector,
    ClassConditionalReliabilityEstimator,
    MultiSignalReliabilityEngine,
)
from robust_adapt.rla.scorer import DensityAwareMarginScorer
from robust_adapt.rla.weighting import ClassBalancedWeights

__all__ = [
    "DensityAwareMarginScorer",
    "SymmetricCrossEntropyLoss",
    "GeneralizedCrossEntropyLoss",
    "FocalLoss",
    "ReliabilityWeightedLoss",
    "ClassBalancedWeights",
    "RobustLearningPipeline",
    "RLA30RobustLearner",
    "MultiSignalReliabilityEngine",
    "ClassConditionalReliabilityEstimator",
    "AsymmetricTransitionDetector",
    "NoiseTaxonomyClassifier",
    "NoiseType",
    "PatternType",
    "EvidenceBasedLabelCorrector",
    "CorrectionAuditRecord",
]
