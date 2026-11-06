"""Unified Learning Controller V4.1 (ULC-v4.1 Hybrid).

Production-promoted master controller integrating ALA 2.0, RLA 2.0, RAO 2.0,
and Adaptive Minority Intelligence with spatial feature discordance gating,
noise-gated prior tracking, on-demand explainability, and full checkpoint serialization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from robust_adapt.core.validation import check_array_2d, check_labels_1d
from robust_adapt.ulc.confidence import ConfidenceEngine, ConfidenceScores
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.explainer import ULCExplainer
from robust_adapt.ulc.spatial import compute_spatial_discordance
from robust_adapt.ulc.v4_automaton import (
    ArbitrationAutomatonV4,
    AutomatonStateV4,
    DirectiveV4,
)
from robust_adapt.ulc.v4_evidence import EvidenceSynthesizerV4, EvidenceVectorV4

logger = logging.getLogger(__name__)


@dataclass
class ULCv41Config:
    """Configuration hyperparameters for UnifiedLearningControllerV4_1.

    Parameters
    ----------
    spatial_k : int, default=5
        Number of nearest neighbors to evaluate for spatial discordance.
    spatial_discordance_threshold : float, default=0.25
        Maximum spatial discordance to classify an event as genuine concept drift.
        Discordance above this threshold indicates label noise corruption.
    prior_freeze_threshold : float, default=0.30
        Discordance ceiling above which online minority prior updates are frozen.
    tau_tie : float, default=0.10
        Hoeffding tie-breaking threshold under streaming attribute parity.
    gamma_smoothing : float, default=0.50
        Exponential moving average smoothing factor for cost-sensitive thresholds.
    max_noise_dwell : int, default=20
        Maximum consecutive steps allowed in NOISE_BURST state before timeout escape.
    max_history_len : int, default=1000
        Maximum number of historical steps retained in memory ring-buffers.
    generate_explanations : bool, default=False
        Whether to generate verbose natural-language explanation narratives on every step.
    cooldown_steps : int, default=10
        Number of steps to remain in COOLDOWN state following adaptation intervention.
    """

    spatial_k: int = 5
    spatial_discordance_threshold: float = 0.25
    prior_freeze_threshold: float = 0.30
    tau_tie: float = 0.10
    gamma_smoothing: float = 0.50
    max_noise_dwell: int = 20
    max_history_len: int = 1000
    generate_explanations: bool = False
    cooldown_steps: int = 10

    def __post_init__(self) -> None:
        if self.spatial_k < 1:
            raise ValueError(f"spatial_k must be >= 1, got {self.spatial_k}")
        if not (0.0 <= self.spatial_discordance_threshold <= 1.0):
            raise ValueError(
                f"spatial_discordance_threshold must be in [0, 1], got {self.spatial_discordance_threshold}"
            )
        if not (0.0 <= self.prior_freeze_threshold <= 1.0):
            raise ValueError(
                f"prior_freeze_threshold must be in [0, 1], got {self.prior_freeze_threshold}"
            )
        if self.tau_tie < 0.0:
            raise ValueError(f"tau_tie must be >= 0.0, got {self.tau_tie}")
        if not (0.0 < self.gamma_smoothing <= 1.0):
            raise ValueError(
                f"gamma_smoothing must be in (0, 1], got {self.gamma_smoothing}"
            )
        if self.max_noise_dwell < 1:
            raise ValueError(f"max_noise_dwell must be >= 1, got {self.max_noise_dwell}")
        if self.max_history_len < 1:
            raise ValueError(f"max_history_len must be >= 1, got {self.max_history_len}")
        if self.cooldown_steps < 0:
            raise ValueError(f"cooldown_steps must be >= 0, got {self.cooldown_steps}")


class UnifiedLearningControllerV4_1:
    """ULC-v4.1 Master Controller coordinating all four pillars in AdaptiveML.

    Features:
    - Spatial Feature Discordance to resolve the Scenario A noise vs drift deadlock.
    - Noise-gated class-prior and threshold tracking for Minority Intelligence.
    - Safe maximum dwell timeout escaping absorbing noise states.
    - On-demand zero-overhead explainability.
    - Bounded $O(1)$ memory ring buffers.
    - Complete checkpoint serialization and recovery.

    Parameters
    ----------
    config : Optional[ULCv41Config], default=None
        Hyperparameter configuration dataclass. If None, default config is used.
    classifier : Optional[Any], default=None
        Streaming classifier instance (e.g. AdaptiveClassifier or VectorizedHoeffdingTree).
    optimizer : Optional[Any], default=None
        Resource-aware optimizer instance (e.g. LowMemoryAdamW).
    adwin : Optional[Any], default=None
        Drift detector or multi-detector consensus engine.
    pipeline : Optional[Any], default=None
        Robust learning pipeline or multi-signal reliability scorer.
    budget_manager : Optional[Any], default=None
        Dynamic resource budget manager.
    prior_tracker : Optional[Any], default=None
        Online class-prior tracker for minority intelligence.
    threshold_manager : Optional[Any], default=None
        Adaptive cost-sensitive threshold manager.
    concept_memory : Optional[Any], default=None
        Concept memory for recurring concept retrieval.
    automaton : Optional[ArbitrationAutomatonV4], default=None
        Custom 12-state arbitration automaton.
    """

    def __init__(
        self,
        config: Optional[ULCv41Config] = None,
        classifier: Optional[Any] = None,
        optimizer: Optional[Any] = None,
        adwin: Optional[Any] = None,
        pipeline: Optional[Any] = None,
        budget_manager: Optional[Any] = None,
        prior_tracker: Optional[Any] = None,
        threshold_manager: Optional[Any] = None,
        concept_memory: Optional[Any] = None,
        automaton: Optional[ArbitrationAutomatonV4] = None,
        generate_explanations: Optional[bool] = None,
    ) -> None:
        self.config = config or ULCv41Config()
        if generate_explanations is not None:
            self.config.generate_explanations = generate_explanations

        self.classifier = classifier
        self.optimizer = optimizer
        self.adwin = adwin
        self.pipeline = pipeline
        self.budget_manager = budget_manager
        self.prior_tracker = prior_tracker
        self.threshold_manager = threshold_manager
        self.concept_memory = concept_memory

        self.automaton = automaton or ArbitrationAutomatonV4()
        self.evidence_synthesizer = EvidenceSynthesizerV4()
        self.confidence_engine = ConfidenceEngine()
        self.conflict_resolver = CrossPillarConflictResolver()
        self.explainer = ULCExplainer()

        self.total_steps: int = 0
        self.noise_dwell_counter: int = 0
        self.last_directive_: Optional[DirectiveV4] = None
        self.last_telemetry_: Optional[Dict[str, Any]] = None
        self.history_: List[Dict[str, Any]] = []
        self.intervention_history_: List[Dict[str, Any]] = []

    def step(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_ids: Optional[Sequence[str]] = None,
        logits: Optional[np.ndarray] = None,
        delta_drift: Optional[float] = None,
        current_loss: Optional[float] = None,
        observed_delay: float = 0.0,
    ) -> Tuple[DirectiveV4, Dict[str, Any]]:
        """Execute a coordinated streaming step across all connected pillars.

        Parameters
        ----------
        X : np.ndarray
            Feature batch of shape ``(n_samples, n_features)``.
        y : np.ndarray
            Target labels of shape ``(n_samples,)``.
        sample_ids : Optional[Sequence[str]], default=None
            Sample identifiers for delayed-label tracking.
        logits : Optional[np.ndarray], default=None
            Pre-computed model logits.
        delta_drift : Optional[float], default=None
            Externally provided drift magnitude.
        current_loss : Optional[float], default=None
            Observed batch loss for trend tracking.
        observed_delay : float, default=0.0
            Mean observed label delay steps.

        Returns
        -------
        Tuple[DirectiveV4, Dict[str, Any]]
            (final_action_directive, detailed_telemetry_dict)
        """
        self.total_steps += 1
        X_val = check_array_2d(X, name="X")
        n_samples = X_val.shape[0]
        y_val = check_labels_1d(y, expected_len=n_samples, name="y")

        # 1. Prediction / Posterior probabilities
        probas = None
        if logits is not None:
            max_z = np.max(logits, axis=1, keepdims=True)
            exp_z = np.exp(logits - max_z)
            probas = exp_z / np.sum(exp_z, axis=1, keepdims=True)
        elif self.classifier is not None and hasattr(self.classifier, "predict_proba"):
            try:
                probas = self.classifier.predict_proba(X_val)
            except Exception:
                pass

        # 2. Spatial Feature Discordance
        effective_k = min(self.config.spatial_k, max(1, n_samples - 1))
        spatial_disc = compute_spatial_discordance(X_val, y_val, k=effective_k)

        # 3. RLA Reliability Scoring
        if self.pipeline is not None and hasattr(self.pipeline, "scorer"):
            if logits is None and probas is not None:
                logits = np.log(np.clip(probas, 1e-12, 1.0))
            reliabilities = self.pipeline.scorer.score_samples(X_val, logits, y_val)
        elif self.pipeline is not None and hasattr(self.pipeline, "score_reliability"):
            reliabilities = self.pipeline.score_reliability(X_val, y_val, probas=probas)
        elif probas is not None:
            correct_p = probas[np.arange(n_samples), y_val]
            reliabilities = np.clip(correct_p, 0.05, 1.0)
        else:
            reliabilities = np.ones(n_samples, dtype=np.float64)

        # Decouple sample weight from unadapted model during genuine drift
        if spatial_disc <= 0.15:
            # Genuine drift: features are internally coherent, trust new labels
            training_weights = np.ones(n_samples, dtype=np.float64)
        else:
            training_weights = reliabilities

        # 4. Minority Prior Tracking with Noise Gating
        imbalance_ratio = 1.0
        is_emerging = False
        if self.prior_tracker is not None:
            if spatial_disc <= self.config.prior_freeze_threshold:
                self.prior_tracker.update(y_val)
            imbalance_ratio = getattr(self.prior_tracker, "imbalance_ratio", 1.0)
            if hasattr(self.prior_tracker, "is_emerging"):
                is_emerging = any(self.prior_tracker.is_emerging(c) for c in np.unique(y_val))
            if self.threshold_manager is not None and hasattr(self.prior_tracker, "priors"):
                if hasattr(self.threshold_manager, "update_from_priors"):
                    self.threshold_manager.update_from_priors(self.prior_tracker.priors)

        # 5. Drift Signal & Concept Memory Query
        if delta_drift is None:
            if self.adwin is not None:
                errs = (
                    (np.argmax(probas, axis=1) != y_val).astype(float)
                    if probas is not None
                    else np.zeros(n_samples)
                )
                drift_found = False
                mean_r = float(np.mean(reliabilities))
                for e in errs:
                    if hasattr(self.adwin, "update"):
                        if self.adwin.update(e, reliability=mean_r):
                            drift_found = True
                delta = 1.20 if drift_found else 0.10
            else:
                delta = 0.10
        else:
            delta = float(delta_drift)

        recurring_sim = 0.0
        matched_concept = None
        if self.concept_memory is not None and delta >= 0.50:
            query_res = self.concept_memory.query_recurring(X_val)
            if query_res is not None:
                matched_concept, _, recurring_sim = query_res

        # 6. RAO Budget Telemetry
        u_res = 0.20
        if self.budget_manager is not None:
            cur_mb = getattr(self.budget_manager, "current_memory_mb", 200.0)
            max_b = getattr(self.budget_manager, "max_memory_bytes", 1024 * 1024 * 1024)
            u_res = float(cur_mb / (max_b / (1024**2)))

        # 7. Synthesize 10D Evidence Vector
        evidence = self.evidence_synthesizer.synthesize(
            delta_drift=delta,
            reliabilities=reliabilities,
            probas=probas,
            current_loss=current_loss,
            resource_utilization=u_res,
            imbalance_ratio=imbalance_ratio,
            observed_delay=observed_delay,
            recurring_similarity=recurring_sim,
            is_emerging_class=is_emerging,
        )

        # 8. Adaptive Confidence & Automaton Transition
        raw_directive = self.automaton.transition(evidence)
        base_conf = self.confidence_engine.evaluate(evidence, tau_r=self.automaton.tau_R)

        # Calibrated spatial confidence adjustments
        ent = evidence.predictive_entropy
        spatial_coherence = max(0.0, 1.0 - spatial_disc * 2.0)
        c_adapt = float(np.clip(delta * spatial_coherence * (1.0 - 0.5 * ent), 0.0, 1.0))
        c_suppress = float(np.clip(delta * spatial_disc, 0.0, 1.0))
        conf = ConfidenceScores(
            adapt=c_adapt,
            suppress_noise=c_suppress,
            throttle_resources=base_conf.throttle_resources,
            restore_concept=base_conf.restore_concept,
            mitigate_asymmetric_noise=base_conf.mitigate_asymmetric_noise,
        )

        # 9. Remediated Cross-Pillar Conflict Resolution
        final_directive, scenario_name = self.conflict_resolver.resolve_conflicts(
            directive=raw_directive,
            evidence=evidence,
            confidence=conf,
            spatial_discordance=spatial_disc,
            noise_dwell=self.noise_dwell_counter,
        )

        # 10. Maximum Dwell Timeout Safety Valve
        if final_directive.state == AutomatonStateV4.NOISE_BURST:
            self.noise_dwell_counter += 1
            if self.noise_dwell_counter > self.config.max_noise_dwell:
                # Force escape from absorbing noise state into RECOVERY
                final_directive = DirectiveV4(
                    state=AutomatonStateV4.RECOVERY,
                    learning_rate_scale=1.0,
                    sample_filter_threshold=0.50,
                    confidence=0.75,
                    message=f"[Timeout Escape] Exceeded maximum noise dwell ({self.config.max_noise_dwell} steps): resuming adaptation.",
                )
                scenario_name = "Safety Valve: Dwell Timeout Escape"
        else:
            self.noise_dwell_counter = 0

        # 11. Execute Coordinated Actions across Connected Submodules
        # A. Sample Filtering
        if final_directive.sample_filter_threshold > 0.0:
            mask = reliabilities >= final_directive.sample_filter_threshold
            if not np.any(mask):
                mask = np.ones(n_samples, dtype=bool)
            X_train = X_val[mask]
            y_train = y_val[mask]
            w_train = training_weights[mask]
        else:
            X_train = X_val
            y_train = y_val
            w_train = training_weights

        # B. Classifier Updates
        if self.classifier is not None and len(X_train) > 0:
            # Recurring concept restoration
            if final_directive.restore_concept_id and self.concept_memory is not None:
                match_info = self.concept_memory.query_recurring(X_val)
                if match_info is not None and hasattr(self.classifier, "load_state_dict"):
                    _, restored_state, _ = match_info
                    self.classifier.load_state_dict(restored_state)
            elif final_directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
                # Confirmed drift: reset tree while preserving replay buffer
                buf = getattr(self.classifier, "_replay_buffer", None)
                if hasattr(self.classifier, "reset"):
                    self.classifier.reset()
                if buf is not None and hasattr(self.classifier, "_replay_buffer"):
                    self.classifier._replay_buffer = buf

            # Replay Buffer Purge
            if final_directive.purge_replay_policy != "none":
                if hasattr(self.classifier, "purge_replay"):
                    self.classifier.purge_replay(
                        policy=final_directive.purge_replay_policy,
                        keep_minority=final_directive.keep_minority_in_replay,
                    )
                elif hasattr(self.classifier, "replay_buffer"):
                    buf = getattr(self.classifier, "replay_buffer")
                    if hasattr(buf, "purge"):
                        buf.purge(
                            policy=final_directive.purge_replay_policy,
                            keep_minority=final_directive.keep_minority_in_replay,
                        )

            # Partial fit
            if hasattr(self.classifier, "partial_fit"):
                self.classifier.partial_fit(X_train, y_train, sample_weight=w_train)

        # C. Optimizer Updates
        if self.optimizer is not None:
            if final_directive.reset_momentum and hasattr(self.optimizer, "reset_momenta"):
                self.optimizer.reset_momenta()
            if final_directive.learning_rate_scale != 1.0 and hasattr(self.optimizer, "scale_learning_rate"):
                self.optimizer.scale_learning_rate(final_directive.learning_rate_scale)

        # 12. On-Demand Explainability
        if self.config.generate_explanations:
            explanation = self.explainer.explain(final_directive, evidence, scenario_name)
        else:
            explanation = {
                "scenario": scenario_name,
                "state": final_directive.state.value,
                "confidence": final_directive.confidence,
                "message": final_directive.message,
            }

        self.last_directive_ = final_directive

        telemetry: Dict[str, Any] = {
            "step": self.total_steps,
            "state": final_directive.state.value,
            "scenario": scenario_name,
            "spatial_discordance": spatial_disc,
            "evidence": evidence.to_dict(),
            "explanation": explanation,
            "n_input_samples": n_samples,
            "n_retained_samples": len(X_train),
            "mean_reliability": float(np.mean(reliabilities)),
            "noise_dwell": self.noise_dwell_counter,
        }
        self.last_telemetry_ = telemetry

        # 13. Maintain Bounded History
        self._record_history(telemetry, final_directive)

        return final_directive, telemetry

    def _record_history(self, telemetry: Dict[str, Any], directive: DirectiveV4) -> None:
        """Record bounded step history and interventions."""
        if len(self.history_) >= self.config.max_history_len:
            self.history_.pop(0)
        self.history_.append(telemetry)

        # Track active interventions
        is_intervention = (
            directive.state
            in (
                AutomatonStateV4.CONFIRMED_DRIFT,
                AutomatonStateV4.NOISE_BURST,
                AutomatonStateV4.RESOURCE_CONSTRAINED,
                AutomatonStateV4.ASYMMETRIC_NOISE_MITIGATION,
            )
            or directive.reset_momentum
            or directive.purge_replay_policy != "none"
            or directive.restore_concept_id is not None
        )
        if is_intervention:
            if len(self.intervention_history_) >= self.config.max_history_len:
                self.intervention_history_.pop(0)
            self.intervention_history_.append(
                {
                    "step": self.total_steps,
                    "state": directive.state.value,
                    "scenario": telemetry["scenario"],
                    "confidence": directive.confidence,
                    "spatial_discordance": telemetry["spatial_discordance"],
                    "message": directive.message,
                }
            )

    def explain(
        self,
        directive: Optional[DirectiveV4] = None,
        evidence: Optional[EvidenceVectorV4] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete natural-language explanation on demand."""
        d = directive or self.last_directive_
        if d is None:
            return {"error": "No directive available to explain."}
        ev = evidence or self.evidence_synthesizer.synthesize()
        sc = scenario or (self.last_telemetry_["scenario"] if self.last_telemetry_ else "Nominal")
        return self.explainer.explain(d, ev, sc)

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent controller step history up to limit."""
        if limit is None or limit >= len(self.history_):
            return list(self.history_)
        return list(self.history_[-limit:])

    def get_intervention_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve historical controller intervention events up to limit."""
        if limit is None or limit >= len(self.intervention_history_):
            return list(self.intervention_history_)
        return list(self.intervention_history_[-limit:])

    def reset(self) -> None:
        """Reset all stateful counters and history buffers."""
        self.total_steps = 0
        self.noise_dwell_counter = 0
        self.last_directive_ = None
        self.last_telemetry_ = None
        self.history_.clear()
        self.intervention_history_.clear()
        self.automaton.reset()

    def state_dict(self) -> Dict[str, Any]:
        """Serialize controller state into a JSON-compatible dictionary."""
        return {
            "version": "4.1",
            "total_steps": self.total_steps,
            "noise_dwell_counter": self.noise_dwell_counter,
            "automaton_state": self.automaton.state.value,
            "config": asdict(self.config),
            "last_directive": asdict(self.last_directive_) if self.last_directive_ else None,
            "intervention_count": len(self.intervention_history_),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore controller state from a dictionary.

        Raises
        ------
        ValueError
            If state is invalid or incompatible.
        """
        if not isinstance(state, dict):
            raise ValueError(f"state must be a dictionary, got {type(state)}")
        version = state.get("version", "")
        if version != "4.1":
            raise ValueError(f"Incompatible state_dict version: expected '4.1', got '{version}'")

        self.total_steps = int(state.get("total_steps", 0))
        self.noise_dwell_counter = int(state.get("noise_dwell_counter", 0))

        # Restore automaton state
        state_str = state.get("automaton_state")
        if state_str:
            try:
                self.automaton.state = AutomatonStateV4(state_str)
            except ValueError:
                logger.warning(f"Unknown automaton state '{state_str}', defaulting to NOMINAL")
                self.automaton.state = AutomatonStateV4.NOMINAL

        # Restore config if provided
        if "config" in state and isinstance(state["config"], dict):
            try:
                self.config = ULCv41Config(**state["config"])
            except Exception as e:
                logger.warning(f"Could not restore ULCv41Config from state_dict: {e}")
