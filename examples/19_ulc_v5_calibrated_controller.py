"""Example 19: Unified Learning Controller V5 (ULC-v5) Multi-Tier Calibration.

Demonstrates:
- 5-Tier Intervention Hierarchy (NOOP, PARAM_DAMPING, CONCEPT_RESTORE, SOFT_REPLAY_RESET, HARD_RESET)
- Expected Utility Scoring governing structural vs non-structural interventions
- Exponential cooldown backoff mitigating high-frequency thrashing
"""

import numpy as np
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config, InterventionTier


def main() -> None:
    print("=== Example 19: ULC-v5 Multi-Tier Calibrated Controller ===")
    rng = np.random.RandomState(42)

    config = ULCv5Config(
        grace_period=20,
        delta=0.005,
        base_cooldown=3,
        catastrophic_drift_threshold=0.95,
    )
    controller = UnifiedLearningControllerV5(
        n_features=4,
        n_classes=2,
        config=config,
    )

    # 1. Stationary stream (seeking Tier 0 NOOP)
    print("\n--- Phase 1: Stationary Stream (Steps 1-15) ---")
    for step in range(15):
        X = rng.randn(30, 4)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        directive, telemetry = controller.step(X, y)
        if step % 5 == 0:
            print(f"Step {step:2d} | Tier: {directive.tier.value:24s} | Action: {directive.action_name:25s} | Util: {directive.expected_utility:.2f}")

    # 2. Mild noise variance (triggering Tier 1 DAMPING)
    print("\n--- Phase 2: Moderate Drift / Variance Elevation (Steps 16-30) ---")
    for step in range(15, 30):
        X = rng.randn(30, 4)
        # Flip ~15% labels to induce moderate error
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        flip = rng.rand(30) < 0.15
        y[flip] = 1 - y[flip]
        directive, telemetry = controller.step(X, y)
        if step % 5 == 0:
            print(f"Step {step:2d} | Tier: {directive.tier.value:24s} | Action: {directive.action_name:25s} | Err: {telemetry['error_rate']:.2f}")

    print("\n--- Controller Telemetry Summary ---")
    print(f"Total Steps: {controller.total_steps}")
    print(f"Tier Breakdown: {controller.tier_counts}")
    print(f"Structural Resets: {controller.total_resets} (Hard Resets: {controller.total_hard_resets})")
    print("ULC-v5 execution completed successfully.")


if __name__ == "__main__":
    main()
