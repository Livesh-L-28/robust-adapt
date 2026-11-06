"""AdaptiveML Unified Learning Controller (ULC) Module.

Provides holistic cross-pillar arbitration between concept drift adaptation,
noise burst suppression, resource-aware optimization, and minority intelligence.
Includes both the baseline controller and the advanced ULC-v4 orchestration suite.
"""

from __future__ import annotations

from robust_adapt.ulc.arbitrator import ArbitrationWeights, MultiObjectiveArbitrator
from robust_adapt.ulc.automaton import ArbitrationAutomaton
from robust_adapt.ulc.confidence import ConfidenceEngine, ConfidenceScores
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.controller import AdaptiveLearningController
from robust_adapt.ulc.directives import ControllerDirective, ControllerState
from robust_adapt.ulc.evidence import EvidenceSynthesizer, EvidenceVector
from robust_adapt.ulc.explainer import ULCExplainer
from robust_adapt.ulc.spatial import compute_spatial_discordance
from robust_adapt.ulc.v4_automaton import (
    ArbitrationAutomatonV4,
    AutomatonStateV4,
    DirectiveV4,
)
from robust_adapt.ulc.v4_controller import UnifiedLearningControllerV4
from robust_adapt.ulc.v4_evidence import EvidenceSynthesizerV4, EvidenceVectorV4
from robust_adapt.ulc.v4_1_controller import ULCv41Config, UnifiedLearningControllerV4_1
from robust_adapt.ulc.v5_controller import (
    InterventionTier,
    ULCv5Config,
    ULCv5Directive,
    UnifiedLearningControllerV5,
    UtilityScorer,
)

__all__ = [
    # Baseline ULC interfaces (v1/v2/v3)
    "ControllerState",
    "ControllerDirective",
    "EvidenceVector",
    "EvidenceSynthesizer",
    "ArbitrationAutomaton",
    "AdaptiveLearningController",
    # Advanced ULC-v4 Architecture
    "AutomatonStateV4",
    "DirectiveV4",
    "EvidenceVectorV4",
    "EvidenceSynthesizerV4",
    "ConfidenceEngine",
    "ConfidenceScores",
    "ArbitrationWeights",
    "MultiObjectiveArbitrator",
    "ArbitrationAutomatonV4",
    "CrossPillarConflictResolver",
    "ULCExplainer",
    "UnifiedLearningControllerV4",
    # Promoted ULC-v4.1 Architecture
    "compute_spatial_discordance",
    "ULCv41Config",
    "UnifiedLearningControllerV4_1",
    # Promoted ULC-v5 Architecture
    "InterventionTier",
    "ULCv5Directive",
    "UtilityScorer",
    "ULCv5Config",
    "UnifiedLearningControllerV5",
]
