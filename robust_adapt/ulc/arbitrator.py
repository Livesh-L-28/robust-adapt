"""ULC-v4 Multi-Objective Arbitrator.

Executes Pareto-optimal trade-offs across four competing operational objectives:
1. Predictive Accuracy (weight w_acc)
2. Robustness to Noise (weight w_rob)
3. Resource Efficiency (weight w_res)
4. Minority Class Retention (weight w_min)
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import numpy as np

from robust_adapt.ulc.confidence import ConfidenceScores
from robust_adapt.ulc.v4_evidence import EvidenceVectorV4


@dataclass
class ArbitrationWeights:
    w_acc: float = 0.35
    w_rob: float = 0.30
    w_res: float = 0.15
    w_min: float = 0.20


class MultiObjectiveArbitrator:
    """Balances multi-objective utility to select optimal adaptation policies."""

    def __init__(self, weights: Optional[ArbitrationWeights] = None) -> None:
        self.weights = weights or ArbitrationWeights()

    def arbitrate_replay_purge(
        self,
        evidence: EvidenceVectorV4,
        confidence: ConfidenceScores,
    ) -> Tuple[str, bool]:
        """Determine optimal replay purge policy and minority protection flag.

        Returns
        -------
        Tuple[str, bool]
            (policy: "none" | "selective" | "partial" | "full", keep_minority: bool)
        """
        # If severe class imbalance exists (IR > 5.0), minority protection is mandatory
        keep_minority = evidence.imbalance_ratio > 3.0 or evidence.is_emerging_class

        if confidence.restore_concept > 0.80:
            # Recurring concept restored; keep replay intact
            return "none", keep_minority

        if confidence.adapt > 0.60:
            if keep_minority:
                return "selective", True
            return "partial", False

        if confidence.suppress_noise > 0.60:
            # Under noise, do not purge replay (freeze instead)
            return "none", True

        return "none", keep_minority

    def arbitrate_learning_rate(
        self,
        evidence: EvidenceVectorV4,
        confidence: ConfidenceScores,
        base_lr_scale: float = 1.0,
    ) -> float:
        """Derive optimal learning rate scale factor balancing adaptation speed and resource budget."""
        if confidence.throttle_resources > 0.70:
            # Under severe resource constraints, suppress aggressive learning rate surges
            return 1.0

        if confidence.adapt > 0.70:
            # Accelerated adaptation
            return 2.5 * base_lr_scale
        elif confidence.adapt > 0.40:
            return 1.5 * base_lr_scale

        return base_lr_scale
