"""
Unit tests for compute backends.
"""

import numpy as np
import pytest

from robust_adapt.backends import NumPyBackend, TorchBackend, get_backend
from robust_adapt.backends.torch_backend import _TORCH_AVAILABLE


def test_numpy_backend_operations() -> None:
    backend = get_backend("numpy")
    assert backend.name == "numpy"
    assert backend.device == "cpu"

    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    b = np.array([[2.0, 0.0], [0.0, 2.0]])

    c = backend.matmul(a, b)
    expected = np.array([[2.0, 4.0], [6.0, 8.0]])
    np.testing.assert_allclose(c, expected)

    clipped = backend.clip(a, 2.0, 3.5)
    np.testing.assert_allclose(clipped, [[2.0, 2.0], [3.0, 3.5]])


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch is required for TorchBackend test")
def test_torch_backend_operations() -> None:
    backend = get_backend("torch")
    assert backend.name == "torch"
    assert backend.device == "cpu"

    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    b = np.array([[2.0, 0.0], [0.0, 2.0]])

    t_a = backend.to_backend(a)
    t_b = backend.to_backend(b)

    t_c = backend.matmul(t_a, t_b)
    c_np = backend.to_numpy(t_c)

    expected = np.array([[2.0, 4.0], [6.0, 8.0]])
    np.testing.assert_allclose(c_np, expected)

