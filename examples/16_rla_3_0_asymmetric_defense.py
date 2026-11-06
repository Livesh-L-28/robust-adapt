"""Example 16: RLA 3.0 Asymmetric Noise Defense & Disguised Minority Protection.

Demonstrates:
- AsymmetricTransitionDetector identifying directional flip bias
- ClassConditionalReliabilityEstimator maintaining per-class margin statistics
- RLA30RobustLearner operating in high_security_evasion mode to protect genuine minority
"""

import numpy as np
from robust_adapt.rla import RLA30RobustLearner


def main() -> None:
    print("=== Example 16: RLA 3.0 Asymmetric Noise Defense ===")
    rng = np.random.RandomState(42)

    learner = RLA30RobustLearner(
        n_features=4,
        n_classes=2,
        security_mode="high_security_evasion",
        minority_class=1,
    )

    print("\n--- Streaming Corrupted Instances with Asymmetric Noise ---")
    for step in range(25):
        X = rng.randn(40, 4)
        # Minority class is rare (10%)
        y_true = (rng.rand(40) < 0.10).astype(int)
        y_noisy = y_true.copy()

        # Asymmetric noise: 30% of class 1 is flipped to class 0 (evasion attack)
        for i in range(40):
            if y_true[i] == 1 and rng.rand() < 0.30:
                y_noisy[i] = 0

        stats = learner.fit_batch(X, y_noisy)
        if step % 5 == 0:
            print(
                f"Step {step:2d} | Retained: {stats['retained']:2d} | "
                f"Abstained: {stats['abstained']:2d} | "
                f"AsymRatio: {stats['asymmetry_ratio']:.2f} | "
                f"Rel: {stats['mean_reliability']:.2f}"
            )

    print(f"\nFinal Totals: Retained={learner.retained_samples}, Abstained={learner.abstained_samples}")
    print("RLA 3.0 execution completed successfully.")


if __name__ == "__main__":
    main()
