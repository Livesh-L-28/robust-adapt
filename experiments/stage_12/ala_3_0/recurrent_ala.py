"""
Stage 12 — Workstream A: ALA 3.0 Recurring-Concept Intelligence.

Implements next-generation streaming adaptation with:
1. Concept Fingerprinting (rolling feature moments and class distributions)
2. Bounded Recurring Concept Memory (capacity M with LRU/frequency eviction)
3. Cosine/Gaussian Concept Similarity Matching
4. Confidence-Aware Selective Model Restoration (vs Destructive Hard Resets)
5. Adaptation Cooldown to prevent cascading oscillation
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN
from adaptive_ml.ala.replay import ClassBalancedReservoirReplay

logger = logging.getLogger(__name__)


@dataclass
class ConceptSnapshot:
    """Represents a stored historical concept and its associated model state."""
    concept_id: str
    fingerprint: np.ndarray
    classifier: AdaptiveClassifier
    creation_step: int
    last_used_step: int
    usage_count: int = 1
    mean_accuracy: float = 0.0


class ConceptFingerprinter:
    """Extracts compact statistical fingerprints from data windows."""

    def __init__(self, n_features: int, n_classes: int = 2):
        self.n_features = n_features
        self.n_classes = n_classes

    def compute_fingerprint(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes a fixed-dimensional summary vector:
        [mean(X_1..D), std(X_1..D), class_prior_0..C-1]
        """
        mu = np.mean(X, axis=0)
        sigma = np.std(X, axis=0) + 1e-6
        if y is not None:
            counts = np.bincount(y.astype(int), minlength=self.n_classes)
            priors = counts / max(1, len(y))
        else:
            priors = np.ones(self.n_classes) / self.n_classes
        
        raw_fp = np.concatenate([mu, sigma, priors])
        norm = np.linalg.norm(raw_fp)
        return raw_fp / max(norm, 1e-8)


class RecurringConceptMemory:
    """Bounded concept store with cosine similarity matching and LRU/LFU eviction."""

    def __init__(
        self,
        max_concepts: int = 5,
        similarity_threshold: float = 0.88,
    ):
        self.max_concepts = max_concepts
        self.similarity_threshold = similarity_threshold
        self.concepts: Dict[str, ConceptSnapshot] = {}
        self._next_id = 0

    def find_matching_concept(self, fingerprint: np.ndarray) -> Tuple[Optional[ConceptSnapshot], float]:
        """Finds the most similar stored concept snapshot."""
        if not self.concepts:
            return None, 0.0

        best_concept: Optional[ConceptSnapshot] = None
        best_sim = -1.0

        for snap in self.concepts.values():
            sim = float(np.dot(fingerprint, snap.fingerprint))
            if sim > best_sim:
                best_sim = sim
                best_concept = snap

        if best_sim >= self.similarity_threshold and best_concept is not None:
            return best_concept, best_sim
        return None, best_sim

    def store_concept(
        self,
        fingerprint: np.ndarray,
        classifier: AdaptiveClassifier,
        step: int,
    ) -> Optional[ConceptSnapshot]:
        """Stores a new concept snapshot, evicting the least valuable if at capacity."""
        if self.max_concepts <= 0:
            return None

        if len(self.concepts) >= self.max_concepts:
            # Evict least-frequently / least-recently used concept
            evict_id = min(
                self.concepts.keys(),
                key=lambda cid: (self.concepts[cid].usage_count, self.concepts[cid].last_used_step),
            )
            del self.concepts[evict_id]

        cid = f"concept_{self._next_id}"
        self._next_id += 1
        snap = ConceptSnapshot(
            concept_id=cid,
            fingerprint=fingerprint.copy(),
            classifier=copy.deepcopy(classifier),
            creation_step=step,
            last_used_step=step,
            usage_count=1,
        )
        self.concepts[cid] = snap
        return snap

    def update_concept(self, concept_id: str, fingerprint: np.ndarray, classifier: AdaptiveClassifier, step: int) -> None:
        """Updates an existing concept snapshot with EMA fingerprint smoothing."""
        if concept_id in self.concepts:
            snap = self.concepts[concept_id]
            snap.fingerprint = 0.8 * snap.fingerprint + 0.2 * fingerprint
            norm = np.linalg.norm(snap.fingerprint)
            snap.fingerprint /= max(norm, 1e-8)
            snap.classifier = copy.deepcopy(classifier)
            snap.last_used_step = step
            snap.usage_count += 1


class ALA30AdaptiveLearner:
    """
    ALA 3.0 Recurring-Concept Adaptive Classifier.
    Integrates ADWIN drift detection with Recurring Concept Memory to avoid
    catastrophic forgetting on cyclical and recurrent non-stationary data streams.
    """

    def __init__(
        self,
        n_features: int,
        n_classes: int = 2,
        grace_period: int = 50,
        delta: float = 0.002,
        max_concepts: int = 5,
        similarity_threshold: float = 0.85,
        cooldown_steps: int = 5,
        replay_capacity: int = 1000,
    ):
        self.n_features = n_features
        self.n_classes = n_classes
        self.grace_period = grace_period
        self.delta = delta
        self.cooldown_steps = cooldown_steps

        self.classifier = AdaptiveClassifier(
            n_features=n_features,
            n_classes=n_classes,
            grace_period=grace_period,
            delta=delta,
        )
        self.adwin = ReliabilityWeightedADWIN(delta=delta)
        self.replay = ClassBalancedReservoirReplay(capacity=replay_capacity, n_classes=n_classes)
        self.fingerprinter = ConceptFingerprinter(n_features=n_features, n_classes=n_classes)
        self.memory = RecurringConceptMemory(
            max_concepts=max_concepts,
            similarity_threshold=similarity_threshold,
        )

        self.total_steps = 0
        self.drift_resets = 0
        self.recurring_restorations = 0
        self.cooldown_remaining = 0
        self.active_concept_id: Optional[str] = None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.classifier.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def update(self, X_b: np.ndarray, y_b: np.ndarray) -> Dict[str, Any]:
        """Prequential update step coordinating drift detection, memory matching, and rehearsal."""
        self.total_steps += 1
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # 1. Evaluate prequential errors
        probas = self.predict_proba(X_b)
        preds = np.argmax(probas, axis=1)
        errs = (preds != y_b).astype(float)
        batch_acc = 1.0 - float(np.mean(errs))

        # 2. Check for concept drift via ADWIN
        drift_detected = any(self.adwin.update(e) for e in errs)
        action_taken = "INCREMENTAL_UPDATE"
        matched_concept_id = None
        similarity_score = 0.0

        if drift_detected and self.cooldown_remaining == 0:
            fp = self.fingerprinter.compute_fingerprint(X_b, y_b)
            matching_snap, sim = self.memory.find_matching_concept(fp)
            similarity_score = sim

            if matching_snap is not None:
                # Recurring concept identified: RESTORE instead of blank reset
                self.recurring_restorations += 1
                action_taken = f"RECURRING_RESTORE_{matching_snap.concept_id}"
                self.classifier = copy.deepcopy(matching_snap.classifier)
                self.active_concept_id = matching_snap.concept_id
                self.memory.update_concept(matching_snap.concept_id, fp, self.classifier, self.total_steps)
                matched_concept_id = matching_snap.concept_id
            else:
                # Novel concept: save current model snapshot before reset
                if self.active_concept_id is not None:
                    curr_fp = self.fingerprinter.compute_fingerprint(X_b, y_b)
                    self.memory.update_concept(self.active_concept_id, curr_fp, self.classifier, self.total_steps)
                else:
                    curr_fp = self.fingerprinter.compute_fingerprint(X_b, y_b)
                    new_snap = self.memory.store_concept(curr_fp, self.classifier, self.total_steps)
                    self.active_concept_id = new_snap.concept_id if new_snap is not None else None

                # Reset classifier and seed from reservoir replay
                self.drift_resets += 1
                action_taken = "NOVEL_CONCEPT_RESET"
                self.classifier = AdaptiveClassifier(
                    n_features=self.n_features,
                    n_classes=self.n_classes,
                    grace_period=self.grace_period,
                    delta=self.delta,
                )
                if self.replay.total_stored >= 100:
                    X_rep, y_rep = self.replay.sample(min(200, self.replay.total_stored))
                    self.classifier.partial_fit(X_rep, y_rep)

            self.cooldown_remaining = self.cooldown_steps
            # Reset ADWIN window after drift handling
            self.adwin = ReliabilityWeightedADWIN(delta=self.delta)

        # 3. Partial fit on current batch and add to replay
        self.classifier.partial_fit(X_b, y_b)
        self.replay.add(X_b, y_b)

        return {
            "step": self.total_steps,
            "drift_detected": drift_detected,
            "action": action_taken,
            "matched_concept": matched_concept_id,
            "similarity": similarity_score,
            "batch_acc": batch_acc,
            "stored_concepts": len(self.memory.concepts),
        }
