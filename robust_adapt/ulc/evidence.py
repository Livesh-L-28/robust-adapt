"""
AdaptiveML Unified Learning Controller (ULC) Evidence Synthesis.

Formalizes the 4-dimensional evidence vector synthesized from
ALA drift metrics, RLA sample reliability, model predictive entropy,
and short-term loss trends.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from robust_adapt.core.constants import EPS_DIV


@dataclass(frozen=True)
class EvidenceVector:
    """Four-dimensional normalized evidence vector e_tau in [0, 1]^4."""

    delta_drift: float
    mean_reliability: float
    predictive_entropy: float
    loss_trend: float

    def to_array(self) -> np.ndarray:
        """Convert evidence vector to 1D NumPy array."""
        return np.array(
            [self.delta_drift, self.mean_reliability, self.predictive_entropy, self.loss_trend],
            dtype=np.float64,
        )


class EvidenceSynthesizer:
    """Synthesizes incoming cross-pillar telemetry into normalized evidence vectors."""

    def __init__(self, ema_alpha: float = 0.2, slope_gain: float = 2.0) -> None:
        self.ema_alpha = ema_alpha
        self.slope_gain = slope_gain
        self._loss_ema: Optional[float] = None

    def compute_predictive_entropy(self, probabilities: np.ndarray) -> float:
        """Compute normalized predictive entropy H_pred in [0, 1] for a batch.

        Args:
            probabilities: Array of predicted probabilities of shape (B, C).

        Returns:
            Normalized entropy in [0, 1].
        """
        if probabilities.ndim != 2:
            return 0.0

        n_samples, n_classes = probabilities.shape
        if n_samples == 0 or n_classes <= 1:
            return 0.0

        probs = np.clip(probabilities, EPS_DIV, 1.0)
        entropy_per_sample = -np.sum(probs * np.log(probs), axis=1)
        max_entropy = math.log(n_classes)

        norm_entropy = float(np.mean(entropy_per_sample) / (max_entropy + EPS_DIV))
        return float(np.clip(norm_entropy, 0.0, 1.0))

    def update_loss_trend(self, current_loss: Optional[float]) -> float:
        """Compute directional loss trend T_loss in [0, 1] via moving average.

        Args:
            current_loss: Latest evaluation loss or None.

        Returns:
            Sigmoid-scaled loss trend in [0, 1]. Neutral is 0.5.
        """
        if current_loss is None or math.isnan(current_loss):
            return 0.5

        if self._loss_ema is None:
            self._loss_ema = float(current_loss)
            return 0.5

        delta_loss = float(current_loss) - self._loss_ema
        self._loss_ema = (1.0 - self.ema_alpha) * self._loss_ema + self.ema_alpha * float(current_loss)

        # Sigmoid mapping
        trend = 1.0 / (1.0 + math.exp(-self.slope_gain * delta_loss))
        return float(np.clip(trend, 0.0, 1.0))

    def synthesize(
        self,
        delta_drift: float,
        mean_reliability: float,
        probabilities: Optional[np.ndarray] = None,
        current_loss: Optional[float] = None,
    ) -> EvidenceVector:
        """Synthesize telemetry into a bounded EvidenceVector."""
        bounded_drift = float(np.clip(delta_drift, 0.0, 2.0))
        # Normalized drift: >= 1.0 indicates threshold crossing
        bounded_rel = float(np.clip(mean_reliability, 0.0, 1.0))

        if probabilities is not None:
            pred_entropy = self.compute_predictive_entropy(probabilities)
        else:
            pred_entropy = 0.0

        loss_trend = self.update_loss_trend(current_loss)

        return EvidenceVector(
            delta_drift=bounded_drift,
            mean_reliability=bounded_rel,
            predictive_entropy=pred_entropy,
            loss_trend=loss_trend,
        )
