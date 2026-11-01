"""Robust loss functions: Symmetric Cross Entropy (SCE) and Generalized Cross Entropy (GCE).

Mathematical formulations and analytical gradients specified in DOC-DES-P6-004 and DOC-DES-P6-009 (Algorithm 6).
"""

from typing import Optional, Tuple
import numpy as np
from adaptive_ml.core.constants import EPS_CLIP_RCE, EPS_DIV, EPS_LOG
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray1D, FloatArray2D, IntArray1D
from adaptive_ml.core.validation import check_array_2d, check_labels_1d, check_sample_weights

# Optional PyTorch Module integration
try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    nn = object  # type: ignore[assignment,misc]
    _TORCH_AVAILABLE = False


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    max_z = np.max(logits, axis=1, keepdims=True)
    exp_z = np.exp(logits - max_z)
    return exp_z / (np.sum(exp_z, axis=1, keepdims=True) + EPS_DIV)


class SymmetricCrossEntropyLoss:
    """Symmetric Cross Entropy (SCE) combining Cross Entropy (CE) and Reverse Cross Entropy (RCE).

    Bounds gradient distortion under symmetric and asymmetric label corruption.

    Parameters
    ----------
    alpha : float, default=1.0
        Weight factor for standard Cross Entropy term.
    beta : float, default=0.5
        Weight factor for bounded Reverse Cross Entropy term.
    eps_clip : float, default=1e-4
        Clipping constant for Reverse Cross Entropy bounding.
    """

    def __init__(self, alpha: float = 1.0, beta: float = 0.5, eps_clip: float = EPS_CLIP_RCE) -> None:
        if alpha < 0.0 or beta < 0.0:
            raise ValidationError(f"alpha and beta must be non-negative, got alpha={alpha}, beta={beta}")
        if eps_clip <= 0.0 or eps_clip >= 1.0:
            raise ValidationError(f"eps_clip must be in (0, 1), got {eps_clip}")

        self.alpha = float(alpha)
        self.beta = float(beta)
        self.eps_clip = float(eps_clip)
        self._log_eps = abs(float(np.log(self.eps_clip)))

    def forward(
        self,
        logits: np.ndarray,
        y: np.ndarray,
        sample_weights: Optional[np.ndarray] = None,
    ) -> Tuple[float, FloatArray2D]:
        """Compute forward loss value and analytical logit gradients.

        Parameters
        ----------
        logits : np.ndarray of shape (n_samples, n_classes)
            Unnormalized model logits.
        y : np.ndarray of shape (n_samples,)
            Target class labels.
        sample_weights : Optional[np.ndarray], default=None
            Per-sample importance or reliability weights.

        Returns
        -------
        loss : float
            Scalar batch loss.
        grad_logits : FloatArray2D of shape (n_samples, n_classes)
            Analytical gradients dL/dz.
        """
        logits_val = check_array_2d(logits, name="logits")
        n_samples, n_classes = logits_val.shape
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=n_classes, name="y")
        w_val = check_sample_weights(sample_weights, expected_len=n_samples, name="sample_weights")

        probs = _softmax(logits_val)
        p_y = probs[np.arange(n_samples), y_val]

        # 1. Cross Entropy term: -ln(p_y)
        loss_ce = -np.log(np.maximum(p_y, EPS_LOG))

        # 2. Reverse Cross Entropy term: |ln(eps_clip)| * (1 - p_y)
        loss_rce = self._log_eps * (1.0 - p_y)

        # Composite per-sample loss
        loss_per_sample = self.alpha * loss_ce + self.beta * loss_rce

        if w_val is not None:
            w_sum = float(np.sum(w_val)) + EPS_DIV
            total_loss = float(np.sum(w_val * loss_per_sample) / w_sum)
            norm_weights = (w_val / w_sum)[:, np.newaxis]
        else:
            total_loss = float(np.mean(loss_per_sample))
            norm_weights = (1.0 / n_samples) * np.ones((n_samples, 1), dtype=np.float64)

        # Analytical Logit Gradients:
        # dL_ce / dz_k = p_k - I(k=y)
        # dL_rce / dz_k = |log_eps| * p_k * (p_y - I(k=y))
        Y_one_hot = np.zeros((n_samples, n_classes), dtype=np.float64)
        Y_one_hot[np.arange(n_samples), y_val] = 1.0

        grad_ce = probs - Y_one_hot
        grad_rce = self._log_eps * probs * (p_y[:, np.newaxis] - Y_one_hot)

        grad_logits = norm_weights * (self.alpha * grad_ce + self.beta * grad_rce)

        return total_loss, np.ascontiguousarray(grad_logits, dtype=np.float64)


class GeneralizedCrossEntropyLoss:
    """Generalized Cross Entropy (GCE) loss based on Box-Cox power transformation.

    Parameters
    ----------
    q : float, default=0.7
        Noise robustness parameter in (0, 1]. When q->0, approaches Cross Entropy;
        when q=1, equals Mean Absolute Error.
    """

    def __init__(self, q: float = 0.7) -> None:
        if q <= 0.0 or q > 1.0:
            raise ValidationError(f"q must be in (0, 1], got {q}")
        self.q = float(q)

    def forward(
        self,
        logits: np.ndarray,
        y: np.ndarray,
        sample_weights: Optional[np.ndarray] = None,
    ) -> Tuple[float, FloatArray2D]:
        """Compute GCE loss and analytical logit gradients."""
        logits_val = check_array_2d(logits, name="logits")
        n_samples, n_classes = logits_val.shape
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=n_classes, name="y")
        w_val = check_sample_weights(sample_weights, expected_len=n_samples, name="sample_weights")

        probs = _softmax(logits_val)
        p_y = probs[np.arange(n_samples), y_val]

        # GCE: (1 - p_y^q) / q
        p_y_safe = np.maximum(p_y, EPS_LOG)
        loss_per_sample = (1.0 - (p_y_safe ** self.q)) / self.q

        if w_val is not None:
            w_sum = float(np.sum(w_val)) + EPS_DIV
            total_loss = float(np.sum(w_val * loss_per_sample) / w_sum)
            norm_weights = (w_val / w_sum)[:, np.newaxis]
        else:
            total_loss = float(np.mean(loss_per_sample))
            norm_weights = (1.0 / n_samples) * np.ones((n_samples, 1), dtype=np.float64)

        # Analytical gradient: p_y^q * (p_k - I(k=y))
        Y_one_hot = np.zeros((n_samples, n_classes), dtype=np.float64)
        Y_one_hot[np.arange(n_samples), y_val] = 1.0

        scale_factor = (p_y_safe ** self.q)[:, np.newaxis]
        grad_logits = norm_weights * scale_factor * (probs - Y_one_hot)

        return total_loss, np.ascontiguousarray(grad_logits, dtype=np.float64)

