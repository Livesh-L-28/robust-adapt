"""Streaming Decision Forest Ensemble combining multiple Hoeffding trees via online bagging."""

from typing import Any, Dict, List, Optional
import numpy as np
from robust_adapt.ala.tree import VectorizedHoeffdingTree
from robust_adapt.core.exceptions import ValidationError
from robust_adapt.core.types import FloatArray2D, IntArray1D
from robust_adapt.core.validation import check_array_2d, check_labels_1d, check_sample_weights


class StreamingEnsemble:
    """Ensemble of VectorizedHoeffdingTree classifiers trained via online bootstrap bagging.

    Parameters
    ----------
    n_estimators : int, default=5
        Number of streaming decision trees in the ensemble.
    n_features : int
        Feature dimensionality.
    n_classes : int
        Number of target classes.
    grace_period : int, default=200
        Hoeffding split grace period per tree.
    delta : float, default=1e-5
        Hoeffding bound confidence per tree.
    random_state : Optional[int], default=None
        Seed for reproducible online bootstrap sampling.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int,
        n_estimators: int = 5,
        grace_period: int = 200,
        delta: float = 1e-5,
        random_state: Optional[int] = None,
    ) -> None:
        if n_estimators <= 0:
            raise ValidationError(f"n_estimators must be >= 1, got {n_estimators}")

        self.n_estimators = int(n_estimators)
        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.grace_period = int(grace_period)
        self.delta = float(delta)

        self._rng = np.random.default_rng(random_state)
        self.estimators: List[VectorizedHoeffdingTree] = [
            VectorizedHoeffdingTree(
                n_features=self.n_features,
                n_classes=self.n_classes,
                grace_period=self.grace_period,
                delta=self.delta,
            )
            for _ in range(self.n_estimators)
        ]

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "StreamingEnsemble":
        """Incrementally update each ensemble estimator using Poisson online bootstrap weights."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=self.n_classes, name="y")
        w_val = check_sample_weights(sample_weight, expected_len=n_samples, name="sample_weight")
        if w_val is None:
            w_val = np.ones(n_samples, dtype=np.float64)

        for tree in self.estimators:
            # Poisson(lambda=1.0) online bootstrap weight
            poisson_k = self._rng.poisson(lam=1.0, size=n_samples).astype(np.float64)
            combined_w = w_val * poisson_k
            nonzero_mask = combined_w > 0.0

            if np.any(nonzero_mask):
                tree.partial_fit(
                    X_val[nonzero_mask],
                    y_val[nonzero_mask],
                    sample_weight=combined_w[nonzero_mask],
                )

        return self

    def predict_proba(self, X: np.ndarray) -> FloatArray2D:
        """Predict averaged class probabilities across all trees."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        n_samples = X_val.shape[0]
        accum_probs = np.zeros((n_samples, self.n_classes), dtype=np.float64)

        for tree in self.estimators:
            accum_probs += tree.predict_proba(X_val)

        avg_probs = accum_probs / float(self.n_estimators)
        return np.ascontiguousarray(avg_probs)

    def predict(self, X: np.ndarray) -> IntArray1D:
        """Predict class with highest average posterior probability."""
        probs = self.predict_proba(X)
        return np.ascontiguousarray(np.argmax(probs, axis=1), dtype=np.int64)
