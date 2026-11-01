"""
AdaptiveML Unified Learning Controller (ULC) Arbitration Automaton.

Implements the 5-state finite automaton governing arbitration between
concept drift adaptation and noise burst suppression.
"""

from __future__ import annotations

from typing import Optional

from adaptive_ml.core.config import ULCConfig
from adaptive_ml.ulc.directives import ControllerDirective, ControllerState
from adaptive_ml.ulc.evidence import EvidenceVector


class ArbitrationAutomaton:
    """Finite State Automaton governing cross-pillar adaptation vs noise rejection."""

    def __init__(self, config: Optional[ULCConfig] = None) -> None:
        self.config = config or ULCConfig()
        self.state = ControllerState.STABLE
        self.dwell_counter = 0

    def transition(self, evidence: EvidenceVector) -> ControllerDirective:
        """Execute state transition kernel Gamma(S, e_tau) and emit ControllerDirective.

        Args:
            evidence: Normalized 4D EvidenceVector.

        Returns:
            ControllerDirective containing pillar coordination instructions.
        """
        tau_r = self.config.tau_R
        hyst = self.config.hysteresis_band
        delta = evidence.delta_drift
        rel = evidence.mean_reliability

        next_state = self.state

        if self.state == ControllerState.STABLE:
            if delta >= 1.0:
                if rel >= tau_r:
                    next_state = ControllerState.CONFIRMED_DRIFT
                else:
                    next_state = ControllerState.NOISE_BURST
            elif delta >= 0.5:
                next_state = ControllerState.WARNING
            else:
                next_state = ControllerState.STABLE

        elif self.state == ControllerState.WARNING:
            if delta >= 1.0:
                if rel >= tau_r:
                    next_state = ControllerState.CONFIRMED_DRIFT
                else:
                    next_state = ControllerState.NOISE_BURST
            elif delta < (0.5 - hyst):
                next_state = ControllerState.STABLE
            else:
                next_state = ControllerState.WARNING

        elif self.state == ControllerState.CONFIRMED_DRIFT:
            # Transitions immediately into RECOVERY mode with initialized dwell counter
            self.dwell_counter = self.config.recovery_steps
            next_state = ControllerState.RECOVERY

        elif self.state == ControllerState.NOISE_BURST:
            if rel >= tau_r and delta < 0.5:
                next_state = ControllerState.STABLE
            else:
                next_state = ControllerState.NOISE_BURST

        elif self.state == ControllerState.RECOVERY:
            if self.dwell_counter <= 0 and delta < 0.5:
                next_state = ControllerState.STABLE
            else:
                self.dwell_counter = max(0, self.dwell_counter - 1)
                next_state = ControllerState.RECOVERY

        # If entering CONFIRMED_DRIFT now, setup dwell counter for subsequent recovery
        if next_state == ControllerState.CONFIRMED_DRIFT:
            self.dwell_counter = self.config.recovery_steps

        self.state = next_state
        return self._build_directive()

    def _build_directive(self) -> ControllerDirective:
        """Construct the specific action directive for current state."""
        if self.state == ControllerState.CONFIRMED_DRIFT:
            return ControllerDirective(
                state=ControllerState.CONFIRMED_DRIFT,
                learning_rate_scale=2.5,
                reset_momentum=True,
                purge_replay=True,
                split_immediate=True,
                dwell_remaining=self.dwell_counter,
                message="Confirmed concept drift: adapting models and resetting obsolete buffers.",
            )

        if self.state == ControllerState.NOISE_BURST:
            return ControllerDirective(
                state=ControllerState.NOISE_BURST,
                learning_rate_scale=1.0,
                suppress_adwin=True,
                freeze_buffer=True,
                sample_filter_threshold=self.config.tau_R,
                gradient_clip_factor=0.5,
                message="Noise burst detected: suppressing drift reset and filtering low-reliability samples.",
            )

        if self.state == ControllerState.RECOVERY:
            frac = self.dwell_counter / max(1, self.config.recovery_steps)
            lr_scale = 1.0 + 1.5 * frac
            return ControllerDirective(
                state=ControllerState.RECOVERY,
                learning_rate_scale=lr_scale,
                dwell_remaining=self.dwell_counter,
                message=f"Post-drift recovery phase ({self.dwell_counter} steps remaining); annealing LR.",
            )

        if self.state == ControllerState.WARNING:
            return ControllerDirective(
                state=ControllerState.WARNING,
                learning_rate_scale=1.0,
                message="Elevated divergence observed; warning state active.",
            )

        # STABLE default
        return ControllerDirective(
            state=ControllerState.STABLE,
            learning_rate_scale=1.0,
            message="Stream steady; normal operation.",
        )

