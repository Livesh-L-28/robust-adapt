"""Scikit-learn Integration Adapters for AdaptiveML.

Provides scikit-learn compliant estimators, transformers, and pipeline components
adhering strictly to the BaseEstimator, ClassifierMixin, and TransformerMixin protocols.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.integrations.data import to_numpy

try:
    from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    class BaseEstimator:  # type: ignore[no-redef]
        """Fallback dummy class when scikit-learn is not installed."""
        pass

    class ClassifierMixin:  # type: ignore[no-redef]
        """Fallback dummy class when scikit-learn is not installed."""
        pass

    class TransformerMixin:  # type: ignore[no-redef]
        """Fallback dummy class when scikit-learn is not installed."""
        pass

from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine


class SklearnAdaptiveClassifier(BaseEstimator, ClassifierMixin):
    """Scikit-learn compliant streaming classifier wrapper around AdaptiveClassifier.

    Supports:
    - Standard fit() and incremental partial_fit()
    - Pipeline integration and cross-validation
    - sklearn.base.clone() compatibility
    - predict() and predict_proba()
    - Input conversion from pandas, Polars, and PyTorch

    Parameters
    ----------
    n_features : int, default=10
        Number of input feature dimensions.
    n_classes : int, default=2
        Number of discrete target classes.
    grace_period : int, default=200
        Number of instances accumulated at a leaf before testing split criteria.
    delta : float, default=1e-5
        Hoeffding split confidence parameter.
    tau_tie : float, default=0.05
        Tie-breaking split threshold.
    enable_drift_detection : bool, default=True
        Whether to monitor stream loss using internal ADWIN drift detection.
    replay_capacity : int, default=5000
        Maximum capacity of the class-balanced reservoir replay buffer.
    replay_ratio : float, default=0.2
        Fraction of incoming batch size sampled from replay buffer during training.
    n_estimators : int, default=1
        Number of trees in ensemble (1 for single tree, >1 for online bagging).
    random_state : Optional[int], default=None
        Seed for reproducible random state initialization.
    """

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

    def _record_input_metadata(self, X: Any) -> None:
        if hasattr(X, "columns"):
            try:
                self.feature_names_in_ = np.array([str(c) for c in X.columns], dtype=object)
            except Exception:
                pass
        if hasattr(X, "shape") and len(X.shape) >= 2:
            self.n_features_in_ = int(X.shape[1])

    def fit(self, X: Any, y: Any, sample_weight: Optional[Any] = None) -> "SklearnAdaptiveClassifier":
        """Fit the model on initial batch data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training feature vectors (NumPy, pandas, Polars, or PyTorch).
        y : array-like of shape (n_samples,)
            Target class labels.
        sample_weight : Optional[array-like], default=None
            Per-sample importance weights.

        Returns
        -------
        self : SklearnAdaptiveClassifier
            Fitted estimator.
        """
        self._record_input_metadata(X)
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        y_arr = to_numpy(y, dtype=np.int64, ensure_1d=True, name="y")
        w_arr = to_numpy(sample_weight, dtype=np.float64, ensure_1d=True, name="sample_weight") if sample_weight is not None else None

        # Reset estimator on fresh fit
        self._estimator = None
        est = self._ensure_estimator()

        # Update n_features if dynamically inferred
        if X_arr.shape[1] != self.n_features:
            self.n_features = int(X_arr.shape[1])
            self._estimator = None
            est = self._ensure_estimator()

        self.classes_ = np.arange(self.n_classes, dtype=np.int64)
        est.fit(X_arr, y_arr)
        return self

    def partial_fit(
        self,
        X: Any,
        y: Any,
        classes: Optional[Sequence[int]] = None,
        sample_weight: Optional[Any] = None,
    ) -> "SklearnAdaptiveClassifier":
        """Incrementally update the streaming classifier with incoming batch.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Streaming feature batch.
        y : array-like of shape (n_samples,)
            Target labels.
        classes : Optional[Sequence[int]], default=None
            Expected classes across the stream (required by scikit-learn on first partial_fit).
        sample_weight : Optional[array-like], default=None
            Per-sample importance or reliability weights.

        Returns
        -------
        self : SklearnAdaptiveClassifier
            Updated estimator.
        """
        self._record_input_metadata(X)
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        y_arr = to_numpy(y, dtype=np.int64, ensure_1d=True, name="y")
        w_arr = to_numpy(sample_weight, dtype=np.float64, ensure_1d=True, name="sample_weight") if sample_weight is not None else None

        if not hasattr(self, "classes_"):
            if classes is not None:
                self.classes_ = np.asarray(classes, dtype=np.int64)
            else:
                self.classes_ = np.arange(self.n_classes, dtype=np.int64)

        est = self._ensure_estimator()
        est.partial_fit(X_arr, y_arr, classes=classes, sample_weight=w_arr)
        return self

    def predict(self, X: Any) -> np.ndarray:
        """Predict class labels for input instances."""
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        est = self._ensure_estimator()
        return est.predict(X_arr)

    def predict_proba(self, X: Any) -> np.ndarray:
        """Predict class posterior probabilities for input instances."""
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        est = self._ensure_estimator()
        return est.predict_proba(X_arr)

    def score(self, X: Any, y: Any) -> float:
        """Compute mean classification accuracy on test dataset."""
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        y_arr = to_numpy(y, dtype=np.int64, ensure_1d=True, name="y")
        preds = self.predict(X_arr)
        return float(np.mean(preds == y_arr))

    @property
    def drift_count_(self) -> int:
        """Number of drift adaptation events detected by the underlying estimator."""
        if self._estimator is None:
            return 0
        return self._estimator.drift_count_

    @property
    def samples_seen_(self) -> int:
        """Total cumulative stream samples processed."""
        if self._estimator is None:
            return 0
        return self._estimator.samples_seen_


class SklearnDriftDetectorTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn pipeline transformer monitoring stream distribution drift via ADWIN.

    Passes feature vectors through transparently while tracking distribution shifts.

    Parameters
    ----------
    delta : float, default=0.002
        ADWIN statistical confidence threshold.
    monitored_feature_index : int, default=0
        Index of the feature column monitored for drift.
    """

    def __init__(self, delta: float = 0.002, monitored_feature_index: int = 0) -> None:
        self.delta = delta
        self.monitored_feature_index = monitored_feature_index
        self._detector: Optional[ReliabilityWeightedADWIN] = None
        self.drift_count_: int = 0
        self.last_drift_detected_: bool = False

    def fit(self, X: Any, y: Any = None) -> "SklearnDriftDetectorTransformer":
        self._detector = ReliabilityWeightedADWIN(delta=self.delta)
        self.drift_count_ = 0
        self.last_drift_detected_ = False
        return self

    def transform(self, X: Any) -> np.ndarray:
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        if self._detector is None:
            self.fit(X_arr)

        feat_idx = min(max(0, self.monitored_feature_index), X_arr.shape[1] - 1)
        monitored_values = X_arr[:, feat_idx]

        self.last_drift_detected_ = False
        for val in monitored_values:
            drift = self._detector.update(float(val))  # type: ignore[union-attr]
            if drift:
                self.drift_count_ += 1
                self.last_drift_detected_ = True

        return X_arr


class SklearnReliabilityFilter(BaseEstimator, TransformerMixin):
    """Scikit-learn pipeline transformer filtering out low-reliability samples during streaming.

    Parameters
    ----------
    n_classes : int, default=2
        Number of classes.
    min_reliability : float, default=0.35
        Minimum sample reliability score required to retain an instance.
    """

    def __init__(self, n_classes: int = 2, min_reliability: float = 0.35) -> None:
        self.n_classes = n_classes
        self.min_reliability = min_reliability
        self._engine: Optional[MultiSignalReliabilityEngine] = None
        self.filtered_count_: int = 0

    def fit(self, X: Any, y: Any = None) -> "SklearnReliabilityFilter":
        self._engine = MultiSignalReliabilityEngine(n_classes=self.n_classes)
        self.filtered_count_ = 0
        return self

    def transform(self, X: Any) -> np.ndarray:
        """Transparent feature pass-through."""
        return to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")

    def filter_batch(self, X: Any, y: Any, probas: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Filter incoming batch to retain only high-reliability instances.

        Returns
        -------
        Tuple[X_filtered, y_filtered, weights_filtered]
        """
        X_arr = to_numpy(X, dtype=np.float64, ensure_2d=True, name="X")
        y_arr = to_numpy(y, dtype=np.int64, ensure_1d=True, name="y")
        prob_arr = to_numpy(probas, dtype=np.float64, ensure_2d=True, name="probas")

        if self._engine is None:
            self.fit(X_arr, y_arr)

        reliabilities = self._engine.compute_reliability(X_arr, y_arr, prob_arr)  # type: ignore[union-attr]
        mask = reliabilities >= self.min_reliability
        self.filtered_count_ += int(np.sum(~mask))

        return X_arr[mask], y_arr[mask], reliabilities[mask]


# Canonical Ergonomic Aliases (ALPHA-DEF-004)
ScikitLearnAdaptiveClassifier = SklearnAdaptiveClassifier
ScikitLearnDriftDetectorTransformer = SklearnDriftDetectorTransformer
ScikitLearnReliabilityFilter = SklearnReliabilityFilter

__all__ = [
    "SklearnAdaptiveClassifier",
    "SklearnDriftDetectorTransformer",
    "SklearnReliabilityFilter",
    "ScikitLearnAdaptiveClassifier",
    "ScikitLearnDriftDetectorTransformer",
    "ScikitLearnReliabilityFilter",
]
