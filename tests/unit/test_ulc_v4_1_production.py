"""
Unit, Contract, Integration, and Regression Test Suite for Production ULC-v4.1.

Tests the promoted modules:
- robust_adapt.ulc.spatial: compute_spatial_discordance
- robust_adapt.ulc.conflict_resolver: resolve_conflicts with spatial discordance
- robust_adapt.ulc.v4_1_controller: ULCv41Config, UnifiedLearningControllerV4_1
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.minority import OnlineClassPriorTracker, AdaptiveThresholdManager
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.rla.pipeline import RobustLearningPipeline
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine
from robust_adapt.state.serializer import load_state, save_state
from robust_adapt.ulc.confidence import ConfidenceEngine
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.spatial import compute_spatial_discordance
from robust_adapt.ulc.v4_automaton import (
    ArbitrationAutomatonV4,
    AutomatonStateV4,
    DirectiveV4,
)
from robust_adapt.ulc.v4_evidence import EvidenceVectorV4
from robust_adapt.ulc.v4_1_controller import ULCv41Config, UnifiedLearningControllerV4_1


# =============================================================================
# 1. Unit Tests: Spatial Discordance Engine
# =============================================================================
class TestSpatialDiscordanceUnit:
    """Verifies nearest-neighbor spatial discordance calculations."""

    def test_perfectly_coherent_clusters(self) -> None:
        # Two well-separated clusters with consistent labels
        c0 = np.random.randn(20, 2) - 10.0
        c1 = np.random.randn(20, 2) + 10.0
        X = np.vstack([c0, c1])
        y = np.array([0] * 20 + [1] * 20, dtype=np.int64)

        disc = compute_spatial_discordance(X, y, k=5)
        assert disc == 0.0

    def test_maximally_corrupted_labels(self) -> None:
        # Uniform feature space with alternating labels
        np.random.seed(42)
        X = np.random.randn(100, 2)
        # Random binary labels in the same cluster
        y = np.random.choice([0, 1], size=100)

        disc = compute_spatial_discordance(X, y, k=5)
        assert disc > 0.40  # Random labels yield ~0.50 discordance

    def test_insufficient_samples_boundary(self) -> None:
        # If n <= k, defaults safely to 0.0
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([0, 1])
        disc = compute_spatial_discordance(X, y, k=5)
        assert disc == 0.0

    def test_invalid_parameters_raise_error(self) -> None:
        X = np.random.randn(10, 2)
        y = np.zeros(10, dtype=np.int64)

        with pytest.raises(ValueError, match="k must be a positive integer"):
            compute_spatial_discordance(X, y, k=0)

        with pytest.raises(ValueError, match="Unsupported metric"):
            compute_spatial_discordance(X, y, k=3, metric="cosine")


# =============================================================================
# 2. Unit Tests: ULCv41Config Hyperparameter Validation
# =============================================================================
class TestULCv41ConfigUnit:
    """Verifies hyperparameter validation in ULCv41Config."""

    def test_valid_default_config(self) -> None:
        cfg = ULCv41Config()
        assert cfg.spatial_k == 5
        assert cfg.spatial_discordance_threshold == 0.25
        assert cfg.prior_freeze_threshold == 0.30
        assert cfg.max_noise_dwell == 20

    def test_invalid_thresholds_raise_error(self) -> None:
        with pytest.raises(ValueError, match="spatial_k must be >= 1"):
            ULCv41Config(spatial_k=0)

        with pytest.raises(ValueError, match="spatial_discordance_threshold must be in"):
            ULCv41Config(spatial_discordance_threshold=1.5)

        with pytest.raises(ValueError, match="gamma_smoothing must be in"):
            ULCv41Config(gamma_smoothing=0.0)

        with pytest.raises(ValueError, match="max_noise_dwell must be >= 1"):
            ULCv41Config(max_noise_dwell=0)


# =============================================================================
# 3. Unit Tests: Conflict Resolver Spatial Gating & Backward Compatibility
# =============================================================================
class TestConflictResolverUnit:
    """Verifies conflict resolution under spatial discordance and legacy calls."""

    def setup_method(self) -> None:
        self.resolver = CrossPillarConflictResolver()
        self.automaton = ArbitrationAutomatonV4()
        self.conf_engine = ConfidenceEngine()

    def test_legacy_call_without_spatial_discordance(self) -> None:
        ev = EvidenceVectorV4(delta_drift=1.2, mean_reliability=0.30)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)

        # Legacy call with 3 arguments
        resolved, name = self.resolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario A: Noise vs Drift"
        assert resolved.state == AutomatonStateV4.NOISE_BURST

    def test_spatial_gating_verified_drift(self) -> None:
        ev = EvidenceVectorV4(delta_drift=1.2, mean_reliability=0.30)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)

        # Coherent features (discordance <= 0.25) resolves to genuine drift
        resolved, name = self.resolver.resolve_conflicts(
            directive, ev, conf, spatial_discordance=0.10
        )
        assert name == "Scenario A: Resolved Genuine Drift"
        assert resolved.state == AutomatonStateV4.CONFIRMED_DRIFT
        assert resolved.learning_rate_scale == 2.5
        assert resolved.reset_momentum is True

    def test_spatial_gating_verified_noise(self) -> None:
        ev = EvidenceVectorV4(delta_drift=1.2, mean_reliability=0.30)
        directive = self.automaton.transition(ev)
        conf = self.conf_engine.evaluate(ev)

        # Discordant features (discordance > 0.25) resolves to noise burst
        resolved, name = self.resolver.resolve_conflicts(
            directive, ev, conf, spatial_discordance=0.60
        )
        assert "Verified Noise" in name
        assert resolved.state == AutomatonStateV4.NOISE_BURST
        assert resolved.suppress_adwin is True
        assert resolved.freeze_buffer is True


# =============================================================================
# 4. Contract Tests: Cross-Pillar Integration & Safe Fallbacks
# =============================================================================
class TestPillarContractIntegration:
    """Verifies contracts across ALA, RLA, RAO, Minority, and graceful degradation."""

    def test_standalone_controller_without_submodules(self) -> None:
        # ULC-v4.1 must operate seamlessly even if no pillars are connected
        ctrl = UnifiedLearningControllerV4_1()
        X = np.random.randn(25, 4)
        y = np.random.choice([0, 1], size=25)

        directive, telemetry = ctrl.step(X, y)
        assert directive.state in AutomatonStateV4
        assert "spatial_discordance" in telemetry
        assert telemetry["n_retained_samples"] == 25

    def test_ala_tree_and_optimizer_contract(self) -> None:
        clf = AdaptiveClassifier(n_classes=2, grace_period=10, n_features=4)
        params = [np.zeros((4, 4), dtype=np.float32)]
        opt = LowMemoryAdamW(params, lr=0.01)
        ctrl = UnifiedLearningControllerV4_1(classifier=clf, optimizer=opt)

        X = np.random.randn(30, 4)
        y = np.random.choice([0, 1], size=30)
        clf.fit(X, y)

        # Trigger drift step
        directive, telemetry = ctrl.step(X, y, delta_drift=1.5)
        # Should execute without errors and maintain valid state
        assert ctrl.total_steps == 1
        assert opt.param_groups[0]["lr"] > 0.0

    def test_minority_prior_gated_under_noise(self) -> None:
        prior_tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.9)
        thresh_mgr = AdaptiveThresholdManager(n_classes=2)
        ctrl = UnifiedLearningControllerV4_1(
            prior_tracker=prior_tracker,
            threshold_manager=thresh_mgr,
            config=ULCv41Config(prior_freeze_threshold=0.30),
        )

        # 1. Clean batch (discordance 0.0) -> prior updates
        c0 = np.random.randn(15, 2) - 5.0
        c1 = np.random.randn(15, 2) + 5.0
        X_clean = np.vstack([c0, c1])
        y_clean = np.array([0] * 15 + [1] * 15, dtype=np.int64)
        ctrl.step(X_clean, y_clean)
        priors_before = np.copy(prior_tracker.priors)

        # 2. Corrupted noise batch (discordance > 0.40) -> prior frozen
        np.random.seed(42)
        X_noise = np.random.randn(30, 2)
        y_noise = np.random.choice([0, 1], size=30)
        ctrl.step(X_noise, y_noise)
        priors_after = prior_tracker.priors

        # Under noise burst, prior tracker was frozen!
        np.testing.assert_allclose(priors_before, priors_after)


# =============================================================================
# 5. Integration Tests: All Ten Scenarios A Through J
# =============================================================================
class TestAllTenScenariosUnderULCv41:
    """Verifies that all ten conflict scenarios (A-J) resolve correctly."""

    def setup_method(self) -> None:
        self.ctrl = UnifiedLearningControllerV4_1()

    def test_scenario_a_verified_drift_and_noise(self) -> None:
        # Verified drift: high delta, coherent features
        c0 = np.random.randn(20, 2) - 10.0
        c1 = np.random.randn(20, 2) + 10.0
        X_coherent = np.vstack([c0, c1])
        y_coherent = np.array([0] * 20 + [1] * 20, dtype=np.int64)
        dir_drift, tel_drift = self.ctrl.step(X_coherent, y_coherent, delta_drift=1.4)
        assert dir_drift.state == AutomatonStateV4.CONFIRMED_DRIFT

        # Verified noise: high delta, scrambled labels
        np.random.seed(42)
        X_scrambled = np.random.randn(40, 2)
        y_scrambled = np.random.choice([0, 1], size=40)
        dir_noise, tel_noise = self.ctrl.step(X_scrambled, y_scrambled, delta_drift=1.4)
        assert dir_noise.state == AutomatonStateV4.NOISE_BURST

    def test_scenario_b_extreme_imbalance_with_drift(self) -> None:
        prior_tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.9)
        # Seed extreme imbalance (IR ~ 50.0)
        prior_tracker._priors = np.array([0.98, 0.02])
        ctrl = UnifiedLearningControllerV4_1(prior_tracker=prior_tracker)

        X = np.random.randn(30, 2) - 5.0
        y = np.ones(30, dtype=np.int64)
        directive, telemetry = ctrl.step(X, y, delta_drift=1.2)
        assert directive.state == AutomatonStateV4.CONFIRMED_DRIFT
        assert directive.purge_replay_policy == "selective"
        assert directive.keep_minority_in_replay is True

    def test_scenario_c_budget_ceiling_breached(self) -> None:
        class MockBudget:
            current_memory_mb = 90.0
            max_memory_bytes = 100 * 1024 * 1024

        ctrl = UnifiedLearningControllerV4_1(budget_manager=MockBudget())

        X = np.random.randn(30, 2)
        y = np.ones(30, dtype=np.int64)
        directive, telemetry = ctrl.step(X, y, delta_drift=1.2)
        assert directive.state == AutomatonStateV4.RESOURCE_CONSTRAINED
        assert directive.batch_size_scale == 0.50
        assert directive.skip_expensive_ops is True

    def test_scenario_d_recurring_concept(self) -> None:
        memory = ConceptMemory(similarity_threshold=0.75)
        X_saved = np.ones((10, 4))
        memory.store_concept(concept_id="c_recur", model_state={"w": 1}, X=X_saved, y=np.ones(10, dtype=np.int64))
        ctrl = UnifiedLearningControllerV4_1(concept_memory=memory)

        directive, telemetry = ctrl.step(X_saved, np.ones(10, dtype=np.int64), delta_drift=0.80)
        assert directive.restore_concept_id == "matched_recurring"
        assert directive.state == AutomatonStateV4.COOLDOWN

    def test_scenario_e_epistemic_boundary(self) -> None:
        ev = EvidenceVectorV4(predictive_entropy=0.80, mean_reliability=0.85)
        directive = ArbitrationAutomatonV4().transition(ev)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario E: Epistemic Boundary Uncertainty"
        assert resolved.state == AutomatonStateV4.ELEVATED_VARIANCE

    def test_scenario_f_adversarial_inverted_label(self) -> None:
        ev = EvidenceVectorV4(predictive_entropy=0.10, mean_reliability=0.20)
        directive = ArbitrationAutomatonV4().transition(ev)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario F: Adversarial / Inverted Label"
        assert resolved.state == AutomatonStateV4.NOISE_BURST
        assert resolved.correct_labels is True

    def test_scenario_g_delayed_labels_during_recovery(self) -> None:
        ev = EvidenceVectorV4(observed_delay=15.0)
        dir_recovery = DirectiveV4(state=AutomatonStateV4.RECOVERY)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(dir_recovery, ev, conf)
        assert name == "Scenario G: Delayed Labels during Recovery"
        assert resolved.sample_filter_threshold == 0.60

    def test_scenario_h_emerging_class_under_resource_pressure(self) -> None:
        ev = EvidenceVectorV4(is_emerging_class=True, resource_utilization=0.90)
        directive = ArbitrationAutomatonV4().transition(ev)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario H: Emerging Class under Resource Pressure"
        assert resolved.state == AutomatonStateV4.RESOURCE_CONSTRAINED
        assert resolved.keep_minority_in_replay is True

    def test_scenario_i_asymmetric_noise_mitigation(self) -> None:
        ev = EvidenceVectorV4(asymmetric_noise_rate=0.25)
        directive = ArbitrationAutomatonV4().transition(ev)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario I: Asymmetric Noise with Cost Sensitivity"
        assert resolved.state == AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION

    def test_scenario_j_multi_detector_disagreement(self) -> None:
        ev = EvidenceVectorV4(delta_drift=0.75)  # between 0.50 and 1.0
        directive = ArbitrationAutomatonV4().transition(ev)
        conf = ConfidenceEngine().evaluate(ev)
        resolved, name = CrossPillarConflictResolver.resolve_conflicts(directive, ev, conf)
        assert name == "Scenario J: Multi-Detector Disagreement"
        assert resolved.state == AutomatonStateV4.ADAPTATION_PENDING


# =============================================================================
# 6. Lifecycle, Checkpoint, and Bounded History Tests
# =============================================================================
class TestLifecycleAndCheckpointUnit:
    """Verifies controller lifecycle, checkpointing, and memory boundedness."""

    def test_bounded_history_length(self) -> None:
        ctrl = UnifiedLearningControllerV4_1(config=ULCv41Config(max_history_len=15))
        X = np.random.randn(10, 2)
        y = np.zeros(10, dtype=np.int64)

        for _ in range(50):
            ctrl.step(X, y)

        assert len(ctrl.history_) == 15
        assert len(ctrl.get_history()) == 15
        assert len(ctrl.get_history(limit=5)) == 5

    def test_dwell_timeout_escape(self) -> None:
        ctrl = UnifiedLearningControllerV4_1(
            config=ULCv41Config(max_noise_dwell=5, spatial_discordance_threshold=0.25)
        )
        np.random.seed(42)
        X_noise = np.random.randn(20, 2)
        y_noise = np.random.choice([0, 1], size=20)

        # Step 6 consecutive noise bursts
        states = []
        for _ in range(7):
            d, t = ctrl.step(X_noise, y_noise, delta_drift=1.5)
            states.append(d.state)

        # After step 5, it must escape into RECOVERY
        assert AutomatonStateV4.RECOVERY in states

    def test_checkpoint_roundtrip_state_dict(self) -> None:
        ctrl = UnifiedLearningControllerV4_1(
            config=ULCv41Config(spatial_k=8, spatial_discordance_threshold=0.20)
        )
        X = np.random.randn(10, 2)
        y = np.zeros(10, dtype=np.int64)
        for _ in range(5):
            ctrl.step(X, y)

        sd = ctrl.state_dict()
        assert sd["total_steps"] == 5
        assert sd["config"]["spatial_k"] == 8

        ctrl_new = UnifiedLearningControllerV4_1()
        ctrl_new.load_state_dict(sd)
        assert ctrl_new.total_steps == 5
        assert ctrl_new.config.spatial_k == 8
        assert ctrl_new.config.spatial_discordance_threshold == 0.20

    def test_explain_on_demand(self) -> None:
        ctrl = UnifiedLearningControllerV4_1(config=ULCv41Config(generate_explanations=False))
        X = np.random.randn(10, 2)
        y = np.zeros(10, dtype=np.int64)
        d, tel = ctrl.step(X, y)

        # Explanations were not generated eagerly
        assert isinstance(tel["explanation"], dict)
        assert "narrative" not in tel["explanation"]

        # Call explain explicitly on-demand
        exp = ctrl.explain()
        assert "narrative" in exp
        assert "state" in exp
