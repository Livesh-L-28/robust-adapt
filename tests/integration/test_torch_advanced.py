"""
Advanced PyTorch adapter and loss function integration test suite.

Verifies:
- TorchGeneralizedCrossEntropyLoss forward and backward propagation.
- TorchSymmetricCrossEntropyLoss numerical stability and gradient correctness.
- TorchTrainingBudgetHook runtime monitoring and budget state evaluation.
- TorchCheckpointAdapter safe checkpointing with SafeTensors and JSON metadata.
- create_torch_low_memory_adamw parameter updates.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from robust_adapt.integrations.torch_module import (
    TorchGeneralizedCrossEntropyLoss,
    TorchSymmetricCrossEntropyLoss,
)
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw
from robust_adapt.integrations.torch_callback import (
    TorchCheckpointAdapter,
    TorchTrainingBudgetHook,
)
from robust_adapt.rao.budget import BudgetState, DynamicResourceBudgetManager


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch is required")
class TestTorchAdvanced:
    """Test suite for PyTorch integration components."""

    def test_generalized_cross_entropy_loss_backward(self) -> None:
        """Verify TorchGeneralizedCrossEntropyLoss forward and backward autograd pass."""
        loss_fn = TorchGeneralizedCrossEntropyLoss(q=0.7)

        linear = nn.Linear(5, 3)
        x = torch.randn(8, 5)
        targets = torch.randint(0, 3, (8,), dtype=torch.long)

        logits = linear(x)
        loss = loss_fn(logits, targets)

        assert loss.ndim == 0
        assert not torch.isnan(loss)
        assert loss.item() >= 0.0

        loss.backward()
        assert linear.weight.grad is not None
        assert not torch.isnan(linear.weight.grad).any()

    def test_generalized_cross_entropy_q_boundary(self) -> None:
        """Verify parameter bounds for q in GCE loss."""
        with pytest.raises(ValueError, match="q must be in"):
            TorchGeneralizedCrossEntropyLoss(q=0.0)

        with pytest.raises(ValueError, match="q must be in"):
            TorchGeneralizedCrossEntropyLoss(q=1.5)

    def test_symmetric_cross_entropy_loss(self) -> None:
        """Verify TorchSymmetricCrossEntropyLoss combines CE and RCE."""
        loss_fn = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.8)

        logits = torch.tensor([[2.0, -1.0, 0.5], [-0.5, 3.0, 1.0]], requires_grad=True)
        targets = torch.tensor([0, 1], dtype=torch.long)

        loss = loss_fn(logits, targets)
        assert not torch.isnan(loss)
        assert loss.item() > 0.0

        loss.backward()
        assert logits.grad is not None
        assert not torch.isnan(logits.grad).any()

    def test_torch_training_budget_hook(self) -> None:
        """Verify TorchTrainingBudgetHook monitors steps and emits budget states."""
        budget_mgr = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=4096.0)
        hook = TorchTrainingBudgetHook(budget_mgr)

        for _ in range(5):
            hook.on_step_begin()
            # Simulate short work
            _ = torch.matmul(torch.randn(50, 50), torch.randn(50, 50))
            state = hook.on_step_end()
            assert isinstance(state, BudgetState)

        assert len(hook.step_latencies) == 5
        assert hook.recommended_batch_size > 0

    def test_torch_checkpoint_adapter_round_trip(self, tmp_path: Path) -> None:
        """Verify TorchCheckpointAdapter saves and restores neural weights identically."""
        model = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 2),
        )
        optimizer = torch.optim.SGD(model.parameters(), lr=0.05)

        # Run one step to modify weights
        x = torch.randn(4, 8)
        y = torch.tensor([0, 1, 0, 1], dtype=torch.long)
        loss = nn.functional.cross_entropy(model(x), y)
        loss.backward()
        optimizer.step()

        original_weights = {k: v.clone() for k, v in model.state_dict().items()}

        ckpt_file = tmp_path / "model_ckpt.safetensors"
        saved_path = TorchCheckpointAdapter.save_hybrid_checkpoint(
            model=model,
            optimizer=optimizer,
            controller=None,
            filepath=ckpt_file,
        )
        assert saved_path.exists()

        # Create a fresh model with different initial weights
        restored_model = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 2),
        )
        restored_optimizer = torch.optim.SGD(restored_model.parameters(), lr=0.01)

        TorchCheckpointAdapter.load_hybrid_checkpoint(
            model=restored_model,
            optimizer=restored_optimizer,
            controller=None,
            filepath=saved_path,
        )

        # Check weights are restored exactly
        for name, orig_tensor in original_weights.items():
            restored_tensor = restored_model.state_dict()[name]
            assert torch.allclose(orig_tensor, restored_tensor, atol=1e-6)

    def test_torch_low_memory_adamw_step(self) -> None:
        """Verify create_torch_low_memory_adamw updates parameters properly."""
        model = nn.Linear(4, 2)
        optimizer = create_torch_low_memory_adamw(model.parameters(), lr=0.1)

        x = torch.randn(10, 4)
        targets = torch.randint(0, 2, (10,), dtype=torch.long)

        initial_loss = nn.functional.cross_entropy(model(x), targets).item()

        for _ in range(10):
            optimizer.zero_grad()
            out = model(x)
            loss = nn.functional.cross_entropy(out, targets)
            loss.backward()
            optimizer.step()

        final_loss = nn.functional.cross_entropy(model(x), targets).item()
        assert final_loss < initial_loss
