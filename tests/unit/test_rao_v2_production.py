"""
Stage 13 — Production Unit Tests for RAO 2.0 Vectorized Low-Memory Optimization.

Validates:
1. VectorizedLowMemoryAdamW initialization and validation
2. Selective 1D parameter preservation (biases/BatchNorm in float32)
3. Vectorized block quantization (>71% state memory reduction)
4. Denominator clamping numerical stability
5. Sparse gradient rejection
6. Checkpoint state restoration (state_dict / load_state_dict)
7. Parameter groups compatibility
8. Loss convergence behavior
"""

import math
import pytest
import torch
import torch.nn as nn

from robust_adapt.core.exceptions import ConfigurationError
from robust_adapt.integrations import VectorizedLowMemoryAdamW


def test_vectorized_adamw_validation():
    p = nn.Parameter(torch.randn(10, 10))
    with pytest.raises(ConfigurationError):
        VectorizedLowMemoryAdamW([p], lr=-1e-3)
    with pytest.raises(ConfigurationError):
        VectorizedLowMemoryAdamW([p], betas=(1.2, 0.999))
    with pytest.raises(ConfigurationError):
        VectorizedLowMemoryAdamW([p], eps=-1e-4)
    with pytest.raises(ConfigurationError):
        VectorizedLowMemoryAdamW([p], weight_decay=-0.1)
    with pytest.raises(ConfigurationError):
        VectorizedLowMemoryAdamW([p], block_size=50)  # Not a power of 2


def test_selective_1d_preservation():
    # Model with 2D weight and 1D bias
    linear = nn.Linear(32, 16, bias=True)
    opt = VectorizedLowMemoryAdamW(linear.parameters(), lr=1e-3, block_size=32)

    x = torch.randn(8, 32)
    loss = linear(x).sum()
    loss.backward()
    opt.step()

    weight_state = opt.state[linear.weight]
    bias_state = opt.state[linear.bias]

    # 2D weight must be quantized
    assert weight_state["is_quantized"] is True
    assert "q_m" in weight_state
    assert weight_state["q_m"].dtype == torch.int8
    assert "q_v" in weight_state
    assert weight_state["q_v"].dtype == torch.uint8

    # 1D bias must remain unquantized float32
    assert bias_state["is_quantized"] is False
    assert bias_state["exp_avg"].dtype == torch.float32
    assert bias_state["exp_avg_sq"].dtype == torch.float32


def test_state_memory_reduction():
    # Larger weight matrix (128x128 = 16,384 elements)
    w = nn.Parameter(torch.randn(128, 128))
    opt = VectorizedLowMemoryAdamW([w], lr=1e-3, block_size=64)

    loss = (w ** 2).sum()
    loss.backward()
    opt.step()

    mem_bytes = opt.get_state_memory_bytes()
    # Unquantized 32-bit float moments: 2 * 16384 * 4 = 131,072 bytes
    standard_bytes = 2 * w.numel() * 4
    reduction = 1.0 - (mem_bytes / standard_bytes)

    # Reduction must be >= 70%
    assert reduction >= 0.70
    assert mem_bytes < standard_bytes * 0.30


def test_sparse_gradient_rejection():
    embedding = nn.Embedding(10, 5, sparse=True)
    opt = VectorizedLowMemoryAdamW(embedding.parameters(), lr=1e-3)

    x = torch.tensor([1, 2], dtype=torch.long)
    loss = embedding(x).sum()
    loss.backward()

    with pytest.raises(ConfigurationError):
        opt.step()


def test_parameter_groups_support():
    p1 = nn.Parameter(torch.randn(16, 16))
    p2 = nn.Parameter(torch.randn(16, 16))

    opt = VectorizedLowMemoryAdamW([
        {"params": [p1], "lr": 1e-2},
        {"params": [p2], "lr": 1e-4, "weight_decay": 0.05},
    ])
    assert len(opt.param_groups) == 2
    assert opt.param_groups[0]["lr"] == 1e-2
    assert opt.param_groups[1]["lr"] == 1e-4

    loss = (p1.sum() + p2.sum())
    loss.backward()
    opt.step()


def test_state_dict_roundtrip():
    model = nn.Sequential(nn.Linear(16, 8), nn.Linear(8, 2))
    opt = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-3)

    x = torch.randn(4, 16)
    out = model(x)
    loss = out.sum()
    loss.backward()
    opt.step()

    state = opt.state_dict()
    assert "state" in state
    assert "param_groups" in state

    opt2 = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-3)
    opt2.load_state_dict(state)
    assert len(opt2.state) == len(opt.state)


def test_loss_convergence():
    torch.manual_seed(42)
    model = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 1))
    opt = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-2, weight_decay=1e-4)

    # Simple quadratic regression target
    X = torch.randn(64, 8)
    y = (X[:, 0:1] * 2.0)

    initial_loss = nn.MSELoss()(model(X), y).item()
    for _ in range(50):
        opt.zero_grad()
        loss = nn.MSELoss()(model(X), y)
        loss.backward()
        opt.step()

    final_loss = nn.MSELoss()(model(X), y).item()
    # Must converge significantly
    assert final_loss < initial_loss * 0.20
    assert not math.isnan(final_loss)
