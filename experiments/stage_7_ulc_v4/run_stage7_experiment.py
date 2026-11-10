"""
AdaptiveML Stage 7: Master Benchmark Battery Experiment
======================================================
Comprehensive 13-Model Matrix Benchmark across 5 Seeds:
1. Static Baseline
2. Pure Hoeffding Tree
3. Standalone ADWIN (ALA 1.0)
4. Standalone RLA (SCE + Margin)
5. Standalone RAO (LowMemoryAdamW)
6. Standalone Minority (Prior + Threshold)
7. ALA + RLA (reliability-weighted ADWIN)
8. ALA + RAO (drift-triggered momentum reset)
9. RLA + RAO (robust loss + low-memory optimizer)
10. ULC-v1 Baseline (heuristic arbitration)
11. ULC-v2 Baseline (rule-based)
12. ULC-v3 Audited (evidence-based, audited)
13. ULC-v4 Master System (10D evidence, Pareto arbitration, 12-state automaton)
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Ensure repository root is on path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ala.detector import ReliabilityWeightedADWIN
from adaptive_ml.ala.concept_memory import ConceptMemory
from adaptive_ml.rla import (
    DensityAwareMarginScorer,
    MultiSignalReliabilityEngine,
    RobustLearningPipeline,
    SymmetricCrossEntropyLoss,
    FocalLoss,
)
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.budget import DynamicResourceBudgetManager
from adaptive_ml.minority.prior import OnlineClassPriorTracker
from adaptive_ml.minority.threshold import AdaptiveThresholdManager
from adaptive_ml.minority.replay import MinorityAwareReplayBuffer
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.directives import ControllerState
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4


SEEDS = [42, 123, 456, 789, 2024]
N_BATCHES = 60
BATCH_SIZE = 30
N_FEATURES = 4


class LinearSurrogate:
    """Param wrapper and forward model for gradient-based optimizer benchmarking."""
    def __init__(self, n_features: int, n_classes: int, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        self.weights = rng.normal(0, 0.05, size=(n_features, n_classes)).astype(np.float32)
        self.grad = np.zeros_like(self.weights)

    @property
    def data(self) -> np.ndarray:
        return self.weights

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        logits = X @ self.weights
        max_z = np.max(logits, axis=1, keepdims=True)
        exp_z = np.exp(logits - max_z)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def backward(self, X: np.ndarray, y: np.ndarray, sample_weights: Optional[np.ndarray] = None) -> None:
        probs = self.predict_proba(X)
        n = X.shape[0]
        one_hot = np.zeros((n, probs.shape[1]), dtype=np.float32)
        one_hot[np.arange(n), y] = 1.0
        diff = probs - one_hot
        if sample_weights is not None:
            diff *= sample_weights[:, np.newaxis]
        self.grad = (X.T @ diff / n).astype(np.float32)


def generate_stream(seed: int, n_batches: int = N_BATCHES, batch_size: int = BATCH_SIZE, n_features: int = N_FEATURES) -> List[Dict[str, Any]]:
    """Generates the standardized 60-batch imbalanced stream across 5 dynamic regimes."""
    rng = np.random.default_rng(seed)
    n_maj = int(batch_size * 0.90)  # 27 samples (90%)
    n_min = int(batch_size * 0.10)  # 3 samples (10%)

    batches = []
    for b in range(1, n_batches + 1):
        if b <= 15:
            # Regime 1: Clean Stationary Concept 0
            loc0 = [-1.5] * n_features
            loc1 = [1.5] * n_features
            delta = 0.05
            is_noise = False
            is_true_drift = False
        elif 16 <= b <= 25:
            # Regime 2: Severe Noise Burst (40% majority label noise, no true drift)
            loc0 = [-1.5] * n_features
            loc1 = [1.5] * n_features
            delta = 1.25
            is_noise = True
            is_true_drift = False
        elif 26 <= b <= 35:
            # Regime 3: Gradual Concept Drift
            alpha = (b - 25) / 10.0
            loc0 = [float(-1.5 * (1.0 - alpha) + 1.5 * alpha)] * n_features
            loc1 = [float(1.5 * (1.0 - alpha) - 1.5 * alpha)] * n_features
            delta = 0.40
            is_noise = False
            is_true_drift = True
        elif 36 <= b <= 45:
            # Regime 4: Abrupt Inverted Concept Drift
            loc0 = [2.5] * n_features
            loc1 = [-2.5] * n_features
            delta = 1.40 if b in (36, 37) else 0.10
            is_noise = False
            is_true_drift = True
        else:
            # Regime 5: Recurring Drift returning to Concept 0
            loc0 = [-1.5] * n_features
            loc1 = [1.5] * n_features
            delta = 1.30 if b in (46, 47) else 0.05
            is_noise = False
            is_true_drift = True

        X0 = rng.normal(loc=loc0, scale=0.6, size=(n_maj, n_features))
        X1 = rng.normal(loc=loc1, scale=0.6, size=(n_min, n_features))
        X_batch = np.vstack([X0, X1])
        y_batch = np.array([0] * n_maj + [1] * n_min, dtype=np.int64)

        y_clean = y_batch.copy()

        # Inject noise in Regime 2: flip 11 majority instances
        if is_noise:
            corrupt_idx = rng.choice(n_maj, size=11, replace=False)
            y_batch[corrupt_idx] = 1

        batches.append({
            "batch_idx": b,
            "X": X_batch,
            "y_observed": y_batch,
            "y_clean": y_clean,
            "delta": delta,
            "is_noise": is_noise,
            "is_true_drift": is_true_drift,
        })
    return batches


def calculate_prequential_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """Calculate accuracy, macro F1, and minority (class 1) recall."""
    acc = float(np.mean(y_true == y_pred))

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    recall_min = float(tp / max(1, (tp + fn)))
    prec_min = float(tp / max(1, (tp + fp)))
    f1_min = float(2 * prec_min * recall_min / max(1e-6, prec_min + recall_min))

    recall_maj = float(tn / max(1, (tn + fp)))
    prec_maj = float(tn / max(1, (tn + fn)))
    f1_maj = float(2 * prec_maj * recall_maj / max(1e-6, prec_maj + recall_maj))

    macro_f1 = float((f1_maj + f1_min) / 2.0)
    return acc, macro_f1, recall_min


def run_single_model(
    model_name: str,
    stream: List[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """Run an individual model configuration over the prequential stream."""
    all_y_clean = []
    all_y_pred = []
    total_drift_alarms = 0
    false_drift_resets = 0
    start_time = time.perf_counter()

    # Pre-train baseline model on first 3 batches
    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    if model_name == "Static Baseline":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, enable_drift_detection=False, random_state=seed)
        clf.fit(init_X, init_y)

        for batch in stream[3:]:
            X_b, y_clean = batch["X"], batch["y_clean"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

    elif model_name == "Pure Hoeffding Tree":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=0, enable_drift_detection=False, random_state=seed)
        clf.fit(init_X, init_y)

        for batch in stream[3:]:
            X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            clf.partial_fit(X_b, y_obs)

    elif model_name == "Standalone ADWIN (ALA 1.0)":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            # Standard unweighted ADWIN logic
            if delta >= 1.0:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.reset()
                clf.fit(X_b, y_obs)
            else:
                clf.partial_fit(X_b, y_obs)

    elif model_name == "Standalone RLA (SCE + Margin)":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=False, random_state=seed)
        clf.fit(init_X, init_y)
        scorer = DensityAwareMarginScorer(n_classes=2)

        for batch in stream[3:]:
            X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            # RLA sample weights
            probs = clf.predict_proba(X_b)
            logits_b = np.log(np.clip(probs, 1e-12, 1.0))
            w = scorer.score_samples(X_b, logits_b, y_obs)
            clf.partial_fit(X_b, y_obs, sample_weight=w)

    elif model_name == "Standalone RAO (LowMemoryAdamW)":
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)

        for batch in stream[3:]:
            X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
            probs = surrogate.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            surrogate.backward(X_b, y_obs)
            opt.step()
            opt.zero_grad()

    elif model_name == "Standalone Minority (Prior + Threshold)":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=False, random_state=seed)
        clf.fit(init_X, init_y)
        prior_tracker = OnlineClassPriorTracker(n_classes=2)
        thresh_mgr = AdaptiveThresholdManager(n_classes=2)

        for batch in stream[3:]:
            X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
            prior_tracker.update(y_obs)
            thresh_mgr.update_from_priors(prior_tracker.priors)
            probs = clf.predict_proba(X_b)
            preds = thresh_mgr.predict(probs)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)
            clf.partial_fit(X_b, y_obs)

    elif model_name == "ALA + RLA":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        scorer = DensityAwareMarginScorer(n_classes=2)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            probs = clf.predict_proba(X_b)
            logits_b = np.log(np.clip(probs, 1e-12, 1.0))
            w = scorer.score_samples(X_b, logits_b, y_obs)
            mean_w = float(np.mean(w))

            if delta >= 1.0 and mean_w >= 0.70:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.reset()
                clf.fit(X_b, y_obs, sample_weight=w)
            else:
                clf.partial_fit(X_b, y_obs, sample_weight=w)

    elif model_name == "ALA + RAO":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            preds = clf.predict(X_b)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            if delta >= 1.0:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.reset()
                opt.reset_momenta()
                clf.fit(X_b, y_obs)
            else:
                clf.partial_fit(X_b, y_obs)
                surrogate.backward(X_b, y_obs)
                opt.step()
                opt.zero_grad()

    elif model_name == "RLA + RAO":
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)
        scorer = DensityAwareMarginScorer(n_classes=2)

        for batch in stream[3:]:
            X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
            probs = surrogate.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            logits_b = np.log(np.clip(probs, 1e-12, 1.0))
            w = scorer.score_samples(X_b, logits_b, y_obs)
            surrogate.backward(X_b, y_obs, sample_weights=w)
            opt.step()
            opt.zero_grad()

    elif model_name == "ULC-v1 Baseline":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        pipeline = RobustLearningPipeline(n_classes=2)
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)
        controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            directive, _ = controller.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if directive.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

    elif model_name == "ULC-v2 Baseline":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        pipeline = RobustLearningPipeline(n_classes=2)
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)
        controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            directive, _ = controller.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if directive.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.purge_replay(policy="partial")
                opt.reset_momenta()
            elif directive.state == ControllerState.NOISE_BURST:
                pass
            else:
                clf.partial_fit(X_b, y_obs)

    elif model_name == "ULC-v3 Audited":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        pipeline = RobustLearningPipeline(n_classes=2)
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)
        controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            probs = clf.predict_proba(X_b)
            preds = np.argmax(probs, axis=1)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            directive, _ = controller.step(X_b, y_obs, logits=np.log(np.clip(probs, 1e-12, 1.0)), delta_drift=delta)
            if directive.state == ControllerState.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1
                clf.purge_replay(policy="selective", keep_minority=True)
                opt.reset_momenta()
            elif directive.state != ControllerState.NOISE_BURST:
                clf.partial_fit(X_b, y_obs)

    elif model_name == "ULC-v4 Master System":
        clf = AdaptiveClassifier(n_features=N_FEATURES, n_classes=2, grace_period=10, replay_capacity=100, enable_drift_detection=True, random_state=seed)
        clf.fit(init_X, init_y)
        surrogate = LinearSurrogate(N_FEATURES, 2, seed=seed)
        opt = LowMemoryAdamW([surrogate], lr=0.01)
        budget = DynamicResourceBudgetManager(max_memory_mb=4096.0)
        prior_tracker = OnlineClassPriorTracker(n_classes=2)
        thresh_mgr = AdaptiveThresholdManager(n_classes=2)
        concept_mem = ConceptMemory(max_concepts=5)
        rel_engine = MultiSignalReliabilityEngine()

        pipeline = RobustLearningPipeline(n_classes=2)
        controller = UnifiedLearningControllerV4(
            classifier=clf,
            optimizer=opt,
            pipeline=pipeline,
            budget_manager=budget,
            prior_tracker=prior_tracker,
            threshold_manager=thresh_mgr,
            concept_memory=concept_mem,
        )

        for batch in stream[3:]:
            X_b, y_obs, y_clean, delta = batch["X"], batch["y_observed"], batch["y_clean"], batch["delta"]
            # 1. Prequential prediction before observing labels
            probs = clf.predict_proba(X_b)
            thresh = thresh_mgr.primary_threshold
            preds = (probs[:, 1] >= thresh).astype(int)
            all_y_clean.extend(y_clean)
            all_y_pred.extend(preds)

            # 2. Store concepts before transition
            if batch["batch_idx"] == 15:
                concept_mem.store_concept(concept_id="concept_0", model_state=clf.state_dict(), X=X_b, y=y_obs)
            elif batch["batch_idx"] == 35:
                concept_mem.store_concept(concept_id="concept_1", model_state=clf.state_dict(), X=X_b, y=y_obs)

            # 3. Coordinated controller step
            logits = np.log(np.clip(probs, 1e-12, 1.0))
            directive, _ = controller.step(X_b, y_obs, logits=logits, delta_drift=delta)

            # 4. Update adaptive threshold manager from tracking priors
            thresh_mgr.update_from_priors(prior_tracker.priors)

            if directive.state == AutomatonStateV4.CONFIRMED_DRIFT:
                total_drift_alarms += 1
                if batch["is_noise"] or not batch["is_true_drift"]:
                    false_drift_resets += 1

            if directive.restore_concept_id is not None:
                total_drift_alarms += 1

    elapsed = time.perf_counter() - start_time
    total_samples = len(all_y_clean)
    throughput = float(total_samples / max(1e-6, elapsed))
    latency_ms = float((elapsed / max(1, len(stream) - 3)) * 1000.0)

    acc, f1, recall = calculate_prequential_metrics(np.array(all_y_clean), np.array(all_y_pred))

    return {
        "model": model_name,
        "seed": seed,
        "accuracy": acc * 100.0,
        "macro_f1": f1,
        "minority_recall": recall * 100.0,
        "drift_alarms": total_drift_alarms,
        "false_drift_resets": false_drift_resets,
        "throughput": throughput,
        "latency_ms": latency_ms,
    }


def main() -> None:
    print("================================================================================")
    print("ADAPTIVEML STAGE 7: MASTER BENCHMARK BATTERY (13 MODELS x 5 SEEDS)")
    print("================================================================================\n")

    models = [
        "Static Baseline",
        "Pure Hoeffding Tree",
        "Standalone ADWIN (ALA 1.0)",
        "Standalone RLA (SCE + Margin)",
        "Standalone RAO (LowMemoryAdamW)",
        "Standalone Minority (Prior + Threshold)",
        "ALA + RLA",
        "ALA + RAO",
        "RLA + RAO",
        "ULC-v1 Baseline",
        "ULC-v2 Baseline",
        "ULC-v3 Audited",
        "ULC-v4 Master System",
    ]

    all_raw_results: List[Dict[str, Any]] = []

    for seed in SEEDS:
        print(f"\n--- Executing Stream with Seed {seed} ---")
        stream = generate_stream(seed=seed)
        for model_name in models:
            res = run_single_model(model_name, stream, seed)
            all_raw_results.append(res)
            print(f"  [{model_name:36s}] Acc: {res['accuracy']:5.2f}% | F1: {res['macro_f1']:5.3f} | MinRec: {res['minority_recall']:5.2f}% | FDR: {res['false_drift_resets']}")

    # Aggregate by model
    summary_by_model: Dict[str, Dict[str, Any]] = {}
    for m in models:
        m_runs = [r for r in all_raw_results if r["model"] == m]
        accs = [r["accuracy"] for r in m_runs]
        f1s = [r["macro_f1"] for r in m_runs]
        recs = [r["minority_recall"] for r in m_runs]
        alarms = [r["drift_alarms"] for r in m_runs]
        fdrs = [r["false_drift_resets"] for r in m_runs]
        tps = [r["throughput"] for r in m_runs]
        lats = [r["latency_ms"] for r in m_runs]

        summary_by_model[m] = {
            "accuracy_mean": float(np.mean(accs)),
            "accuracy_std": float(np.std(accs)),
            "macro_f1_mean": float(np.mean(f1s)),
            "macro_f1_std": float(np.std(f1s)),
            "minority_recall_mean": float(np.mean(recs)),
            "minority_recall_std": float(np.std(recs)),
            "drift_alarms_mean": float(np.mean(alarms)),
            "false_drift_resets_mean": float(np.mean(fdrs)),
            "throughput_mean": float(np.mean(tps)),
            "latency_ms_mean": float(np.mean(lats)),
        }

    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "stage7_ulc_v4_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"raw_runs": all_raw_results, "summary": summary_by_model}, f, indent=2)

    csv_path = out_dir / "stage7_ulc_v4_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Model", "Accuracy (%)", "Accuracy Std",
            "Macro F1", "Macro F1 Std",
            "Minority Recall (%)", "Minority Recall Std",
            "Drift Alarms", "False Drift Resets",
            "Throughput (samples/s)", "Latency (ms/step)",
        ])
        for m in models:
            s = summary_by_model[m]
            writer.writerow([
                m,
                f"{s['accuracy_mean']:.2f}", f"{s['accuracy_std']:.2f}",
                f"{s['macro_f1_mean']:.3f}", f"{s['macro_f1_std']:.3f}",
                f"{s['minority_recall_mean']:.2f}", f"{s['minority_recall_std']:.2f}",
                f"{s['drift_alarms_mean']:.1f}", f"{s['false_drift_resets_mean']:.1f}",
                f"{s['throughput_mean']:.1f}", f"{s['latency_ms_mean']:.2f}",
            ])

    print("\n================================================================================")
    print("MASTER BENCHMARK BATTERY SUMMARY")
    print("================================================================================")
    print(f"{'Model':36s} | {'Acc (%)':12s} | {'Macro F1':11s} | {'Min Recall':12s} | {'FDR':5s}")
    print("-" * 88)
    for m in models:
        s = summary_by_model[m]
        print(f"{m:36s} | {s['accuracy_mean']:5.2f} ± {s['accuracy_std']:4.2f} | {s['macro_f1_mean']:5.3f} ± {s['macro_f1_std']:4.3f} | {s['minority_recall_mean']:5.2f} ± {s['minority_recall_std']:4.2f} | {s['false_drift_resets_mean']:4.1f}")
    print("================================================================================\n")
    print(f"Results successfully saved to:\n  - {json_path}\n  - {csv_path}")


if __name__ == "__main__":
    main()
