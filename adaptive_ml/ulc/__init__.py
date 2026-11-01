"""
AdaptiveML Unified Learning Controller (ULC) Module.

Provides holistic cross-pillar arbitration between concept drift adaptation
and noise burst suppression.
"""

from __future__ import annotations

from adaptive_ml.ulc.automaton import ArbitrationAutomaton
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.directives import ControllerDirective, ControllerState
from adaptive_ml.ulc.evidence import EvidenceSynthesizer, EvidenceVector

__all__ = [
    "ControllerState",
    "ControllerDirective",
    "EvidenceVector",
    "EvidenceSynthesizer",
    "ArbitrationAutomaton",
    "AdaptiveLearningController",
]

