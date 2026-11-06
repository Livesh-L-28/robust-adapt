"""Unified Learning Controller V4: Comprehensive Cross-Pillar Evidence Model.

Synthesizes evidence across all four pillars:
- delta_drift: Multi-detector drift divergence score
- mean_reliability: Multi-signal sample and label reliability
- predictive_entropy: Normalized model uncertainty H(p) / log(K)
- loss_trend: Normalized loss moving average gradient
- resource_utilization: Peak of CPU latency and RAM budget usage
- imbalance_ratio: Current streaming class imbalance ratio
- observed_delay: Streaming label feedback latency Delta t
- recurring_similarity: Concept memory matching similarity score
- is_emerging_class: Flag indicating arrival of an unseen or transitioning class
- asymmetric_noise_rate: Estimated off-diagonal noise transition magnitude
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np

from robust_adapt.core.constants import EPS_DIV


@dataclass(frozen=True)
class EvidenceVectorV4:
    """10-dimensional cross-pillar evidence vector driving ULC-v4 arbitration."""
    delta_drift: float = 0.0
    mean_reliability: float = 1.0
    predictive_entropy: float = 0.0
    loss_trend: float = 0.5
    resource_utilization: float = 0.2
    imbalance_ratio: float = 1.0
    observed_delay: float = 0.0
    recurring_similarity: float = 0.0
    is_emerging_class: bool = False
    asymmetric_noise_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence vector to dictionary."""
        return {
            "delta_drift": round(self.delta_drift, 4),
            "mean_reliability": round(self.mean_reliability, 4),
            "predictive_entropy": round(self.predictive_entropy, 4),
            "loss_trend": round(self.loss_trend, 4),
            "resource_utilization": round(self.resource_utilization, 4),
            "imbalance_ratio": round(self.imbalance_ratio, 2),
            "observed_delay": round(self.observed_delay, 2),
            "recurring_similarity": round(self.recurring_similarity, 4),
            "is_emerging_class": self.is_emerging_class,
            "asymmetric_noise_rate": round(self.asymmetric_noise_rate, 4),
        }


class EvidenceSynthesizerV4:
    """Synthesizes raw pipeline signals into normalized EvidenceVectorV4."""

    def __init__(self, alpha_trend: float = 0.15) -> None:
        self.alpha_trend = float(alpha_trend)
        self._prev_loss: Optional[float] = None
        self._loss_ema: float = 0.0

    def synthesize(
        self,
        delta_drift: float = 0.0,
        reliabilities: Optional[np.ndarray] = None,
        probas: Optional[np.ndarray] = None,
        current_loss: Optional[float] = None,
        resource_utilization: float = 0.20,
        imbalance_ratio: float = 1.0,
        observed_delay: float = 0.0,
        recurring_similarity: float = 0.0,
        is_emerging_class: bool = False,
        asymmetric_noise_rate: float = 0.0,
    ) -> EvidenceVectorV4:
        """Construct normalized EvidenceVectorV4 from incoming signals."""
        # 1. Mean reliability
        if reliabilities is not None and len(reliabilities) > 0:
            mean_rel = float(np.clip(np.mean(reliabilities), 0.0, 1.0))
        else:
            mean_rel = 1.0

        # 2. Predictive entropy
        if probas is not None and len(probas) > 0:
            p = np.clip(probas, 1e-7, 1.0)
            n_classes = p.shape[1] if p.ndim == 2 else 2
            if p.ndim == 1:
                p = np.column_stack([1.0 - p, p])
            ent = -np.sum(p * np.log(p), axis=1)
            norm_ent = float(np.mean(ent) / max(np.log(n_classes), 1e-6))
            predictive_entropy = float(np.clip(norm_ent, 0.0, 1.0))
        else:
            predictive_entropy = 0.0

        # 3. Loss trend gradient
        if current_loss is not None:
            if self._prev_loss is None:
                self._prev_loss = current_loss
                loss_trend = 0.50
            else:
                loss_diff = current_loss - self._prev_loss
                # Map loss diff to [0, 1] sigmoid-like
                loss_trend = float(1.0 / (1.0 + np.exp(-loss_diff * 2.0)))
                self._prev_loss = current_loss
        else:
            loss_trend = 0.50

        return EvidenceVectorV4(
            delta_drift=float(delta_drift),
            mean_reliability=mean_rel,
            predictive_entropy=predictive_entropy,
            loss_trend=loss_trend,
            resource_utilization=float(np.clip(resource_utilization, 0.0, 1.0)),
            imbalance_ratio=float(max(1.0, imbalance_ratio)),
            observed_delay=float(max(0.0, observed_delay)),
            recurring_similarity=float(np.clip(recurring_similarity, 0.0, 1.0)),
            is_emerging_class=bool(is_emerging_class),
            asymmetric_noise_rate=float(np.clip(asymmetric_noise_rate, 0.0, 1.0)),
        )
