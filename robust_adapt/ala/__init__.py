"""Adaptive Learning Algorithms (ALA) module.

Provides streaming classifiers, vector Hoeffding trees, multi-detector drift ensembles,
drift taxonomy classification, concept memory, and delayed-label streaming.
"""

from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.classifier import ALA30AdaptiveLearner, AdaptiveClassifier
from robust_adapt.ala.concept_memory import (
    ConceptFingerprinter,
    ConceptMemory,
    ConceptSignature,
    ConceptSnapshot,
    RecurringConceptMemory,
)
from robust_adapt.ala.delayed_labels import DelayedLabelQueue
from robust_adapt.ala.detector import (
    BaseDriftDetector,
    CUSUMDetector,
    MultiDetectorConsensus,
    PageHinkleyDetector,
)
from robust_adapt.ala.drift_classifier import (
    DriftAnalysisResult,
    DriftClassifier,
    DriftNature,
    DriftType,
)
from robust_adapt.ala.ensemble import StreamingEnsemble
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.ala.tree import VectorizedHoeffdingTree

__all__ = [
    "VectorizedHoeffdingTree",
    "ReliabilityWeightedADWIN",
    "ClassBalancedReservoirReplay",
    "StreamingEnsemble",
    "AdaptiveClassifier",
    "BaseDriftDetector",
    "CUSUMDetector",
    "PageHinkleyDetector",
    "MultiDetectorConsensus",
    "DriftClassifier",
    "DriftType",
    "DriftNature",
    "DriftAnalysisResult",
    "ConceptMemory",
    "ConceptSignature",
    "ConceptFingerprinter",
    "RecurringConceptMemory",
    "ConceptSnapshot",
    "ALA30AdaptiveLearner",
    "DelayedLabelQueue",
]
