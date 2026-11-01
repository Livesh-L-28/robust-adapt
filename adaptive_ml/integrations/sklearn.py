"""
Scikit-learn Integration Adapters for AdaptiveML.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import numpy as np

try:
    from sklearn.base import BaseEstimator, ClassifierMixin
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    BaseEstimator = object  # type: ignore
    ClassifierMixin = object  # type: ignore

from adaptive_ml.ala.classifier import AdaptiveClassifier


class SklearnAdaptiveClassifier(BaseEstimator, ClassifierMixin):
    """Scikit-learn compliant estimator wrapper around AdaptiveClassifier."""

    _estimator_type = "classifier"

    def __init__(
        self,
        n_features: int = 10,
        n_classes: int = 2,
        grace_period: int = 200,
        delta: float = 1e-5,
        tau_tie: float = 0.05,
        enable_drift_detection: bool = True,
        replay_capacity: int = 5000,
        replay_ratio: float = 0.2,
        n_estimators: int = 1,
        random_state: Optional[int] = None,
    ) -> None:
        self.n_features = n_features
        self.n_classes = n_classes
        self.grace_period = grace_period
        self.delta = delta
        self.tau_tie = tau_tie
        self.enable_drift_detection = enable_drift_detection
        self.replay_capacity = replay_capacity
        self.replay_ratio = replay_ratio
        self.n_estimators = n_estimators
        self.random_state = random_state

        self._estimator: Optional[AdaptiveClassifier] = None

    def _ensure_estimator(self) -> AdaptiveClassifier:
        if self._estimator is None:
            self._estimator = AdaptiveClassifier(
                n_features=self.n_features,
                n_classes=self.n_classes,
                grace_period=self.grace_period,
                delta=self.delta,
                tau_tie=self.tau_tie,
                enable_drift_detection=self.enable_drift_detection,
                replay_capacity=self.replay_capacity,
                replay_ratio=self.replay_ratio,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
            )
        return self._estimator

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnAdaptiveClassifier":
        est = self._ensure_estimator()
        est.fit(X, y)
        self.classes_ = np.arange(self.n_classes)
        return self

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[Sequence[int]] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "SklearnAdaptiveClassifier":
        est = self._ensure_estimator()
        est.partial_fit(X, y, classes=classes, sample_weight=sample_weight)
        self.classes_ = np.arange(self.n_classes)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        est = self._ensure_estimator()
        return est.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        est = self._ensure_estimator()
        return est.predict_proba(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute mean classification accuracy on test dataset."""
        preds = self.predict(X)
        return float(np.mean(preds == y))
