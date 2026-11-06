"""Compatibility forwarding module for adaptive_ml.rla.losses -> robust_adapt.rla.losses."""

import robust_adapt.rla.losses as _canonical
from robust_adapt.rla.losses import *  # noqa: F401, F403

__all__ = getattr(_canonical, "__all__", [name for name in dir(_canonical) if not name.startswith("_")])


def __getattr__(name: str):
    return getattr(_canonical, name)


def __dir__():
    return dir(_canonical)
