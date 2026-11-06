"""AdaptiveClassifier: Scikit-learn compliant streaming classifier with integrated drift adaptation."""

from typing import Any, Dict, Optional, Sequence, Union
import copy
import numpy as np
from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.concept_memory import ConceptFingerprinter, RecurringConceptMemory
from robust_adapt.ala.ensemble import StreamingEnsemble
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.ala.tree import VectorizedHoeffdingTree
from robust_adapt.core.exceptions import ValidationError
from robust_adapt.core.types import FloatArray2D, IntArray1D
from robust_adapt.core.validation import check_array_2d, check_labels_1d, check_sample_weights

# Pure-Python scikit-learn protocol mixins (zero mandatory sklearn dependency)
class BaseEstimator:
    """Lightweight base estimator mixin supporting standard get_params and set_params."""

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get parameters for this estimator."""
        out = {}
        for key in ["n_features", "n_classes", "grace_period", "delta", "tau_tie",
                    "enable_drift_detection", "replay_capacity", "replay_ratio",
                    "n_estimators", "random_state"]:
            if hasattr(self, key):
                out[key] = getattr(self, key)
        return out

    def set_params(self, **params: Any) -> Any:
        """Set parameters for this estimator."""
        for key, value in params.items():
            setattr(self, key, value)
        return self


class ClassifierMixin:
    """Lightweight classifier mixin providing score and _estimator_type."""

    _estimator_type = "classifier"

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return the mean accuracy on the given test data and labels."""
        return float(np.mean(self.predict(X) == y))  # type: ignore[attr-defined]


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
        enable_concept_memory: bool = False,
        concept_memory_capacity: int = 5,
        concept_similarity_threshold: float = 0.82,
        adaptation_cooldown_steps: int = 5,
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
        self.enable_concept_memory = bool(enable_concept_memory)
        self.concept_memory_capacity = int(concept_memory_capacity)
        self.concept_similarity_threshold = float(concept_similarity_threshold)
        self.adaptation_cooldown_steps = int(adaptation_cooldown_steps)

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
        self.concept_restorations_: int = 0
        self.cooldown_remaining_: int = 0
        self.active_concept_id_: Optional[str] = None

        if self.enable_concept_memory:
            self._fingerprinter = ConceptFingerprinter(n_features=self.n_features, n_classes=self.n_classes)
            self._concept_memory = RecurringConceptMemory(
                max_concepts=self.concept_memory_capacity,
                similarity_threshold=self.concept_similarity_threshold,
            )
        else:
            self._fingerprinter = None  # type: ignore[assignment]
            self._concept_memory = None  # type: ignore[assignment]
        self.samples_seen_: int = 0

    @property
    def replay_buffer(self) -> Optional[ClassBalancedReservoirReplay]:
        """Public access to the underlying class-balanced reservoir replay buffer (DEF-006 canonical contract)."""
        return self._replay_buffer

    def purge_replay(
        self,
        policy: str = "selective",
        min_reliability: float = 0.0,
        keep_minority: bool = True,
    ) -> int:
        """Purge obsolete or low-reliability instances from the replay buffer (DEF-006 canonical contract).

        Parameters
        ----------
        policy : str, default="selective"
            Purge policy ("full", "selective", or "partial").
        min_reliability : float, default=0.0
            Minimum sample reliability threshold for retention.
        keep_minority : bool, default=True
            Whether to preserve minority class instances during purge.

        Returns
        -------
        int
            Number of instances purged from memory.
        """
        if self._replay_buffer is None:
            return 0
        return self._replay_buffer.purge(
            policy=policy,
            min_reliability=min_reliability,
            keep_minority=keep_minority,
        )

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
                    if self.enable_concept_memory and self._concept_memory is not None and self.cooldown_remaining_ == 0:
                        fp = self._fingerprinter.compute_fingerprint(X_val, y_val)
                        match_snap, sim = self._concept_memory.find_matching_concept(fp)
                        if match_snap is not None and sim >= self.concept_similarity_threshold:
                            self.concept_restorations_ += 1
                            self.active_concept_id_ = match_snap.concept_id
                            if hasattr(self._model, "load_state_dict") and match_snap.model_state is not None:
                                self._model.load_state_dict(match_snap.model_state)
                            self._concept_memory.update_concept(
                                match_snap.concept_id, fp, self._model.state_dict(), self.samples_seen_
                            )
                        else:
                            curr_fp = self._fingerprinter.compute_fingerprint(X_val, y_val)
                            model_state = self._model.state_dict() if hasattr(self._model, "state_dict") else None
                            new_snap = self._concept_memory.store_concept(curr_fp, model_state, self.samples_seen_)
                            self.active_concept_id_ = new_snap.concept_id if new_snap is not None else None
                            self._model = VectorizedHoeffdingTree(
                                n_features=self.n_features,
                                n_classes=self.n_classes,
                                grace_period=self.grace_period,
                                delta=self.delta,
                                tau_tie=self.tau_tie,
                            )
                        self.cooldown_remaining_ = self.adaptation_cooldown_steps

        if self.cooldown_remaining_ > 0:
            self.cooldown_remaining_ -= 1

        # 2. Replay buffer ingestion & augmentation
        X_train = X_val
        y_train = y_val
        w_train = w_val

        if self._replay_buffer is not None:
            X_train, y_train = self._replay_buffer.update_and_sample(
                X_val, y_val, replay_ratio=self.replay_ratio, sample_weight=w_val
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


class ALA30AdaptiveLearner:
    """ALA 3.0 Recurring-Concept Adaptive Streaming Learner.

    Coordinates Reliability-Weighted ADWIN drift detection with bounded Recurring Concept
    Memory and reservoir replay rehearsal, preventing catastrophic forgetting on cyclical
    or non-stationary data streams.

    Parameters
    ----------
    n_features : int
        Feature dimensionality of streaming instances.
    n_classes : int, default=2
        Number of distinct target classes.
    grace_period : int, default=50
        Instances per leaf node between Hoeffding split checks.
    delta : float, default=0.002
        ADWIN drift confidence parameter.
    max_concepts : int, default=5
        Maximum distinct historical concept snapshots retained in memory.
    similarity_threshold : float, default=0.82
        Minimum cosine similarity required to trigger historical concept restoration.
    cooldown_steps : int, default=5
        Number of steps to suppress drift intervention following adaptation.
    replay_capacity : int, default=1000
        Maximum size of the class-balanced reservoir replay buffer.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        grace_period: int = 50,
        delta: float = 0.002,
        max_concepts: int = 5,
        similarity_threshold: float = 0.82,
        cooldown_steps: int = 5,
        replay_capacity: int = 1000,
    ) -> None:
        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.grace_period = int(grace_period)
        self.delta = float(delta)
        self.cooldown_steps = int(cooldown_steps)

        self.classifier = AdaptiveClassifier(
            n_features=self.n_features,
            n_classes=self.n_classes,
            grace_period=self.grace_period,
            delta=self.delta,
        )
        self.adwin = ReliabilityWeightedADWIN(delta=self.delta)
        self.replay = ClassBalancedReservoirReplay(capacity=replay_capacity, n_classes=self.n_classes)
        self.fingerprinter = ConceptFingerprinter(n_features=self.n_features, n_classes=self.n_classes)
        self.memory = RecurringConceptMemory(
            max_concepts=max_concepts,
            similarity_threshold=similarity_threshold,
        )

        self.total_steps: int = 0
        self.drift_resets: int = 0
        self.recurring_restorations: int = 0
        self.cooldown_remaining: int = 0
        self.active_concept_id: Optional[str] = None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class posterior probabilities."""
        return self.classifier.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict target labels for input batch."""
        return np.argmax(self.predict_proba(X), axis=1)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate mean classification accuracy."""
        preds = self.predict(X)
        return float(np.mean(preds == y))

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "ALA30AdaptiveLearner":
        """Incremental scikit-learn compatible fit."""
        self.update(X, y)
        return self

    def update(self, X_b: np.ndarray, y_b: np.ndarray) -> Dict[str, Any]:
        """Prequential update step coordinating drift detection, concept restoration, and rehearsal.

        Returns
        -------
        Dict[str, Any]
            Structured telemetry containing action taken, matched concept, similarity, and accuracy.
        """
        self.total_steps += 1
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # 1. Prequential prediction evaluation
        probas = self.predict_proba(X_b)
        preds = np.argmax(probas, axis=1)
        errs = (preds != y_b).astype(float)
        batch_acc = 1.0 - float(np.mean(errs))

        # 2. Concept drift monitoring via ADWIN
        drift_detected = any(self.adwin.update(e) for e in errs)
        action_taken = "INCREMENTAL_UPDATE"
        matched_concept_id = None
        similarity_score = 0.0

        if drift_detected and self.cooldown_remaining == 0:
            fp = self.fingerprinter.compute_fingerprint(X_b, y_b)
            matching_snap, sim = self.memory.find_matching_concept(fp)
            similarity_score = sim

            if matching_snap is not None:
                # Recurring concept matched: RESTORE previous model state
                self.recurring_restorations += 1
                action_taken = f"RECURRING_RESTORE_{matching_snap.concept_id}"
                self.classifier = copy.deepcopy(matching_snap.model_state)
                self.active_concept_id = matching_snap.concept_id
                self.memory.update_concept(matching_snap.concept_id, fp, self.classifier, self.total_steps)
                matched_concept_id = matching_snap.concept_id
            else:
                # Novel concept: snapshot current model before reset
                curr_fp = self.fingerprinter.compute_fingerprint(X_b, y_b)
                if self.active_concept_id is not None:
                    self.memory.update_concept(self.active_concept_id, curr_fp, self.classifier, self.total_steps)
                else:
                    new_snap = self.memory.store_concept(curr_fp, self.classifier, self.total_steps)
                    self.active_concept_id = new_snap.concept_id if new_snap is not None else None

                # Reset classifier state and seed from replay
                self.drift_resets += 1
                action_taken = "NOVEL_CONCEPT_RESET"
                self.classifier = AdaptiveClassifier(
                    n_features=self.n_features,
                    n_classes=self.n_classes,
                    grace_period=self.grace_period,
                    delta=self.delta,
                )
                if self.replay.total_stored >= 100:
                    X_rep, y_rep = self.replay.sample(min(200, self.replay.total_stored))
                    self.classifier.partial_fit(X_rep, y_rep)

            self.cooldown_remaining = self.cooldown_steps
            self.adwin = ReliabilityWeightedADWIN(delta=self.delta)

        # 3. Model parameter learning and replay ingestion
        self.classifier.partial_fit(X_b, y_b)
        self.replay.add(X_b, y_b)

        return {
            "step": self.total_steps,
            "drift_detected": drift_detected,
            "action": action_taken,
            "matched_concept": matched_concept_id,
            "similarity": similarity_score,
            "batch_acc": batch_acc,
            "stored_concepts": len(self.memory.concepts),
        }

    def state_dict(self) -> Dict[str, Any]:
        """Serialize complete learner state."""
        return {
            "n_features": self.n_features,
            "n_classes": self.n_classes,
            "grace_period": self.grace_period,
            "delta": self.delta,
            "cooldown_steps": self.cooldown_steps,
            "total_steps": self.total_steps,
            "drift_resets": self.drift_resets,
            "recurring_restorations": self.recurring_restorations,
            "cooldown_remaining": self.cooldown_remaining,
            "active_concept_id": self.active_concept_id,
            "classifier_state": self.classifier.state_dict(),
            "adwin_state": self.adwin.state_dict(),
            "replay_state": self.replay.state_dict(),
            "memory_state": self.memory.to_dict(),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore complete learner state."""
        self.total_steps = int(state["total_steps"])
        self.drift_resets = int(state["drift_resets"])
        self.recurring_restorations = int(state["recurring_restorations"])
        self.cooldown_remaining = int(state["cooldown_remaining"])
        self.active_concept_id = state["active_concept_id"]
        if "classifier_state" in state:
            self.classifier.load_state_dict(state["classifier_state"])
        if "adwin_state" in state:
            self.adwin.load_state_dict(state["adwin_state"])
        if "replay_state" in state:
            self.replay.load_state_dict(state["replay_state"])
        if "memory_state" in state:
            self.memory = RecurringConceptMemory.from_dict(state["memory_state"])
