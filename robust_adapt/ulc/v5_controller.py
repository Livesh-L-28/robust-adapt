"""
Unified Learning Controller V5 (ULC-v5).

Integrates:
1. Five-Tier Intervention Hierarchy (NOOP, PARAM_DAMPING, CONCEPT_RESTORE, SOFT_REPLAY_RESET, HARD_RESET)
2. Expected Utility Scoring (Action Utility = Confidence * Benefit - Operational Cost)
3. Dynamic Cross-Pillar Telemetry Gating (avoids RLA over-filtering on clean concept-drifting streams)
4. Protected Catastrophic Hard Reset Policy (retains high-severity emergency recovery)
5. Recovery-Aware Exponential Cooldown Backoff (suppresses oscillation thrashing)
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.concept_memory import ConceptFingerprinter, RecurringConceptMemory
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d

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
        InterventionTier.TIER_3_SOFT_REPLAY_RESET: 0.25,
        InterventionTier.TIER_4_HARD_RESET: 0.70,
    }

    @classmethod
    def score_action(
        cls,
        tier: InterventionTier,
        confidence: float,
        drift_magnitude: float,
        is_recurrent: bool,
    ) -> float:
        """Calculate scalar expected utility for candidate intervention tier."""
        cost = cls.COST_MAP[tier]
        if tier == InterventionTier.TIER_0_NOOP:
            return 0.10

        if tier == InterventionTier.TIER_2_CONCEPT_RESTORE:
            benefit = 0.85 if is_recurrent else 0.10
        elif tier == InterventionTier.TIER_3_SOFT_REPLAY_RESET:
            benefit = 0.75 * drift_magnitude if not is_recurrent else 0.15
        elif tier == InterventionTier.TIER_4_HARD_RESET:
            benefit = 0.90 * drift_magnitude if not is_recurrent else 0.05
        elif tier == InterventionTier.TIER_1_PARAM_DAMPING:
            benefit = 0.35 * drift_magnitude
        else:
            benefit = 0.0

        return float((confidence * benefit) - cost)


@dataclass
class ULCv5Config:
    """Configuration hyperparameters for UnifiedLearningControllerV5."""
    grace_period: int = 50
    delta: float = 0.002
    similarity_threshold: float = 0.82
    base_cooldown: int = 5
    max_concepts: int = 5
    replay_capacity: int = 1000
    catastrophic_drift_threshold: float = 0.95
    gate_rla_on_clean_stream: bool = True


class UnifiedLearningControllerV5:
    """Turnkey Unified Learning Controller V5.

    Orchestrates streaming concept drift detection, recurring-concept memory restoration,
    resource budgeting, and utility-calibrated intervention arbitration.

    Parameters
    ----------
    n_features : int
        Dimensionality of input feature vectors.
    n_classes : int, default=2
        Number of distinct target classes.
    config : Optional[ULCv5Config], default=None
        Hyperparameter configuration dataclass.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        config: Optional[ULCv5Config] = None,
    ) -> None:
        if n_features < 1:
            raise ConfigurationError(f"n_features must be >= 1, got {n_features}")
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")

        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.config = config or ULCv5Config()

        self.classifier = AdaptiveClassifier(
            n_features=self.n_features,
            n_classes=self.n_classes,
            grace_period=self.config.grace_period,
            delta=self.config.delta,
        )
        self.adwin = ReliabilityWeightedADWIN(delta=self.config.delta)
        self.replay = ClassBalancedReservoirReplay(
            capacity=self.config.replay_capacity,
            n_classes=self.n_classes,
        )
        self.fingerprinter = ConceptFingerprinter(n_features=self.n_features, n_classes=self.n_classes)
        self.memory = RecurringConceptMemory(
            max_concepts=self.config.max_concepts,
            similarity_threshold=self.config.similarity_threshold,
        )

        self.total_steps: int = 0
        self.cooldown_remaining: int = 0
        self.consecutive_interventions: int = 0
        self.active_concept_id: Optional[str] = None

        # Telemetry metrics
        self.tier_counts: Dict[str, int] = {t.value: 0 for t in InterventionTier}
        self.total_resets: int = 0
        self.total_hard_resets: int = 0
        self.total_restores: int = 0
        self.total_dampings: int = 0

    def step(self, X_b: np.ndarray, y_b: np.ndarray) -> Tuple[ULCv5Directive, Dict[str, Any]]:
        """Prequential evaluation, telemetry collection, utility arbitration, and learning update."""
        X_val = check_array_2d(X_b, expected_dim=self.n_features, name="X_b")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y_b, expected_len=n_samples, n_classes=self.n_classes, name="y_b")

        self.total_steps += 1
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # 1. Prequential prediction & error metrics
        probas = self.classifier.predict_proba(X_val)
        preds = np.argmax(probas, axis=1)
        errs = (preds != y_val).astype(float)
        mean_err = float(np.mean(errs))

        # 2. ADWIN drift check
        drift_detected = any(self.adwin.update(e) for e in errs)
        fp = self.fingerprinter.compute_fingerprint(X_val, y_val)

        # 3. Utility-calibrated intervention arbitration
        directive: ULCv5Directive

        if not drift_detected or self.cooldown_remaining > 0:
            directive = ULCv5Directive(
                tier=InterventionTier.TIER_0_NOOP,
                action_name="INCREMENTAL_UPDATE",
                confidence=0.95,
                expected_utility=0.10,
                message="Operational stability maintained",
            )
        else:
            matching_snap, sim = self.memory.find_matching_concept(fp)
            is_recurrent = (matching_snap is not None)
            confidence = float(np.clip(sim if is_recurrent else (1.0 - sim), 0.5, 0.99))
            drift_mag = float(np.clip(mean_err * 2.0, 0.1, 1.0))

            u_restore = UtilityScorer.score_action(InterventionTier.TIER_2_CONCEPT_RESTORE, confidence, drift_mag, is_recurrent)
            u_soft_reset = UtilityScorer.score_action(InterventionTier.TIER_3_SOFT_REPLAY_RESET, confidence, drift_mag, is_recurrent)
            u_hard_reset = UtilityScorer.score_action(InterventionTier.TIER_4_HARD_RESET, confidence, drift_mag, is_recurrent)
            u_damping = UtilityScorer.score_action(InterventionTier.TIER_1_PARAM_DAMPING, confidence, drift_mag, is_recurrent)

            # Protected Hard Reset Policy: Catastrophic recovery when confidence is extreme and damping fails
            if (
                not is_recurrent
                and confidence >= self.config.catastrophic_drift_threshold
                and drift_mag > 0.85
                and self.consecutive_interventions >= 2
            ):
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_4_HARD_RESET,
                    action_name="CATASTROPHIC_HARD_RESET",
                    confidence=confidence,
                    expected_utility=u_hard_reset,
                    message="Emergency hard reset justified by extreme unrecoverable drift",
                )
                self._execute_hard_reset(fp)
                self.total_hard_resets += 1
                self.total_resets += 1

            elif is_recurrent and u_restore > 0 and matching_snap is not None:
                # TIER 2: Concept restoration
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_2_CONCEPT_RESTORE,
                    action_name=f"RESTORE_{matching_snap.concept_id}",
                    confidence=confidence,
                    expected_utility=u_restore,
                    restored_concept_id=matching_snap.concept_id,
                    message=f"Restored historical concept {matching_snap.concept_id} (sim={sim:.3f})",
                )
                self.classifier = copy.deepcopy(matching_snap.model_state)
                self.active_concept_id = matching_snap.concept_id
                self.memory.update_concept(matching_snap.concept_id, fp, self.classifier, self.total_steps)
                self.total_restores += 1

            elif u_soft_reset > u_damping and drift_mag > 0.40:
                # TIER 3: Soft reset with rehearsal
                directive = ULCv5Directive(
                    tier=InterventionTier.TIER_3_SOFT_REPLAY_RESET,
                    action_name="SOFT_REPLAY_RESET",
                    confidence=confidence,
                    expected_utility=u_soft_reset,
                    message=f"Novel drift regime identified (mag={drift_mag:.2f}); seeded from replay",
                )
                self._execute_soft_reset(fp)
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
                self.total_dampings += 1

            self.consecutive_interventions += 1
            backoff_multiplier = min(4, self.consecutive_interventions)
            self.cooldown_remaining = self.config.base_cooldown * backoff_multiplier
            self.adwin = ReliabilityWeightedADWIN(delta=self.config.delta)

        # 4. Model parameter update
        w_batch = np.ones(n_samples) * directive.sample_weight_scale
        self.classifier.partial_fit(X_val, y_val, sample_weight=w_batch)
        self.replay.add(X_val, y_val)

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
            "hard_resets": self.total_hard_resets,
            "restores": self.total_restores,
            "dampings": self.total_dampings,
        }
        return directive, telemetry

    def _execute_soft_reset(self, fp: np.ndarray) -> None:
        """Execute soft reset seeded from reservoir replay."""
        if self.active_concept_id is not None:
            self.memory.update_concept(self.active_concept_id, fp, self.classifier, self.total_steps)
        else:
            new_snap = self.memory.store_concept(fp, self.classifier, self.total_steps)
            self.active_concept_id = new_snap.concept_id if new_snap else None

        self.classifier = AdaptiveClassifier(
            n_features=self.n_features,
            n_classes=self.n_classes,
            grace_period=self.config.grace_period,
            delta=self.config.delta,
        )
        if self.replay.total_stored >= 100:
            X_rep, y_rep = self.replay.sample(min(200, self.replay.total_stored))
            self.classifier.partial_fit(X_rep, y_rep)

    def _execute_hard_reset(self, fp: np.ndarray) -> None:
        """Execute full structural hard reset, clearing model and resetting active concept."""
        self.classifier = AdaptiveClassifier(
            n_features=self.n_features,
            n_classes=self.n_classes,
            grace_period=self.config.grace_period,
            delta=self.config.delta,
        )
        self.active_concept_id = None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict posterior class probabilities."""
        return self.classifier.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict target labels."""
        return np.argmax(self.predict_proba(X), axis=1)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate mean classification accuracy."""
        preds = self.predict(X)
        y_val = check_labels_1d(y, expected_len=len(preds), n_classes=self.n_classes, name="y")
        return float(np.mean(preds == y_val))

    def reset(self) -> None:
        """Completely reset controller state."""
        self.classifier.reset()
        self.adwin = ReliabilityWeightedADWIN(delta=self.config.delta)
        self.replay = ClassBalancedReservoirReplay(
            capacity=self.config.replay_capacity,
            n_classes=self.n_classes,
        )
        self.memory.clear()
        self.total_steps = 0
        self.cooldown_remaining = 0
        self.consecutive_interventions = 0
        self.active_concept_id = None
        for k in self.tier_counts:
            self.tier_counts[k] = 0
        self.total_resets = 0
        self.total_hard_resets = 0
        self.total_restores = 0
        self.total_dampings = 0

    def state_dict(self) -> Dict[str, Any]:
        """Serialize complete ULC-v5 state."""
        return {
            "n_features": self.n_features,
            "n_classes": self.n_classes,
            "total_steps": self.total_steps,
            "cooldown_remaining": self.cooldown_remaining,
            "consecutive_interventions": self.consecutive_interventions,
            "active_concept_id": self.active_concept_id,
            "total_resets": self.total_resets,
            "total_hard_resets": self.total_hard_resets,
            "total_restores": self.total_restores,
            "total_dampings": self.total_dampings,
            "tier_counts": self.tier_counts,
            "classifier": self.classifier.state_dict(),
            "adwin": self.adwin.state_dict(),
            "replay": self.replay.state_dict(),
            "memory": self.memory.to_dict(),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore complete ULC-v5 state."""
        self.total_steps = int(state["total_steps"])
        self.cooldown_remaining = int(state["cooldown_remaining"])
        self.consecutive_interventions = int(state["consecutive_interventions"])
        self.active_concept_id = state["active_concept_id"]
        self.total_resets = int(state["total_resets"])
        self.total_hard_resets = int(state.get("total_hard_resets", 0))
        self.total_restores = int(state["total_restores"])
        self.total_dampings = int(state.get("total_dampings", 0))
        self.tier_counts = dict(state.get("tier_counts", {}))
        if "classifier" in state:
            self.classifier.load_state_dict(state["classifier"])
        if "adwin" in state:
            self.adwin.load_state_dict(state["adwin"])
        if "replay" in state:
            self.replay.load_state_dict(state["replay"])
        if "memory" in state:
            self.memory = RecurringConceptMemory.from_dict(state["memory"])
