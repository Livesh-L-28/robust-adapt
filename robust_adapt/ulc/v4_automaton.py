"""ULC-v4 12-State Arbitration Automaton.

Implements the formal 12-state finite automaton coordinating all four pillars:
1. STABLE
2. ELEVATED_VARIANCE
3. WARNING
4. CONFIRMED_DRIFT
5. NOISE_BURST
6. RECOVERY
7. ADAPTATION_PENDING
8. ADAPTING
9. COOLDOWN
10. RESOURCE_CONSTRAINED
11. ASYMMETRIC_NOISE_MITIGATION
12. SAFE_FALLBACK
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import numpy as np

from robust_adapt.ulc.arbitrator import MultiObjectiveArbitrator
from robust_adapt.ulc.confidence import ConfidenceEngine, ConfidenceScores
from robust_adapt.ulc.v4_evidence import EvidenceVectorV4


class AutomatonStateV4(str, Enum):
    """12 discrete operational states of the ULC-v4 automaton."""
    STABLE = "STABLE"
    ELEVATED_VARIANCE = "ELEVATED_VARIANCE"
    WARNING = "WARNING"
    CONFIRMED_DRIFT = "CONFIRMED_DRIFT"
    NOISE_BURST = "NOISE_BURST"
    RECOVERY = "RECOVERY"
    ADAPTATION_PENDING = "ADAPTATION_PENDING"
    ADAPTING = "ADAPTING"
    COOLDOWN = "COOLDOWN"
    RESOURCE_CONSTRAINED = "RESOURCE_CONSTRAINED"
    ASYMMETRIC_NOISE_MITIGATION = "ASYMMETRIC_NOISE_MITIGATION"
    SAFE_FALLBACK = "SAFE_FALLBACK"


@dataclass(frozen=True)
class DirectiveV4:
    """Action directive emitted by the ULC-v4 automaton to coordinate all 4 pillars."""
    state: AutomatonStateV4
    learning_rate_scale: float = 1.0
    reset_momentum: bool = False
    suppress_adwin: bool = False
    freeze_buffer: bool = False
    purge_replay_policy: str = "none"
    keep_minority_in_replay: bool = True
    restore_concept_id: Optional[str] = None
    sample_filter_threshold: float = 0.0
    batch_size_scale: float = 1.0
    skip_expensive_ops: bool = False
    correct_labels: bool = False
    dwell_remaining: int = 0
    confidence: float = 1.0
    message: str = ""


class ArbitrationAutomatonV4:
    """12-state Finite State Automaton governing ULC-v4 cross-pillar orchestration.

    Parameters
    ----------
    tau_R : float, default=0.65
        Reliability threshold distinguishing genuine drift from corrupt noise bursts.
    recovery_steps : int, default=5
        Number of steps to dwell in RECOVERY mode while annealing learning rate.
    cooldown_steps : int, default=3
        Stabilization steps following active adaptation.
    hysteresis_band : float, default=0.15
        Deadband preventing high-frequency chattering between states.
    """

    def __init__(
        self,
        tau_R: float = 0.65,
        recovery_steps: int = 5,
        cooldown_steps: int = 3,
        hysteresis_band: float = 0.15,
    ) -> None:
        self.tau_R = float(tau_R)
        self.recovery_steps = int(recovery_steps)
        self.cooldown_steps = int(cooldown_steps)
        self.hysteresis_band = float(hysteresis_band)

        self.state: AutomatonStateV4 = AutomatonStateV4.STABLE
        self.dwell_counter: int = 0
        self.cooldown_counter: int = 0

        self.confidence_engine = ConfidenceEngine()
        self.arbitrator = MultiObjectiveArbitrator()

    def reset(self) -> None:
        """Reset automaton operational state to STABLE and clear counters."""
        self.state = AutomatonStateV4.STABLE
        self.dwell_counter = 0
        self.cooldown_counter = 0

    def transition(self, evidence: EvidenceVectorV4) -> DirectiveV4:
        """Execute state transition kernel Gamma(S, evidence) and emit DirectiveV4."""
        conf = self.confidence_engine.evaluate(evidence, tau_r=self.tau_R)
        delta = evidence.delta_drift
        rel = evidence.mean_reliability
        u_res = evidence.resource_utilization
        hyst = self.hysteresis_band

        next_state = self.state

        # Check for Critical Anomaly -> SAFE_FALLBACK
        if evidence.predictive_entropy > 0.95 and rel < 0.15 and delta > 2.0:
            next_state = AutomatonStateV4.SAFE_FALLBACK

        # State Transition Machine
        elif self.state == AutomatonStateV4.SAFE_FALLBACK:
            if rel >= self.tau_R and delta < 0.5:
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.SAFE_FALLBACK

        elif self.state == AutomatonStateV4.STABLE:
            if u_res >= 0.85:
                next_state = AutomatonStateV4.RESOURCE_CONSTRAINED
            elif evidence.asymmetric_noise_rate >= 0.20:
                next_state = AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION
            elif delta >= 1.0:
                if rel >= self.tau_R:
                    next_state = AutomatonStateV4.CONFIRMED_DRIFT
                else:
                    next_state = AutomatonStateV4.NOISE_BURST
            elif delta >= 0.50:
                next_state = AutomatonStateV4.WARNING
            elif evidence.predictive_entropy > 0.70:
                next_state = AutomatonStateV4.ELEVATED_VARIANCE
            else:
                next_state = AutomatonStateV4.STABLE

        elif self.state == AutomatonStateV4.ELEVATED_VARIANCE:
            if delta >= 1.0:
                next_state = AutomatonStateV4.CONFIRMED_DRIFT if rel >= self.tau_R else AutomatonStateV4.NOISE_BURST
            elif delta >= 0.50:
                next_state = AutomatonStateV4.WARNING
            elif evidence.predictive_entropy < 0.50:
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.ELEVATED_VARIANCE

        elif self.state == AutomatonStateV4.WARNING:
            if delta >= 1.0:
                next_state = AutomatonStateV4.CONFIRMED_DRIFT if rel >= self.tau_R else AutomatonStateV4.NOISE_BURST
            elif delta < (0.50 - hyst):
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.WARNING

        elif self.state == AutomatonStateV4.CONFIRMED_DRIFT:
            # Transitions immediately into RECOVERY mode with initialized dwell counter
            self.dwell_counter = self.recovery_steps
            next_state = AutomatonStateV4.RECOVERY

        elif self.state == AutomatonStateV4.RECOVERY:
            if self.dwell_counter <= 0 and delta < 0.50:
                self.cooldown_counter = self.cooldown_steps
                next_state = AutomatonStateV4.COOLDOWN
            else:
                self.dwell_counter = max(0, self.dwell_counter - 1)
                next_state = AutomatonStateV4.RECOVERY

        elif self.state == AutomatonStateV4.COOLDOWN:
            if self.cooldown_counter <= 0:
                next_state = AutomatonStateV4.STABLE
            else:
                self.cooldown_counter = max(0, self.cooldown_counter - 1)
                next_state = AutomatonStateV4.COOLDOWN

        elif self.state == AutomatonStateV4.NOISE_BURST:
            if rel >= self.tau_R and delta < 0.50:
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.NOISE_BURST

        elif self.state == AutomatonStateV4.RESOURCE_CONSTRAINED:
            if u_res < 0.70:
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.RESOURCE_CONSTRAINED

        elif self.state == AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION:
            if evidence.asymmetric_noise_rate < 0.10:
                next_state = AutomatonStateV4.STABLE
            else:
                next_state = AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION

        if next_state == AutomatonStateV4.CONFIRMED_DRIFT:
            self.dwell_counter = self.recovery_steps

        self.state = next_state
        return self._build_directive(evidence, conf)

    def _build_directive(self, evidence: EvidenceVectorV4, conf: ConfidenceScores) -> DirectiveV4:
        """Construct the specific action directive for current state and evidence."""
        purge_pol, keep_min = self.arbitrator.arbitrate_replay_purge(evidence, conf)

        if self.state == AutomatonStateV4.CONFIRMED_DRIFT:
            return DirectiveV4(
                state=AutomatonStateV4.CONFIRMED_DRIFT,
                learning_rate_scale=2.5,
                reset_momentum=True,
                purge_replay_policy=purge_pol,
                keep_minority_in_replay=keep_min,
                dwell_remaining=self.dwell_counter,
                confidence=conf.adapt,
                message="Confirmed concept drift: adapting models, flusing momentum, and updating buffers.",
            )

        if self.state == AutomatonStateV4.NOISE_BURST:
            return DirectiveV4(
                state=AutomatonStateV4.NOISE_BURST,
                learning_rate_scale=1.0,
                suppress_adwin=True,
                freeze_buffer=True,
                sample_filter_threshold=self.tau_R,
                correct_labels=True,
                confidence=conf.suppress_noise,
                message="Noise burst detected: suppressing drift reset and filtering low-reliability instances.",
            )

        if self.state == AutomatonStateV4.RECOVERY:
            frac = self.dwell_counter / max(1, self.recovery_steps)
            lr_scale = 1.0 + 1.5 * frac
            return DirectiveV4(
                state=AutomatonStateV4.RECOVERY,
                learning_rate_scale=lr_scale,
                dwell_remaining=self.dwell_counter,
                confidence=conf.adapt,
                message=f"Post-drift recovery phase ({self.dwell_counter} steps remaining); annealing LR.",
            )

        if self.state == AutomatonStateV4.COOLDOWN:
            return DirectiveV4(
                state=AutomatonStateV4.COOLDOWN,
                learning_rate_scale=1.0,
                dwell_remaining=self.cooldown_counter,
                confidence=0.90,
                message=f"Post-adaptation cooldown ({self.cooldown_counter} steps remaining).",
            )

        if self.state == AutomatonStateV4.RESOURCE_CONSTRAINED:
            return DirectiveV4(
                state=AutomatonStateV4.RESOURCE_CONSTRAINED,
                learning_rate_scale=1.0,
                batch_size_scale=0.50,
                skip_expensive_ops=True,
                confidence=conf.throttle_resources,
                message="Resource budget ceiling breached: throttling batch size and shedding expensive ops.",
            )

        if self.state == AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION:
            return DirectiveV4(
                state=AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION,
                learning_rate_scale=1.0,
                correct_labels=True,
                sample_filter_threshold=0.40,
                confidence=conf.mitigate_asymmetric_noise,
                message="Asymmetric class-conditional noise detected: applying label correction.",
            )

        if self.state == AutomatonStateV4.WARNING:
            return DirectiveV4(
                state=AutomatonStateV4.WARNING,
                learning_rate_scale=1.0,
                confidence=0.70,
                message="Elevated divergence observed; warning state active.",
            )

        if self.state == AutomatonStateV4.ELEVATED_VARIANCE:
            return DirectiveV4(
                state=AutomatonStateV4.ELEVATED_VARIANCE,
                learning_rate_scale=1.0,
                confidence=0.60,
                message="Elevated predictive entropy; monitoring boundary uncertainty.",
            )

        if self.state == AutomatonStateV4.SAFE_FALLBACK:
            return DirectiveV4(
                state=AutomatonStateV4.SAFE_FALLBACK,
                learning_rate_scale=0.20,
                suppress_adwin=True,
                freeze_buffer=True,
                skip_expensive_ops=True,
                confidence=0.99,
                message="Extreme pipeline anomaly: entering safe fallback state to protect model integrity.",
            )

        # STABLE default
        return DirectiveV4(
            state=AutomatonStateV4.STABLE,
            learning_rate_scale=1.0,
            confidence=0.95,
            message="Stream steady; normal operation.",
        )
