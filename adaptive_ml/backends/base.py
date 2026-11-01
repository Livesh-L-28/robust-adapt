"""
AdaptiveML Backend Abstractions.

Defines the pluggable tensor and compute engine protocol.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class BackendEngine(Protocol):
    """Protocol for hardware and computational backend engines."""

    @property
    def name(self) -> str:
        """Name of the execution backend."""
        ...

    @property
    def device(self) -> str:
        """Active computing device string (e.g., 'cpu', 'cuda')."""
        ...

    def to_backend(self, array: np.ndarray) -> Any:
        """Convert a NumPy array to the backend's native tensor format."""
        ...

    def to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert a backend native tensor back to a NumPy ndarray."""
        ...

    def matmul(self, a: Any, b: Any) -> Any:
        """Execute matrix multiplication on backend tensors."""
        ...

    def clip(self, a: Any, a_min: float, a_max: float) -> Any:
        """Elementwise clamping of tensor values."""
        ...

