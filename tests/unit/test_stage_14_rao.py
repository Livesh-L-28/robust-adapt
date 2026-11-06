"""Unit tests for Stage 14 RAO and Deep-Learning Performance.

Verifies:
1. VectorizedLowMemoryAdamW convergence over long duration.
2. Memory reduction (>70%) vs standard PyTorch AdamW.
3. Non-finite gradient rejection (NaN/Inf) preserving state integrity.
4. Parameter group handling with distinct learning rates.
5. LowMemoryAdamW resilience to non-finite gradients (NumPy & Torch).
"""

import numpy as np
import pytest

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW
from robust_adapt.rao.adamw import LowMemoryAdamW


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch required")
def test_vectorized_adamw_convergence():
    """Verify VectorizedLowMemoryAdamW converges stably on linear regression."""
    torch.manual_seed(42)
    # Target: y = 2*x1 - 3*x2 + 1.5
    X = torch.randn(200, 2)
    true_w = torch.tensor([[2.0], [-3.0]])
    true_b = torch.tensor([1.5])
    y = X @ true_w + true_b

    model = nn.Linear(2, 1)
    optimizer = VectorizedLowMemoryAdamW(model.parameters(), lr=0.05, block_size=16)

    initial_loss = nn.functional.mse_loss(model(X), y).item()
    for _ in range(100):
        optimizer.zero_grad()
        loss = nn.functional.mse_loss(model(X), y)
        loss.backward()
        optimizer.step()

    final_loss = nn.functional.mse_loss(model(X), y).item()
    assert final_loss < initial_loss * 0.05, f"Loss did not decrease sufficiently: {initial_loss} -> {final_loss}"


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch required")
def test_vectorized_adamw_memory_reduction():
    """Verify VectorizedLowMemoryAdamW delivers >70% state memory savings."""
    model = nn.Sequential(
        nn.Linear(256, 512),
        nn.ReLU(),
        nn.Linear(512, 256),
    )
    optimizer = VectorizedLowMemoryAdamW(model.parameters(), block_size=64)

    # Step once to initialize state
    dummy_input = torch.randn(16, 256)
    loss = model(dummy_input).sum()
    loss.backward()
    optimizer.step()

    total_quantized_bytes = optimizer.get_state_memory_bytes()

    # Calculate uncompressed float32 AdamW state (2 moments * 4 bytes per param)
    total_elements = sum(p.numel() for p in model.parameters())
    uncompressed_bytes = total_elements * 2 * 4

    reduction = 1.0 - (total_quantized_bytes / uncompressed_bytes)
    assert reduction >= 0.70, f"Expected >= 70% state reduction, got {reduction:.2%}"


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch required")
def test_vectorized_adamw_non_finite_rejection():
    """Verify non-finite gradients (NaN/Inf) are cleanly rejected without state corruption."""
    model = nn.Linear(4, 2)
    optimizer = VectorizedLowMemoryAdamW(model.parameters(), lr=0.01, block_size=16)

    # Clean step
    x = torch.randn(2, 4)
    loss = model(x).sum()
    loss.backward()
    optimizer.step()

    weights_before = model.weight.clone().detach()

    # Inject NaN gradient
    optimizer.zero_grad()
    loss = model(x).sum()
    loss.backward()
    model.weight.grad[0, 0] = float("nan")

    # Step should detect NaN and skip
    optimizer.step()

    # Weights must be completely identical and finite
    assert torch.all(torch.isfinite(model.weight))
    assert torch.allclose(model.weight, weights_before)

    # Inject Inf gradient
    optimizer.zero_grad()
    loss = model(x).sum()
    loss.backward()
    model.weight.grad[0, 0] = float("inf")

    optimizer.step()
    assert torch.all(torch.isfinite(model.weight))
    assert torch.allclose(model.weight, weights_before)


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch required")
def test_vectorized_adamw_param_groups():
    """Verify VectorizedLowMemoryAdamW handles parameter groups with distinct learning rates."""
    layer1 = nn.Linear(8, 8)
    layer2 = nn.Linear(8, 8)
    optimizer = VectorizedLowMemoryAdamW(
        [
            {"params": layer1.parameters(), "lr": 0.01},
            {"params": layer2.parameters(), "lr": 0.05, "weight_decay": 0.1},
        ],
        block_size=16,
    )
    assert len(optimizer.param_groups) == 2
    assert optimizer.param_groups[0]["lr"] == 0.01
    assert optimizer.param_groups[1]["lr"] == 0.05
    assert optimizer.param_groups[1]["weight_decay"] == 0.1

    x = torch.randn(4, 8)
    out = layer2(layer1(x)).sum()
    out.backward()
    optimizer.step()
    assert torch.all(torch.isfinite(layer1.weight))
    assert torch.all(torch.isfinite(layer2.weight))


def test_low_memory_adamw_numpy_non_finite_rejection():
    """Verify LowMemoryAdamW rejects NaN/Inf in pure NumPy mode."""
    param = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    grad = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)

    class DummyParam:
        def __init__(self, data):
            self.data = data
            self.grad = grad

    p = DummyParam(param)
    opt = LowMemoryAdamW([p], lr=0.01, block_size=16)

    # Clean step
    opt.step()
    val_after_clean = p.data.copy()

    # Step with NaN gradient
    p.grad = np.array([[np.nan, 0.2], [0.3, 0.4]], dtype=np.float32)
    opt.step()
    assert np.all(np.isfinite(p.data))
    assert np.allclose(p.data, val_after_clean)

    # Step with Inf gradient
    p.grad = np.array([[np.inf, 0.2], [0.3, 0.4]], dtype=np.float32)
    opt.step()
    assert np.all(np.isfinite(p.data))
    assert np.allclose(p.data, val_after_clean)
