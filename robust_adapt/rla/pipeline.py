"""Robust Learning Pipeline integrating reliability scoring, class-balancing, and robust loss."""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.types import FloatArray1D, FloatArray2D
from robust_adapt.core.validation import check_array_2d, check_labels_1d
from robust_adapt.rla.losses import SymmetricCrossEntropyLoss
from robust_adapt.rla.reliability import AsymmetricTransitionDetector, ClassConditionalReliabilityEstimator
from robust_adapt.rla.scorer import DensityAwareMarginScorer
from robust_adapt.rla.weighting import ClassBalancedWeights


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


class RLA30RobustLearner:
    """RLA 3.0 Asymmetric Robust Streaming Learner.

    Defends against asymmetric label noise (e.g. directional evasion attacks where minority
    samples are disguised as majority instances) through class-conditional density modeling,
    minority-preservation rules, and safe selective abstention.

    Note: This algorithm provides empirical resilience against directional evasion attacks,
    but must not be construed as a universal adversarial defense. Under heavy evasion,
    higher recall is traded for lower precision on borderline samples.

    Parameters
    ----------
    n_features : int
        Dimensionality of streaming instances.
    n_classes : int, default=2
        Number of distinct target classes.
    security_mode : str, default="standard"
        Operating mode:
        - "standard": Balanced noise filtering for moderate noise.
        - "high_security_evasion": Aggressive minority preservation against evasion attacks.
        - "conservative_abstain": Abstains from updates on ambiguous or low-reliability samples.
    reliability_threshold : float, default=0.35
        Minimum sample reliability required for model gradient updates.
    minority_class : int, default=1
        Class index receiving asymmetric preservation priority.
    random_state : Optional[int], default=42
        Seed for reproducible random state initialization.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        security_mode: str = "standard",
        reliability_threshold: float = 0.35,
        minority_class: int = 1,
        random_state: Optional[int] = 42,
    ) -> None:
        if n_features < 1:
            raise ConfigurationError(f"n_features must be >= 1, got {n_features}")
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        valid_modes = {"standard", "high_security_evasion", "conservative_abstain"}
        if security_mode not in valid_modes:
            raise ConfigurationError(f"security_mode must be one of {valid_modes}, got '{security_mode}'")
        if not 0.0 <= reliability_threshold <= 1.0:
            raise ConfigurationError(f"reliability_threshold must be in [0, 1], got {reliability_threshold}")

        self.n_features = int(n_features)
        self.n_classes = int(n_classes)
        self.security_mode = security_mode
        self.reliability_threshold = float(reliability_threshold)
        self.minority_class = int(minority_class)
        self.random_state = random_state

        self.estimator = ClassConditionalReliabilityEstimator(
            n_features=self.n_features,
            n_classes=self.n_classes,
            minority_protection=(security_mode == "high_security_evasion"),
        )
        self.detector = AsymmetricTransitionDetector(n_classes=self.n_classes)

        # Online linear weights for pure-NumPy independence
        rng = np.random.RandomState(random_state)
        self.weights = rng.normal(0.0, 0.01, size=(self.n_classes, self.n_features))
        self.biases = np.zeros(self.n_classes, dtype=np.float64)
        self.lr = 0.01

        self.total_samples_seen: int = 0
        self.retained_samples: int = 0
        self.abstained_samples: int = 0
        self.is_fitted: bool = False

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict posterior probabilities via softmax."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        logits = np.dot(X_val, self.weights.T) + self.biases
        # Stable softmax
        logits_max = np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(np.clip(logits - logits_max, -30.0, 30.0))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict discrete class labels."""
        return np.argmax(self.predict_proba(X), axis=1)

    def fit_batch(self, X_batch: np.ndarray, y_batch: np.ndarray) -> Dict[str, Any]:
        """Processes a training batch with class-conditional filtering and selective abstention.

        Returns
        -------
        Dict[str, Any]
            Telemetry report detailing retained, abstained, and filtered counts.
        """
        X_val = check_array_2d(X_batch, expected_dim=self.n_features, name="X_batch")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y_batch, expected_len=n_samples, n_classes=self.n_classes, name="y_batch")
        self.total_samples_seen += n_samples

        # 1. Warm-up phase
        if not self.is_fitted:
            self._sgd_step(X_val, y_val, np.ones(n_samples))
            self.estimator.update(X_val, y_val)
            self.is_fitted = True
            self.retained_samples += n_samples
            return {
                "total_seen": self.total_samples_seen,
                "retained": n_samples,
                "abstained": 0,
                "asymmetry_ratio": 1.0,
                "mean_reliability": 1.0,
            }

        # 2. Prequential prediction & directional discordance monitoring
        probas = self.predict_proba(X_val)
        y_pred = np.argmax(probas, axis=1)
        self.detector.update(y_pred, y_val)
        asym_ratio = self.detector.get_asymmetry_ratio()

        # 3. Class-conditional reliability estimation
        reliabilities = self.estimator.compute_reliability(X_val, y_val)

        # 4. Abstention & filtering policy
        abstain_mask = np.zeros(n_samples, dtype=bool)
        for i in range(n_samples):
            # If high security evasion mode: check if model strongly suspects disguised minority
            if self.security_mode == "high_security_evasion":
                if y_val[i] != self.minority_class and probas[i, self.minority_class] >= 0.65 and asym_ratio > 1.3:
                    abstain_mask[i] = True
            elif self.security_mode == "conservative_abstain":
                # Abstain on all low-margin uncertain samples
                if reliabilities[i] < 0.50:
                    abstain_mask[i] = True

        keep_mask = (reliabilities >= self.reliability_threshold) & (~abstain_mask)
        n_keep = int(np.sum(keep_mask))
        n_abstain = int(np.sum(abstain_mask))

        self.retained_samples += n_keep
        self.abstained_samples += n_abstain

        # 5. Gradient update on retained instances
        if n_keep > 0:
            self._sgd_step(X_val[keep_mask], y_val[keep_mask], reliabilities[keep_mask])
            self.estimator.update(X_val[keep_mask], y_val[keep_mask])

        return {
            "total_seen": self.total_samples_seen,
            "retained": n_keep,
            "abstained": n_abstain,
            "asymmetry_ratio": float(asym_ratio),
            "mean_reliability": float(np.mean(reliabilities)),
        }

    def _sgd_step(self, X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> None:
        """Executes one weighted gradient descent step."""
        n = X.shape[0]
        if n == 0:
            return
        probas = self.predict_proba(X)
        one_hot = np.zeros((n, self.n_classes), dtype=np.float64)
        for i in range(n):
            one_hot[i, y[i]] = 1.0

        grad_logits = (probas - one_hot) * weights[:, np.newaxis]
        grad_w = np.dot(grad_logits.T, X) / n
        grad_b = np.sum(grad_logits, axis=0) / n

        self.weights -= self.lr * grad_w
        self.biases -= self.lr * grad_b

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate mean classification accuracy."""
        X_val = check_array_2d(X, expected_dim=self.n_features, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")
        preds = self.predict(X_val)
        return float(np.mean(preds == y_val))

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "RLA30RobustLearner":
        """Incremental scikit-learn compatible fit."""
        self.fit_batch(X, y)
        return self
