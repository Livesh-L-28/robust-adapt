"""Frozen configuration dataclasses for AdaptiveML components."""

from dataclasses import dataclass
from typing import Optional, Tuple
from robust_adapt.core.constants import (
    DEFAULT_BLOCK_SIZE,
    DEFAULT_TAU_R,
    DEFAULT_RECOVERY_STEPS,
)


@dataclass(frozen=True)
class TreeConfig:
    """Configuration for VectorizedHoeffdingTree."""

    n_features: int
    n_classes: int
    grace_period: int = 200
    delta: float = 1e-5
    tau_tie: float = 0.05
    n_bins: int = 32
    min_leaf_samples: int = 10
    max_depth: int = 20


@dataclass(frozen=True)
class ADWINConfig:
    """Configuration for ReliabilityWeightedADWIN."""

    delta: float = 0.002
    min_subwindow_weight: float = 5.0
    eps_r: float = 1e-4


@dataclass(frozen=True)
class ReplayConfig:
    """Configuration for ClassBalancedReservoirReplay."""

    capacity: int = 5000
    replay_ratio: float = 0.2


@dataclass(frozen=True)
class ScorerConfig:
    """Configuration for DensityAwareMarginScorer."""

    n_classes: int
    n_neighbors: int = 5
    alpha: float = 1.0
    gamma: float = 0.5
    min_reliability: float = 1e-4


@dataclass(frozen=True)
class AdamWConfig:
    """Configuration for LowMemoryAdamW."""

    lr: float = 1e-3
    betas: Tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 1e-2
    block_size: int = DEFAULT_BLOCK_SIZE


@dataclass(frozen=True)
class ULCConfig:
    """Configuration for AdaptiveLearningController."""

    tau_R: float = DEFAULT_TAU_R
    recovery_steps: int = DEFAULT_RECOVERY_STEPS
    hysteresis_band: float = 0.15
