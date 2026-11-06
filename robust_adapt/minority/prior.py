"""Online Class-Prior Tracking and Emerging Class Detection.

Mathematical formulation for streaming non-stationary class distributions:
    \\hat{\\pi}_c^{(t)} = (1 - \\alpha) \\hat{\\pi}_c^{(t-1)} + \\alpha \\frac{n_c^{(t)} + \\epsilon}{N^{(t)} + K \\epsilon}

Provides real-time imbalance ratio tracking, sliding-window estimation, Laplace smoothing,
and automated detection of emerging or dormant concept classes.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Sequence
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_labels_1d


class OnlineClassPriorTracker:
    """Tracks class distribution shifts in non-stationary streaming environments.

    Maintains both an exponential moving average prior and a sliding window history,
    with Laplace smoothing and automated emerging class detection.

    Parameters
    ----------
    n_classes : int, default=2
        Initial number of distinct target classes.
    alpha : float, default=0.05
        Exponential moving average update rate in (0, 1].
    window_size : int, default=500
        Size of sliding window history for local empirical statistics.
    smoothing : float, default=1.0
        Additive Laplace smoothing parameter (epsilon) to avoid zero-prior probabilities.
    imbalance_threshold : float, default=0.20
        Prior fraction below which a class is designated as a minority class.
    """

    def __init__(
        self,
        n_classes: int = 2,
        alpha: float = 0.05,
        window_size: int = 500,
        smoothing: float = 1.0,
        imbalance_threshold: float = 0.20,
    ) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if not 0.0 < alpha <= 1.0:
            raise ConfigurationError(f"alpha must be in (0, 1], got {alpha}")
        if window_size < 10:
            raise ConfigurationError(f"window_size must be >= 10, got {window_size}")
        if smoothing < 0.0:
            raise ConfigurationError(f"smoothing must be >= 0.0, got {smoothing}")

        self.n_classes = int(n_classes)
        self.alpha = float(alpha)
        self.window_size = int(window_size)
        self.smoothing = float(smoothing)
        self.imbalance_threshold = float(imbalance_threshold)

        # Priors vector initialized to uniform distribution
        self._priors: np.ndarray = np.full(self.n_classes, 1.0 / self.n_classes, dtype=np.float64)

        # Sliding window buffer of recent labels
        self._window: deque = deque(maxlen=self.window_size)
        self._total_samples_seen: int = 0
        self._class_seen_totals: np.ndarray = np.zeros(self.n_classes, dtype=np.int64)

        # Emerging classes set
        self._emerging_classes: set = set()

    @property
    def priors(self) -> np.ndarray:
        """Current estimated prior probability vector of shape (n_classes,)."""
        return self._priors.copy()

    @property
    def total_samples_seen(self) -> int:
        """Total cumulative stream samples processed."""
        return self._total_samples_seen

    @property
    def imbalance_ratio(self) -> float:
        """Ratio of maximum to minimum class prior: max(pi) / max(min(pi), 1e-6)."""
        min_p = float(np.min(self._priors))
        max_p = float(np.max(self._priors))
        return max_p / max(min_p, 1e-6)

    @property
    def minority_classes(self) -> List[int]:
        """Class indices whose estimated prior is at or below the imbalance threshold."""
        # Either below threshold or below 1 / (2 * n_classes)
        cutoff = min(self.imbalance_threshold, 1.0 / (2.0 * self.n_classes))
        return [int(c) for c in range(self.n_classes) if self._priors[c] <= cutoff]

    @property
    def majority_class(self) -> int:
        """Class index with the highest estimated prior."""
        return int(np.argmax(self._priors))

    def is_emerging(self, class_id: int) -> bool:
        """Check if a specific class recently emerged into the stream."""
        return class_id in self._emerging_classes

    def register_class(self, new_class_id: int) -> None:
        """Dynamically expand the tracker to accommodate a newly discovered class."""
        if new_class_id < self.n_classes:
            return

        target_size = new_class_id + 1
        diff = target_size - self.n_classes

        # Extend arrays
        init_prob = 1.0 / (target_size * 2.0)
        new_priors = np.pad(self._priors * (1.0 - init_prob * diff), (0, diff), constant_values=init_prob)
        new_totals = np.pad(self._class_seen_totals, (0, diff), constant_values=0)

        self._priors = new_priors / np.sum(new_priors)
        self._class_seen_totals = new_totals
        self.n_classes = target_size
        self._emerging_classes.add(new_class_id)

    def update(self, y: np.ndarray) -> np.ndarray:
        """Incrementally update class priors with an incoming label batch.

        Parameters
        ----------
        y : np.ndarray
            1D array of class integer labels.

        Returns
        -------
        np.ndarray
            Updated prior probability vector of shape (n_classes,).
        """
        y_arr = check_labels_1d(y, name="y")
        n_samples = y_arr.shape[0]
        if n_samples == 0:
            return self.priors

        # Check for unseen class labels
        max_incoming_label = int(np.max(y_arr))
        if max_incoming_label >= self.n_classes:
            self.register_class(max_incoming_label)

        # Batch counts
        batch_counts = np.bincount(y_arr, minlength=self.n_classes)
        self._class_seen_totals += batch_counts
        self._total_samples_seen += n_samples

        # Check for emerging classes (newly registered or seen < 50 times in a mature stream)
        for c in range(self.n_classes):
            if batch_counts[c] > 0:
                if self._total_samples_seen > 100 and (self._class_seen_totals[c] < 50 or self._priors[c] < 0.01):
                    self._emerging_classes.add(c)
                elif self._class_seen_totals[c] >= 50 and self._priors[c] > 0.05:
                    self._emerging_classes.discard(c)

        # Update sliding window
        for label in y_arr:
            self._window.append(int(label))

        # 1. Smoothed batch empirical prior
        batch_smoothed = (batch_counts + self.smoothing) / (n_samples + self.n_classes * self.smoothing)

        # 2. Exponential moving average update
        self._priors = (1.0 - self.alpha) * self._priors + self.alpha * batch_smoothed
        self._priors = np.clip(self._priors, 1e-8, 1.0)
        self._priors /= np.sum(self._priors)

        return self.priors

    def get_window_priors(self) -> np.ndarray:
        """Compute empirical class priors strictly from the current sliding window."""
        if len(self._window) == 0:
            return self.priors

        win_labels = np.array(self._window, dtype=np.int64)
        win_counts = np.bincount(win_labels, minlength=self.n_classes)
        smoothed = (win_counts + self.smoothing) / (len(self._window) + self.n_classes * self.smoothing)
        return smoothed / np.sum(smoothed)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize complete prior tracker state."""
        return {
            "n_classes": self.n_classes,
            "alpha": self.alpha,
            "window_size": self.window_size,
            "smoothing": self.smoothing,
            "imbalance_threshold": self.imbalance_threshold,
            "priors": self._priors.tolist(),
            "window": list(self._window),
            "total_samples_seen": self._total_samples_seen,
            "class_seen_totals": self._class_seen_totals.tolist(),
            "emerging_classes": list(self._emerging_classes),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore prior tracker state."""
        self.n_classes = int(state["n_classes"])
        self.alpha = float(state["alpha"])
        self.window_size = int(state["window_size"])
        self.smoothing = float(state["smoothing"])
        self.imbalance_threshold = float(state["imbalance_threshold"])
        self._priors = np.array(state["priors"], dtype=np.float64)
        self._window = deque(state["window"], maxlen=self.window_size)
        self._total_samples_seen = int(state["total_samples_seen"])
        self._class_seen_totals = np.array(state["class_seen_totals"], dtype=np.int64)
        self._emerging_classes = set(state.get("emerging_classes", []))


class BetaBinomialPriorTracker:
    """Online Bayesian conjugate prior tracker with exponential decay for non-stationary streams.

    Maintains a conjugate Beta distribution Beta(alpha, beta) over the minority class prior,
    applying exponential forgetting to track non-stationary class prevalence without memory leaks.

    Parameters
    ----------
    alpha_prior : float, default=1.0
        Prior pseudo-count for minority class.
    beta_prior : float, default=100.0
        Prior pseudo-count for majority class.
    decay : float, default=0.995
        Exponential forgetting factor in (0, 1].
    minority_class : int, default=1
        Class index treated as minority.
    """

    def __init__(
        self,
        alpha_prior: float = 1.0,
        beta_prior: float = 100.0,
        decay: float = 0.995,
        minority_class: int = 1,
    ) -> None:
        if alpha_prior <= 0.0:
            raise ConfigurationError(f"alpha_prior must be positive, got {alpha_prior}")
        if beta_prior <= 0.0:
            raise ConfigurationError(f"beta_prior must be positive, got {beta_prior}")
        if not 0.0 < decay <= 1.0:
            raise ConfigurationError(f"decay must be in (0, 1], got {decay}")

        self.alpha_prior = float(alpha_prior)
        self.beta_prior = float(beta_prior)
        self.decay = float(decay)
        self.minority_class = int(minority_class)

        self.alpha = float(alpha_prior)
        self.beta = float(beta_prior)

    def update(self, y_batch: np.ndarray) -> float:
        """Incorporate a new batch of labels into the Beta posterior."""
        y_arr = np.asarray(y_batch, dtype=np.int64).ravel()
        n_pos = float(np.sum(y_arr == self.minority_class))
        n_neg = float(len(y_arr) - n_pos)

        self.alpha = self.decay * self.alpha + n_pos
        self.beta = self.decay * self.beta + n_neg
        return self.current_prior

    @property
    def current_prior(self) -> float:
        """Instantaneous expected minority class prior P(y=minority)."""
        return float((self.alpha + 1e-6) / (self.alpha + self.beta + 2e-6))

    @property
    def imbalance_ratio(self) -> float:
        """Instantaneous imbalance ratio (majority / minority)."""
        prior = self.current_prior
        return float((1.0 - prior) / max(prior, 1e-6))

    def state_dict(self) -> Dict[str, Any]:
        """Serialize Bayesian prior tracker state."""
        return {
            "alpha_prior": self.alpha_prior,
            "beta_prior": self.beta_prior,
            "decay": self.decay,
            "minority_class": self.minority_class,
            "alpha": self.alpha,
            "beta": self.beta,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore Bayesian prior tracker state."""
        self.alpha_prior = float(state["alpha_prior"])
        self.beta_prior = float(state["beta_prior"])
        self.decay = float(state["decay"])
        self.minority_class = int(state["minority_class"])
        self.alpha = float(state["alpha"])
        self.beta = float(state["beta"])
