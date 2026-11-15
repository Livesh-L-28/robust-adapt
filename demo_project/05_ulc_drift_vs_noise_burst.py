"""
Demo 05: Uncertainty-Loss Coupling (ULC Pillar)
==============================================
Demonstrates ROBUST-ADAPT's flagship multi-signal arbitrator:
disentangling transient adversarial noise bursts from genuine concept drifts.

Key Components:
- robust_adapt.ulc.UnifiedLearningControllerV5: Multi-tier intervention controller
- robust_adapt.ulc.InterventionTier: Graded response tiers (0: NOOP, 1: DAMP, 2: RESTORE, 3: SOFT RESET, 4: HARD RESET)
- robust_adapt.ulc.compute_spatial_discordance: Spatial feature-neighborhood validation
"""

import numpy as np
import robust_adapt
from robust_adapt.ulc import (
    UnifiedLearningControllerV5,
    ULCv5Config,
    InterventionTier,
)


def generate_stream_with_noise_and_drift(n_steps: int = 15, batch_size: int = 30, seed: int = 42):
    """
    Generates batches across 3 distinct operational phases:
    - Steps 1 to 5: Clean stationary distribution
    - Steps 6 to 9: Transient Noise Burst (Random corrupted labels, features unchanged)
    - Steps 10 to 15: Genuine Concept Drift (Coherent spatial distribution flip)
    """
    rng = np.random.default_rng(seed)
    batches = []

    for step in range(1, n_steps + 1):
        if step <= 5:
            # Phase 1: Clean stationary
            X = rng.normal(loc=0.0, scale=1.0, size=(batch_size, 4))
            y = (X[:, 0] >= 0.0).astype(int)
            phase = "Stationary (Clean)"
        elif step <= 9:
            # Phase 2: Noise burst (Discordant random labels, spatial features unchanged)
            X = rng.normal(loc=0.0, scale=1.0, size=(batch_size, 4))
            y = rng.choice([0, 1], size=batch_size) # High entropy noise
            phase = "Noise Burst (Spurious)"
        else:
            # Phase 3: Genuine concept drift (True boundary inversion)
            X = rng.normal(loc=1.5, scale=1.0, size=(batch_size, 4))
            y = (X[:, 0] < 1.0).astype(int)
            phase = "Genuine Drift (Coherent)"

        batches.append((X, y, phase))

    return batches


def main():
    print("=" * 70)
    print("DEMO 05: ULC-v5 CONTROLLER (NOISE BURST VS. GENUINE DRIFT)")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    # 1. Initialize ULC-v5 Controller
    config = ULCv5Config(
        grace_period=20,
        delta=0.005,
        similarity_threshold=0.80,
    )
    controller = UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)

    batches = generate_stream_with_noise_and_drift(n_steps=15, batch_size=30)

    print("\nStreaming through Stationary, Noise Burst, and Genuine Drift phases...")
    print(f"{'Step':<5} | {'Phase Type':<25} | {'Error':<8} | {'Intervention Tier':<22} | {'Action Summary'}")
    print("-" * 80)

    for step_idx, (X_b, y_b, phase_name) in enumerate(batches, 1):
        directive, telemetry = controller.step(X_b, y_b)

        tier_name = directive.tier.name if hasattr(directive.tier, "name") else str(directive.tier)
        err = telemetry.get("error_rate", 0.0) * 100

        # Formulate actionable description
        if directive.tier == InterventionTier.TIER_0_NOOP:
            desc = "Stable operation; standard incremental update"
        elif directive.tier == InterventionTier.TIER_1_PARAM_DAMPING:
            desc = "Noise detected; dampening learning rate, NO state wipe"
        elif directive.tier == InterventionTier.TIER_2_CONCEPT_RESTORE:
            desc = "Recurring drift matched; restoring prior concept"
        elif directive.tier == InterventionTier.TIER_3_SOFT_REPLAY_RESET:
            desc = "Genuine novel drift verified; soft replay-guided reset"
        else:
            desc = "Catastrophic shift; full hard reset"

        print(f"{step_idx:<5} | {phase_name:<25} | {err:>5.1f}% | {tier_name:<22} | {desc}")

    print("-" * 80)
    print("Conclusion: ULC correctly filters transient noise without catastrophic forgetfulness,")
    print("            while executing structured adaptation upon genuine distribution shifts.")


if __name__ == "__main__":
    main()
