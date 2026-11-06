"""
Pure NumPy CPU SIMD execution backend.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class NumPyBackend:
    """Default local-first CPU compute backend using NumPy vectorization."""

    @property
    def name(self) -> str:
        return "numpy"

    @property
    def device(self) -> str:
        return "cpu"

    def to_backend(self, array: np.ndarray) -> np.ndarray:
        if not isinstance(array, np.ndarray):
            return np.asarray(array, dtype=np.float64)
        return array

    def to_numpy(self, tensor: Any) -> np.ndarray:
        if isinstance(tensor, np.ndarray):
            return tensor
        return np.asarray(tensor)

    def matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.matmul(a, b)

    def clip(self, a: np.ndarray, a_min: float, a_max: float) -> np.ndarray:
        return np.clip(a, a_min, a_max)
