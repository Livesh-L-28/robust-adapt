"""Multi-Signal Sample and Label Reliability Engine.

Combines three orthogonal signals to estimate true sample reliability r_i in [0, 1]:
1. Prediction Margin & Entropy: s_margin = p_top1 - p_top2, s_entropy = 1 - H(p)/log(K)
2. Neighborhood Consistency: fraction of k-NN neighbors agreeing with reported label y_i
3. Temporal Consistency: agreement across consecutive temporal predictions
"""

from collections import deque
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.constants import EPS_DIV
from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d


class MultiSignalReliabilityEngine:
    """Computes composite sample reliability scores combining prediction, spatial, and temporal signals.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    k_neighbors : int, default=5
        Number of spatial nearest neighbors to query for neighborhood agreement.
    buffer_size : int, default=500
        Maximum recent instances retained in spatial search index.
    weight_margin : float, default=0.40
        Weight assigned to prediction margin/entropy signal.
    weight_neighbor : float, default=0.40
        Weight assigned to spatial k-NN neighborhood agreement.
    weight_temporal : float, default=0.20
        Weight assigned to temporal consistency across consecutive predictions.
    """

    def __init__(
        self,
        n_classes: int = 2,
        k_neighbors: int = 5,
        buffer_size: int = 500,
        weight_margin: float = 0.40,
        weight_neighbor: float = 0.40,
        weight_temporal: float = 0.20,
    ) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if k_neighbors < 1:
            raise ConfigurationError(f"k_neighbors must be >= 1, got {k_neighbors}")
        if buffer_size < 10:
            raise ConfigurationError(f"buffer_size must be >= 10, got {buffer_size}")

        total_w = weight_margin + weight_neighbor + weight_temporal
        if total_w <= 0.0:
            raise ConfigurationError("Sum of weights must be positive.")

        self.n_classes = int(n_classes)
        self.k_neighbors = int(k_neighbors)
        self.buffer_size = int(buffer_size)

        self.w_margin = float(weight_margin / total_w)
        self.w_neighbor = float(weight_neighbor / total_w)
        self.w_temporal = float(weight_temporal / total_w)

        # Spatial search buffer
        self._history_X: deque = deque(maxlen=self.buffer_size)
        self._history_y: deque = deque(maxlen=self.buffer_size)

        # Temporal moving agreement average
        self._recent_agreement: deque = deque(maxlen=50)

    def compute_reliability(
        self,
        X: np.ndarray,
        y: np.ndarray,
        probas: np.ndarray,
    ) -> np.ndarray:
        """Compute composite sample reliability scores in [0, 1].

        Parameters
        ----------
        X : np.ndarray of shape (N, D)
            Feature vectors.
        y : np.ndarray of shape (N,)
            Reported ground-truth integer labels.
        probas : np.ndarray of shape (N, n_classes)
            Predicted class posterior probabilities.

        Returns
        -------
        np.ndarray of shape (N,)
            Reliability scores r_i in [0, 1].
        """
        X_arr = check_array_2d(X, name="X")
        y_arr = check_labels_1d(y, expected_len=X_arr.shape[0], n_classes=self.n_classes, name="y")
        prob_arr = np.asarray(probas, dtype=np.float64)
        n_samples = X_arr.shape[0]

        # 1. Prediction Margin & Entropy Signal
        # Margin: probability of true reported class y_i minus max probability among other classes
        margin_scores = np.zeros(n_samples, dtype=np.float64)
        for i in range(n_samples):
            true_c = y_arr[i]
            p_true = prob_arr[i, true_c]
            # Max prob among other classes
            other_probs = np.delete(prob_arr[i], true_c)
            p_other = np.max(other_probs) if len(other_probs) > 0 else 0.0
            margin = p_true - p_other  # in [-1, 1]
            margin_scores[i] = np.clip((margin + 1.0) / 2.0, 0.0, 1.0)

        # 2. Spatial Neighborhood Agreement Signal
        neighbor_scores = np.ones(n_samples, dtype=np.float64)
        if len(self._history_X) >= self.k_neighbors:
            hist_X_mat = np.array(self._history_X)
            hist_y_mat = np.array(self._history_y)

            # Pairwise distance from batch X to hist_X
            # dist[i, j] = ||X[i] - hist_X[j]||_2
            for i in range(n_samples):
                dists = np.linalg.norm(hist_X_mat - X_arr[i], axis=1)
                k = min(self.k_neighbors, len(dists))
                k_idx = np.argpartition(dists, k - 1)[:k]
                agreeing = np.sum(hist_y_mat[k_idx] == y_arr[i])
                neighbor_scores[i] = float(agreeing / k)
        else:
            # During warm-up, fall back to prediction margin
            neighbor_scores = margin_scores.copy()

        # 3. Temporal Consistency Signal
        temp_mean = float(np.mean(self._recent_agreement)) if self._recent_agreement else 0.70
        temporal_scores = np.full(n_samples, temp_mean, dtype=np.float64)

        # Composite score
        composite = (
            self.w_margin * margin_scores
            + self.w_neighbor * neighbor_scores
            + self.w_temporal * temporal_scores
        )
        reliability = np.clip(composite, 0.0, 1.0)

        # Update buffers
        for i in range(n_samples):
            self._history_X.append(X_arr[i].copy())
            self._history_y.append(int(y_arr[i]))
            # 1 if prediction matches reported label, else 0
            pred_match = 1.0 if np.argmax(prob_arr[i]) == y_arr[i] else 0.0
            self._recent_agreement.append(pred_match)

        return reliability

    def clear(self) -> None:
        """Reset historical search index."""
        self._history_X.clear()
        self._history_y.clear()
        self._recent_agreement.clear()


class AsymmetricTransitionDetector:
    """Monitors directional prediction-label disagreement to detect asymmetric corruption.

    In adversarial or evasion regimes (e.g. spam disguised as ham), corruption is asymmetric:
    P(label=0 | true=1) >> P(label=1 | true=0). This detector measures the directional
    discordance ratio to alert controllers of directional label corruption.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    window_size : int, default=300
        Size of sliding window history for discordance monitoring.
    """

    def __init__(self, n_classes: int = 2, window_size: int = 300) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if window_size < 10:
            raise ConfigurationError(f"window_size must be >= 10, got {window_size}")

        self.n_classes = int(n_classes)
        self.window_size = int(window_size)
        self.history: deque = deque(maxlen=self.window_size)

    def update(self, y_pred: np.ndarray, y_true: np.ndarray) -> None:
        """Record batch of predictions and reported labels."""
        p_arr = np.asarray(y_pred, dtype=np.int64).ravel()
        t_arr = np.asarray(y_true, dtype=np.int64).ravel()
        for p, t in zip(p_arr, t_arr):
            self.history.append((int(p), int(t)))

    def get_asymmetry_ratio(self) -> float:
        """Calculates directional discordance ratio: discordance(pred=1, true=0) / discordance(pred=0, true=1)."""
        if len(self.history) < 20:
            return 1.0

        d_10 = sum(1 for p, t in self.history if p == 1 and t == 0)
        d_01 = sum(1 for p, t in self.history if p == 0 and t == 1)

        if d_01 == 0:
            return float(d_10 + 1)
        return float(max(d_10 / max(d_01, 1), d_01 / max(d_10, 1)))

    def is_asymmetric(self, threshold: float = 1.5) -> bool:
        """Check whether directional discordance exceeds symmetry threshold."""
        return self.get_asymmetry_ratio() >= float(threshold)

    def clear(self) -> None:
        """Clear history."""
        self.history.clear()


class ClassConditionalReliabilityEstimator:
    """Class-conditional density and discordance estimator for robust learning under asymmetric noise.

    Models sample likelihoods separately per class P(x | y=c) using robust medians and
    Median Absolute Deviations (MAD), preventing disguised minority samples from being
    purged as 'noisy outliers'.

    Parameters
    ----------
    n_features : int
        Dimensionality of input feature vectors.
    n_classes : int, default=2
        Number of target classes.
    buffer_per_class : int, default=300
        Maximum exemplar instances retained per class for density modeling.
    minority_protection : bool, default=True
        Whether to enforce a safety floor preventing minority sample deletion.
    min_minority_prior : float, default=0.35
        Prior prevalence threshold below which a class receives minority protection.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        buffer_per_class: int = 300,
        minority_protection: bool = True,
        min_minority_prior: float = 0.35,
    ) -> None:
        if n_features < 1:
            raise ConfigurationError(f"n_features must be >= 1, got {n_features}")
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if buffer_per_class < 10:
            raise ConfigurationError(f"buffer_per_class must be >= 10, got {buffer_per_class}")

        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.buffer_per_class = int(buffer_per_class)
        self.minority_protection = bool(minority_protection)
        self.min_minority_prior = float(min_minority_prior)

        self._class_buffers: Dict[int, deque] = {c: deque(maxlen=self.buffer_per_class) for c in range(self.n_classes)}
        self._class_counts: np.ndarray = np.zeros(self.n_classes, dtype=np.int64)

    def update(self, X: np.ndarray, y: np.ndarray) -> None:
        """Incorporate new instances into class-conditional buffers."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")

        for x_i, y_i in zip(X_val, y_val):
            c = int(y_i)
            self._class_buffers[c].append(x_i.copy())
            self._class_counts[c] += 1

    def compute_reliability(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> np.ndarray:
        """Computes class-conditional sample reliability scores r_i in [0, 1].

        Samples that fit their reported class distribution receive high scores.
        Under minority protection, instances from rare classes are shielded against aggressive filtering.
        """
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")
        n_samples = X_val.shape[0]

        total_seen = max(1, int(np.sum(self._class_counts)))
        class_priors = self._class_counts / total_seen

        reliabilities = np.ones(n_samples, dtype=np.float64)

        for i in range(n_samples):
            c = int(y_val[i])
            buf = self._class_buffers[c]

            if len(buf) < 10:
                # Insufficient class statistics; default to high reliability
                reliabilities[i] = 1.0
                continue

            mat = np.array(buf)
            median = np.median(mat, axis=0)
            mad = np.median(np.abs(mat - median), axis=0) + 1e-4

            # Normalized distance from class centroid
            norm_dist = np.mean(np.abs(X_val[i] - median) / mad)
            # Gaussian density score in [0, 1]
            raw_score = float(np.exp(-0.5 * min(norm_dist, 10.0)))

            # Minority protection rule: shield rare classes from deletion
            if self.minority_protection and class_priors[c] < self.min_minority_prior:
                raw_score = max(raw_score, 0.70)

            reliabilities[i] = np.clip(raw_score, 0.0, 1.0)

        return reliabilities

    def clear(self) -> None:
        """Reset all class buffers."""
        for c in range(self.n_classes):
            self._class_buffers[c].clear()
        self._class_counts.fill(0)
