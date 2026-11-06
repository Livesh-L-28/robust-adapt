"""Example 17: Adaptive Minority Intelligence 2.0 Streaming Classification.

Demonstrates:
- BetaBinomialPriorTracker estimating dynamic streaming class prior
- Sublinear cost-sensitive gradient weighting
- DynamicFPBudgetThresholdManager regulating false positives via PID control
"""

import numpy as np
from robust_adapt.minority import MinorityIntelligence20Learner


def main() -> None:
    print("=== Example 17: Minority Intelligence 2.0 Calibrated Stream ===")
    rng = np.random.RandomState(42)

    learner = MinorityIntelligence20Learner(
        target_fp_budget_per_1k=1.5,
        sublinear_cost_power=0.52,
    )

    print("\n--- Streaming High-Imbalance Data Stream (~4% Minority) ---")
    for step in range(25):
        X = rng.randn(50, 4)
        y = (rng.rand(50) < 0.04).astype(int)

        stats = learner.fit_batch(X, y)
        if step % 5 == 0:
            print(
                f"Batch {step:2d} | Prior: {stats['prior']:.4f} | "
                f"MinWeight: {stats['minority_weight']:.2f} | "
                f"ActiveThresh: {stats['active_threshold']:.3f}"
            )

    X_test = rng.randn(100, 4)
    preds = learner.predict(X_test)
    positives = int(np.sum(preds == 1))
    print(f"\nInference on 100 test samples: Positive alarms = {positives}")
    print("Minority 2.0 execution completed successfully.")


if __name__ == "__main__":
    main()
