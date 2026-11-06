"""Class-Aware Probability Calibration and Temperature Scaling.

Mathematical formulation:
    P(y = c \\mid x) = \\frac{\\exp(z_c / T_c)}{\\sum_{j=1}^K \\exp(z_j / T_j)}

Where T_c > 0 are class-specific temperatures optimized via Negative Log-Likelihood (NLL)
on streaming validation buffers. Includes Expected Calibration Error (ECE) and Brier scoring.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_labels_1d


class ClassAwareCalibrator:
    """Performs online probability calibration and temperature scaling for streaming classifiers.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    lr : float, default=0.05
        Learning rate for online gradient descent on temperature parameters.
    max_iter : int, default=50
        Maximum optimization steps per validation update.
    min_temp : float, default=0.1
        Minimum allowable temperature bound.
    max_temp : float, default=10.0
        Maximum allowable temperature bound.
    """

    def __init__(
        self,
        n_classes: int = 2,
        lr: float = 0.05,
        max_iter: int = 50,
        min_temp: float = 0.1,
        max_temp: float = 10.0,
    ) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if lr <= 0.0:
            raise ConfigurationError(f"lr must be positive, got {lr}")
        if max_iter < 1:
            raise ConfigurationError(f"max_iter must be >= 1, got {max_iter}")
        if min_temp >= max_temp or min_temp <= 0.0:
            raise ConfigurationError(f"Invalid temperature bounds: [{min_temp}, {max_temp}]")

        self.n_classes = int(n_classes)
        self.lr = float(lr)
        self.max_iter = int(max_iter)
        self.min_temp = float(min_temp)
        self.max_temp = float(max_temp)

        # Class-specific temperatures initialized to 1.0 (uncalibrated identity)
        self._temperatures: np.ndarray = np.ones(self.n_classes, dtype=np.float64)

    @property
    def temperatures(self) -> np.ndarray:
        """Current learned temperature vector of shape (n_classes,)."""
        return self._temperatures.copy()

    def fit_validation(
        self,
        val_logits_or_probas: np.ndarray,
        val_labels: np.ndarray,
        is_logit: bool = False,
    ) -> "ClassAwareCalibrator":
        """Optimize class-specific temperatures on validation instances.

        Parameters
        ----------
        val_logits_or_probas : np.ndarray
            Predicted probabilities or raw logits of shape (n_val, n_classes) or (n_val,).
        val_labels : np.ndarray
            True ground-truth integer labels of shape (n_val,).
        is_logit : bool, default=False
            Whether input represents raw unscaled logits. If False, inputs are treated
            as predicted probabilities and converted to log-scale.

        Returns
        -------
        ClassAwareCalibrator
            Self instance with optimized temperatures.
        """
        labels = check_labels_1d(val_labels, name="val_labels")
        n_samples = labels.shape[0]
        if n_samples == 0:
            return self

        # Format input to (N, K) logits
        raw = np.asarray(val_logits_or_probas, dtype=np.float64)
        if self.n_classes == 2 and raw.ndim == 1:
            p1 = np.clip(raw, 1e-7, 1.0 - 1e-7)
            z = np.column_stack([np.log(1.0 - p1), np.log(p1)])
        elif is_logit:
            z = raw
        else:
            p = np.clip(raw, 1e-7, 1.0)
            z = np.log(p)

        # One-hot labels
        y_onehot = np.zeros((n_samples, self.n_classes), dtype=np.float64)
        y_onehot[np.arange(n_samples), labels] = 1.0

        # Gradient descent optimization on log(temperature) to enforce positivity
        log_t = np.log(self._temperatures)

        for _ in range(self.max_iter):
            t = np.exp(log_t)
            # Scaled logits
            scaled_z = z / t
            # Stable softmax
            max_z = np.max(scaled_z, axis=1, keepdims=True)
            exp_z = np.exp(scaled_z - max_z)
            probs = exp_z / np.sum(exp_z, axis=1, keepdims=True)

            # Gradient w.r.t. log_t_c: (p_c - y_c) * (-z_c / t_c)
            # dNLL / d(log T_c) = (1 / N) * sum_i (probs_{i, c} - y_{i, c}) * (-z_{i, c} / T_c)
            diff = probs - y_onehot
            grad_log_t = np.mean(diff * (-scaled_z), axis=0)

            # Gradient step
            log_t -= self.lr * grad_log_t
            # Project bounds
            log_t = np.clip(log_t, np.log(self.min_temp), np.log(self.max_temp))

        self._temperatures = np.exp(log_t)
        return self

    def calibrate(
        self,
        logits_or_probas: np.ndarray,
        is_logit: bool = False,
    ) -> np.ndarray:
        """Apply temperature scaling to predict calibrated posterior probabilities.

        Parameters
        ----------
        logits_or_probas : np.ndarray
            Input array of shape (N, n_classes) or (N,).
        is_logit : bool, default=False
            Whether inputs are raw logits or probabilities.

        Returns
        -------
        np.ndarray
            Calibrated probabilities of shape (N, n_classes).
        """
        raw = np.asarray(logits_or_probas, dtype=np.float64)
        if self.n_classes == 2 and raw.ndim == 1:
            p1 = np.clip(raw, 1e-7, 1.0 - 1e-7)
            z = np.column_stack([np.log(1.0 - p1), np.log(p1)])
        elif is_logit:
            z = raw
        else:
            p = np.clip(raw, 1e-7, 1.0)
            z = np.log(p)

        scaled_z = z / self._temperatures
        max_z = np.max(scaled_z, axis=1, keepdims=True)
        exp_z = np.exp(scaled_z - max_z)
        calibrated = exp_z / np.sum(exp_z, axis=1, keepdims=True)
        return calibrated

    def compute_ece(
        self,
        probas: np.ndarray,
        labels: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """Calculate the Expected Calibration Error (ECE).

        Parameters
        ----------
        probas : np.ndarray
            Predicted probabilities of shape (N, n_classes) or (N,).
        labels : np.ndarray
            Ground truth integer labels of shape (N,).
        n_bins : int, default=10
            Number of confidence bins.

        Returns
        -------
        float
            Expected Calibration Error in [0, 1].
        """
        p_arr = np.asarray(probas, dtype=np.float64)
        y_arr = check_labels_1d(labels, name="labels")
        n_samples = y_arr.shape[0]
        if n_samples == 0:
            return 0.0

        if p_arr.ndim == 1 and self.n_classes == 2:
            p_full = np.column_stack([1.0 - p_arr, p_arr])
        else:
            p_full = p_arr

        preds = np.argmax(p_full, axis=1)
        confs = np.max(p_full, axis=1)
        accuracies = (preds == y_arr).astype(np.float64)

        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0

        for b in range(n_bins):
            bin_lower = bin_boundaries[b]
            bin_upper = bin_boundaries[b + 1]

            in_bin = (confs > bin_lower) & (confs <= bin_upper) if b > 0 else (confs >= bin_lower) & (confs <= bin_upper)
            prop_in_bin = np.mean(in_bin)

            if prop_in_bin > 0:
                acc_in_bin = np.mean(accuracies[in_bin])
                conf_in_bin = np.mean(confs[in_bin])
                ece += np.abs(acc_in_bin - conf_in_bin) * prop_in_bin

        return float(ece)

    def compute_brier_score(
        self,
        probas: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """Compute the multi-class Brier score (mean squared calibration error)."""
        p_arr = np.asarray(probas, dtype=np.float64)
        y_arr = check_labels_1d(labels, name="labels")
        n_samples = y_arr.shape[0]
        if n_samples == 0:
            return 0.0

        if p_arr.ndim == 1 and self.n_classes == 2:
            p_full = np.column_stack([1.0 - p_arr, p_arr])
        else:
            p_full = p_arr

        y_onehot = np.zeros((n_samples, self.n_classes), dtype=np.float64)
        y_onehot[np.arange(n_samples), y_arr] = 1.0

        return float(np.mean(np.sum((p_full - y_onehot) ** 2, axis=1)))

    def state_dict(self) -> Dict[str, Any]:
        """Serialize calibrator state."""
        return {
            "n_classes": self.n_classes,
            "lr": self.lr,
            "max_iter": self.max_iter,
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "temperatures": self._temperatures.tolist(),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore calibrator state."""
        self.n_classes = int(state["n_classes"])
        self.lr = float(state["lr"])
        self.max_iter = int(state["max_iter"])
        self.min_temp = float(state["min_temp"])
        self.max_temp = float(state["max_temp"])
        self._temperatures = np.array(state["temperatures"], dtype=np.float64)
