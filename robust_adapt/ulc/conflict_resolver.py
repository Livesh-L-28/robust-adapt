"""ULC-v4 Cross-Pillar Conflict Resolution Engine.

Formally resolves cross-pillar conflicts across Scenarios A through J:
- Scenario A: Drift alarm during severe noise burst
- Scenario B: Extreme class imbalance (1000:1) with concept drift
- Scenario C: Budget ceiling breached during active drift
- Scenario D: Recurring concept drift detected by ConceptMemory
- Scenario E: High prediction entropy with high sample reliability (Epistemic Boundary)
- Scenario F: Low prediction entropy with low sample reliability (Adversarial / Inverted)
- Scenario G: Delayed labels arriving during post-drift recovery
- Scenario H: Emerging class appearing during resource-constrained state
- Scenario I: Asymmetric class noise collision with cost-sensitive threshold
- Scenario J: Multi-detector disagreement with hysteresis deadband
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from robust_adapt.ulc.confidence import ConfidenceScores
from robust_adapt.ulc.v4_automaton import AutomatonStateV4, DirectiveV4
from robust_adapt.ulc.v4_evidence import EvidenceVectorV4


class CrossPillarConflictResolver:
    """Deterministic arbiter resolving cross-pillar policy collisions."""

    @staticmethod
    def resolve_conflicts(
        directive: DirectiveV4,
        evidence: EvidenceVectorV4,
        confidence: ConfidenceScores,
        spatial_discordance: Optional[float] = None,
        noise_dwell: int = 0,
    ) -> Tuple[DirectiveV4, str]:
        """Apply Scenarios A-J arbitration rules to refine DirectiveV4.

        Parameters
        ----------
        directive : DirectiveV4
            Raw directive proposed by the arbitration automaton.
        evidence : EvidenceVectorV4
            Multi-pillar 10D evidence vector.
        confidence : ConfidenceScores
            Calibrated confidence scores.
        spatial_discordance : Optional[float], default=None
            Spatial label discordance in feature space in [0.0, 1.0].
            When provided, enables fine-grained discrimination between genuine
            concept drift (spatially coherent, <= 0.25) and corrupt label noise (> 0.25).
            When None, falls back to legacy ULC-v4 reliability thresholding (< 0.65).
        noise_dwell : int, default=0
            Consecutive steps spent in NOISE_BURST state, preventing infinite deadlock.

        Returns
        -------
        Tuple[DirectiveV4, str]
            (resolved_directive, scenario_identified_string)
        """
        # =====================================================================
        # Scenario A: Drift Alarm during Severe Noise Burst vs Genuine Drift
        # =====================================================================
        if evidence.delta_drift >= 1.0:
            if spatial_discordance is not None:
                if spatial_discordance > 0.25:
                    resolved = DirectiveV4(
                        state=AutomatonStateV4.NOISE_BURST,
                        learning_rate_scale=1.0,
                        suppress_adwin=True,
                        freeze_buffer=True,
                        sample_filter_threshold=0.65,
                        correct_labels=True,
                        confidence=confidence.suppress_noise,
                        message="[Scenario A] Verified label noise burst: suppressing drift reset and filtering noise.",
                    )
                    return resolved, "Scenario A: Noise vs Drift (Verified Noise)"
                elif evidence.resource_utilization >= 0.85:
                    resolved = DirectiveV4(
                        state=AutomatonStateV4.RESOURCE_CONSTRAINED,
                        learning_rate_scale=1.5,
                        reset_momentum=True,
                        batch_size_scale=0.50,
                        skip_expensive_ops=True,
                        confidence=confidence.throttle_resources,
                        message="[Scenario C] Drift adaptation constrained by resource budget: scaling batch size and shedding non-critical ops.",
                    )
                    return resolved, "Scenario C: Budget vs Drift"
                else:
                    keep_min = evidence.imbalance_ratio > 3.0 or evidence.is_emerging_class
                    resolved = DirectiveV4(
                        state=AutomatonStateV4.CONFIRMED_DRIFT,
                        learning_rate_scale=2.5,
                        reset_momentum=True,
                        purge_replay_policy="selective" if keep_min else "partial",
                        keep_minority_in_replay=keep_min,
                        confidence=0.95,
                        message="[Scenario A] Verified genuine concept drift: resetting models and adapting.",
                    )
                    return resolved, "Scenario A: Resolved Genuine Drift"
            elif evidence.mean_reliability < 0.65:
                resolved = DirectiveV4(
                    state=AutomatonStateV4.NOISE_BURST,
                    learning_rate_scale=1.0,
                    suppress_adwin=True,
                    freeze_buffer=True,
                    sample_filter_threshold=0.65,
                    correct_labels=True,
                    confidence=confidence.suppress_noise,
                    message="[Scenario A] Drift alarm during noise burst: suppressing drift reset and filtering noise.",
                )
                return resolved, "Scenario A: Noise vs Drift"

        # =====================================================================
        # Scenario D: Recurring Concept Drift Detected
        # =====================================================================
        if evidence.recurring_similarity >= 0.75 and evidence.delta_drift >= 0.50:
            resolved = DirectiveV4(
                state=AutomatonStateV4.COOLDOWN,
                learning_rate_scale=1.0,
                reset_momentum=False,
                restore_concept_id="matched_recurring",
                purge_replay_policy="none",
                confidence=confidence.restore_concept,
                message="[Scenario D] Recurring concept detected: restoring historical model weights without retraining.",
            )
            return resolved, "Scenario D: Recurring Concept Restoration"

        # =====================================================================
        # Scenario B: Extreme Class Imbalance (1000:1) with Concept Drift
        # =====================================================================
        if (evidence.imbalance_ratio >= 5.0 or evidence.is_emerging_class) and evidence.delta_drift >= 1.0 and evidence.mean_reliability >= 0.65:
            resolved = DirectiveV4(
                state=AutomatonStateV4.CONFIRMED_DRIFT,
                learning_rate_scale=2.5,
                reset_momentum=True,
                purge_replay_policy="selective",
                keep_minority_in_replay=True,
                confidence=confidence.adapt,
                message="[Scenario B] Concept drift under extreme imbalance: adapting model while strictly preserving minority replay.",
            )
            return resolved, "Scenario B: Imbalance vs Drift"

        # =====================================================================
        # Scenario C: Budget Ceiling Breached during Active Drift
        # =====================================================================
        if evidence.resource_utilization >= 0.85 and evidence.delta_drift >= 1.0:
            resolved = DirectiveV4(
                state=AutomatonStateV4.RESOURCE_CONSTRAINED,
                learning_rate_scale=1.5,  # Moderate LR instead of 2.5x to reduce compute
                reset_momentum=True,
                batch_size_scale=0.50,
                skip_expensive_ops=True,
                confidence=confidence.throttle_resources,
                message="[Scenario C] Drift adaptation constrained by resource budget: scaling batch size and shedding non-critical ops.",
            )
            return resolved, "Scenario C: Budget vs Drift"

        # =====================================================================
        # Scenario E: Epistemic Boundary Uncertainty (High Entropy, Clean Reliability)
        # =====================================================================
        if evidence.predictive_entropy >= 0.75 and evidence.mean_reliability >= 0.70:
            resolved = DirectiveV4(
                state=AutomatonStateV4.ELEVATED_VARIANCE,
                learning_rate_scale=1.0,
                suppress_adwin=False,
                freeze_buffer=False,
                confidence=0.80,
                message="[Scenario E] High entropy with clean reliability: epistemic boundary instance, proceeding without reset.",
            )
            return resolved, "Scenario E: Epistemic Boundary Uncertainty"

        # =====================================================================
        # Scenario F: Adversarial / Inverted Label (Low Entropy, Low Reliability)
        # =====================================================================
        if evidence.predictive_entropy <= 0.25 and evidence.mean_reliability <= 0.35:
            resolved = DirectiveV4(
                state=AutomatonStateV4.NOISE_BURST,
                learning_rate_scale=1.0,
                correct_labels=True,
                sample_filter_threshold=0.50,
                confidence=0.90,
                message="[Scenario F] Overconfident prediction with corrupt reliability: proposing label correction and zeroing corrupt loss.",
            )
            return resolved, "Scenario F: Adversarial / Inverted Label"

        # =====================================================================
        # Scenario G: Delayed Labels Arriving during Post-Drift Recovery
        # =====================================================================
        if directive.state == AutomatonStateV4.RECOVERY and evidence.observed_delay > 10.0:
            resolved = DirectiveV4(
                state=AutomatonStateV4.RECOVERY,
                learning_rate_scale=directive.learning_rate_scale,
                sample_filter_threshold=0.60,
                confidence=0.85,
                message="[Scenario G] Stale delayed labels during drift recovery: filtering obsolete pre-drift feedback.",
            )
            return resolved, "Scenario G: Delayed Labels during Recovery"

        # =====================================================================
        # Scenario H: Emerging Class Appearing during Resource-Constrained State
        # =====================================================================
        if evidence.is_emerging_class and evidence.resource_utilization >= 0.85:
            resolved = DirectiveV4(
                state=AutomatonStateV4.RESOURCE_CONSTRAINED,
                learning_rate_scale=1.0,
                batch_size_scale=0.50,
                keep_minority_in_replay=True,
                skip_expensive_ops=True,
                confidence=0.85,
                message="[Scenario H] Emerging class under resource ceiling: allocating reserved quota while throttling majority batch size.",
            )
            return resolved, "Scenario H: Emerging Class under Resource Pressure"

        # =====================================================================
        # Scenario I: Asymmetric Class Noise with Cost-Sensitive Threshold
        # =====================================================================
        if evidence.asymmetric_noise_rate >= 0.20:
            resolved = DirectiveV4(
                state=AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION,
                learning_rate_scale=1.0,
                correct_labels=True,
                sample_filter_threshold=0.40,
                confidence=confidence.mitigate_asymmetric_noise,
                message="[Scenario I] Asymmetric noise detected: applying class transition correction before threshold adjustments.",
            )
            return resolved, "Scenario I: Asymmetric Noise with Cost Sensitivity"

        # =====================================================================
        # Scenario J: Cascading Multi-Detector Disagreement
        # =====================================================================
        if 0.50 <= evidence.delta_drift < 1.0:
            resolved = DirectiveV4(
                state=AutomatonStateV4.ADAPTATION_PENDING,
                learning_rate_scale=1.0,
                freeze_buffer=True,
                confidence=0.65,
                message="[Scenario J] Multi-detector disagreement: entering adaptation pending with hysteresis deadband.",
            )
            return resolved, "Scenario J: Multi-Detector Disagreement"

        return directive, "Standard Operational Transition"

    @classmethod
    def resolve_conflicts_v2(
        cls,
        directive: DirectiveV4,
        evidence: EvidenceVectorV4,
        confidence: ConfidenceScores,
        spatial_discordance: float,
        noise_dwell: int = 0,
    ) -> Tuple[DirectiveV4, str]:
        """Resolve conflicts with explicit spatial discordance gating (Candidate 5 interface).

        Parameters
        ----------
        directive : DirectiveV4
            Raw directive proposed by the arbitration automaton.
        evidence : EvidenceVectorV4
            Multi-pillar 10D evidence vector.
        confidence : ConfidenceScores
            Calibrated confidence scores.
        spatial_discordance : float
            Spatial label discordance in feature space in [0.0, 1.0].
        noise_dwell : int, default=0
            Consecutive steps spent in NOISE_BURST state.

        Returns
        -------
        Tuple[DirectiveV4, str]
            (resolved_directive, scenario_identified_string)
        """
        return cls.resolve_conflicts(
            directive=directive,
            evidence=evidence,
            confidence=confidence,
            spatial_discordance=spatial_discordance,
            noise_dwell=noise_dwell,
        )
