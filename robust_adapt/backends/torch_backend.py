"""
Optional PyTorch execution backend.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None


class TorchBackend:
    """Hardware accelerated backend bridging PyTorch Tensors and autograd."""

    def __init__(self, device: str = "cpu") -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed in the active environment.")
        self._device = device

    @property
    def name(self) -> str:
        return "torch"

    @property
    def device(self) -> str:
        return self._device

    def to_backend(self, array: np.ndarray) -> "torch.Tensor":
        t = torch.from_numpy(np.ascontiguousarray(array))
        if self._device != "cpu":
            t = t.to(self._device)
        return t

    def to_numpy(self, tensor: Any) -> np.ndarray:
        if isinstance(tensor, torch.Tensor):
            return tensor.detach().cpu().numpy()
        return np.asarray(tensor)

    def matmul(self, a: "torch.Tensor", b: "torch.Tensor") -> "torch.Tensor":
        return torch.matmul(a, b)

    def clip(self, a: "torch.Tensor", a_min: float, a_max: float) -> "torch.Tensor":
        return torch.clamp(a, min=a_min, max=a_max)
