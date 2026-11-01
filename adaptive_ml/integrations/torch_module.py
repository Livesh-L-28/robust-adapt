"""
PyTorch Neural Network Integration Modules for AdaptiveML.

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
    torch = None
    nn = object  # type: ignore
    F = None


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
        # For one-hot y: y_k = 1, y_j = 0 for j != k
        # RCE_i = - p_{i, y_i} * log(1) - sum_{j != y_i} p_{i, j} * log(eps)
        #       = - (1.0 - p_{i, y_i}) * log(eps)
        batch_size, n_classes = logits.shape
        target_probs = probs_clamped[torch.arange(batch_size, device=logits.device), targets]
        rce_loss = - (1.0 - target_probs) * np.log(self.eps)

        loss_per_sample = self.alpha * ce_loss + self.beta * rce_loss

        if sample_weights is not None:
            loss_per_sample = loss_per_sample * sample_weights

        return torch.mean(loss_per_sample)
