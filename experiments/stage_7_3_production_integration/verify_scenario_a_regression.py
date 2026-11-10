"""
Stage 7.3 Workstream E: Empirical Verification of Scenario A Deadlock Elimination.
Evaluates 20+ consecutive post-drift batches under ULC-v4 vs ULC-v4.1.
Tests both genuine abrupt drift and verified severe label noise bursts.
"""

from __future__ import annotations

import json
import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.ulc.v4_controller import UnifiedLearningControllerV4
from adaptive_ml.ulc.v4_1_controller import UnifiedLearningControllerV4_1, ULCv41Config
from adaptive_ml.ulc.v4_automaton import AutomatonStateV4


def run_scenario_a_comparison() -> dict:
    np.random.seed(42)
    n_features = 4
    batch_size = 50
    n_steps = 25

    # Base dataset: Concept 0
    # Mean: [1, 1, 1, 1]
    X_base = np.random.randn(batch_size, n_features) + 1.0
    y_base = np.zeros(batch_size, dtype=np.int64)

    # Concept 1 (abrupt drift at step 5):
    # Mean: [-2, -2, -2, -2] -> completely new distribution, but internally coherent!
    X_drift = np.random.randn(batch_size, n_features) - 2.0
    y_drift = np.ones(batch_size, dtype=np.int64)

    # Initialize two classifiers & controllers
    clf_v4 = AdaptiveClassifier(n_classes=2, grace_period=10, n_features=n_features)
    clf_v4.fit(X_base, y_base)
    ctrl_v4 = UnifiedLearningControllerV4(classifier=clf_v4)

    clf_v41 = AdaptiveClassifier(n_classes=2, grace_period=10, n_features=n_features)
    clf_v41.fit(X_base, y_base)
    ctrl_v41 = UnifiedLearningControllerV4_1(
        config=ULCv41Config(spatial_k=5, spatial_discordance_threshold=0.25),
        classifier=clf_v41,
    )

    history_v4 = []
    history_v41 = []

    # Stream evaluation:
    # Steps 0-4: Concept 0
    # Steps 5-24: Concept 1 (20 post-drift batches)
    for step in range(n_steps):
        if step < 5:
            X_b = np.random.randn(batch_size, n_features) + 1.0
            y_b = np.zeros(batch_size, dtype=np.int64)
            delta = 0.10
        else:
            X_b = np.random.randn(batch_size, n_features) - 2.0
            y_b = np.ones(batch_size, dtype=np.int64)
            delta = 1.20  # Abrupt drift signal

        # Step ULC-v4
        dir_v4, tel_v4 = ctrl_v4.step(X_b, y_b, delta_drift=delta)
        history_v4.append({
            "step": step,
            "state": dir_v4.state.value,
            "suppress_adwin": dir_v4.suppress_adwin,
            "freeze_buffer": dir_v4.freeze_buffer,
            "retained_samples": tel_v4["n_retained_samples"],
        })

        # Step ULC-v4.1
        dir_v41, tel_v41 = ctrl_v41.step(X_b, y_b, delta_drift=delta)
        history_v41.append({
            "step": step,
            "state": dir_v41.state.value,
            "spatial_discordance": tel_v41["spatial_discordance"],
            "suppress_adwin": dir_v41.suppress_adwin,
            "freeze_buffer": dir_v41.freeze_buffer,
            "retained_samples": tel_v41["n_retained_samples"],
        })

    # Also test genuine noise burst under ULC-v4.1 to verify noise protection is NOT disabled
    # Uniform noise labels randomly scrambled across existing clusters
    X_noise = np.random.randn(batch_size, n_features) + 1.0
    y_noise = np.random.choice([0, 1], size=batch_size)  # Scrambled labels -> high discordance
    dir_noise, tel_noise = ctrl_v41.step(X_noise, y_noise, delta_drift=1.20)

    results = {
        "v4_post_drift_states": [h["state"] for h in history_v4[5:]],
        "v41_post_drift_states": [h["state"] for h in history_v41[5:]],
        "v4_trapped_in_noise_burst": all(h["state"] == AutomatonStateV4.NOISE_BURST.value for h in history_v4[5:]),
        "v41_adapted": any(h["state"] == AutomatonStateV4.CONFIRMED_DRIFT.value for h in history_v41[5:]),
        "v41_retained_samples_post_drift": sum(h["retained_samples"] for h in history_v41[5:]),
        "v4_retained_samples_post_drift": sum(h["retained_samples"] for h in history_v4[5:]),
        "genuine_noise_burst_handled_safely": dir_noise.state == AutomatonStateV4.NOISE_BURST,
        "genuine_noise_burst_discordance": tel_noise["spatial_discordance"],
        "genuine_noise_burst_suppress_adwin": dir_noise.suppress_adwin,
    }

    with open("experiments/stage_7_3_production_integration/scenario_a_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Scenario A Comparison Results:")
    print(f"ULC-v4 Trapped in NOISE_BURST across all 20 post-drift steps: {results['v4_trapped_in_noise_burst']}")
    print(f"ULC-v4.1 Successfully Adapted (CONFIRMED_DRIFT triggered): {results['v41_adapted']}")
    print(f"ULC-v4.1 Genuine Noise Burst Handled Safely: {results['genuine_noise_burst_handled_safely']}")
    print(f"Genuine Noise Discordance: {results['genuine_noise_burst_discordance']:.4f}")
    return results


if __name__ == "__main__":
    run_scenario_a_comparison()
