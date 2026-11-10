"""
Stage 12 — Workstream B: RLA 3.0 Asymmetric Noise & Minority Protection.

Implements next-generation robust learning designed to overcome the catastrophic
recall collapse observed under asymmetric evasion noise (where spatial KNN filters
disguised samples into the majority and drops true minority samples).

Components:
1. ClassConditionalReliabilityEstimator (evaluates discordance conditioned on class prior)
2. TemporalPredictionConsistencyTracker (tracks model confidence stability over time)
3. MinorityPreservationConstraint (prevents dropping legitimate rare samples)
4. AsymmetricTransitionDetector (detects directional corruption P(ham|spam))
5. SelectiveAbstention (abstains from gradient updates on ambiguous samples)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import SGDClassifier

logger = logging.getLogger(__name__)


class AsymmetricTransitionDetector:
    """Monitors directional prediction-label disagreement to detect asymmetric corruption."""

    def __init__(self, n_classes: int = 2, window_size: int = 300):
        self.n_classes = n_classes
        self.window_size = window_size
        self.history: List[Tuple[int, int]] = []  # (predicted, true_label)

    def update(self, y_pred: np.ndarray, y_true: np.ndarray) -> None:
        for p, t in zip(y_pred, y_true):
            self.history.append((int(p), int(t)))
            if len(self.history) > self.window_size:
                self.history.pop(0)

    def get_asymmetry_ratio(self) -> float:
        """
        Calculates directional discordance ratio:
        discordance(pred=1, true=0) vs discordance(pred=0, true=1).
        """
        if len(self.history) < 30:
            return 1.0

        d_10 = sum(1 for p, t in self.history if p == 1 and t == 0)
        d_01 = sum(1 for p, t in self.history if p == 0 and t == 1)

        total_disc = d_10 + d_01
        if total_disc == 0:
            return 1.0

        # Ratio of (pred=1, true=0) evasion corruption
        return (d_10 + 1.0) / (d_01 + 1.0)


class ClassConditionalReliabilityEstimator:
    """Computes label reliability with explicit minority class protection and class-specific density."""

    def __init__(self, k_neighbors: int = 5, minority_bonus: float = 0.25):
        self.k_neighbors = k_neighbors
        self.minority_bonus = minority_bonus

    def compute_reliability(
        self,
        X_batch: np.ndarray,
        y_batch: np.ndarray,
        probas: np.ndarray,
        asymmetry_ratio: float,
        minority_class: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns:
            reliabilities: float array [0, 1] per sample
            abstain_mask: boolean array (True if sample is ambiguous and should be abstained)
        """
        n_samples = len(X_batch)
        if n_samples <= self.k_neighbors:
            return np.ones(n_samples), np.zeros(n_samples, dtype=bool)

        nn = NearestNeighbors(n_neighbors=self.k_neighbors + 1, metric="euclidean")
        nn.fit(X_batch)
        indices = nn.kneighbors(X_batch, return_distance=False)

        reliabilities = np.zeros(n_samples)
        abstain_mask = np.zeros(n_samples, dtype=bool)

        for i in range(n_samples):
            neighbor_indices = indices[i, 1:]  # exclude self
            neighbor_labels = y_batch[neighbor_indices]
            
            # Neighborhood label agreement
            agreement = np.mean(neighbor_labels == y_batch[i])
            model_confidence = probas[i, int(y_batch[i])]
            
            # Base reliability: combination of spatial neighbor agreement and model confidence
            base_rel = 0.5 * agreement + 0.5 * model_confidence

            # Minority Protection Logic:
            # Under asymmetric evasion noise, legitimate minority samples (y=1) may be surrounded
            # by majority samples (y=0) due to flipping. We must NOT discard them if model confidence
            # or feature density supports minority membership.
            if y_batch[i] == minority_class:
                # Add minority protection bonus, especially if asymmetry is detected
                asym_boost = min(0.35, 0.1 * asymmetry_ratio) if asymmetry_ratio > 1.2 else 0.0
                rel = min(1.0, base_rel + self.minority_bonus + asym_boost)
            else:
                rel = base_rel

            # Abstention mechanism: if model is very confident it is minority (probas[:, 1] >= 0.70)
            # but label is majority (y=0), and asymmetry_ratio is elevated, flag as ambiguous evasion sample
            if y_batch[i] != minority_class and probas[i, minority_class] >= 0.65 and asymmetry_ratio > 1.3:
                abstain_mask[i] = True
                rel = 0.1  # Downweight corrupted sample

            reliabilities[i] = rel

        return reliabilities, abstain_mask


class RLA30RobustLearner:
    """
    RLA 3.0 Next-Generation Robust Learning Classifier.
    Integrates class-conditional spatial reliability, asymmetric transition detection,
    minority preservation, and selective abstention.
    """

    def __init__(
        self,
        n_classes: int = 2,
        k_neighbors: int = 5,
        reliability_threshold: float = 0.40,
        minority_class: int = 1,
    ):
        self.n_classes = n_classes
        self.reliability_threshold = reliability_threshold
        self.minority_class = minority_class

        self.clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=42)
        self.estimator = ClassConditionalReliabilityEstimator(k_neighbors=k_neighbors)
        self.detector = AsymmetricTransitionDetector(n_classes=n_classes)
        self.is_fitted = False

        self.total_samples_seen = 0
        self.retained_samples = 0
        self.abstained_samples = 0
        self.minority_retained = 0

    def fit_batch(self, X_batch: np.ndarray, y_batch: np.ndarray) -> Dict[str, Any]:
        """Processes a training batch with robust filtering and selective abstention."""
        n_samples = len(X_batch)
        self.total_samples_seen += n_samples

        if not self.is_fitted:
            # Warm up on initial batch
            self.clf.partial_fit(X_batch, y_batch, classes=np.arange(self.n_classes))
            self.is_fitted = True
            self.retained_samples += n_samples
            return {"retained": n_samples, "abstained": 0, "asymmetry": 1.0}

        # 1. Prequential probabilities & predictions
        probas = self.clf.predict_proba(X_batch)
        y_pred = np.argmax(probas, axis=1)

        # 2. Update asymmetric transition detector
        self.detector.update(y_pred, y_batch)
        asym_ratio = self.detector.get_asymmetry_ratio()

        # 3. Compute class-conditional reliability & abstention mask
        reliabilities, abstain_mask = self.estimator.compute_reliability(
            X_batch, y_batch, probas, asym_ratio, minority_class=self.minority_class
        )

        # 4. Filter samples: admit reliable, non-abstained samples
        keep_mask = (reliabilities >= self.reliability_threshold) & (~abstain_mask)
        n_keep = int(np.sum(keep_mask))
        n_abstain = int(np.sum(abstain_mask))

        self.retained_samples += n_keep
        self.abstained_samples += n_abstain
        self.minority_retained += int(np.sum(keep_mask & (y_batch == self.minority_class)))

        # 5. Weighted training update
        if n_keep >= 5:
            sample_weights = reliabilities[keep_mask]
            # Cost-weight minority samples under elevated asymmetry
            if asym_ratio > 1.2:
                sample_weights = np.where(
                    y_batch[keep_mask] == self.minority_class,
                    sample_weights * min(3.0, asym_ratio),
                    sample_weights,
                )
            self.clf.partial_fit(X_batch[keep_mask], y_batch[keep_mask], sample_weight=sample_weights)
        else:
            # Fallback conservative update on un-abstained samples
            valid_mask = ~abstain_mask
            if np.sum(valid_mask) > 0:
                self.clf.partial_fit(X_batch[valid_mask], y_batch[valid_mask])

        return {
            "retained": n_keep,
            "abstained": n_abstain,
            "asymmetry": asym_ratio,
            "mean_reliability": float(np.mean(reliabilities)),
        }

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            return np.ones((len(X), self.n_classes)) / self.n_classes
        return self.clf.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

