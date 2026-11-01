"""Robust Learning Pipeline integrating reliability scoring, class-balancing, and robust loss."""

from typing import Optional, Tuple
import numpy as np
from adaptive_ml.core.types import FloatArray1D, FloatArray2D
from adaptive_ml.rla.losses import SymmetricCrossEntropyLoss
from adaptive_ml.rla.scorer import DensityAwareMarginScorer
from adaptive_ml.rla.weighting import ClassBalancedWeights


class RobustLearningPipeline:
    """Integrated pipeline combining DensityAwareMarginScorer with SymmetricCrossEntropyLoss.

    Parameters
    ----------
    n_classes : int
        Number of target classes.
    alpha : float, default=1.0
        SCE loss alpha parameter.
    beta : float, default=0.5
        SCE loss beta parameter.
    gamma_density : float, default=0.5
        Density protection bonus coefficient for tail classes.
    beta_cb : float, default=0.999
        Class-balanced effective number parameter.
    """

    def __init__(
        self,
        n_classes: int,
        alpha: float = 1.0,
        beta: float = 0.5,
        gamma_density: float = 0.5,
        beta_cb: float = 0.999,
    ) -> None:
        self.n_classes = n_classes
        self.scorer = DensityAwareMarginScorer(
            n_classes=n_classes,
            gamma=gamma_density,
        )
        self.loss_fn = SymmetricCrossEntropyLoss(alpha=alpha, beta=beta)
        self.cb_weighter = ClassBalancedWeights(beta=beta_cb)
        self.running_class_counts = np.zeros(n_classes, dtype=np.float64)

    def evaluate_batch(
        self,
        X: np.ndarray,
        logits: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[float, FloatArray2D, FloatArray1D]:
        """Compute reliability scores, composite sample weights, and robust loss gradients.

        Returns
        -------
        loss : float
            Scalar batch loss.
        grad_logits : FloatArray2D of shape (n_samples, n_classes)
            Gradients for backprop.
        reliabilities : FloatArray1D of shape (n_samples,)
            Reliability scores.
        """
        # 1. Update running class frequency
        for c in range(self.n_classes):
            self.running_class_counts[c] += float(np.sum(y == c))

        # 2. Compute sample reliability
        reliabilities = self.scorer.score_samples(X, logits, y)

        # 3. Compute class-balanced sample weights
        cb_weights = self.cb_weighter.compute_sample_weights(y, self.running_class_counts)

        # 4. Composite weights: reliability * class_weight
        composite_weights = reliabilities * cb_weights

        # 5. Compute robust loss and gradients
        loss, grad_logits = self.loss_fn.forward(logits, y, sample_weights=composite_weights)

        return loss, grad_logits, reliabilities

