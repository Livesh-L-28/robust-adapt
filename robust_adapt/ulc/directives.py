"""
AdaptiveML Unified Learning Controller (ULC) Directives.

Defines the discrete operational states and structured action directives
communicated across the ALA, RLA, and RAO pillars.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControllerState(str, Enum):
    """Discrete operational states of the arbitration automaton."""

    STABLE = "STABLE"
    WARNING = "WARNING"
    CONFIRMED_DRIFT = "CONFIRMED_DRIFT"
    NOISE_BURST = "NOISE_BURST"
    RECOVERY = "RECOVERY"
    ADAPTATION_PENDING = "ADAPTATION_PENDING"
    ADAPTING = "ADAPTING"
    COOLDOWN = "COOLDOWN"
    SAFE_FALLBACK = "SAFE_FALLBACK"


@dataclass(frozen=True)
class ControllerDirective:
    """Action directive emitted by the ULC automaton to coordinate pillars."""

    state: ControllerState
    learning_rate_scale: float = 1.0
    reset_momentum: bool = False
    suppress_adwin: bool = False
    freeze_buffer: bool = False
    purge_replay: bool = False
    split_immediate: bool = False
    sample_filter_threshold: float = 0.0
    gradient_clip_factor: float = 1.0
    dwell_remaining: int = 0
    message: str = ""
