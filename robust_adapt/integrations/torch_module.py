"""PyTorch Neural Network Integration Modules for AdaptiveML.

Provides native PyTorch nn.Module loss functions and model wrappers.
"""

from __future__ import annotations

from typing import Optional
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore[assignment]
    nn = object  # type: ignore[assignment,misc]
    F = None  # type: ignore[assignment]


class TorchSymmetricCrossEntropyLoss(nn.Module if _TORCH_AVAILABLE else object):
    """PyTorch native implementation of Symmetric Cross-Entropy Loss (Wang et al., ICCV 2019).

    Combines standard Cross-Entropy (sensitive to easy noise-free learning)
    with Reverse Cross-Entropy (strictly bounded gradient against corrupted labels):
        L_SCE = alpha * L_CE + beta * L_RCE

    Parameters
    ----------
    alpha : float, default=1.0
        Weight of standard cross-entropy loss.
    beta : float, default=0.5
        Weight of reverse cross-entropy loss.
    eps : float, default=1e-7
        Numerical safety epsilon guard.
    """

    def __init__(self, alpha: float = 1.0, beta: float = 0.5, eps: float = 1e-7) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to use TorchSymmetricCrossEntropyLoss.")
        super().__init__()
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.eps = float(eps)

    def forward(
        self,
        logits: "torch.Tensor",
        targets: "torch.Tensor",
        sample_weights: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """Compute SCE loss over model logits and target labels.

        Args:
            logits: Output tensor of shape (batch_size, n_classes).
            targets: LongTensor of shape (batch_size,) with ground-truth class indices.
            sample_weights: Optional 1D tensor of per-sample weights in [0, 1].

        Returns:
            Scalar loss tensor.
        """
        probs = F.softmax(logits, dim=-1)
        probs_clamped = torch.clamp(probs, min=self.eps, max=1.0)

        # 1. Standard Cross-Entropy: -log(p_y)
        ce_loss = F.cross_entropy(logits, targets, reduction="none")

        # 2. Reverse Cross-Entropy: - sum_c p_c * log(y_c + eps)
        batch_size, n_classes = logits.shape
        target_probs = probs_clamped[torch.arange(batch_size, device=logits.device), targets]
        rce_loss = - (1.0 - target_probs) * np.log(self.eps)

        loss_per_sample = self.alpha * ce_loss + self.beta * rce_loss

        if sample_weights is not None:
            loss_per_sample = loss_per_sample * sample_weights

        return torch.mean(loss_per_sample)


class TorchGeneralizedCrossEntropyLoss(nn.Module if _TORCH_AVAILABLE else object):
    """PyTorch native implementation of Generalized Cross-Entropy Loss (Zhang & Sabuncu, NeurIPS 2018).

    Bridges standard Cross-Entropy (q -> 0) and Mean Absolute Error (q = 1) via Box-Cox transformation:
        L_GCE = (1 - p_y^q) / q

    Parameters
    ----------
    q : float, default=0.7
        Noise-robustness hyperparameter in (0.0, 1.0].
    eps : float, default=1e-7
        Numerical stability epsilon.
    """

    def __init__(self, q: float = 0.7, eps: float = 1e-7) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to use TorchGeneralizedCrossEntropyLoss.")
        super().__init__()
        if not 0.0 < q <= 1.0:
            raise ValueError(f"q must be in (0.0, 1.0], got {q}")
        self.q = float(q)
        self.eps = float(eps)

    def forward(
        self,
        logits: "torch.Tensor",
        targets: "torch.Tensor",
        sample_weights: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """Compute GCE loss over model logits and target labels."""
        probs = F.softmax(logits, dim=-1)
        probs_clamped = torch.clamp(probs, min=self.eps, max=1.0)

        batch_size = logits.shape[0]
        p_y = probs_clamped[torch.arange(batch_size, device=logits.device), targets]

        loss_per_sample = (1.0 - torch.pow(p_y, self.q)) / self.q

        if sample_weights is not None:
            loss_per_sample = loss_per_sample * sample_weights

        return torch.mean(loss_per_sample)
