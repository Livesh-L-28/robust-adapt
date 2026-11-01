"""AdaptiveClassifier: Scikit-learn compliant streaming classifier with integrated drift adaptation."""

from typing import Any, Dict, Optional, Sequence, Union
import numpy as np
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.ensemble import StreamingEnsemble
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from adaptive_ml.ala.tree import VectorizedHoeffdingTree
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray2D, IntArray1D
from adaptive_ml.core.validation import check_array_2d, check_labels_1d, check_sample_weights

# Optional scikit-learn base classes
try:
    from sklearn.base import BaseEstimator, ClassifierMixin
    _SKLEARN_AVAILABLE = True
except ImportError:
    class BaseEstimator:  # type: ignore[no-redef]
        def get_params(self, deep: bool = True) -> Dict[str, Any]:
            return {}

        def set_params(self, **params: Any) -> Any:
            for k, v in params.items():
                setattr(self, k, v)
            return self

    class ClassifierMixin:  # type: ignore[no-redef]
        def score(self, X: np.ndarray, y: np.ndarray) -> float:
            return float(np.mean(self.predict(X) == y))  # type: ignore[attr-defined]

    _SKLEARN_AVAILABLE = False


class AdaptiveClassifier(BaseEstimator, ClassifierMixin):
    """Online streaming classifier combining vectorized Hoeffding trees with drift adaptation.

    Parameters
    ----------
    n_features : int
        Feature dimensionality.
    n_classes : int
        Number of discrete target classes.
    grace_period : int, default=200
        Number of instances a leaf node accumulates before evaluating Hoeffding split check.
    delta : float, default=1e-5
        Hoeffding split confidence parameter.
    tau_tie : float, default=0.05
        Tie-breaking split threshold.
    enable_drift_detection : bool, default=True
        Whether to monitor incoming stream loss with Reliability-Weighted ADWIN.
    replay_capacity : int, default=5000
        Maximum capacity of the class-balanced reservoir replay buffer.
    replay_ratio : float, default=0.2
        Fraction of incoming batch size sampled from replay buffer during updates.
    n_estimators : int, default=1
        Number of trees in ensemble (1 for single tree, >1 for online bagging forest).
    random_state : Optional[int], default=None
        Seed for reproducible random state initialization.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int,
        grace_period: int = 200,
        delta: float = 1e-5,
        tau_tie: float = 0.05,
        enable_drift_detection: bool = True,
        replay_capacity: int = 5000,
        replay_ratio: float = 0.2,
        n_estimators: int = 1,
        random_state: Optional[int] = None,
    ) -> None:
        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.grace_period = int(grace_period)
        self.delta = float(delta)
        self.tau_tie = float(tau_tie)
        self.enable_drift_detection = bool(enable_drift_detection)
        self.replay_capacity = int(replay_capacity)
        self.replay_ratio = float(replay_ratio)
        self.n_estimators = int(n_estimators)
        self.random_state = random_state

        self._init_components()

    def _init_components(self) -> None:
        if self.n_estimators > 1:
            self._model: Union[VectorizedHoeffdingTree, StreamingEnsemble] = StreamingEnsemble(
                n_features=self.n_features,
                n_classes=self.n_classes,
                n_estimators=self.n_estimators,
                grace_period=self.grace_period,
                delta=self.delta,
                random_state=self.random_state,
            )
        else:
            self._model = VectorizedHoeffdingTree(
                n_features=self.n_features,
                n_classes=self.n_classes,
                grace_period=self.grace_period,
                delta=self.delta,
                tau_tie=self.tau_tie,
            )

        self._drift_detector: Optional[ReliabilityWeightedADWIN] = (
            ReliabilityWeightedADWIN(delta=0.002) if self.enable_drift_detection else None
        )

        self._replay_buffer: Optional[ClassBalancedReservoirReplay] = (
            ClassBalancedReservoirReplay(
                capacity=self.replay_capacity,
                n_classes=self.n_classes,
                random_state=self.random_state,
            )
            if self.replay_capacity > 0
            else None
        )

        self.drift_count_: int = 0
        self.samples_seen_: int = 0

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[Sequence[int]] = None,
    ) -> "AdaptiveClassifier":
        """Fit the model on initial batch data by calling partial_fit."""
        return self.partial_fit(X, y, classes=classes)

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[Sequence[int]] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "AdaptiveClassifier":
        """Incrementally update the streaming classifier with incoming batch."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=self.n_classes, name="y")
        w_val = check_sample_weights(sample_weight, expected_len=n_samples, name="sample_weight")
        if w_val is None:
            w_val = np.ones(n_samples, dtype=np.float64)

        # 1. Evaluate drift before updating model if drift detector enabled
        if self._drift_detector is not None and self.samples_seen_ > 0:
            preds = self.predict(X_val)
            errors = (preds != y_val).astype(np.float64)

            for i in range(n_samples):
                drift_detected = self._drift_detector.update(errors[i], reliability=w_val[i])
                if drift_detected:
                    self.drift_count_ += 1

        # 2. Replay buffer ingestion & augmentation
        X_train = X_val
        y_train = y_val
        w_train = w_val

        if self._replay_buffer is not None:
            X_train, y_train = self._replay_buffer.update_and_sample(
                X_val, y_val, replay_ratio=self.replay_ratio
            )
            if X_train.shape[0] > n_samples:
                n_replay = X_train.shape[0] - n_samples
                w_rep = np.ones(n_replay, dtype=np.float64)
                w_train = np.concatenate([w_val, w_rep])

        # 3. Model parameter update
        self._model.partial_fit(X_train, y_train, sample_weight=w_train)
        self.samples_seen_ += n_samples
        return self

    def predict(self, X: np.ndarray) -> IntArray1D:
        """Predict class labels for input instances."""
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> FloatArray2D:
        """Predict class posterior probabilities."""
        return self._model.predict_proba(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return the mean accuracy on given test data and labels."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")
        preds = self.predict(X_val)
        return float(np.mean(preds == y_val))

    def reset(self) -> None:
        """Reset classifier state completely."""
        self._init_components()

    def state_dict(self) -> Dict[str, Any]:
        """Serialize complete adaptive classifier state."""
        state = {
            "n_features": self.n_features,
            "n_classes": self.n_classes,
            "grace_period": self.grace_period,
            "delta": self.delta,
            "tau_tie": self.tau_tie,
            "enable_drift_detection": self.enable_drift_detection,
            "replay_capacity": self.replay_capacity,
            "replay_ratio": self.replay_ratio,
            "n_estimators": self.n_estimators,
            "drift_count_": self.drift_count_,
            "samples_seen_": self.samples_seen_,
            "model_state": self._model.state_dict() if hasattr(self._model, "state_dict") else None,
            "drift_state": self._drift_detector.state_dict() if self._drift_detector is not None else None,
            "replay_state": self._replay_buffer.state_dict() if self._replay_buffer is not None else None,
        }
        return state

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore classifier state."""
        self.n_features = int(state["n_features"])
        self.n_classes = int(state["n_classes"])
        self.grace_period = int(state["grace_period"])
        self.delta = float(state["delta"])
        self.tau_tie = float(state["tau_tie"])
        self.enable_drift_detection = bool(state["enable_drift_detection"])
        self.replay_capacity = int(state["replay_capacity"])
        self.replay_ratio = float(state["replay_ratio"])
        self.n_estimators = int(state["n_estimators"])
        self.drift_count_ = int(state["drift_count_"])
        self.samples_seen_ = int(state["samples_seen_"])

        if state["model_state"] is not None and hasattr(self._model, "load_state_dict"):
            self._model.load_state_dict(state["model_state"])
        if state["drift_state"] is not None and self._drift_detector is not None:
            self._drift_detector.load_state_dict(state["drift_state"])
        if state["replay_state"] is not None and self._replay_buffer is not None:
            self._replay_buffer.load_state_dict(state["replay_state"])
