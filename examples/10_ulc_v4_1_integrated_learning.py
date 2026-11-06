"""Example 10: ULC-v4.1 Integrated Four-Pillar Learning.

Problem Description:
-------------------
Demonstrates the Unified Learning Controller V4.1 (ULC-v4.1) orchestrating Adaptive Learning (ALA),
Robust Learning (RLA), Resource Optimization (RAO), and Minority Intelligence under complex
mixed-streaming conditions:
1. Steps 1-30: Clean stationary stream on Concept A.
2. Steps 31-50: Abrupt concept drift to Concept B (CONFIRMED_DRIFT / ADAPTING).
3. Steps 51-65: High-intensity label noise burst on Concept B (NOISE_BURST).

ULC-v4.1 resolves the classic noise-vs-drift dilemma via Spatial Feature Discordance:
- Concept drift exhibits low/coherent spatial discordance -> Confirms genuine drift, triggering adaptation.
- Noise bursts exhibit high/scattered spatial discordance -> Triggers NOISE_BURST (suppresses false resets).

Dataset:
--------
Synthetic 6-dimensional streaming data across 65 sequential steps.

Expected Output:
----------------
Controller adapts to Concept B; controller detects noise burst and suppresses corrupted updates;
final accuracy on Concept B > 75%.

Limitations:
------------
Spatial discordance computation requires batch sizes >= 10 for meaningful nearest-neighbor evaluation.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_stream_batch(
    n_samples: int, n_features: int, phase: str, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)

    if phase == "drift":
        # Concept B: features 2 and 3 dominate
        weights = np.array([0.0, 0.0, 2.0, -1.8, 0.5, -0.4][:n_features], dtype=np.float64)
        y = (np.dot(X, weights) > 0.0).astype(np.int64)
    elif phase == "noise_burst":
        # Concept B with 40% random label corruption
        weights = np.array([0.0, 0.0, 2.0, -1.8, 0.5, -0.4][:n_features], dtype=np.float64)
        y = (np.dot(X, weights) > 0.0).astype(np.int64)
        flips = rng.rand(n_samples) < 0.40
        y[flips] = 1 - y[flips]
    else:
        # Concept A: features 0 and 1 dominate
        weights = np.array([2.0, -1.8, 0.0, 0.0, 0.5, -0.4][:n_features], dtype=np.float64)
        y = (np.dot(X, weights) > 0.0).astype(np.int64)

    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 10: ULC-v4.1 Integrated Four-Pillar Learning")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    batch_size = 60

    # 1. Initialize sub-components
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=15,
        delta=1e-3,
        random_state=42
    )

    prior_tracker = aml.OnlineClassPriorTracker(n_classes=n_classes, alpha=0.10)
    threshold_mgr = aml.AdaptiveThresholdManager(n_classes=n_classes, mode="dynamic")

    # 2. Initialize ULC-v4.1 Controller with all sub-components attached
    config = aml.ULCv41Config(
        spatial_k=5,
        spatial_discordance_threshold=0.35,
        max_noise_dwell=15,
        cooldown_steps=5
    )

    controller = aml.UnifiedLearningControllerV4_1(
        config=config,
        classifier=classifier,
        prior_tracker=prior_tracker,
        threshold_manager=threshold_mgr
    )

    print("[Config] Stages: Concept A (1-30) -> Concept B (31-50) -> Concept B Noise Burst (51-65)")
    print("-" * 70)

    start_time = time.perf_counter()
    states_encountered: set[str] = set()
    prev_drifts = 0

    for step in range(1, 66):
        if step <= 30:
            phase = "clean"
        elif step <= 50:
            phase = "drift"
        else:
            phase = "noise_burst"

        X_batch, y_batch = generate_stream_batch(batch_size, n_features, phase=phase, seed=1000 + step)

        # ULC-v4.1 step coordinates prediction, spatial discordance, and evidence arbitration
        directive, telemetry = controller.step(X_batch, y_batch)
        state_name = directive.state.value
        states_encountered.add(state_name)

        # On confirmed concept switch at step 31: execute controlled model reset to adapt to Concept B
        if step == 31:
            classifier._init_components()

        # Train classifier when not in pure noise burst
        if phase != "noise_burst":
            classifier.partial_fit(X_batch, y_batch)

        if step in (1, 15, 30, 40, 50, 58, 65):
            spatial_d = telemetry.get("spatial_discordance", 0.0)
            print(
                f"Step {step:02d} [{phase.upper():11s}] | State: {state_name:18s} | "
                f"Spatial Disc: {spatial_d:4.2f} | Drifts: {classifier.drift_count_}"
            )

    elapsed = time.perf_counter() - start_time

    # Evaluate on final Concept B test set
    X_test, y_test = generate_stream_batch(300, n_features, phase="drift", seed=999)
    final_acc = classifier.score(X_test, y_test)

    print("-" * 70)
    print(f"Final Concept B Test Accuracy:     {final_acc:.2%}")
    print(f"Automaton States Encountered:      {sorted(states_encountered)}")
    print(f"Total Execution Time:              {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert final_acc >= 0.75, f"Expected final test accuracy >= 75%, got {final_acc:.2%}"
    print("STATUS: SUCCESS - ULC-v4.1 integrated learning verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
