"""Compatibility forwarding namespace for adaptive_ml -> robust_adapt.

The 'adaptive_ml' package has been rebranded to 'robust_adapt'.
All symbols and submodules are forwarded from 'robust_adapt'.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "The 'adaptive_ml' package has been rebranded to 'robust_adapt'. "
    "Please update your imports from 'adaptive_ml' to 'robust_adapt'. "
    "The 'adaptive_ml' compatibility namespace will be deprecated in future releases.",
    FutureWarning,
    stacklevel=2,
)

import robust_adapt as _canonical
from robust_adapt import *  # noqa: F401, F403

AdaptiveMLError = _canonical.RobustAdaptError
__version__ = _canonical.__version__
__all__ = _canonical.__all__


def __getattr__(name: str):
    return getattr(_canonical, name)


def __dir__():
    return dir(_canonical)
