"""
Stage 12 — Workstream E: ULC-v5 Evidence-Based Intervention Calibration.

Implements the next-generation Unified Learning Controller (ULC-v5) with:
1. Multi-Tier Intervention Hierarchy (TIER_0 No-op to TIER_4 Hard Reset)
2. Expected Utility Scoring (Action Utility = Confidence * Benefit - Operational Cost)
3. Recovery-Aware Dynamic Cooldown (exponential backoff against reset oscillation)
4. Concept Memory Coordination (restoration prioritized over structural reset)
5. Evidence Confidence Calibration & Safe Abstention under Epistemic Ambiguity
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay
from experiments.stage_12.ala_3_0.recurrent_ala import ConceptFingerprinter, RecurringConceptMemory

logger = logging.getLogger(__name__)


class InterventionTier(str, Enum):
    """5-level hierarchical intervention severity."""
    TIER_0_NOOP = "TIER_0_NOOP"
    TIER_1_PARAM_DAMPING = "TIER_1_PARAM_DAMPING"
    TIER_2_CONCEPT_RESTORE = "TIER_2_CONCEPT_RESTORE"
    TIER_3_SOFT_REPLAY_RESET = "TIER_3_SOFT_REPLAY_RESET"
    TIER_4_HARD_RESET = "TIER_4_HARD_RESET"


@dataclass(frozen=True)
class ULCv5Directive:
    """Action directive emitted by ULC-v5."""
    tier: InterventionTier
    action_name: str
    confidence: float
    expected_utility: float
    restored_concept_id: Optional[str] = None
    learning_rate_scale: float = 1.0
    sample_weight_scale: float = 1.0
    message: str = ""


class UtilityScorer:
    """Computes expected intervention utility based on evidence confidence and operational cost."""

    COST_MAP = {
        InterventionTier.TIER_0_NOOP: 0.0,
        InterventionTier.TIER_1_PARAM_DAMPING: 0.05,
        InterventionTier.TIER_2_CONCEPT_RESTORE: 0.15,
        InterventionTier.TIER_3_SOFT_REPLAY_RESET: 0.45,
        InterventionTier.TIER_4_HARD_RESET: 0.85,
    }

    @classmethod
    def score_action(
        cls,
        tier: InterventionTier,
        confidence: float,
        drift_magnitude: float,
        is_recurrent: bool,
    ) -> float:
        cost = cls.COST_MAP[tier]
        if tier == InterventionTier.TIER_0_NOOP:
            return 0.1  # Default positive bias for stability

        if tier == InterventionTier.TIER_2_CONCEPT_RESTORE:
            benefit = 0.85 if is_recurrent else 0.1
        elif tier == InterventionTier.TIER_3_SOFT_REPLAY_RESET:
            benefit = 0.70 * drift_magnitude if not is_recurrent else 0.2
        elif tier == InterventionTier.TIER_4_HARD_RESET:
            benefit = 0.90 * drift_magnitude if (not is_recurrent and drift_magnitude > 0.8) else 0.05
        elif tier == InterventionTier.TIER_1_PARAM_DAMPING:
            benefit = 0.40 * drift_magnitude
        else:
            benefit = 0.0

        utility = (confidence * benefit) - cost
        return float(utility)


class UnifiedLearningControllerV5:
    """
    Unified Learning Controller V5 (ULC-v5).
    Calibrates all cross-pillar interventions to eliminate unnecessary resets while
    maintaining high-fidelity drift responsiveness and noise resilience.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        grace_period: int = 50,
        delta: float = 0.002,
        similarity_threshold: float = 0.82,
        base_cooldown: int = 5,
        max_concepts: int = 5,
    ):
        self.n_features = n_features
        self.n_classes = n_classes
        self.grace_period = grace_period
        self.delta = delta
        self.base_cooldown = base_cooldown

        self.classifier = AdaptiveClassifier(
            n_features=n_features,
            n_classes=n_classes,
            grace_period=grace_period,
            delta=delta,
        )
        self.adwin = ReliabilityWeightedADWIN(delta=delta)
        self.replay = ClassBalancedReservoirReplay(capacity=1000, n_classes=n_classes)
        self.fingerprinter = ConceptFingerprinter(n_features=n_features, n_classes=n_classes)
        self.memory = RecurringConceptMemory(max_concepts=max_concepts, similarity_threshold=similarity_threshold)

        self.total_steps = 0
        self.cooldown_remaining = 0
        self.consecutive_interventions = 0
        self.active_concept_id: Optional[str] = None

        # Telemetry counts
        self.tier_counts: Dict[str, int] = {t.value: 0 for t in InterventionTier}
        self.total_resets = 0
        self.total_restores = 0

    def step(self, X_b: np.ndarray, y_b: np.ndarray) -> Tuple[ULCv5Directive, Dict[str, Any]]:
        self.total_steps += 1
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # 1. Prequential prediction & error evaluation
        probas = self.classifier.predict_proba(X_b)
        preds = np.argmax(probas, axis=1)
        errs = (preds != y_b).astype(float)
        mean_err = float(np.mean(errs))

        # 2. ADWIN drift check
        drift_detected = any(self.adwin.update(e) for e in errs)
        fp = self.fingerprinter.compute_fingerprint(X_b, y_b)

        # 3. Decision arbitration
        directive: ULCv5Directive

        if not drift_detected or self.cooldown_remaining > 0:
            # Stable operation or in cooldown
            directive = ULCv5Directive(
                tier=InterventionTier.TIER_0_NOOP,
                action_name="INCREMENTAL_UPDATE",
                confidence=0.95,
                expected_utility=0.10,
                message="Operational stability maintained",
            )
        else:
            # Drift detected: evaluate recurring match vs novel concept
            matching_snap, sim = self.memory.find_matching_concept(fp)
            is_recurrent = (matching_snap is not None)
            confidence = float(np.clip(sim if is_recurrent else (1.0 - sim), 0.5, 0.99))
            drift_mag = float(np.clip(mean_err * 2.0, 0.1, 1.0))

            # Score candidates
            u_restore = UtilityScorer.score_action(InterventionTier.TIER_2_CONCEPT_RESTORE, confidence, drift_mag, is_recurrent)
            u_soft_reset = UtilityScorer.score_action(InterventionTier.TIER_3_SOFT_REPLAY_RESET, confidence, drift_mag, is_recurrent)
            u_damping = UtilityScorer.score_action(InterventionTier.TIER_1_PARAM_DAMPING, confidence, drift_mag, is_recurrent)

            if is_recurrent and u_restore > 0 and matching_snap is not None:
                # TIER 2: Concept restoration
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_2_CONCEPT_RESTORE,
                    action_name=f"RESTORE_{matching_snap.concept_id}",
                    confidence=confidence,
                    expected_utility=u_restore,
                    restored_concept_id=matching_snap.concept_id,
                    message=f"Restored historical concept {matching_snap.concept_id} (sim={sim:.3f})",
                )
                self.classifier = copy.deepcopy(matching_snap.classifier)
                self.active_concept_id = matching_snap.concept_id
                self.memory.update_concept(matching_snap.concept_id, fp, self.classifier, self.total_steps)
                self.total_restores += 1

            elif u_soft_reset > u_damping and drift_mag > 0.40:
                # TIER 3: Soft reset with replay
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_3_SOFT_REPLAY_RESET,
                    action_name="SOFT_REPLAY_RESET",
                    confidence=confidence,
                    expected_utility=u_soft_reset,
                    message=f"Novel drift regime identified (mag={drift_mag:.2f}); seeded from replay",
                )
                # Store prior concept before reset
                if self.active_concept_id is not None:
                    self.memory.update_concept(self.active_concept_id, fp, self.classifier, self.total_steps)
                else:
                    new_snap = self.memory.store_concept(fp, self.classifier, self.total_steps)
                    self.active_concept_id = new_snap.concept_id

                self.classifier = AdaptiveClassifier(
                    n_features=self.n_features,
                    n_classes=self.n_classes,
                    grace_period=self.grace_period,
                    delta=self.delta,
                )
                if self.replay.total_stored >= 100:
                    X_rep, y_rep = self.replay.sample(min(200, self.replay.total_stored))
                    self.classifier.partial_fit(X_rep, y_rep)
                self.total_resets += 1

            else:
                # TIER 1: Parameter damping without structural reset
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_1_PARAM_DAMPING,
                    action_name="DAMP_AND_MONITOR",
                    confidence=confidence,
                    expected_utility=max(u_damping, 0.05),
                    sample_weight_scale=0.80,
                    message="Mild variance elevation; damped sample weights without reset",
                )

            # Apply recovery cooldown with exponential backoff
            self.consecutive_interventions += 1
            backoff_multiplier = min(4, self.consecutive_interventions)
            self.cooldown_remaining = self.base_cooldown * backoff_multiplier
            self.adwin = ReliabilityWeightedADWIN(delta=self.delta)

        # 4. Partial fit on current batch
        w_batch = np.ones(len(y_b)) * directive.sample_weight_scale
        self.classifier.partial_fit(X_b, y_b, sample_weight=w_batch)
        self.replay.add(X_b, y_b)

        self.tier_counts[directive.tier.value] += 1
        if directive.tier == InterventionTier.TIER_0_NOOP:
            self.consecutive_interventions = max(0, self.consecutive_interventions - 1)

        telemetry = {
            "step": self.total_steps,
            "tier": directive.tier.value,
            "action": directive.action_name,
            "confidence": directive.confidence,
            "utility": directive.expected_utility,
            "error_rate": mean_err,
            "resets": self.total_resets,
            "restores": self.total_restores,
        }
        return directive, telemetry

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.classifier.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

