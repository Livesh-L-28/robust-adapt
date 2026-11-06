"""Multi-Detector Drift Protocol and Ensemble Consensus Engine.

Provides standard CUSUM, Page-Hinkley, Statistical Distribution monitoring,
and Multi-Detector Consensus alongside ReliabilityWeightedADWIN.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.core.exceptions import ConfigurationError, ValidationError


class BaseDriftDetector:
    """Abstract base protocol for streaming drift detectors."""

    def update(self, value: float, reliability: float = 1.0) -> bool:
        """Process incoming scalar observation and return True if drift detected."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset internal accumulator statistics."""
        raise NotImplementedError

    def state_dict(self) -> Dict[str, Any]:
        """Serialize detector state."""
        raise NotImplementedError

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore detector state."""
        raise NotImplementedError


class CUSUMDetector(BaseDriftDetector):
    """Cumulative Sum (CUSUM) change detection algorithm.

    Tracks accumulated positive deviations from baseline mean:
        S_t = \\max(0, S_{t-1} + w_t \\cdot (x_t - \\mu_0 - \\delta))
    Triggers when S_t > \\lambda.

    Parameters
    ----------
    target_mean : float, default=0.0
        Expected baseline mean mu_0 under stationary conditions.
    delta : float, default=0.005
        Allowable slack/tolerance parameter.
    threshold : float, default=5.0
        Decision threshold lambda for signaling change.
    """

    def __init__(
        self,
        target_mean: float = 0.0,
        delta: float = 0.005,
        threshold: float = 5.0,
    ) -> None:
        if threshold <= 0.0:
            raise ConfigurationError(f"threshold must be positive, got {threshold}")
        self.target_mean = float(target_mean)
        self.delta = float(delta)
        self.threshold = float(threshold)

        self.sum_pos: float = 0.0
        self.samples_seen: int = 0

    def update(self, value: float, reliability: float = 1.0) -> bool:
        """Update CUSUM with incoming observation weighted by sample reliability."""
        w = max(0.0, min(1.0, float(reliability)))
        val = float(value)
        self.samples_seen += 1

        # Reliability suppresses noise fluctuations
        deviation = w * (val - self.target_mean - self.delta)
        self.sum_pos = max(0.0, self.sum_pos + deviation)

        if self.sum_pos > self.threshold:
            self.reset()
            return True
        return False

    def reset(self) -> None:
        """Reset cumulative sum to zero."""
        self.sum_pos = 0.0

    def state_dict(self) -> Dict[str, Any]:
        return {
            "target_mean": self.target_mean,
            "delta": self.delta,
            "threshold": self.threshold,
            "sum_pos": self.sum_pos,
            "samples_seen": self.samples_seen,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        self.target_mean = float(state["target_mean"])
        self.delta = float(state["delta"])
        self.threshold = float(state["threshold"])
        self.sum_pos = float(state["sum_pos"])
        self.samples_seen = int(state["samples_seen"])


class PageHinkleyDetector(BaseDriftDetector):
    """Page-Hinkley test for streaming change detection.

    Monitors cumulative deviation from empirical mean:
        m_t = \\sum_{i=1}^t w_i \\cdot (x_i - \\bar{x}_t - \\delta)
        M_t = \\min_{1 \\le i \\le t} m_i
        PH_t = m_t - M_t
    Triggers when PH_t > \\lambda.

    Parameters
    ----------
    delta : float, default=0.01
        Magnitude of change tolerance.
    threshold : float, default=10.0
        Cumulative threshold lambda signaling drift.
    alpha : float, default=0.99
        Exponential decay for running mean.
    """

    def __init__(
        self,
        delta: float = 0.01,
        threshold: float = 10.0,
        alpha: float = 0.99,
    ) -> None:
        if threshold <= 0.0:
            raise ConfigurationError(f"threshold must be positive, got {threshold}")
        if not 0.0 < alpha <= 1.0:
            raise ConfigurationError(f"alpha must be in (0, 1], got {alpha}")

        self.delta = float(delta)
        self.threshold = float(threshold)
        self.alpha = float(alpha)

        self.running_mean: float = 0.0
        self.cum_sum: float = 0.0
        self.min_cum_sum: float = 0.0
        self.samples_seen: int = 0

    def update(self, value: float, reliability: float = 1.0) -> bool:
        """Update Page-Hinkley statistics."""
        w = max(0.0, min(1.0, float(reliability)))
        val = float(value)
        self.samples_seen += 1

        if self.samples_seen == 1:
            self.running_mean = val
        else:
            self.running_mean = self.alpha * self.running_mean + (1.0 - self.alpha) * val

        diff = w * (val - self.running_mean - self.delta)
        self.cum_sum += diff
        if self.cum_sum < self.min_cum_sum:
            self.min_cum_sum = self.cum_sum

        ph_val = self.cum_sum - self.min_cum_sum
        if ph_val > self.threshold:
            self.reset()
            return True
        return False

    def reset(self) -> None:
        """Reset running statistics."""
        self.cum_sum = 0.0
        self.min_cum_sum = 0.0

    def state_dict(self) -> Dict[str, Any]:
        return {
            "delta": self.delta,
            "threshold": self.threshold,
            "alpha": self.alpha,
            "running_mean": self.running_mean,
            "cum_sum": self.cum_sum,
            "min_cum_sum": self.min_cum_sum,
            "samples_seen": self.samples_seen,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        self.delta = float(state["delta"])
        self.threshold = float(state["threshold"])
        self.alpha = float(state["alpha"])
        self.running_mean = float(state["running_mean"])
        self.cum_sum = float(state["cum_sum"])
        self.min_cum_sum = float(state["min_cum_sum"])
        self.samples_seen = int(state["samples_seen"])


class MultiDetectorConsensus:
    """Consensus engine arbitrating drift detection across a portfolio of diverse detectors.

    Parameters
    ----------
    detectors : Optional[Dict[str, Any]], default=None
        Dictionary mapping detector name to detector instance. If None, instantiates
        a default ensemble of ADWIN, CUSUM, and Page-Hinkley.
    voting_strategy : str, default="majority"
        Voting rule: "any" (triggers if any detector fires), "majority" (>= 50% fire),
        or "weighted" (weights detectors by assigned confidence).
    weights : Optional[Dict[str, float]], default=None
        Custom detector weights for "weighted" voting strategy.
    """

    def __init__(
        self,
        detectors: Optional[Dict[str, Any]] = None,
        voting_strategy: str = "majority",
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        valid_strategies = {"any", "majority", "weighted"}
        if voting_strategy not in valid_strategies:
            raise ConfigurationError(f"voting_strategy must be one of {valid_strategies}, got '{voting_strategy}'")

        if detectors is None:
            self.detectors: Dict[str, Any] = {
                "adwin": ReliabilityWeightedADWIN(delta=0.002),
                "cusum": CUSUMDetector(target_mean=0.1, threshold=4.0),
                "page_hinkley": PageHinkleyDetector(threshold=8.0),
            }
        else:
            self.detectors = dict(detectors)

        self.voting_strategy = voting_strategy

        if weights is not None:
            self.weights = {k: float(v) for k, v in weights.items()}
        else:
            # Equal weighting by default
            self.weights = {k: 1.0 for k in self.detectors}

        self.last_votes_: Dict[str, bool] = {}
        self.consensus_confidence_: float = 0.0

    def update(self, value: float, reliability: float = 1.0) -> Tuple[bool, float, Dict[str, bool]]:
        """Update all member detectors with incoming scalar observation.

        Returns
        -------
        drift_detected : bool
            Whether ensemble consensus signals concept drift.
        confidence : float
            Fraction of detectors (or weighted confidence) voting for drift in [0, 1].
        individual_votes : Dict[str, bool]
            Per-detector vote breakdown.
        """
        votes: Dict[str, bool] = {}
        total_weight = 0.0
        drift_weight = 0.0

        for name, det in self.detectors.items():
            fired = det.update(value, reliability=reliability)
            votes[name] = bool(fired)
            w = self.weights.get(name, 1.0)
            total_weight += w
            if fired:
                drift_weight += w

        self.last_votes_ = votes
        confidence = drift_weight / max(total_weight, 1e-6)
        self.consensus_confidence_ = float(confidence)

        if self.voting_strategy == "any":
            decision = any(votes.values())
        elif self.voting_strategy == "majority":
            n_fired = sum(1 for v in votes.values() if v)
            decision = n_fired >= (len(self.detectors) / 2.0)
        elif self.voting_strategy == "weighted":
            decision = confidence >= 0.50
        else:
            decision = False

        return decision, float(confidence), votes

    def reset(self) -> None:
        """Reset all member detectors."""
        for det in self.detectors.values():
            if hasattr(det, "reset"):
                det.reset()
        self.last_votes_.clear()
        self.consensus_confidence_ = 0.0

    def state_dict(self) -> Dict[str, Any]:
        return {
            "voting_strategy": self.voting_strategy,
            "weights": self.weights,
            "detector_states": {
                name: det.state_dict() for name, det in self.detectors.items() if hasattr(det, "state_dict")
            },
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        self.voting_strategy = state["voting_strategy"]
        self.weights = state["weights"]
        det_states = state.get("detector_states", {})
        for name, d_state in det_states.items():
            if name in self.detectors and hasattr(self.detectors[name], "load_state_dict"):
                self.detectors[name].load_state_dict(d_state)
