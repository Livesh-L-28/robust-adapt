"""Delayed-Label Streaming Learning and Queue Management.

Handles real-world asynchronous streaming environments where predictions are made at time t,
but ground truth feedback y arrives with a non-zero delay Delta t.
Matches delayed labels with cached prediction representations and computes empirical delay metrics.
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError


@dataclass
class UnlabelledSample:
    sample_id: str
    features: np.ndarray
    prediction: Optional[int]
    predict_time: float
    metadata: Dict[str, Any]


@dataclass
class PairedSample:
    sample_id: str
    features: np.ndarray
    label: int
    delay: float
    predict_time: float
    label_time: float
    sample_weight: float


class DelayedLabelQueue:
    """Bounded priority queue managing asynchronous delayed label matching.

    Parameters
    ----------
    max_queue_size : int, default=10000
        Maximum unlabelled instances held in memory waiting for labels.
    max_wait_time : Optional[float], default=None
        Maximum allowable elapsed time (seconds or stream steps) before unlabelled sample is pruned.
    """

    def __init__(
        self,
        max_queue_size: int = 10000,
        max_wait_time: Optional[float] = None,
        *,
        max_delay: Optional[float] = None,
    ) -> None:
        if max_delay is not None and max_wait_time is not None:
            if max_delay != max_wait_time:
                raise ValidationError(
                    f"Conflicting parameters: max_wait_time={max_wait_time} and max_delay={max_delay}"
                )
        effective_wait = max_delay if max_delay is not None else max_wait_time

        if max_queue_size < 10:
            raise ConfigurationError(f"max_queue_size must be >= 10, got {max_queue_size}")

        self.max_queue_size = int(max_queue_size)
        self.max_wait_time = float(effective_wait) if effective_wait is not None else None

        # Queue of waiting samples indexed by unique sample_id
        self._waiting_samples: OrderedDict[str, UnlabelledSample] = OrderedDict()
        # Matched samples ready for training
        self._ready_samples: List[PairedSample] = []

        # Latency statistics
        self._delays_history: List[float] = []
        self._total_enqueued: int = 0
        self._total_matched: int = 0
        self._total_timed_out: int = 0

    @property
    def pending_count(self) -> int:
        """Number of samples currently waiting for labels."""
        return len(self._waiting_samples)

    @property
    def ready_count(self) -> int:
        """Number of paired samples ready for training."""
        return len(self._ready_samples)

    @property
    def mean_observed_delay(self) -> float:
        """Average observed delay Delta t for paired samples."""
        if not self._delays_history:
            return 0.0
        return float(np.mean(self._delays_history[-500:]))

    @property
    def max_delay(self) -> Optional[float]:
        """Alias for max_wait_time."""
        return self.max_wait_time

    def enqueue(
        self,
        sample_id: str,
        X: np.ndarray,
        prediction: Optional[int] = None,
        timestamp: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enqueue an unlabelled inference sample waiting for its delayed ground truth label."""
        if sample_id in self._waiting_samples:
            return

        # Prune oldest if max capacity reached
        if len(self._waiting_samples) >= self.max_queue_size:
            oldest_id, _ = self._waiting_samples.popitem(last=False)
            self._total_timed_out += 1

        sample = UnlabelledSample(
            sample_id=str(sample_id),
            features=np.asarray(X, dtype=np.float64),
            prediction=prediction,
            predict_time=float(timestamp),
            metadata=dict(metadata or {}),
        )
        self._waiting_samples[sample.sample_id] = sample
        self._total_enqueued += 1

    def provide_label(
        self,
        sample_id: str,
        label: int,
        arrival_timestamp: float = 0.0,
        sample_weight: float = 1.0,
    ) -> bool:
        """Provide ground truth feedback for a previously enqueued sample.

        Returns
        -------
        bool
            True if sample was found and matched; False if sample timed out or not found.
        """
        s_id = str(sample_id)
        if s_id not in self._waiting_samples:
            return False

        unlabelled = self._waiting_samples.pop(s_id)
        label_time = float(arrival_timestamp)
        delay = max(0.0, label_time - unlabelled.predict_time)

        paired = PairedSample(
            sample_id=s_id,
            features=unlabelled.features,
            label=int(label),
            delay=delay,
            predict_time=unlabelled.predict_time,
            label_time=label_time,
            sample_weight=float(sample_weight),
        )

        self._ready_samples.append(paired)
        self._delays_history.append(delay)
        self._total_matched += 1
        return True

    def extract_ready_batch(
        self,
        max_batch_size: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Extract a batch of matched instances ready for model incremental updates.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            (X_batch, y_batch, sample_weights, observed_delays)
        """
        if not self._ready_samples:
            return (
                np.empty((0, 0), dtype=np.float64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.float64),
                np.empty(0, dtype=np.float64),
            )

        k = len(self._ready_samples) if max_batch_size is None else min(len(self._ready_samples), int(max_batch_size))
        batch = self._ready_samples[:k]
        self._ready_samples = self._ready_samples[k:]

        X = np.stack([p.features for p in batch], axis=0)
        y = np.array([p.label for p in batch], dtype=np.int64)
        w = np.array([p.sample_weight for p in batch], dtype=np.float64)
        delays = np.array([p.delay for p in batch], dtype=np.float64)

        return X, y, w, delays

    def prune_timeouts(self, current_time: float) -> int:
        """Prune unlabelled samples whose wait time exceeds max_wait_time."""
        if self.max_wait_time is None:
            return 0

        now = float(current_time)
        expired_ids = [
            s_id for s_id, s in self._waiting_samples.items()
            if (now - s.predict_time) > self.max_wait_time
        ]

        for s_id in expired_ids:
            self._waiting_samples.pop(s_id, None)
            self._total_timed_out += 1

        return len(expired_ids)
