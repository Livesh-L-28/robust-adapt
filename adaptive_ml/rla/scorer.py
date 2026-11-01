"""Density-Aware Margin Reliability Scorer.

Mathematical formulation specified in DOC-DES-P6-004 and DOC-DES-P6-009 (Algorithm 5).
Protects legitimate minority instances from false-positive noise deletion (Theorem 2).
"""

from typing import Any, Dict, Optional
import numpy as np
from adaptive_ml.core.constants import EPS_DIV, EPS_RELIABILITY, EPS_VAR
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray1D, FloatArray2D, IntArray1D
from adaptive_ml.core.validation import check_array_2d, check_labels_1d


class DensityAwareMarginScorer:
    """Couples signed logit margins with local k-NN feature density to evaluate sample reliability.

    Parameters
    ----------
    n_classes : int
        Total number of target classes.
    n_neighbors : int, default=5
        Number of nearest neighbors evaluated for local density estimation.
    alpha : float, default=1.0
        Logit margin scaling sensitivity.
    gamma : float, default=0.5
        Density protection coefficient for tail minority instances.
    min_reliability : float, default=1e-4
        Lower-bound epsilon guard on reliability scores.
    """

    def __init__(
        self,
        n_classes: int,
        n_neighbors: int = 5,
        alpha: float = 1.0,
        gamma: float = 0.5,
        min_reliability: float = EPS_RELIABILITY,
    ) -> None:
        if n_classes < 2:
            raise ValidationError(f"n_classes must be >= 2, got {n_classes}")
        if n_neighbors <= 0:
            raise ValidationError(f"n_neighbors must be >= 1, got {n_neighbors}")
        if alpha <= 0.0:
            raise ValidationError(f"alpha must be positive, got {alpha}")
        if gamma < 0.0:
            raise ValidationError(f"gamma must be non-negative, got {gamma}")

        self.n_classes = int(n_classes)
        self.n_neighbors = int(n_neighbors)
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.min_reliability = float(min_reliability)

    def score_samples(
        self,
        X: np.ndarray,
        logits: np.ndarray,
        y: np.ndarray,
    ) -> FloatArray1D:
        """Compute density-aware reliability scores for a batch of instances.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input feature embeddings.
        logits : np.ndarray of shape (n_samples, n_classes)
            Model logit outputs.
        y : np.ndarray of shape (n_samples,)
            Observed target labels.

        Returns
        -------
        reliabilities : FloatArray1D of shape (n_samples,)
            Per-sample reliability scores in [min_reliability, 1.0].
        """
        X_val = check_array_2d(X, name="X")
        n_samples = X_val.shape[0]
        logits_val = check_array_2d(logits, expected_dim=self.n_classes, name="logits")
        if logits_val.shape[0] != n_samples:
            raise ValidationError(
                f"Row count mismatch: X has {n_samples} rows but logits has {logits_val.shape[0]} rows"
            )
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=self.n_classes, name="y")

        # Step 1: Compute signed logit margins M_i = z_{y_i} - max_{j != y_i} z_j
        target_logits = logits_val[np.arange(n_samples), y_val]
        masked_logits = logits_val.copy()
        masked_logits[np.arange(n_samples), y_val] = -np.inf
        max_competitor = np.max(masked_logits, axis=1)
        raw_margins = target_logits - max_competitor

        # Batch margin normalization
        mu_M = float(np.mean(raw_margins))
        sigma_M = float(np.std(raw_margins)) + EPS_VAR
        norm_margins = (raw_margins - mu_M) / sigma_M

        # Step 2: Compute local k-NN feature density rho_k(x_i)
        k = min(self.n_neighbors, n_samples - 1)
        if k > 0:
            # Pairwise squared Euclidean distance matrix: ||x - y||^2 = ||x||^2 + ||y||^2 - 2x.y
            sq_norms = np.sum(X_val ** 2, axis=1, keepdims=True)
            D_sq = sq_norms + sq_norms.T - 2.0 * np.dot(X_val, X_val.T)
            D_sq = np.maximum(0.0, D_sq)  # Denominator safety

            # Partition to find k-nearest neighbors (excluding self at distance 0)
            sorted_dists = np.partition(np.sqrt(D_sq), kth=k, axis=1)[:, 1 : k + 1]
            mean_knn_dist = np.mean(sorted_dists, axis=1)
            rho_k = 1.0 / (mean_knn_dist + 1e-6)

            # Relative density ratio delta_k = rho_k / mean(rho_k)
            mean_rho = float(np.mean(rho_k)) + EPS_DIV
            delta_k = rho_k / mean_rho
        else:
            delta_k = np.ones(n_samples, dtype=np.float64)

        # Step 3: Density-aware reliability score
        # psi(delta) = -ln(delta + eps)
        # In low-density regions (delta << 1), psi > 0 providing protective margin bonus
        psi_delta = -np.log(delta_k + 1e-6)
        linear_score = self.alpha * norm_margins + self.gamma * psi_delta

        # Sigmoid activation and clipping to [min_reliability, 1.0]
        reliabilities = 1.0 / (1.0 + np.exp(-np.clip(linear_score, -50.0, 50.0)))
        reliabilities = np.clip(reliabilities, self.min_reliability, 1.0)

        return np.ascontiguousarray(reliabilities, dtype=np.float64)

    def get_sample_weights(
        self,
        X: np.ndarray,
        logits: np.ndarray,
        y: np.ndarray,
        threshold: Optional[float] = None,
    ) -> FloatArray1D:
        """Return reliability sample weights, optionally hard-filtering below threshold."""
        reliabilities = self.score_samples(X, logits, y)
        if threshold is not None and threshold > 0.0:
            # Hard filtering: zero out weights for corrupted samples
            reliabilities = np.where(reliabilities >= threshold, reliabilities, 0.0)
        return reliabilities

    def state_dict(self) -> Dict[str, Any]:
        """Serialize scorer parameters."""
        return {
            "n_classes": self.n_classes,
            "n_neighbors": self.n_neighbors,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "min_reliability": self.min_reliability,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore scorer parameters."""
        self.n_classes = int(state["n_classes"])
        self.n_neighbors = int(state["n_neighbors"])
        self.alpha = float(state["alpha"])
        self.gamma = float(state["gamma"])
        self.min_reliability = float(state["min_reliability"])

