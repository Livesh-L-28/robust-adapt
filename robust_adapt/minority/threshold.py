"""Adaptive Decision Threshold Optimization and Calibration.

Mathematical formulation:
    \\tau_c(t) = \\text{clip}\\left( \\tau_0 \\cdot \\left(\\frac{\\hat{\\pi}_c(t)}{\\pi_0}\\right)^\\gamma, \\tau_{\\min}, \\tau_{\\max} \\right)

Under Bayes risk with misclassification cost matrix C:
    \\tau^* = \\frac{C_{FP} - C_{TN}}{(C_{FP} - C_{TN}) + (C_{FN} - C_{TP})}

Provides dynamic threshold tuning, cost-sensitive arbitration, validation-window
F-beta optimization, and automated rollback upon performance degradation.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d


class AdaptiveThresholdManager:
    """Manages adaptive decision thresholds for binary and multi-class classification under class shift.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    mode : str, default="dynamic"
        Optimization mode:
        - "fixed": Uses base_threshold without dynamic adjustment.
        - "dynamic": Adjusts thresholds based on exponential moving priors.
        - "cost_sensitive": Derives optimal threshold from misclassification cost matrix.
        - "pr_constrained": Optimizes F-beta or recall-constrained metric on validation windows.
    base_threshold : float, default=0.5
        Default baseline threshold tau_0 for balanced conditions.
    gamma : float, default=0.5
        Prior sensitivity exponent. Higher values lead to larger threshold shifts.
    tau_min : float, default=0.05
        Minimum allowable decision threshold.
    tau_max : float, default=0.95
        Maximum allowable decision threshold.
    cost_matrix : Optional[np.ndarray], default=None
        Cost matrix of shape (n_classes, n_classes) where entry [i, j] is the cost
        of predicting class j when true label is i.
    """

    def __init__(
        self,
        n_classes: int = 2,
        mode: str = "dynamic",
        base_threshold: float = 0.5,
        gamma: float = 0.5,
        tau_min: float = 0.05,
        tau_max: float = 0.95,
        cost_matrix: Optional[np.ndarray] = None,
    ) -> None:
        valid_modes = {"fixed", "dynamic", "cost_sensitive", "pr_constrained"}
        if mode not in valid_modes:
            raise ConfigurationError(f"mode must be one of {valid_modes}, got '{mode}'")
        if not 0.0 < base_threshold < 1.0:
            raise ConfigurationError(f"base_threshold must be in (0, 1), got {base_threshold}")
        if tau_min >= tau_max or tau_min <= 0.0 or tau_max >= 1.0:
            raise ConfigurationError(f"Invalid tau bounds: [{tau_min}, {tau_max}]")

        self.n_classes = int(n_classes)
        self.mode = mode
        self.base_threshold = float(base_threshold)
        self.gamma = float(gamma)
        self.tau_min = float(tau_min)
        self.tau_max = float(tau_max)

        # Baseline priors under balance: pi_0 = 1 / K
        self._pi_0 = 1.0 / self.n_classes

        # Active thresholds per class (for binary, threshold applies to positive class 1)
        self._thresholds: np.ndarray = np.full(self.n_classes, self.base_threshold, dtype=np.float64)
        self._previous_thresholds: Optional[np.ndarray] = None

        # Setup cost matrix
        if cost_matrix is not None:
            c_mat = np.asarray(cost_matrix, dtype=np.float64)
            if c_mat.shape != (self.n_classes, self.n_classes):
                raise ValidationError(f"cost_matrix shape must be {(self.n_classes, self.n_classes)}, got {c_mat.shape}")
            self.cost_matrix = c_mat
            if self.mode == "cost_sensitive":
                self._compute_cost_sensitive_threshold()
        else:
            # Default unit 0-1 loss matrix
            self.cost_matrix = np.ones((self.n_classes, self.n_classes), dtype=np.float64)
            np.fill_diagonal(self.cost_matrix, 0.0)

    @property
    def thresholds(self) -> np.ndarray:
        """Current operational decision thresholds per class."""
        return self._thresholds.copy()

    @property
    def primary_threshold(self) -> float:
        """Primary decision threshold (for binary class 1)."""
        return float(self._thresholds[1] if self.n_classes == 2 else self._thresholds[0])

    def _compute_cost_sensitive_threshold(self) -> None:
        """Derive theoretical Bayes-optimal decision threshold from cost matrix."""
        if self.n_classes == 2:
            # C[0, 1] is False Positive; C[1, 0] is False Negative; diagonal is 0
            c_fp = self.cost_matrix[0, 1]
            c_fn = self.cost_matrix[1, 0]
            if c_fp + c_fn > 0:
                tau_bayes = c_fp / (c_fp + c_fn)
                self._thresholds[1] = np.clip(tau_bayes, self.tau_min, self.tau_max)
                self._thresholds[0] = 1.0 - self._thresholds[1]

    def update_from_priors(self, priors: np.ndarray) -> np.ndarray:
        """Update decision thresholds based on current estimated class priors.

        Parameters
        ----------
        priors : np.ndarray
            Current prior probability vector of shape (n_classes,).

        Returns
        -------
        np.ndarray
            Updated decision thresholds.
        """
        priors_arr = np.asarray(priors, dtype=np.float64)
        if priors_arr.shape[0] != self.n_classes:
            raise ValidationError(f"priors length {priors_arr.shape[0]} != n_classes {self.n_classes}")

        # Checkpoint prior thresholds for potential rollback
        self._previous_thresholds = self._thresholds.copy()

        if self.mode == "fixed":
            return self.thresholds

        if self.mode == "cost_sensitive":
            # Bayes threshold scaled by prior odds: tau(t) = tau_bayes * (pi_0 / pi_1)^gamma
            if self.n_classes == 2:
                c_fp = self.cost_matrix[0, 1]
                c_fn = self.cost_matrix[1, 0]
                tau_star = c_fp / max(c_fp + c_fn, 1e-6)
                prior_ratio = priors_arr[1] / max(priors_arr[0], 1e-6)
                adjusted_tau = tau_star * (self._pi_0 / max(priors_arr[1], 1e-6)) ** self.gamma
                self._thresholds[1] = np.clip(adjusted_tau, self.tau_min, self.tau_max)
                self._thresholds[0] = 1.0 - self._thresholds[1]
            return self.thresholds

        if self.mode == "dynamic":
            for c in range(self.n_classes):
                ratio = priors_arr[c] / self._pi_0
                # When prior drops below balanced, threshold drops (raising sensitivity/recall)
                new_tau = self.base_threshold * (ratio ** self.gamma)
                self._thresholds[c] = np.clip(new_tau, self.tau_min, self.tau_max)
            return self.thresholds

        return self.thresholds

    def optimize_on_validation(
        self,
        val_probas: np.ndarray,
        val_labels: np.ndarray,
        metric: str = "f1",
        beta: float = 1.0,
        n_grid: int = 50,
    ) -> float:
        """Find the optimal decision threshold on a held-out validation batch.

        Parameters
        ----------
        val_probas : np.ndarray
            Predicted posterior probabilities of shape (n_val, n_classes) or (n_val,).
        val_labels : np.ndarray
            True ground-truth integer labels of shape (n_val,).
        metric : str, default="f1"
            Optimization target: "f1", "f_beta", "balanced_accuracy", or "cost".
        beta : float, default=1.0
            Weight of recall in F-beta score.
        n_grid : int, default=50
            Number of threshold candidates to evaluate.

        Returns
        -------
        best_threshold : float
            Optimal decision threshold for positive / minority class.
        """
        labels = check_labels_1d(val_labels, name="val_labels")
        n_samples = labels.shape[0]
        if n_samples == 0:
            return self.primary_threshold

        # For binary classification
        if self.n_classes == 2:
            if val_probas.ndim == 2:
                pos_probs = val_probas[:, 1]
            else:
                pos_probs = val_probas.ravel()

            grid = np.linspace(self.tau_min, self.tau_max, n_grid)
            best_score = -float("inf") if metric != "cost" else float("inf")
            best_tau = self.primary_threshold

            self._previous_thresholds = self._thresholds.copy()

            for tau in grid:
                preds = (pos_probs >= tau).astype(np.int64)
                tp = int(np.sum((preds == 1) & (labels == 1)))
                fp = int(np.sum((preds == 1) & (labels == 0)))
                fn = int(np.sum((preds == 0) & (labels == 1)))
                tn = int(np.sum((preds == 0) & (labels == 0)))

                if metric in ("f1", "f_beta"):
                    b2 = beta ** 2
                    denom = (1.0 + b2) * tp + b2 * fn + fp
                    score = ((1.0 + b2) * tp) / max(denom, 1e-8)
                    if score > best_score:
                        best_score = score
                        best_tau = tau

                elif metric == "balanced_accuracy":
                    rec0 = tn / max(tn + fp, 1)
                    rec1 = tp / max(tp + fn, 1)
                    score = 0.5 * (rec0 + rec1)
                    if score > best_score:
                        best_score = score
                        best_tau = tau

                elif metric == "cost":
                    total_cost = fp * self.cost_matrix[0, 1] + fn * self.cost_matrix[1, 0]
                    if total_cost < best_score:
                        best_score = total_cost
                        best_tau = tau

            self._thresholds[1] = best_tau
            self._thresholds[0] = 1.0 - best_tau
            return best_tau

        return self.primary_threshold

    def rollback(self) -> None:
        """Rollback thresholds to the state prior to the most recent update."""
        if self._previous_thresholds is not None:
            self._thresholds = self._previous_thresholds.copy()

    def predict(self, probas: np.ndarray) -> np.ndarray:
        """Apply active decision thresholds to convert probabilities to class predictions.

        Parameters
        ----------
        probas : np.ndarray
            Predicted probabilities of shape (n_samples, n_classes) or (n_samples,).

        Returns
        -------
        np.ndarray
            Class integer predictions of shape (n_samples,).
        """
        prob_arr = np.asarray(probas, dtype=np.float64)
        if self.n_classes == 2:
            if prob_arr.ndim == 2:
                pos_probs = prob_arr[:, 1]
            else:
                pos_probs = prob_arr.ravel()
            return (pos_probs >= self._thresholds[1]).astype(np.int64)
        else:
            # Multi-class: scale probabilities by inverted class threshold
            scaled = prob_arr / np.maximum(self._thresholds, 1e-6)
            return np.argmax(scaled, axis=1).astype(np.int64)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize threshold manager state."""
        return {
            "n_classes": self.n_classes,
            "mode": self.mode,
            "base_threshold": self.base_threshold,
            "gamma": self.gamma,
            "tau_min": self.tau_min,
            "tau_max": self.tau_max,
            "thresholds": self._thresholds.tolist(),
            "cost_matrix": self.cost_matrix.tolist(),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore threshold manager state."""
        self.n_classes = int(state["n_classes"])
        self.mode = str(state["mode"])
        self.base_threshold = float(state["base_threshold"])
        self.gamma = float(state["gamma"])
        self.tau_min = float(state["tau_min"])
        self.tau_max = float(state["tau_max"])
        self._thresholds = np.array(state["thresholds"], dtype=np.float64)
        self.cost_matrix = np.array(state["cost_matrix"], dtype=np.float64)


def compute_sublinear_cost_weights(prior: float, power: float = 0.52) -> float:
    """Computes sublinear inverse cost weight w_min = (1 / prior)^power.

    Avoids the gradient variance explosion and false-alarm catastrophe of linear inverse weighting.
    """
    if prior <= 0.0 or prior >= 1.0:
        return 1.0
    return float(np.power(1.0 / max(prior, 1e-6), float(power)))


class DynamicFPBudgetThresholdManager:
    """Discrete-time PID decision threshold manager maintaining false positive rates within a defined budget.

    Controls the binary decision threshold theta in [min_threshold, max_threshold] to regulate
    the streaming false positive rate around an operator-specified budget constraint
    (e.g. <= 1.5 false positives per 1,000 transactions).

    Parameters
    ----------
    target_fp_budget_per_1k : float, default=1.5
        Maximum acceptable false positive alerts per 1,000 incoming instances.
    base_threshold : float, default=0.50
        Initial baseline decision threshold theta_0.
    kp : float, default=0.50
        Proportional gain.
    ki : float, default=0.05
        Integral gain.
    kd : float, default=0.02
        Derivative gain.
    min_threshold : float, default=0.15
        Minimum allowable decision threshold.
    max_threshold : float, default=0.85
        Maximum allowable decision threshold.
    anti_windup_max : float, default=0.20
        Maximum integral accumulation ceiling preventing reset windup.
    deadband : float, default=0.0002
        Error deadband within which no threshold correction is applied.
    """

    def __init__(
        self,
        target_fp_budget_per_1k: float = 1.5,
        base_threshold: float = 0.50,
        kp: float = 0.50,
        ki: float = 0.05,
        kd: float = 0.02,
        min_threshold: float = 0.15,
        max_threshold: float = 0.85,
        anti_windup_max: float = 0.20,
        deadband: float = 0.0002,
    ) -> None:
        if target_fp_budget_per_1k <= 0.0:
            raise ConfigurationError(f"target_fp_budget_per_1k must be positive, got {target_fp_budget_per_1k}")
        if not 0.0 < base_threshold < 1.0:
            raise ConfigurationError(f"base_threshold must be in (0, 1), got {base_threshold}")
        if min_threshold >= max_threshold or min_threshold <= 0.0 or max_threshold >= 1.0:
            raise ConfigurationError(f"Invalid threshold bounds: [{min_threshold}, {max_threshold}]")

        self.target_fp_budget_per_1k = float(target_fp_budget_per_1k)
        self.target_fpr = float(target_fp_budget_per_1k / 1000.0)
        self.threshold = float(base_threshold)
        self.base_threshold = float(base_threshold)
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.min_threshold = float(min_threshold)
        self.max_threshold = float(max_threshold)
        self.anti_windup_max = float(anti_windup_max)
        self.deadband = float(deadband)

        self._integral_error: float = 0.0
        self._prev_error: float = 0.0
        self._step_count: int = 0
        self.history_thresholds: List[float] = [self.threshold]
        self.history_fpr: List[float] = []

    def step(self, y_batch: Optional[np.ndarray], pos_probas: np.ndarray) -> float:
        """Executes one PID control step given current batch labels and predicted positive probabilities.

        If y_batch is None (delayed feedback), the threshold remains unchanged.
        """
        self._step_count += 1
        p_arr = np.asarray(pos_probas, dtype=np.float64).ravel()

        if y_batch is None or len(y_batch) == 0:
            self.history_thresholds.append(self.threshold)
            return self.threshold

        y_arr = np.asarray(y_batch, dtype=np.int64).ravel()
        preds = (p_arr >= self.threshold).astype(np.int64)

        # Compute empirical False Positive Rate: FP / (FP + TN)
        neg_mask = (y_arr == 0)
        n_neg = int(np.sum(neg_mask))
        if n_neg == 0:
            self.history_thresholds.append(self.threshold)
            return self.threshold

        fp = int(np.sum((preds == 1) & neg_mask))
        batch_fpr = float(fp / n_neg)
        self.history_fpr.append(batch_fpr)

        error = batch_fpr - self.target_fpr

        # Apply deadband to prevent oscillation
        if abs(error) < self.deadband:
            error = 0.0

        # PID terms
        p_term = self.kp * error
        self._integral_error = float(np.clip(
            self._integral_error + error, -self.anti_windup_max, self.anti_windup_max
        ))
        i_term = self.ki * self._integral_error
        d_term = self.kd * (error - self._prev_error)
        self._prev_error = error

        adjustment = p_term + i_term + d_term
        self.threshold = float(np.clip(self.threshold + adjustment, self.min_threshold, self.max_threshold))
        self.history_thresholds.append(self.threshold)
        return self.threshold

    def predict(self, pos_probas: np.ndarray) -> np.ndarray:
        """Predict positive class (1) if posterior probability exceeds current threshold."""
        p_arr = np.asarray(pos_probas, dtype=np.float64).ravel()
        return (p_arr >= self.threshold).astype(np.int64)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize PID threshold manager state."""
        return {
            "target_fp_budget_per_1k": self.target_fp_budget_per_1k,
            "target_fpr": self.target_fpr,
            "threshold": self.threshold,
            "base_threshold": self.base_threshold,
            "kp": self.kp,
            "ki": self.ki,
            "kd": self.kd,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
            "anti_windup_max": self.anti_windup_max,
            "deadband": self.deadband,
            "integral_error": self._integral_error,
            "prev_error": self._prev_error,
            "step_count": self._step_count,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore PID threshold manager state."""
        self.target_fp_budget_per_1k = float(state["target_fp_budget_per_1k"])
        self.target_fpr = float(state["target_fpr"])
        self.threshold = float(state["threshold"])
        self.base_threshold = float(state["base_threshold"])
        self.kp = float(state["kp"])
        self.ki = float(state["ki"])
        self.kd = float(state["kd"])
        self.min_threshold = float(state["min_threshold"])
        self.max_threshold = float(state["max_threshold"])
        self.anti_windup_max = float(state["anti_windup_max"])
        self.deadband = float(state["deadband"])
        self._integral_error = float(state["integral_error"])
        self._prev_error = float(state["prev_error"])
        self._step_count = int(state["step_count"])
