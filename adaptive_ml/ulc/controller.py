"""
AdaptiveML Unified Learning Controller (ULC) Facade.

Coordinates cross-pillar interactions between ALA, RLA, and RAO,
resolving the concept drift vs noise burst dilemma through formal
dual-evidence arbitration.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

from adaptive_ml.core.config import ULCConfig
from adaptive_ml.core.validation import check_array_2d, check_labels_1d
from adaptive_ml.ulc.automaton import ArbitrationAutomaton
from adaptive_ml.ulc.directives import ControllerDirective, ControllerState
from adaptive_ml.ulc.evidence import EvidenceSynthesizer, EvidenceVector


class AdaptiveLearningController:
    """Holistic coordinator for streaming learning under drift and label noise."""

    def __init__(
        self,
        classifier: Optional[Any] = None,
        pipeline: Optional[Any] = None,
        optimizer: Optional[Any] = None,
        adwin: Optional[Any] = None,
        config: Optional[ULCConfig] = None,
    ) -> None:
        """Initialize the unified learning controller.

        Args:
            classifier: Optional ALA classifier (e.g., AdaptiveClassifier).
            pipeline: Optional RLA pipeline (e.g., RobustLearningPipeline).
            optimizer: Optional RAO optimizer (e.g., LowMemoryAdamW).
            adwin: Optional ALA drift detector (e.g., ReliabilityWeightedADWIN).
            config: Optional ULCConfig configuration.
        """
        self.classifier = classifier
        self.pipeline = pipeline
        self.optimizer = optimizer
        self.adwin = adwin
        self.config = config or ULCConfig()

        self.synthesizer = EvidenceSynthesizer()
        self.automaton = ArbitrationAutomaton(config=self.config)

    @property
    def current_state(self) -> ControllerState:
        """Current operational state of the arbitration automaton."""
        return self.automaton.state

    def step(
        self,
        X: np.ndarray,
        y: np.ndarray,
        logits: Optional[np.ndarray] = None,
        current_loss: Optional[float] = None,
        delta_drift: Optional[float] = None,
    ) -> Tuple[ControllerDirective, Dict[str, Any]]:
        """Process an incoming streaming batch through dual-evidence arbitration.

        Args:
            X: Feature matrix of shape (N, D).
            y: Label vector of shape (N,).
            logits: Optional model logits of shape (N, C).
            current_loss: Optional batch loss value.
            delta_drift: Optional external normalized drift divergence in [0, 2].
                         If None, inferred from attached ADWIN instance or defaults to 0.0.

        Returns:
            Tuple of (ControllerDirective, diagnostic_info_dict).
        """
        X = check_array_2d(X)
        y = check_labels_1d(y)
        n_samples = len(X)

        # 1. Predictive Probabilities for Entropy Synthesis & Logits proxy
        probs: Optional[np.ndarray] = None
        if self.classifier is not None and hasattr(self.classifier, "predict_proba"):
            try:
                probs = self.classifier.predict_proba(X)
            except Exception:
                probs = None

        if logits is None and probs is not None:
            logits = np.log(np.clip(probs, 1e-12, 1.0))

        # 2. RLA Reliability Scoring
        if self.pipeline is not None and hasattr(self.pipeline, "scorer"):
            if logits is None:
                n_c = getattr(self.pipeline.scorer, "n_classes", int(np.max(y) + 1) if len(y) > 0 else 2)
                logits = np.zeros((n_samples, n_c), dtype=np.float64)
            reliabilities = self.pipeline.scorer.score_samples(X, logits, y)
        elif self.pipeline is not None and hasattr(self.pipeline, "evaluate_batch") and logits is not None:
            _, _, reliabilities = self.pipeline.evaluate_batch(X, logits, y)
        elif self.pipeline is not None and hasattr(self.pipeline, "score"):
            reliabilities = self.pipeline.score(X, y)
        else:
            reliabilities = np.ones(n_samples, dtype=np.float64)

        mean_rel = float(np.mean(reliabilities)) if len(reliabilities) > 0 else 1.0

        # 3. Drift Divergence Extraction
        if delta_drift is None:
            if self.adwin is not None:
                # If ADWIN detected drift, delta_drift >= 1.0
                if getattr(self.adwin, "drift_detected", False):
                    delta_drift = 1.0
                else:
                    delta_drift = 0.0
            else:
                delta_drift = 0.0

        # 4. Evidence Vector Synthesis
        evidence = self.synthesizer.synthesize(
            delta_drift=delta_drift,
            mean_reliability=mean_rel,
            probabilities=probs,
            current_loss=current_loss,
        )

        # 5. Automaton State Transition
        directive = self.automaton.transition(evidence)

        # 6. Apply Directives to Attached Pillars
        # Sample filtering based on directive threshold
        if directive.sample_filter_threshold > 0.0:
            mask = reliabilities >= directive.sample_filter_threshold
            # If everything gets filtered, preserve top 10% to prevent starvation
            if not np.any(mask):
                top_k = max(1, int(np.ceil(0.1 * n_samples)))
                top_idx = np.argsort(reliabilities)[-top_k:]
                mask = np.zeros(n_samples, dtype=bool)
                mask[top_idx] = True

            X_train = X[mask]
            y_train = y[mask]
            w_train = reliabilities[mask]
        else:
            X_train = X
            y_train = y
            w_train = reliabilities

        # Classifier updates
        if self.classifier is not None:
            # Purge replay if requested
            if directive.purge_replay and hasattr(self.classifier, "replay_buffer"):
                buf = getattr(self.classifier, "replay_buffer")
                if hasattr(buf, "clear"):
                    buf.clear()

            # Train classifier incrementally
            if hasattr(self.classifier, "partial_fit"):
                self.classifier.partial_fit(X_train, y_train, sample_weight=w_train)

        # Optimizer updates
        if self.optimizer is not None:
            if directive.reset_momentum and hasattr(self.optimizer, "reset_momenta"):
                self.optimizer.reset_momenta()
            if hasattr(self.optimizer, "scale_learning_rate") and directive.learning_rate_scale != 1.0:
                self.optimizer.scale_learning_rate(directive.learning_rate_scale)

        # ADWIN updates
        if self.adwin is not None and not directive.suppress_adwin:
            # If batch error or reliability can be fed to ADWIN
            if hasattr(self.adwin, "add_element"):
                # Feed error indicator or mean reliability
                for r in reliabilities:
                    self.adwin.add_element(r)

        info = {
            "state": directive.state,
            "evidence": evidence,
            "n_input_samples": n_samples,
            "n_retained_samples": len(X_train),
            "mean_reliability": mean_rel,
            "directive": directive,
        }

        return directive, info
