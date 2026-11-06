"""ROBUST-ADAPT: Robust and Adaptive Learning with Resource-Efficient Optimization.

Adaptive. Robust. Resource-Efficient.

An open-source Python machine-learning algorithm library designed to improve learning
under changing data distributions, unreliable training data and computational constraints.
It complements existing machine-learning frameworks rather than replacing them.

Four Independent Pillars:
- ALA: Adaptive Learning Algorithms (concept drift detection, streaming decision trees, balanced replay)
- RLA: Robust Learning Algorithms (sample reliability scoring, robust loss portfolio, label correction)
- RAO: Resource-Aware Optimization (8-bit block-quantized AdamW, multi-dimensional budget management)
- ULC: Unified Learning Controller (cross-pillar Pareto arbitration, ULC-v4.1/v5 hybrid controller)

Additional Capability:
- Minority: Adaptive Minority Intelligence (online prior tracking, cost-sensitive threshold adjustment)
"""

from __future__ import annotations

# Package version
__version__ = "0.1.0.dev0"

# Core Exceptions & Configurations
from robust_adapt.core.exceptions import (
    AdaptiveMLError,
    ConfigurationError,
    DriftStateError,
    NumericalInstabilityError,
    QuantizationError,
    ResourceBudgetExceededError,
    RobustAdaptError,
    SerializationError,
    ValidationError,
)

# 1. Adaptive Learning Algorithms (ALA)
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
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.ala.tree import VectorizedHoeffdingTree

# Canonical ergonomic aliases
ADWIN = ReliabilityWeightedADWIN
HoeffdingTree = VectorizedHoeffdingTree

# 2. Robust Learning Algorithms (RLA)
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

# 3. Resource-Aware Optimization (RAO)
from robust_adapt.rao.accumulator import AdaptiveGradientAccumulator
from robust_adapt.rao.budget import BudgetState, DynamicResourceBudgetManager
from robust_adapt.rao.device import DeviceCapabilityDetector, DeviceProfile
from robust_adapt.rao.profiler import ExecutionProfiler
from robust_adapt.rao.quantizer import BlockQuantizer
from robust_adapt.rao.recovery import ResilientCheckpointManager

# 4. Adaptive Minority Intelligence
from robust_adapt.minority.calibration import ClassAwareCalibrator
from robust_adapt.minority.learner import MinorityIntelligence20Learner
from robust_adapt.minority.prior import (
    BetaBinomialPriorTracker,
    OnlineClassPriorTracker,
)
from robust_adapt.minority.replay import MinorityAwareReplayBuffer
from robust_adapt.minority.threshold import (
    AdaptiveThresholdManager,
    DynamicFPBudgetThresholdManager,
    compute_sublinear_cost_weights,
)

# 5. Unified Learning Controller (ULC)
from robust_adapt.ulc.arbitrator import MultiObjectiveArbitrator
from robust_adapt.ulc.confidence import ConfidenceEngine, ConfidenceScores
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.controller import AdaptiveLearningController
from robust_adapt.ulc.directives import ControllerDirective, ControllerState
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

# 6. State Management & Checkpointing
from robust_adapt.state.checkpoint import CheckpointManager
from robust_adapt.state.serializer import is_safetensors_available, load_state, save_state

__all__ = [
    # Metadata
    "__version__",
    # Core Exceptions
    "RobustAdaptError",
    "AdaptiveMLError",
    "ConfigurationError",
    "ValidationError",
    "DriftStateError",
    "QuantizationError",
    "ResourceBudgetExceededError",
    "NumericalInstabilityError",
    "SerializationError",
    # ALA
    "AdaptiveClassifier",
    "ALA30AdaptiveLearner",
    "HoeffdingTree",
    "VectorizedHoeffdingTree",
    "ADWIN",
    "ReliabilityWeightedADWIN",
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
    "DelayedLabelQueue",
    "ClassBalancedReservoirReplay",
    # RLA
    "RobustLearningPipeline",
    "RLA30RobustLearner",
    "MultiSignalReliabilityEngine",
    "DensityAwareMarginScorer",
    "AsymmetricTransitionDetector",
    "ClassConditionalReliabilityEstimator",
    "SymmetricCrossEntropyLoss",
    "GeneralizedCrossEntropyLoss",
    "FocalLoss",
    "ReliabilityWeightedLoss",
    "ClassBalancedWeights",
    "NoiseTaxonomyClassifier",
    "NoiseType",
    "PatternType",
    "EvidenceBasedLabelCorrector",
    "CorrectionAuditRecord",
    # RAO
    "LowMemoryAdamW",
    "VectorizedLowMemoryAdamW",
    "BlockQuantizer",
    "AdaptiveGradientAccumulator",
    "DynamicResourceBudgetManager",
    "BudgetState",
    "ExecutionProfiler",
    "DeviceCapabilityDetector",
    "DeviceProfile",
    "ResilientCheckpointManager",
    # Minority Intelligence
    "OnlineClassPriorTracker",
    "BetaBinomialPriorTracker",
    "AdaptiveThresholdManager",
    "DynamicFPBudgetThresholdManager",
    "compute_sublinear_cost_weights",
    "MinorityIntelligence20Learner",
    "MinorityAwareReplayBuffer",
    "ClassAwareCalibrator",
    # ULC
    "AdaptiveLearningController",
    "ControllerState",
    "ControllerDirective",
    "UnifiedLearningControllerV4",
    "AutomatonStateV4",
    "DirectiveV4",
    "EvidenceVectorV4",
    "EvidenceSynthesizerV4",
    "ConfidenceEngine",
    "ConfidenceScores",
    "MultiObjectiveArbitrator",
    "ArbitrationAutomatonV4",
    "CrossPillarConflictResolver",
    "UnifiedLearningControllerV4_1",
    "ULCv41Config",
    "compute_spatial_discordance",
    "UnifiedLearningControllerV5",
    "ULCv5Config",
    "InterventionTier",
    "ULCv5Directive",
    "UtilityScorer",
    # State Management
    "save_state",
    "load_state",
    "CheckpointManager",
    "is_safetensors_available",
]


def __getattr__(name: str):
    if name == "LowMemoryAdamW":
        from robust_adapt.rao.adamw import LowMemoryAdamW
        return LowMemoryAdamW
    if name == "VectorizedLowMemoryAdamW":
        try:
            from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW
            return VectorizedLowMemoryAdamW
        except Exception as e:
            raise AttributeError(f"VectorizedLowMemoryAdamW requires PyTorch optional integration: {e}") from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
