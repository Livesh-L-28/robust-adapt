"""
PyTorch Integration Adapters for AdaptiveML Optimizers.
"""

from __future__ import annotations

from typing import Any, Iterable

from adaptive_ml.rao.adamw import LowMemoryAdamW


def create_torch_low_memory_adamw(
    params: Iterable[Any],
    lr: float = 1e-3,
    betas: tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    weight_decay: float = 1e-2,
    block_size: int = 64,
) -> LowMemoryAdamW:
    """Factory helper creating an initialized LowMemoryAdamW optimizer for PyTorch."""
    return LowMemoryAdamW(
        params=params,
        lr=lr,
        betas=betas,
        eps=eps,
        weight_decay=weight_decay,
        block_size=block_size,
    )
