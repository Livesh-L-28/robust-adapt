"""
Integration tests for PyTorch framework compatibility.
"""

from __future__ import annotations

import numpy as np
import pytest

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from adaptive_ml.integrations.torch_module import TorchSymmetricCrossEntropyLoss
from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch is required")
class TestTorchIntegration:
    def test_torch_symmetric_cross_entropy_backward(self) -> None:
        """Verify forward and backward gradients of TorchSymmetricCrossEntropyLoss."""
        loss_fn = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.5)

        # Multi-class linear layer
        linear = nn.Linear(4, 3)
        x = torch.randn(10, 4)
        targets = torch.randint(0, 3, (10,), dtype=torch.long)

        logits = linear(x)
        loss = loss_fn(logits, targets)

        assert loss.ndim == 0
        assert not torch.isnan(loss)
        assert loss.item() > 0.0

        loss.backward()
        assert linear.weight.grad is not None
        assert not torch.isnan(linear.weight.grad).any()

    def test_torch_low_memory_adamw_training_loop(self) -> None:
        """Verify full PyTorch training loop convergence with LowMemoryAdamW."""
        torch.manual_seed(42)

        model = nn.Sequential(
            nn.Linear(6, 12),
            nn.ReLU(),
            nn.Linear(12, 2),
        )

        optimizer = create_torch_low_memory_adamw(model.parameters(), lr=0.02, block_size=64)
        criterion = nn.CrossEntropyLoss()

        X = torch.randn(64, 6)
        y = torch.randint(0, 2, (64,), dtype=torch.long)

        initial_loss = criterion(model(X), y).item()

        for epoch in range(30):
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

        final_loss = criterion(model(X), y).item()
        assert final_loss < initial_loss, f"Loss did not decrease: {initial_loss} -> {final_loss}"
        assert optimizer.get_state_memory_bytes() > 0

