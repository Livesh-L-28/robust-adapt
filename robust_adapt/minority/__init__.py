"""Adaptive Minority Intelligence Package.

Provides online class-prior tracking, adaptive decision thresholds,
reliability-aware minority experience replay, and streaming probability calibration.
"""

from robust_adapt.minority.calibration import ClassAwareCalibrator
from robust_adapt.minority.learner import MinorityIntelligence20Learner
from robust_adapt.minority.prior import BetaBinomialPriorTracker, OnlineClassPriorTracker
from robust_adapt.minority.replay import MinorityAwareReplayBuffer
from robust_adapt.minority.threshold import (
    AdaptiveThresholdManager,
    DynamicFPBudgetThresholdManager,
    compute_sublinear_cost_weights,
)

__all__ = [
    "OnlineClassPriorTracker",
    "BetaBinomialPriorTracker",
    "AdaptiveThresholdManager",
    "DynamicFPBudgetThresholdManager",
    "compute_sublinear_cost_weights",
    "MinorityIntelligence20Learner",
    "MinorityAwareReplayBuffer",
    "ClassAwareCalibrator",
]
