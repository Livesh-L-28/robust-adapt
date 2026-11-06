"""Integration tests for Stage 7: ULC-v4 Unified Learning Intelligence.

Verifies cross-pillar conflict resolution across Scenarios A through J,
the 12-state finite automaton, and natural language explainability.
"""

import numpy as np
import pytest

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.minority.prior import OnlineClassPriorTracker
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.ulc.confidence import ConfidenceEngine
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.explainer import ULCExplainer
from robust_adapt.ulc.v4_automaton import (
    ArbitrationAutomatonV4,
    AutomatonStateV4,
    DirectiveV4,
)
from robust_adapt.ulc.v4_controller import UnifiedLearningControllerV4
from robust_adapt.ulc.v4_evidence import EvidenceSynthesizerV4, EvidenceVectorV4


class TestULCv4ScenariosAthroughJ:
    """Verifies deterministic conflict resolution across Scenarios A through J."""

    def setup_method(self) -> None:
        self.automaton = ArbitrationAutomatonV4()
        self.resolver = CrossPillarConflictResolver()
        self.conf_engine = ConfidenceEngine()

    def test_scenario_a_drift_alarm_during_severe_noise_burst(self) -> None:
        # High delta (1.4), but low reliability (0.25) -> NOISE_BURST
        ev = EvidenceVectorV4(delta_drift=1.4, mean_reliability=0.25)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario A" in name
        assert resolved.state == AutomatonStateV4.NOISE_BURST
        assert resolved.suppress_adwin is True
        assert resolved.freeze_buffer is True
        assert resolved.sample_filter_threshold > 0.0

    def test_scenario_b_extreme_imbalance_with_concept_drift(self) -> None:
        # High delta (1.2), clean reliability (0.90), extreme imbalance (IR=50.0)
        ev = EvidenceVectorV4(delta_drift=1.2, mean_reliability=0.90, imbalance_ratio=50.0)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario B" in name
        assert resolved.state == AutomatonStateV4.CONFIRMED_DRIFT
        assert resolved.learning_rate_scale == 2.5
        assert resolved.reset_momentum is True
        assert resolved.purge_replay_policy == "selective"
        assert resolved.keep_minority_in_replay is True

    def test_scenario_c_budget_ceiling_breached_during_drift(self) -> None:
        # High delta (1.5), resource ceiling breached (u_res=0.92)
        ev = EvidenceVectorV4(delta_drift=1.5, mean_reliability=0.85, resource_utilization=0.92)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario C" in name
        assert resolved.state == AutomatonStateV4.RESOURCE_CONSTRAINED
        assert resolved.batch_size_scale == 0.50
        assert resolved.skip_expensive_ops is True

    def test_scenario_d_recurring_concept_drift_detected(self) -> None:
        # High recurring similarity (0.88), delta (0.80)
        ev = EvidenceVectorV4(delta_drift=0.80, mean_reliability=0.85, recurring_similarity=0.88)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario D" in name
        assert resolved.state == AutomatonStateV4.COOLDOWN
        assert resolved.restore_concept_id == "matched_recurring"
        assert resolved.purge_replay_policy == "none"

    def test_scenario_e_epistemic_boundary_uncertainty(self) -> None:
        # High entropy (0.85), high reliability (0.80)
        ev = EvidenceVectorV4(predictive_entropy=0.85, mean_reliability=0.80)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario E" in name
        assert resolved.state == AutomatonStateV4.ELEVATED_VARIANCE
        assert resolved.suppress_adwin is False
        assert resolved.freeze_buffer is False

    def test_scenario_f_adversarial_inverted_label(self) -> None:
        # Very low entropy (0.10, overconfident), very low reliability (0.20, corrupt)
        ev = EvidenceVectorV4(predictive_entropy=0.10, mean_reliability=0.20)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario F" in name
        assert resolved.state == AutomatonStateV4.NOISE_BURST
        assert resolved.correct_labels is True

    def test_scenario_g_delayed_labels_during_recovery(self) -> None:
        # In recovery state, feedback observed delay is large (25 steps)
        ev = EvidenceVectorV4(observed_delay=25.0)
        dir_recovery = DirectiveV4(state=AutomatonStateV4.RECOVERY, learning_rate_scale=1.8)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(dir_recovery, ev, conf)

        assert "Scenario G" in name
        assert resolved.state == AutomatonStateV4.RECOVERY
        assert resolved.sample_filter_threshold > 0.0

    def test_scenario_h_emerging_class_under_resource_pressure(self) -> None:
        # Emerging class flag true, resource utilization high (0.90)
        ev = EvidenceVectorV4(is_emerging_class=True, resource_utilization=0.90)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario H" in name
        assert resolved.state == AutomatonStateV4.RESOURCE_CONSTRAINED
        assert resolved.keep_minority_in_replay is True
        assert resolved.batch_size_scale == 0.50

    def test_scenario_i_asymmetric_noise_mitigation(self) -> None:
        # High asymmetric noise rate (0.25)
        ev = EvidenceVectorV4(asymmetric_noise_rate=0.25)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario I" in name
        assert resolved.state == AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION
        assert resolved.correct_labels is True

    def test_scenario_j_multi_detector_disagreement(self) -> None:
        # Delta in warning / disagreement deadband: 0.70
        ev = EvidenceVectorV4(delta_drift=0.70, mean_reliability=0.80)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)

        assert "Scenario J" in name
        assert resolved.state == AutomatonStateV4.ADAPTATION_PENDING
        assert resolved.freeze_buffer is True


class TestULCv4UnifiedPipeline:
    """Verifies end-to-end integration of UnifiedLearningControllerV4 with all pillars connected."""

    def test_controller_step_and_explainability(self) -> None:
        clf = AdaptiveClassifier(n_features=4, n_classes=2, replay_capacity=100)
        X_init = np.vstack([np.ones((20, 4)), -np.ones((20, 4))])
        y_init = np.array([1] * 20 + [0] * 20)
        clf.fit(X_init, y_init)

        param = np.random.randn(8, 4).astype(np.float32)
        grad = np.random.randn(8, 4).astype(np.float32)
        p_obj = type("P", (), {"data": param, "grad": grad})()
        opt = LowMemoryAdamW([p_obj], lr=0.01)
        budget = DynamicResourceBudgetManager(max_memory_mb=4096.0)
        prior = OnlineClassPriorTracker(n_classes=2)

        ctrl = UnifiedLearningControllerV4(
            classifier=clf,
            optimizer=opt,
            budget_manager=budget,
            prior_tracker=prior,
        )

        X = np.vstack([np.ones((10, 4)), -np.ones((10, 4))])
        y = np.array([1] * 10 + [0] * 10)
        # Confident logits reflecting known class posteriors
        logits = np.array([[-3.0, 3.0]] * 10 + [[3.0, -3.0]] * 10)

        # Step 1: Nominal operation
        d1, info1 = ctrl.step(X, y, logits=logits)
        assert d1.state == AutomatonStateV4.STABLE
        assert "explanation" in info1
        assert "narrative" in info1["explanation"]
        assert "Controller State: STABLE" in info1["explanation"]["narrative"]

        # Step 2: Injected drift under clean conditions
        d2, info2 = ctrl.step(X, y, logits=logits, delta_drift=1.5)
        assert d2.state == AutomatonStateV4.CONFIRMED_DRIFT
        assert d2.reset_momentum is True
        assert d2.purge_replay_policy in ("selective", "partial")

        # Step 3: Transition to recovery
        d3, info3 = ctrl.step(X, y, logits=logits, delta_drift=0.1)
        assert d3.state == AutomatonStateV4.RECOVERY
        assert d3.dwell_remaining > 0
