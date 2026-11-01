"""
AdaptiveML Compute Backends.
"""

from __future__ import annotations

from typing import Optional

from adaptive_ml.backends.base import BackendEngine
from adaptive_ml.backends.numpy_backend import NumPyBackend
from adaptive_ml.backends.torch_backend import TorchBackend, _TORCH_AVAILABLE


def get_backend(name: str = "numpy", device: str = "cpu") -> BackendEngine:
    """Retrieve an initialized backend engine by name."""
    if name == "numpy":
        return NumPyBackend()
    if name == "torch":
        if not _TORCH_AVAILABLE:
            raise ValueError("TorchBackend requested but PyTorch is not available.")
        return TorchBackend(device=device)
    raise ValueError(f"Unknown backend '{name}'. Available options: 'numpy', 'torch'.")


__all__ = ["BackendEngine", "NumPyBackend", "TorchBackend", "get_backend"]

