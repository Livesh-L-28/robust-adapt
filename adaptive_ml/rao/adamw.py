"""Compatibility forwarding module for adaptive_ml.rao.adamw -> robust_adapt.rao.adamw."""

import robust_adapt.rao.adamw as _canonical
from robust_adapt.rao.adamw import *  # noqa: F401, F403

__all__ = getattr(_canonical, "__all__", [name for name in dir(_canonical) if not name.startswith("_")])


def __getattr__(name: str):
    return getattr(_canonical, name)


def __dir__():
    return dir(_canonical)
