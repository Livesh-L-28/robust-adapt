"""
Stage 7.1 Profiling Script: Measure execution latency of every component in ULC-v4.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.rla.scorer import DensityAwareMarginScorer
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.ulc.v4_evidence import EvidenceSynthesizerV4
from adaptive_ml.ulc.v4_automaton import ArbitrationAutomatonV4
from adaptive_ml.ulc.conflict_resolver import CrossPillarConflictResolver
from adaptive_ml.ulc.explainer import ULCExplainer


def profile_components() -> None:
    clf = AdaptiveClassifier(4, 2)
    scorer = DensityAwareMarginScorer(n_classes=2)
    prior = OnlineClassPriorTracker(2)
    thresh = AdaptiveThresholdManager(2)
    synth = EvidenceSynthesizerV4()
    auto = ArbitrationAutomatonV4()
    resolver = CrossPillarConflictResolver()
    explainer = ULCExplainer()

    X = np.random.randn(30, 4)
    y = np.array([0] * 27 + [1] * 3)
    clf.fit(X, y)

    N = 300

    # 1. Prediction
    t0 = time.perf_counter()
    for _ in range(N):
        p = clf.predict_proba(X)
    t_pred = (time.perf_counter() - t0) / N * 1000.0

    # 2. Reliability Scoring
    logits = np.log(np.clip(p, 1e-12, 1.0))
    t0 = time.perf_counter()
    for _ in range(N):
        r = scorer.score_samples(X, logits, y)
    t_rel = (time.perf_counter() - t0) / N * 1000.0

    # 3. Prior Tracking
    t0 = time.perf_counter()
    for _ in range(N):
        prior.update(y)
    t_prior = (time.perf_counter() - t0) / N * 1000.0

    # 4. Adaptive Threshold Update
    t0 = time.perf_counter()
    for _ in range(N):
        thresh.update_from_priors(prior.priors)
    t_thresh = (time.perf_counter() - t0) / N * 1000.0

    # 5. Evidence Synthesis
    t0 = time.perf_counter()
    for _ in range(N):
        ev = synth.synthesize(delta_drift=0.1, reliabilities=r, probas=p)
    t_synth = (time.perf_counter() - t0) / N * 1000.0

    # 6. Automaton Transition
    t0 = time.perf_counter()
    for _ in range(N):
        directive = auto.transition(ev)
    t_auto = (time.perf_counter() - t0) / N * 1000.0

    # 7. Confidence & Conflict Resolution
    conf = auto.confidence_engine.evaluate(ev)
    t0 = time.perf_counter()
    for _ in range(N):
        resolved, scen = resolver.resolve_conflicts(directive, ev, conf)
    t_res = (time.perf_counter() - t0) / N * 1000.0

    # 8. Explainability
    t0 = time.perf_counter()
    for _ in range(N):
        exp = explainer.explain(resolved, ev, scen)
    t_exp = (time.perf_counter() - t0) / N * 1000.0

    # 9. Partial Fit Update
    t0 = time.perf_counter()
    for _ in range(N):
        clf.partial_fit(X, y)
    t_fit = (time.perf_counter() - t0) / N * 1000.0

    total_step = t_pred + t_rel + t_prior + t_thresh + t_synth + t_auto + t_res + t_exp + t_fit

    profiling_data = {
        "prediction_ms": round(t_pred, 4),
        "reliability_scoring_ms": round(t_rel, 4),
        "prior_tracking_ms": round(t_prior, 4),
        "threshold_updating_ms": round(t_thresh, 4),
        "evidence_synthesis_ms": round(t_synth, 4),
        "automaton_transition_ms": round(t_auto, 4),
        "conflict_resolution_ms": round(t_res, 4),
        "explanation_generation_ms": round(t_exp, 4),
        "model_partial_fit_ms": round(t_fit, 4),
        "total_step_overhead_ms": round(total_step, 4),
        "percentage_in_controller_overhead": round((t_synth + t_auto + t_res + t_exp) / total_step * 100.0, 2),
        "percentage_in_explainer": round(t_exp / total_step * 100.0, 2),
    }

    out_file = Path(__file__).resolve().parent / "ULC_V4_PROFILING_RESULTS.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(profiling_data, f, indent=2)

    print("ULC-v4 Component Latency Breakdown:")
    for k, v in profiling_data.items():
        print(f"  {k:36s}: {v}")


if __name__ == "__main__":
    profile_components()

