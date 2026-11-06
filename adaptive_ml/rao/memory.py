"""Compatibility forwarding module for adaptive_ml.rao.memory -> robust_adapt.rao.memory."""

import robust_adapt.rao.memory as _canonical
from robust_adapt.rao.memory import *  # noqa: F401, F403

__all__ = getattr(_canonical, "__all__", [name for name in dir(_canonical) if not name.startswith("_")])


def __getattr__(name: str):
    return getattr(_canonical, name)


def __dir__():
    return dir(_canonical)
