"""
ULC Pillar Benchmark: Dual-Evidence Cross-Pillar In-Loop Arbitration.

Compares ULC coordination against uncoordinated independent drift reset
and static learning under alternating regimes of drift and label noise bursts.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

# Ensure benchmarks/phase-12 is on sys.path
_BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
if str(_BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(_BENCHMARK_ROOT))

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.core.config import ULCConfig
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.ulc.controller import AdaptiveLearningController
from adaptive_ml.ulc.directives import ControllerState


def run_ulc_benchmark(seeds: List[int] = [42, 101, 2024, 7, 99]) -> Dict[str, Any]:
    """Execute multi-seed ULC arbitration benchmark."""
    results: Dict[str, Any] = {
        "metadata": {
            "pillar": "ULC",
            "seeds": seeds,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "experiments": {},
    }

    ulc_accs, uncoord_accs, static_accs = [], [], []
    ulc_retained_pcts, uncoord_retained_pcts = [], []
    ulc_false_resets, uncoord_false_resets = [], []

    for seed in seeds:
        rng = np.random.default_rng(seed)
        n_features = 4
        n_classes = 2

        # 1. ULC Coordinated Pipeline
        clf_ulc = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=30, random_state=seed)
        rla_ulc = RobustLearningPipeline(n_classes=n_classes)
        controller_ulc = AdaptiveLearningController(
            classifier=clf_ulc,
            pipeline=rla_ulc,
            config=ULCConfig(tau_R=0.48, recovery_steps=4),
        )

        # 2. Uncoordinated Baseline: ALA resets freely without noise suppression
        clf_uncoord = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=30, random_state=seed)

        # 3. Static Baseline
        clf_static = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=30, enable_drift_detection=False, random_state=seed)

        # Generate 4-regime stream (40 batches of 30 samples = 1200 samples)
        # Batches 1-10: Clean Regime (Class 0 at -2.0, Class 1 at +2.0)
        # Batches 11-20: Noise Burst (Class 0 flipped to 1 in 85% of samples; delta_drift = 1.3)
        # Batches 21-30: Clean Return
        # Batches 31-40: True Drift (Class 0 at +3.0, Class 1 at -3.0; delta_drift = 1.4 at batch 31)
        correct_ulc = 0
        correct_uncoord = 0
        correct_static = 0
        total_eval = 0

        noise_samples_total = 0
        noise_samples_ulc_retained = 0
        false_resets_ulc = 0
        false_resets_uncoord = 0

        for b in range(1, 41):
            if b <= 10 or (21 <= b <= 30):
                # Clean
                X0 = rng.normal(loc=[-2.0] * n_features, scale=0.5, size=(15, n_features))
                X1 = rng.normal(loc=[2.0] * n_features, scale=0.5, size=(15, n_features))
                X = np.vstack([X0, X1])
                y = np.array([0] * 15 + [1] * 15)
                logits = np.where(y[:, None] == 0, [3.0, -3.0], [-3.0, 3.0])
                delta = 0.05
            elif 11 <= b <= 20:
                # Noise burst
                X0 = rng.normal(loc=[-2.0] * n_features, scale=0.5, size=(25, n_features))
                X1 = rng.normal(loc=[2.0] * n_features, scale=0.5, size=(5, n_features))
                X = np.vstack([X0, X1])
                y = np.array([1] * 25 + [1] * 5)  # 25 samples flipped
                logits = np.vstack([np.tile([3.0, -3.0], (25, 1)), np.tile([-3.0, 3.0], (5, 1))])
                delta = 1.3
                noise_samples_total += 30
            else:
                # True concept drift
                X0 = rng.normal(loc=[3.0] * n_features, scale=0.5, size=(15, n_features))
                X1 = rng.normal(loc=[-3.0] * n_features, scale=0.5, size=(15, n_features))
                X = np.vstack([X0, X1])
                y = np.array([0] * 15 + [1] * 15)
                logits = np.where(y[:, None] == 0, [3.0, -3.0], [-3.0, 3.0])
                delta = 1.4 if b == 31 else 0.1

            # Prequential evaluation
            if clf_ulc.samples_seen_ > 0:
                p_ulc = clf_ulc.predict(X)
                p_uncoord = clf_uncoord.predict(X)
                p_static = clf_static.predict(X)

                correct_ulc += int(np.sum(p_ulc == y))
                correct_uncoord += int(np.sum(p_uncoord == y))
                correct_static += int(np.sum(p_static == y))
                total_eval += len(X)

            # Step ULC
            directive, info = controller_ulc.step(X, y, logits=logits, delta_drift=delta)
            if 11 <= b <= 20:
                noise_samples_ulc_retained += info["n_retained_samples"]
                if directive.state == ControllerState.CONFIRMED_DRIFT:
                    false_resets_ulc += 1

            # Step Uncoordinated (blindly resets when delta >= 1.0)
            if delta >= 1.0:
                if 11 <= b <= 20:
                    false_resets_uncoord += 1
                clf_uncoord = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=30, random_state=seed)
            clf_uncoord.partial_fit(X, y)

            # Step Static
            clf_static.partial_fit(X, y)

        ulc_accs.append(correct_ulc / max(1, total_eval))
        uncoord_accs.append(correct_uncoord / max(1, total_eval))
        static_accs.append(correct_static / max(1, total_eval))
        ulc_retained_pcts.append((noise_samples_ulc_retained / max(1, noise_samples_total)) * 100.0)
        ulc_false_resets.append(false_resets_ulc)
        uncoord_false_resets.append(false_resets_uncoord)

    results["experiments"]["streaming_arbitration"] = {
        "ulc_accuracy_mean": float(np.mean(ulc_accs)),
        "ulc_accuracy_std": float(np.std(ulc_accs)),
        "uncoordinated_accuracy_mean": float(np.mean(uncoord_accs)),
        "uncoordinated_accuracy_std": float(np.std(uncoord_accs)),
        "static_accuracy_mean": float(np.mean(static_accs)),
        "ulc_noise_sample_retention_pct": float(np.mean(ulc_retained_pcts)),
        "ulc_false_resets_mean": float(np.mean(ulc_false_resets)),
        "uncoordinated_false_resets_mean": float(np.mean(uncoord_false_resets)),
    }

    return results


if __name__ == "__main__":
    res = run_ulc_benchmark()
    print("ULC Benchmark Completed:")
    print(res["experiments"])

