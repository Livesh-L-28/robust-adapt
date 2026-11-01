"""Adaptive Learning Algorithms (ALA) module."""

from adaptive_ml.ala.tree import VectorizedHoeffdingTree
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.ala.ensemble import StreamingEnsemble
from adaptive_ml.ala.classifier import AdaptiveClassifier

__all__ = [
    "VectorizedHoeffdingTree",
    "ReliabilityWeightedADWIN",
    "ClassBalancedReservoirReplay",
    "StreamingEnsemble",
    "AdaptiveClassifier",
]
