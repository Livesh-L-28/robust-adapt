"""Unit tests for Stage 5: RLA 2.0 (Advanced Robust Learning Algorithms).

Verifies MultiSignalReliabilityEngine, NoiseTaxonomyClassifier, Outlier vs Rare Pattern discrimination,
FocalLoss, ReliabilityWeightedLoss, and EvidenceBasedLabelCorrector.
"""

import numpy as np
import pytest

from robust_adapt.rla.label_correction import EvidenceBasedLabelCorrector
from robust_adapt.rla.losses import FocalLoss, ReliabilityWeightedLoss
from robust_adapt.rla.noise_classifier import NoiseTaxonomyClassifier, NoiseType, PatternType
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine


class TestMultiSignalReliabilityEngine:
    """Verifies margin, neighborhood spatial agreement, and temporal consistency."""

    def test_clean_samples_yield_high_reliability(self) -> None:
        engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=3)
        X = np.random.normal(loc=2.0, scale=0.5, size=(20, 4))
        y = np.ones(20, dtype=int)
        # Model strongly predicts class 1 with high confidence
        probs = np.column_stack([np.full(20, 0.05), np.full(20, 0.95)])

        rel = engine.compute_reliability(X, y, probs)
        assert np.all(rel > 0.70)
        assert np.mean(rel) > 0.80

    def test_corrupt_samples_yield_low_reliability(self) -> None:
        engine = MultiSignalReliabilityEngine(n_classes=2, k_neighbors=3)
        # Populate history with class 0
        X_hist = np.random.normal(loc=-2.0, scale=0.5, size=(30, 4))
        y_hist = np.zeros(30, dtype=int)
        probs_hist = np.column_stack([np.full(30, 0.95), np.full(30, 0.05)])
        engine.compute_reliability(X_hist, y_hist, probs_hist)

        # Incoming samples are in the same region (loc=-2.0), but labeled corruptly as 1
        X_corrupt = np.random.normal(loc=-2.0, scale=0.5, size=(10, 4))
        y_corrupt = np.ones(10, dtype=int)  # inverted label
        # Model correctly predicts class 0
        probs_corrupt = np.column_stack([np.full(10, 0.90), np.full(10, 0.10)])

        rel_corrupt = engine.compute_reliability(X_corrupt, y_corrupt, probs_corrupt)
        assert np.all(rel_corrupt < 0.35)


class TestNoiseTaxonomyClassifier:
    """Verifies noise mechanism classification and outlier vs rare pattern discrimination."""

    def test_clean_regime_classification(self) -> None:
        clf = NoiseTaxonomyClassifier(n_classes=2)
        y_reported = np.array([0] * 50 + [1] * 50)
        y_pred = y_reported.copy()  # perfect agreement
        noise_type, T, rate = clf.estimate_noise_transition(y_reported, y_pred)
        assert noise_type == NoiseType.CLEAN
        assert rate == 0.0

    def test_class_conditional_asymmetric_noise(self) -> None:
        clf = NoiseTaxonomyClassifier(n_classes=2, asymmetry_threshold=0.15)
        # Only class 0 is corrupted to class 1 at 40% rate; class 1 is clean
        y_reported = np.array([0] * 60 + [1] * 40 + [1] * 100)
        y_pred = np.array([0] * 60 + [0] * 40 + [1] * 100)  # 40 instances of class 0 were misreported as 1
        noise_type, T, rate = clf.estimate_noise_transition(y_reported, y_pred)
        assert noise_type == NoiseType.CLASS_CONDITIONAL
        assert rate > 0.15

    def test_outlier_vs_rare_valid_pattern_discrimination(self) -> None:
        clf = NoiseTaxonomyClassifier(n_classes=2)
        prototypes = {
            0: np.array([-3.0, -3.0]),
            1: np.array([3.0, 3.0]),
        }
        variances = {
            0: np.array([0.5, 0.5]),
            1: np.array([0.5, 0.5]),
        }

        # Case A: Rare valid minority pattern close to class 1 prototype, low margin
        x_rare = np.array([3.1, 2.9])
        pat_rare = clf.discriminate_sample(x_rare, y_candidate=1, prototypes=prototypes, variances=variances, margin_score=0.45)
        assert pat_rare == PatternType.RARE_VALID_PATTERN

        # Case B: Corrupt outlier situated right in the center of class 0 cluster but falsely labeled 1
        x_outlier = np.array([-3.1, -2.9])
        pat_outlier = clf.discriminate_sample(x_outlier, y_candidate=1, prototypes=prototypes, variances=variances, margin_score=0.20)
        assert pat_outlier == PatternType.CORRUPT_OUTLIER


class TestRobustLossPortfolioV2:
    """Verifies FocalLoss and ReliabilityWeightedLoss numerical properties."""

    def test_focal_loss_finite_difference_gradients(self) -> None:
        focal = FocalLoss(alpha=1.0, gamma=2.0)
        rng = np.random.default_rng(42)

        logits = rng.normal(size=(5, 3))
        y = np.array([0, 1, 2, 0, 1])

        loss, analytical_grad = focal.forward(logits, y)

        # Finite difference gradient check
        eps = 1e-6
        numerical_grad = np.zeros_like(logits)

        for i in range(5):
            for j in range(3):
                l_pos = logits.copy()
                l_pos[i, j] += eps
                loss_pos, _ = focal.forward(l_pos, y)

                l_neg = logits.copy()
                l_neg[i, j] -= eps
                loss_neg, _ = focal.forward(l_neg, y)

                numerical_grad[i, j] = (loss_pos - loss_neg) / (2.0 * eps)

        np.testing.assert_allclose(analytical_grad, numerical_grad, rtol=1e-4, atol=1e-5)

    def test_reliability_weighted_loss_zeros_corrupt_gradient(self) -> None:
        base_focal = FocalLoss(gamma=1.0)
        rwl = ReliabilityWeightedLoss(base_loss=base_focal, min_reliability=0.20)

        logits = np.array([[2.0, -2.0], [-2.0, 2.0]])
        y = np.array([0, 1])
        # Sample 0 is clean (r=0.9), Sample 1 is corrupt noise (r=0.05)
        reliabilities = np.array([0.90, 0.05])

        loss, grad = rwl.forward(logits, y, reliabilities)

        # Sample 1 gradient must be identically 0.0 because r < 0.20
        np.testing.assert_allclose(grad[1], [0.0, 0.0])
        # Sample 0 gradient must be non-zero
        assert np.any(grad[0] != 0.0)


class TestEvidenceBasedLabelCorrection:
    """Verifies non-destructive label correction and audit rollback."""

    def test_label_correction_and_rollback(self) -> None:
        corrector = EvidenceBasedLabelCorrector(n_classes=2, confidence_threshold=0.80, reliability_threshold=0.30)
        X = np.random.randn(5, 4)
        y = np.array([0, 1, 0, 1, 0])

        # Model predicted probabilities:
        # Sample 1: reported label 1, but model is 95% confident it is class 0 with reliability 0.10 -> Should be corrected!
        probas = np.array([
            [0.90, 0.10],
            [0.95, 0.05],  # Corrupted: reported 1, predicted 0
            [0.70, 0.30],
            [0.10, 0.90],
            [0.85, 0.15],
        ])
        reliabilities = np.array([0.9, 0.10, 0.7, 0.9, 0.8])

        corrected_y, audit = corrector.correct_batch(X, y, probas, reliabilities, timestamp=100.0)

        assert len(audit) == 1
        rec = audit[0]
        assert rec.sample_index == 1
        assert rec.original_label == 1
        assert rec.corrected_label == 0
        assert corrected_y[1] == 0  # Successfully corrected

        # Revert corrections via rollback
        reverted_y = corrector.rollback(corrected_y, audit)
        np.testing.assert_array_equal(reverted_y, y)
