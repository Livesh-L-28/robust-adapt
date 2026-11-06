"""Unit tests for Phase 9 RLA (Robust Learning Algorithms)."""

import pytest
import numpy as np
from robust_adapt.rla.scorer import DensityAwareMarginScorer
from robust_adapt.rla.losses import SymmetricCrossEntropyLoss, GeneralizedCrossEntropyLoss
from robust_adapt.rla.weighting import ClassBalancedWeights
from robust_adapt.rla.pipeline import RobustLearningPipeline
from robust_adapt.core.exceptions import ValidationError


class TestDensityAwareMarginScorer:
    """Tests for DensityAwareMarginScorer."""

    def test_corrupted_sample_identification(self) -> None:
        rng = np.random.default_rng(42)
        scorer = DensityAwareMarginScorer(n_classes=2, n_neighbors=5, alpha=1.0, gamma=0.5)

        # Dense cluster of instances at loc [0, 0]
        X = rng.normal(loc=0.0, scale=0.2, size=(20, 2))
        # Logits confident in class 0: logits [3.0, -3.0]
        logits = np.tile([3.0, -3.0], (20, 1))

        # 19 instances labeled correctly as 0, 1 instance corrupted with false label 1
        y = np.zeros(20, dtype=np.int64)
        y[19] = 1  # CORRUPTED in high density!

        reliabilities = scorer.score_samples(X, logits, y)

        # Clean samples have high reliability (> 0.50)
        assert np.mean(reliabilities[:19]) > 0.50
        # Corrupted sample in dense region must be sharply suppressed (< 0.05, >10x lower)
        assert reliabilities[19] < 0.05
        assert np.mean(reliabilities[:19]) / reliabilities[19] > 10.0

    def test_minority_preservation_theorem_2(self) -> None:
        """Theorem 2 verification: difficult minority sample in low-density feature space is protected."""
        scorer = DensityAwareMarginScorer(n_classes=2, n_neighbors=5, alpha=1.0, gamma=1.0)

        # High-density majority cluster
        X_dense = np.random.normal(loc=0.0, scale=0.1, size=(25, 2))
        y_dense = np.zeros(25, dtype=np.int64)
        logits_dense = np.tile([2.0, -2.0], (25, 1))

        # Low-density isolated tail instance
        X_rare = np.array([[10.0, 10.0]])
        y_rare = np.array([1])
        # Model is uncertain / has small negative margin on rare instance
        logits_rare = np.array([[0.5, -0.5]])  # Margin with respect to class 1 is -1.0

        X = np.vstack([X_dense, X_rare])
        logits = np.vstack([logits_dense, logits_rare])
        y = np.concatenate([y_dense, y_rare])

        reliabilities = scorer.score_samples(X, logits, y)

        # The isolated minority instance should receive a protective bonus
        rare_rel = reliabilities[-1]
        assert rare_rel >= 0.20, f"Tail minority instance must be protected, got {rare_rel}"


class TestRobustLosses:
    """Tests for SymmetricCrossEntropyLoss and GeneralizedCrossEntropyLoss."""

    def test_sce_finite_difference_gradients(self) -> None:
        """Numerical verification: analytical logit gradients match finite differences."""
        loss_fn = SymmetricCrossEntropyLoss(alpha=1.0, beta=0.5)

        rng = np.random.default_rng(101)
        logits = rng.normal(size=(5, 3))
        y = np.array([0, 1, 2, 1, 0], dtype=np.int64)

        loss, grad_analytical = loss_fn.forward(logits, y)

        # Finite difference check
        eps = 1e-6
        grad_numerical = np.zeros_like(logits)

        for i in range(5):
            for j in range(3):
                logits_pos = logits.copy()
                logits_pos[i, j] += eps
                l_pos, _ = loss_fn.forward(logits_pos, y)

                logits_neg = logits.copy()
                logits_neg[i, j] -= eps
                l_neg, _ = loss_fn.forward(logits_neg, y)

                grad_numerical[i, j] = (l_pos - l_neg) / (2.0 * eps)

        max_grad_diff = np.max(np.abs(grad_analytical - grad_numerical))
        assert max_grad_diff < 1e-5, f"Gradient diff too large: {max_grad_diff}"

    def test_gce_finite_difference_gradients(self) -> None:
        """Numerical verification: GCE analytical gradients match finite differences."""
        loss_fn = GeneralizedCrossEntropyLoss(q=0.7)

        rng = np.random.default_rng(202)
        logits = rng.normal(size=(4, 3))
        y = np.array([1, 2, 0, 1], dtype=np.int64)

        loss, grad_analytical = loss_fn.forward(logits, y)

        eps = 1e-6
        grad_numerical = np.zeros_like(logits)

        for i in range(4):
            for j in range(3):
                logits_pos = logits.copy()
                logits_pos[i, j] += eps
                l_pos, _ = loss_fn.forward(logits_pos, y)

                logits_neg = logits.copy()
                logits_neg[i, j] -= eps
                l_neg, _ = loss_fn.forward(logits_neg, y)

                grad_numerical[i, j] = (l_pos - l_neg) / (2.0 * eps)

        max_grad_diff = np.max(np.abs(grad_analytical - grad_numerical))
        assert max_grad_diff < 1e-5, f"GCE gradient diff too large: {max_grad_diff}"

    def test_sce_bounded_gradients_under_adversarial_noise(self) -> None:
        """Verify that gradients remain strictly bounded even when model is 100% wrong on corrupted label."""
        loss_fn = SymmetricCrossEntropyLoss(alpha=1.0, beta=0.5, eps_clip=1e-4)

        # Extremely confident logits in class 0 (e.g. z = [50.0, -50.0])
        logits = np.array([[50.0, -50.0]], dtype=np.float64)
        # But observed label is class 1 (completely corrupted)
        y = np.array([1], dtype=np.int64)

        loss, grad = loss_fn.forward(logits, y)
        grad_norm = np.linalg.norm(grad)

        # Standard Cross-Entropy produces exploding/uncalibrated gradients; SCE must remain strictly bounded
        assert np.isfinite(loss)
        assert np.all(np.isfinite(grad))
        assert grad_norm < 20.0, f"Gradient norm must be strictly bounded, got {grad_norm}"


class TestClassBalancedWeights:
    """Tests for ClassBalancedWeights."""

    def test_effective_weights_normalization(self) -> None:
        cb = ClassBalancedWeights(beta=0.999)
        # 1000 majority samples, 10 minority samples
        counts = np.array([1000.0, 10.0])
        weights = cb.compute_weights(counts)

        # Mean of weights must equal 1.0
        assert np.isclose(np.mean(weights), 1.0, atol=1e-5)
        # Minority class MUST receive significantly higher weight than majority class
        assert weights[1] > weights[0]
        assert weights[1] / weights[0] > 10.0


class TestRobustLearningPipeline:
    """Tests for integrated RobustLearningPipeline."""

    def test_pipeline_evaluation(self) -> None:
        pipeline = RobustLearningPipeline(n_classes=3)
        rng = np.random.default_rng(42)

        X = rng.normal(size=(30, 4))
        logits = rng.normal(size=(30, 3))
        y = rng.integers(0, 3, size=30)

        loss, grad, rels = pipeline.evaluate_batch(X, logits, y)

        assert loss > 0.0
        assert grad.shape == (30, 3)
        assert rels.shape == (30,)
        assert np.all(rels >= 1e-4) and np.all(rels <= 1.0)
