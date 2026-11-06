"""Unified Learning Controller V4 (ULC-v4).

Master coordinator orchestrating ALA 2.0, RLA 2.0, RAO 2.0, and Adaptive Minority Intelligence.
Executes multi-objective Pareto arbitration, Scenarios A-J conflict resolution, and auditable explanations.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from robust_adapt.core.validation import check_array_2d, check_labels_1d
from robust_adapt.ulc.confidence import ConfidenceEngine
from robust_adapt.ulc.conflict_resolver import CrossPillarConflictResolver
from robust_adapt.ulc.explainer import ULCExplainer
from robust_adapt.ulc.v4_automaton import ArbitrationAutomatonV4, AutomatonStateV4, DirectiveV4
from robust_adapt.ulc.v4_evidence import EvidenceSynthesizerV4, EvidenceVectorV4


class UnifiedLearningControllerV4:
    """Master controller orchestrating all four pillars in AdaptiveML.

    Parameters
    ----------
    classifier : Optional[Any], default=None
        Streaming classifier instance.
    optimizer : Optional[Any], default=None
        Adaptive optimizer instance.
    adwin : Optional[Any], default=None
        Drift detector or multi-detector consensus engine.
    pipeline : Optional[Any], default=None
        Robust learning pipeline or reliability scorer.
    budget_manager : Optional[Any], default=None
        Dynamic resource budget manager.
    prior_tracker : Optional[Any], default=None
        Online class-prior tracker.
    threshold_manager : Optional[Any], default=None
        Adaptive threshold manager.
    concept_memory : Optional[Any], default=None
        Concept memory for recurring concept retrieval.
    automaton : Optional[ArbitrationAutomatonV4], default=None
        Custom 12-state arbitration automaton.
    """

    def __init__(
        self,
        classifier: Optional[Any] = None,
        optimizer: Optional[Any] = None,
        adwin: Optional[Any] = None,
        pipeline: Optional[Any] = None,
        budget_manager: Optional[Any] = None,
        prior_tracker: Optional[Any] = None,
        threshold_manager: Optional[Any] = None,
        concept_memory: Optional[Any] = None,
        automaton: Optional[ArbitrationAutomatonV4] = None,
    ) -> None:
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
        self.conflict_resolver = CrossPillarConflictResolver()
        self.explainer = ULCExplainer()

        self.total_steps: int = 0
        self.last_directive_: Optional[DirectiveV4] = None
        self.last_explanation_: Optional[Dict[str, Any]] = None

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

        Returns
        -------
        Tuple[DirectiveV4, Dict[str, Any]]
            (action_directive, detailed_telemetry_dict)
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

        # 2. RLA Reliability Scoring
        if self.pipeline is not None and hasattr(self.pipeline, "score_reliability"):
            reliabilities = self.pipeline.score_reliability(X_val, y_val, probas=probas)
        elif probas is not None:
            # Fallback margin-based reliability
            correct_p = probas[np.arange(n_samples), y_val]
            reliabilities = np.clip(correct_p, 0.05, 1.0)
        else:
            reliabilities = np.ones(n_samples, dtype=np.float64)

        # 3. Minority Prior Tracking
        imbalance_ratio = 1.0
        is_emerging = False
        if self.prior_tracker is not None:
            self.prior_tracker.update(y_val)
            imbalance_ratio = self.prior_tracker.imbalance_ratio
            is_emerging = any(self.prior_tracker.is_emerging(c) for c in np.unique(y_val))

        # 4. Drift Signal Generation
        if delta_drift is None:
            if self.adwin is not None:
                # Query adwin / consensus
                errs = (np.argmax(probas, axis=1) != y_val).astype(float) if probas is not None else np.zeros(n_samples)
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

        # 5. Concept Memory Match Query
        recurring_sim = 0.0
        matched_concept = None
        if self.concept_memory is not None and delta >= 0.50:
            query_res = self.concept_memory.query_recurring(X_val)
            if query_res is not None:
                matched_concept, _, recurring_sim = query_res

        # 6. RAO Budget Telemetry
        u_res = 0.20
        if self.budget_manager is not None:
            u_res = float(self.budget_manager.current_memory_mb / (self.budget_manager.max_memory_bytes / (1024**2)))

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

        # 8. 12-State Automaton Transition
        raw_directive = self.automaton.transition(evidence)
        conf = self.automaton.confidence_engine.evaluate(evidence, tau_r=self.automaton.tau_R)

        # 9. Scenarios A-J Cross-Pillar Conflict Resolution
        final_directive, scenario_name = self.conflict_resolver.resolve_conflicts(
            directive=raw_directive,
            evidence=evidence,
            confidence=conf,
        )

        # 10. Execute Directive Actions across Connected Pillars
        # A. Filter samples if filter threshold > 0
        if final_directive.sample_filter_threshold > 0.0:
            mask = reliabilities >= final_directive.sample_filter_threshold
            X_train = X_val[mask]
            y_train = y_val[mask]
            w_train = reliabilities[mask]
        else:
            X_train = X_val
            y_train = y_val
            w_train = reliabilities

        # B. Classifier updates
        if self.classifier is not None and len(X_train) > 0:
            # Recurring concept restoration
            if final_directive.restore_concept_id and self.concept_memory is not None:
                match_info = self.concept_memory.query_recurring(X_val)
                if match_info is not None and hasattr(self.classifier, "load_state_dict"):
                    _, restored_state, _ = match_info
                    self.classifier.load_state_dict(restored_state)
            elif final_directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
                # Confirmed non-recurring drift: reset tree while preserving replay buffer
                buf = getattr(self.classifier, "_replay_buffer", None)
                if hasattr(self.classifier, "reset"):
                    self.classifier.reset()
                if buf is not None and hasattr(self.classifier, "_replay_buffer"):
                    self.classifier._replay_buffer = buf

            # Purge replay if requested
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

        # C. Optimizer updates
        if self.optimizer is not None:
            if final_directive.reset_momentum and hasattr(self.optimizer, "reset_momenta"):
                self.optimizer.reset_momenta()
            if final_directive.learning_rate_scale != 1.0 and hasattr(self.optimizer, "scale_learning_rate"):
                self.optimizer.scale_learning_rate(final_directive.learning_rate_scale)

        # 11. Generate Explainability Narrative
        explanation = self.explainer.explain(final_directive, evidence, scenario_name)

        self.last_directive_ = final_directive
        self.last_explanation_ = explanation

        telemetry = {
            "step": self.total_steps,
            "state": final_directive.state.value,
            "scenario": scenario_name,
            "evidence": evidence.to_dict(),
            "explanation": explanation,
            "n_input_samples": n_samples,
            "n_retained_samples": len(X_train),
            "mean_reliability": float(np.mean(reliabilities)),
        }

        return final_directive, telemetry
