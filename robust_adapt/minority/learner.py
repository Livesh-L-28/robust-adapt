"""
Turnkey Adaptive Minority Intelligence 2.0 Streaming Learner.

Integrates:
1. Online Beta-Binomial Prior Tracking
2. Sublinear Power-Law Cost Scaling (w_min = (1/prior)^power)
3. Discrete-Time PID Dynamic False-Positive Budget Threshold Controller
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d
from robust_adapt.minority.prior import BetaBinomialPriorTracker
from robust_adapt.minority.threshold import DynamicFPBudgetThresholdManager, compute_sublinear_cost_weights


class MinorityIntelligence20Learner:
    """Adaptive Minority Intelligence 2.0 Streaming Classifier.

    Maximizes minority class recall while strictly capping false alarm rates under an
    operator-defined enterprise budget via sublinear cost scaling and PID threshold control.

    Parameters
    ----------
    target_fp_budget_per_1k : float, default=1.5
        Target false positive alerts per 1,000 instances.
    sublinear_cost_power : float, default=0.52
        Power parameter gamma for sublinear cost scaling: w = (1 / prior)^gamma.
    base_threshold : float, default=0.50
        Initial decision boundary threshold.
    min_threshold : float, default=0.15
        Minimum decision threshold.
    max_threshold : float, default=0.85
        Maximum decision threshold.
    lr : float, default=0.01
        Learning rate for online SGD updates.
    minority_class : int, default=1
        Target index of the minority class.
    random_state : Optional[int], default=42
        Random seed for parameter initialization.
    """

    def __init__(
        self,
        target_fp_budget_per_1k: float = 1.5,
        sublinear_cost_power: float = 0.52,
        base_threshold: float = 0.50,
        min_threshold: float = 0.15,
        max_threshold: float = 0.85,
        lr: float = 0.01,
        minority_class: int = 1,
        random_state: Optional[int] = 42,
    ) -> None:
        if target_fp_budget_per_1k <= 0.0:
            raise ConfigurationError(f"target_fp_budget_per_1k must be positive, got {target_fp_budget_per_1k}")
        if not 0.0 < sublinear_cost_power <= 1.0:
            raise ConfigurationError(f"sublinear_cost_power must be in (0, 1], got {sublinear_cost_power}")
        if lr <= 0.0:
            raise ConfigurationError(f"lr must be positive, got {lr}")

        self.target_fp_budget_per_1k = float(target_fp_budget_per_1k)
        self.sublinear_cost_power = float(sublinear_cost_power)
        self.lr = float(lr)
        self.minority_class = int(minority_class)
        self.random_state = random_state

        self.prior_tracker = BetaBinomialPriorTracker(minority_class=minority_class)
        self.threshold_mgr = DynamicFPBudgetThresholdManager(
            target_fp_budget_per_1k=target_fp_budget_per_1k,
            base_threshold=base_threshold,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
        )

        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.total_samples_seen: int = 0
        self.total_batches_seen: int = 0

    def fit_batch(self, X_batch: np.ndarray, y_batch: np.ndarray) -> Dict[str, Any]:
        """Processes an incoming streaming batch with sublinear cost weighting and PID threshold adjustment."""
        X_val = check_array_2d(X_batch, name="X_batch")
        n_samples, n_features = X_val.shape
        y_val = check_labels_1d(y_batch, expected_len=n_samples, n_classes=2, name="y_batch")

        # Initialize weights if first batch
        if self.weights is None:
            rng = np.random.RandomState(self.random_state)
            self.weights = rng.normal(0.0, 0.01, size=n_features)
            self.bias = 0.0

        self.total_samples_seen += n_samples
        self.total_batches_seen += 1

        # 1. Update online Bayesian prior
        current_prior = self.prior_tracker.update(y_val)

        # 2. Derive sublinear cost weight for minority class
        w_min = compute_sublinear_cost_weights(current_prior, power=self.sublinear_cost_power)
        sample_weights = np.where(y_val == self.minority_class, w_min, 1.0)

        # 3. Prequential prediction & threshold control step
        pos_probs = self.predict_proba(X_val)[:, 1]
        active_threshold = self.threshold_mgr.step(y_val, pos_probs)

        # 4. Online weighted logistic SGD step
        logits = np.dot(X_val, self.weights) + self.bias
        p = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))

        grad_logits = (p - y_val) * sample_weights
        grad_w = np.dot(X_val.T, grad_logits) / n_samples
        grad_b = float(np.sum(grad_logits) / n_samples)

        self.weights -= self.lr * grad_w
        self.bias -= self.lr * grad_b

        return {
            "step": self.total_batches_seen,
            "total_samples": self.total_samples_seen,
            "prior": current_prior,
            "minority_weight": w_min,
            "active_threshold": active_threshold,
        }

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict binary posterior probabilities."""
        X_val = check_array_2d(X, name="X")
        if self.weights is None:
            # Unfitted fallback: uniform 0.5
            n = X_val.shape[0]
            return np.full((n, 2), 0.5)

        logits = np.dot(X_val, self.weights) + self.bias
        p1 = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict discrete binary labels according to dynamic PID threshold."""
        pos_probs = self.predict_proba(X)[:, 1]
        return self.threshold_mgr.predict(pos_probs)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute classification accuracy."""
        preds = self.predict(X)
        y_val = check_labels_1d(y, expected_len=len(preds), n_classes=2, name="y")
        return float(np.mean(preds == y_val))

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "MinorityIntelligence20Learner":
        """Incremental scikit-learn compatible fit."""
        self.fit_batch(X, y)
        return self

    def state_dict(self) -> Dict[str, Any]:
        """Serialize complete learner state."""
        return {
            "target_fp_budget_per_1k": self.target_fp_budget_per_1k,
            "sublinear_cost_power": self.sublinear_cost_power,
            "lr": self.lr,
            "minority_class": self.minority_class,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
            "total_samples_seen": self.total_samples_seen,
            "total_batches_seen": self.total_batches_seen,
            "prior_tracker": self.prior_tracker.state_dict(),
            "threshold_mgr": self.threshold_mgr.state_dict(),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore complete learner state."""
        self.target_fp_budget_per_1k = float(state["target_fp_budget_per_1k"])
        self.sublinear_cost_power = float(state["sublinear_cost_power"])
        self.lr = float(state["lr"])
        self.minority_class = int(state["minority_class"])
        self.weights = np.array(state["weights"], dtype=np.float64) if state["weights"] is not None else None
        self.bias = float(state["bias"])
        self.total_samples_seen = int(state["total_samples_seen"])
        self.total_batches_seen = int(state["total_batches_seen"])
        self.prior_tracker.load_state_dict(state["prior_tracker"])
        self.threshold_mgr.load_state_dict(state["threshold_mgr"])
