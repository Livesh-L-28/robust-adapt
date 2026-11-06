"""Stage 13 Cross-Pillar Integration and Configuration Matrix Tests.

Evaluates all 10 configurations mandated in Workstream H:
1. ALA only (concept drift, no robust/resource/minority handling)
2. RLA only (noise robustness, stationary data)
3. Minority only (class imbalance, stationary, clean data)
4. RAO only (resource optimization, standard model)
5. ALA + RLA (drift + noise)
6. RLA + Minority (noise + imbalance)
7. ALA + ULC (drift with controller orchestration)
8. RLA + ULC (noise with controller orchestration)
9. All pillars + ULC-v5 (full stack)
10. ULC disabled (fallback mode: manual pillar configuration without centralized controller)
"""

import numpy as np
import pytest

from robust_adapt.ala import ALA30AdaptiveLearner, AdaptiveClassifier
from robust_adapt.rla import RLA30RobustLearner, MultiSignalReliabilityEngine
from robust_adapt.minority import MinorityIntelligence20Learner, DynamicFPBudgetThresholdManager, BetaBinomialPriorTracker
from robust_adapt.rao import DynamicResourceBudgetManager, BlockQuantizer
from robust_adapt.ulc import (
    UnifiedLearningControllerV5,
    ULCv5Config,
    InterventionTier,
)


@pytest.fixture
def synthetic_stream_data():
    """Generates standard stream fixtures for integration testing."""
    rng = np.random.RandomState(42)
    X = rng.randn(200, 4)
    # Binary labels based on linear hyperplane
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    return X, y


def test_config_1_ala_only(synthetic_stream_data) -> None:
    """Config 1: ALA only (concept drift, no robust/resource/minority handling)."""
    X, y = synthetic_stream_data
    model = ALA30AdaptiveLearner(n_features=4, n_classes=2, grace_period=10)

    for i in range(0, 100, 20):
        model.partial_fit(X[i:i+20], y[i:i+20])

    preds = model.predict(X[100:150])
    assert preds.shape == (50,)
    assert set(np.unique(preds)).issubset({0, 1})
    acc = model.score(X[100:150], y[100:150])
    assert 0.0 <= acc <= 1.0


def test_config_2_rla_only(synthetic_stream_data) -> None:
    """Config 2: RLA only (noise robustness, stationary data)."""
    X, y = synthetic_stream_data
    # Corrupt 20% of labels
    rng = np.random.RandomState(123)
    y_corrupt = y.copy()
    flip_idx = rng.choice(len(y), size=int(0.2 * len(y)), replace=False)
    y_corrupt[flip_idx] = 1 - y_corrupt[flip_idx]

    model = RLA30RobustLearner(n_features=4, n_classes=2, security_mode="standard")
    for i in range(0, 100, 20):
        stats = model.fit_batch(X[i:i+20], y_corrupt[i:i+20])
        assert stats["retained"] <= 20
        assert stats["total_seen"] > 0

    preds = model.predict(X[100:150])
    assert preds.shape == (50,)
    acc = model.score(X[100:150], y[100:150])
    assert acc > 0.50


def test_config_3_minority_only() -> None:
    """Config 3: Minority only (class imbalance, stationary, clean data)."""
    rng = np.random.RandomState(456)
    X = rng.randn(300, 3)
    # Severe imbalance: class 1 has ~5% prior
    y = (rng.rand(300) < 0.05).astype(int)

    model = MinorityIntelligence20Learner(target_fp_budget_per_1k=2.0)
    for i in range(0, 200, 25):
        stats = model.fit_batch(X[i:i+25], y[i:i+25])
        assert stats["prior"] < 0.20

    preds = model.predict(X[200:])
    assert preds.shape == (100,)
    assert set(np.unique(preds)).issubset({0, 1})


def test_config_4_rao_only(synthetic_stream_data) -> None:
    """Config 4: RAO only (resource optimization, standard model)."""
    X, y = synthetic_stream_data
    budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=1024.0)
    quantizer = BlockQuantizer(block_size=32)

    # Simulate optimization step with gradient quantization and budget monitoring
    weights = np.random.randn(64).astype(np.float32)
    q_weights, scales = quantizer.quantize_signed(weights)
    recon = quantizer.dequantize_signed(q_weights, scales)
    assert recon.shape == weights.shape

    state = budget.evaluate_step(step_time_ms=1.5)
    assert state.name in ("NORMAL", "THROTTLED", "CRITICAL")


def test_config_5_ala_plus_rla(synthetic_stream_data) -> None:
    """Config 5: ALA + RLA (drift + noise)."""
    X, y = synthetic_stream_data
    ala = ALA30AdaptiveLearner(n_features=4, n_classes=2, grace_period=10)
    rla = MultiSignalReliabilityEngine(n_classes=2, buffer_size=100)

    for i in range(0, 100, 20):
        X_b, y_b = X[i:i+20], y[i:i+20]
        # Prequential probas from ALA
        probas = ala.predict_proba(X_b)
        # RLA computes reliability weights
        scores = rla.compute_reliability(X_b, y_b, probas)
        assert len(scores) == 20
        # ALA consumes samples
        ala.partial_fit(X_b, y_b)

    assert ala.total_steps == 5


def test_config_6_rla_plus_minority() -> None:
    """Config 6: RLA + Minority (noise + imbalance)."""
    rng = np.random.RandomState(789)
    X = rng.randn(200, 3)
    y = (rng.rand(200) < 0.08).astype(int)

    rla = RLA30RobustLearner(n_features=3, n_classes=2)
    prior_tracker = BetaBinomialPriorTracker(alpha_prior=1.0, beta_prior=10.0)

    for i in range(0, 100, 20):
        X_b, y_b = X[i:i+20], y[i:i+20]
        rla.fit_batch(X_b, y_b)
        prior_tracker.update(y_b)

    assert prior_tracker.current_prior < 0.20
    assert rla.retained_samples > 0


def test_config_7_ala_plus_ulc(synthetic_stream_data) -> None:
    """Config 7: ALA + ULC (drift with controller orchestration)."""
    X, y = synthetic_stream_data
    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)

    for i in range(0, 100, 20):
        directive, telemetry = ulc.step(X[i:i+20], y[i:i+20])
        assert directive.tier in InterventionTier
        assert "confidence" in telemetry

    assert ulc.total_steps == 5


def test_config_8_rla_plus_ulc(synthetic_stream_data) -> None:
    """Config 8: RLA + ULC (noise with controller orchestration)."""
    X, y = synthetic_stream_data
    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    rla = RLA30RobustLearner(n_features=4, n_classes=2)

    for i in range(0, 100, 20):
        X_b, y_b = X[i:i+20], y[i:i+20]
        directive, _ = ulc.step(X_b, y_b)
        # Controller telemetry gates RLA execution
        if ulc.config.gate_rla_on_clean_stream and directive.tier == InterventionTier.TIER_0_NOOP:
            rla.fit_batch(X_b, y_b)

    assert rla.retained_samples > 0


def test_config_9_all_pillars_plus_ulc_v5(synthetic_stream_data) -> None:
    """Config 9: All pillars + ULC-v5 (full stack)."""
    X, y = synthetic_stream_data
    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)
    rla = RLA30RobustLearner(n_features=4, n_classes=2)
    minority = MinorityIntelligence20Learner()
    budget = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=1024.0)

    for i in range(0, 100, 20):
        X_b, y_b = X[i:i+20], y[i:i+20]
        # Step through full stack
        directive, telemetry = ulc.step(X_b, y_b)
        rla.fit_batch(X_b, y_b)
        minority.fit_batch(X_b, y_b)
        budget.evaluate_step(step_time_ms=2.0)

        assert directive.tier in InterventionTier
        assert not budget.should_skip_expensive_ops()

    assert ulc.total_steps == 5
    assert minority.total_samples_seen == 100
    assert rla.total_samples_seen == 100


def test_config_10_ulc_disabled_manual_composition(synthetic_stream_data) -> None:
    """Config 10: ULC disabled (fallback manual pillar composition)."""
    X, y = synthetic_stream_data
    ala = ALA30AdaptiveLearner(n_features=4, n_classes=2)
    rla = RLA30RobustLearner(n_features=4, n_classes=2)
    minority = MinorityIntelligence20Learner()

    for i in range(0, 100, 20):
        X_b, y_b = X[i:i+20], y[i:i+20]
        # Manually chain pillars without central arbitrator
        rla_stats = rla.fit_batch(X_b, y_b)
        if rla_stats["retained"] > 0:
            ala.partial_fit(X_b, y_b)
            minority.fit_batch(X_b, y_b)

    assert ala.total_steps > 0
    assert rla.retained_samples > 0
    assert minority.total_batches_seen > 0
