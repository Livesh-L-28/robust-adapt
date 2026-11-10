"""Robust loss functions: Symmetric Cross Entropy (SCE) and Generalized Cross Entropy (GCE).

Mathematical formulations and analytical gradients specified in DOC-DES-P6-004 and DOC-DES-P6-009 (Algorithm 6).
"""

from typing import Any, Optional, Tuple
import numpy as np
from robust_adapt.core.constants import EPS_CLIP_RCE, EPS_DIV, EPS_LOG
from robust_adapt.core.exceptions import ValidationError
from robust_adapt.core.types import FloatArray1D, FloatArray2D, IntArray1D
from robust_adapt.core.validation import check_array_2d, check_labels_1d, check_sample_weights

# Optional PyTorch Module integration deferred until accessed
_TORCH_AVAILABLE: Optional[bool] = None


def _is_torch_available() -> bool:
    global _TORCH_AVAILABLE
    if _TORCH_AVAILABLE is None:
        try:
            import torch  # noqa: F401
            _TORCH_AVAILABLE = True
        except ImportError:
            _TORCH_AVAILABLE = False
    return _TORCH_AVAILABLE


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


class FocalLoss:
    """Focal Loss for addressing class imbalance and modulating hard noisy examples.

    Formula:
        L_FL(p_t) = -alpha * (1 - p_t)^gamma * ln(p_t)

    Parameters
    ----------
    alpha : float, default=1.0
        Weight factor.
    gamma : float, default=2.0
        Focusing parameter modulating relative loss for easy vs hard examples.
    """

    def __init__(self, alpha: float = 1.0, gamma: float = 2.0) -> None:
        if alpha <= 0.0:
            raise ValidationError(f"alpha must be positive, got {alpha}")
        if gamma < 0.0:
            raise ValidationError(f"gamma must be non-negative, got {gamma}")
        self.alpha = float(alpha)
        self.gamma = float(gamma)

    def forward(
        self,
        logits: np.ndarray,
        y: np.ndarray,
        sample_weights: Optional[np.ndarray] = None,
    ) -> Tuple[float, FloatArray2D]:
        """Compute Focal Loss and analytical logit gradients."""
        logits_val = check_array_2d(logits, name="logits")
        n_samples, n_classes = logits_val.shape
        y_val = check_labels_1d(y, expected_len=n_samples, n_classes=n_classes, name="y")
        w_val = check_sample_weights(sample_weights, expected_len=n_samples, name="sample_weights")

        probs = _softmax(logits_val)
        p_y = probs[np.arange(n_samples), y_val]
        p_y_safe = np.clip(p_y, EPS_LOG, 1.0 - EPS_LOG)

        # L = -alpha * (1 - p_y)^gamma * ln(p_y)
        focal_weight = (1.0 - p_y_safe) ** self.gamma
        loss_per_sample = self.alpha * focal_weight * (-np.log(p_y_safe))

        if w_val is not None:
            w_sum = float(np.sum(w_val)) + EPS_DIV
            total_loss = float(np.sum(w_val * loss_per_sample) / w_sum)
            norm_weights = (w_val / w_sum)[:, np.newaxis]
        else:
            total_loss = float(np.mean(loss_per_sample))
            norm_weights = (1.0 / n_samples) * np.ones((n_samples, 1), dtype=np.float64)

        # Analytical gradient dL/dz_k = alpha * (1 - p_y)^(gamma-1) * [(1 - p_y) - gamma * p_y * ln(p_y)] * (p_k - I(k=y))
        Y_one_hot = np.zeros((n_samples, n_classes), dtype=np.float64)
        Y_one_hot[np.arange(n_samples), y_val] = 1.0

        if self.gamma == 0.0:
            scale_factor = np.ones((n_samples, 1), dtype=np.float64)
        else:
            bracket = (1.0 - p_y_safe) - self.gamma * p_y_safe * np.log(p_y_safe)
            scale = self.alpha * ((1.0 - p_y_safe) ** (self.gamma - 1.0)) * bracket
            scale_factor = scale[:, np.newaxis]

        grad_logits = norm_weights * scale_factor * (probs - Y_one_hot)
        return total_loss, np.ascontiguousarray(grad_logits, dtype=np.float64)


class ReliabilityWeightedLoss:
    """Wraps any base loss function to dynamically scale sample penalties by reliability scores r_i in [0, 1].

    Parameters
    ----------
    base_loss : Any
        Base loss instance implementing forward(logits, y, sample_weights=None).
    min_reliability : float, default=0.0
        Threshold below which samples have zero gradient impact.
    """

    def __init__(self, base_loss: Any, min_reliability: float = 0.0) -> None:
        self.base_loss = base_loss
        self.min_reliability = float(min_reliability)

    def forward(
        self,
        logits: np.ndarray,
        y: np.ndarray,
        reliabilities: np.ndarray,
    ) -> Tuple[float, FloatArray2D]:
        """Compute reliability-weighted loss and gradients."""
        r = np.asarray(reliabilities, dtype=np.float64)
        # Zero out samples below min_reliability
        eff_weights = np.where(r >= self.min_reliability, r, 0.0)
        return self.base_loss.forward(logits, y, sample_weights=eff_weights)


def __getattr__(name: str) -> Any:
    if name == "TorchFocalLoss":
        if not _is_torch_available():
            raise ImportError("TorchFocalLoss requires PyTorch to be installed.")
        import torch
        import torch.nn as nn
        import torch.nn.functional as F

        class TorchFocalLoss(nn.Module):
            """PyTorch Module implementation of Focal Loss."""

            def __init__(self, alpha: float = 1.0, gamma: float = 2.0) -> None:
                super().__init__()
                self.alpha = float(alpha)
                self.gamma = float(gamma)

            def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
                ce_loss = F.cross_entropy(logits, targets, reduction="none")
                p_t = torch.exp(-ce_loss)
                focal_loss = self.alpha * ((1.0 - p_t) ** self.gamma) * ce_loss
                return focal_loss.mean()

        return TorchFocalLoss
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
