"""Noise Taxonomy Classification and Outlier vs Rare Valid Pattern Discrimination.

Categorizes noise mechanisms:
- Uniform Completely Random (Symmetric)
- Class-Conditional Transition Noise (Asymmetric)
- Instance-Dependent Noise
- Outlier vs Rare Valid Pattern Discrimination: protects rare valid minority instances
  from being erroneously rejected as corrupt outliers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError


class NoiseType(str, Enum):
    """Categorical classification of label corruption mechanism."""
    CLEAN = "CLEAN"
    UNIFORM_RANDOM = "UNIFORM_RANDOM"
    CLASS_CONDITIONAL = "CLASS_CONDITIONAL"
    INSTANCE_DEPENDENT = "INSTANCE_DEPENDENT"


class PatternType(str, Enum):
    """Structural classification of individual low-margin instances."""
    INLIER = "INLIER"
    RARE_VALID_PATTERN = "RARE_VALID_PATTERN"
    CORRUPT_OUTLIER = "CORRUPT_OUTLIER"


class NoiseTaxonomyClassifier:
    """Diagnoses noise taxonomy and discriminates between corrupt outliers and rare valid patterns.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    noise_threshold : float, default=0.15
        Estimated corruption fraction required to declare a non-clean regime.
    asymmetry_threshold : float, default=0.20
        Max-min off-diagonal divergence threshold indicating class-conditional noise.
    """

    def __init__(
        self,
        n_classes: int = 2,
        noise_threshold: float = 0.15,
        asymmetry_threshold: float = 0.20,
    ) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")

        self.n_classes = int(n_classes)
        self.noise_threshold = float(noise_threshold)
        self.asymmetry_threshold = float(asymmetry_threshold)

        # Transition matrix T[j, k] = P(pred=k | true=j)
        self.transition_matrix_ = np.eye(self.n_classes, dtype=np.float64)
        self.estimated_noise_rate_: float = 0.0
        self.dominant_noise_type_: NoiseType = NoiseType.CLEAN

    def estimate_noise_transition(
        self,
        y_reported: np.ndarray,
        y_pred: np.ndarray,
    ) -> Tuple[NoiseType, np.ndarray, float]:
        """Estimate the empirical noise transition matrix and classify the noise mechanism.

        Parameters
        ----------
        y_reported : np.ndarray of shape (N,)
            Reported labels from data stream.
        y_pred : np.ndarray of shape (N,)
            High-confidence model predicted labels.

        Returns
        -------
        Tuple[NoiseType, np.ndarray, float]
            (NoiseType, transition_matrix, estimated_noise_rate)
        """
        y_rep = np.asarray(y_reported, dtype=np.int64)
        y_pr = np.asarray(y_pred, dtype=np.int64)
        n = y_rep.shape[0]

        if n == 0:
            return NoiseType.CLEAN, self.transition_matrix_, 0.0

        # Build confusion matrix C[j, k] = count where reported=j and pred=k
        C = np.zeros((self.n_classes, self.n_classes), dtype=np.float64)
        for i in range(n):
            j = y_rep[i]
            k = y_pr[i]
            if 0 <= j < self.n_classes and 0 <= k < self.n_classes:
                C[j, k] += 1.0

        # Normalize row-wise to get P(pred=k | reported=j)
        row_sums = np.sum(C, axis=1, keepdims=True)
        T = np.divide(C, np.maximum(row_sums, 1e-6))
        self.transition_matrix_ = T

        # Overall noise rate: fraction where reported != pred
        noise_rate = float(np.mean(y_rep != y_pr))
        self.estimated_noise_rate_ = noise_rate

        if noise_rate < self.noise_threshold:
            self.dominant_noise_type_ = NoiseType.CLEAN
            return NoiseType.CLEAN, T, noise_rate

        # Analyze off-diagonal elements for asymmetry
        off_diagonals: List[float] = []
        for j in range(self.n_classes):
            for k in range(self.n_classes):
                if j != k:
                    off_diagonals.append(float(T[j, k]))

        diff_asym = max(off_diagonals) - min(off_diagonals) if off_diagonals else 0.0
        if diff_asym >= self.asymmetry_threshold:
            self.dominant_noise_type_ = NoiseType.CLASS_CONDITIONAL
        else:
            self.dominant_noise_type_ = NoiseType.UNIFORM_RANDOM

        return self.dominant_noise_type_, T, noise_rate

    def discriminate_sample(
        self,
        x_candidate: np.ndarray,
        y_candidate: int,
        prototypes: Dict[int, np.ndarray],
        variances: Optional[Dict[int, np.ndarray]] = None,
        margin_score: float = 0.5,
    ) -> PatternType:
        """Discriminate whether a low-margin instance is an invalid corrupt outlier or a rare valid pattern.

        Parameters
        ----------
        x_candidate : np.ndarray of shape (D,)
            Feature vector.
        y_candidate : int
            Reported label.
        prototypes : Dict[int, np.ndarray]
            Dictionary of class centroids / prototypes.
        variances : Optional[Dict[int, np.ndarray]], default=None
            Class feature variance vectors.
        margin_score : float, default=0.5
            Prediction margin score in [0, 1].

        Returns
        -------
        PatternType
            INLIER, RARE_VALID_PATTERN, or CORRUPT_OUTLIER.
        """
        if margin_score >= 0.70:
            return PatternType.INLIER

        c_true = int(y_candidate)
        if c_true not in prototypes:
            return PatternType.CORRUPT_OUTLIER

        # Distance to reported class prototype
        mu_true = prototypes[c_true]
        var_true = variances.get(c_true, np.ones_like(mu_true)) if variances is not None else np.ones_like(mu_true)
        norm_dist_true = float(np.mean(np.abs(x_candidate - mu_true) / np.sqrt(var_true + 1e-6)))

        # Distance to nearest alternative class prototype
        other_dists: List[float] = []
        for c, mu in prototypes.items():
            if c != c_true:
                var_c = variances.get(c, np.ones_like(mu)) if variances is not None else np.ones_like(mu)
                d = float(np.mean(np.abs(x_candidate - mu) / np.sqrt(var_c + 1e-6)))
                other_dists.append(d)

        min_other_dist = min(other_dists) if other_dists else float("inf")

        # Theorem: If candidate is closer to its own prototype than to other prototypes,
        # it is a rare valid pattern despite low margin, NOT a corrupt outlier.
        if norm_dist_true < 2.0 and norm_dist_true <= min_other_dist:
            return PatternType.RARE_VALID_PATTERN
        elif norm_dist_true > 3.5 or norm_dist_true > 2.0 * min_other_dist:
            return PatternType.CORRUPT_OUTLIER
        else:
            return PatternType.CORRUPT_OUTLIER
