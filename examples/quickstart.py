"""
AdaptiveML 5-Minute Quickstart.

Demonstrates streaming classification with concept drift detection
and class-balanced reservoir replay in under 30 lines of code.
"""

from __future__ import annotations

import numpy as np
from adaptive_ml.ala import AdaptiveClassifier


def main() -> None:
    print("=" * 70)
    print("Welcome to AdaptiveML: 5-Minute Quickstart")
    print("=" * 70)

    # 1. Initialize an online streaming classifier
    model = AdaptiveClassifier(
        n_features=4,
        n_classes=2,
        grace_period=20,
        enable_drift_detection=True,
    )

    # 2. Simulate streaming batches
    rng = np.random.default_rng(42)
    print("Streaming 10 mini-batches of data...")

    for step in range(1, 11):
        # Generate batch of 20 samples
        X = rng.normal(loc=1.0 if step <= 5 else -2.0, scale=0.5, size=(20, 4))
        y = (X[:, 0] > 0.0).astype(np.int64)

        # Test before train (prequential evaluation)
        if model.samples_seen_ > 0:
            acc = float(np.mean(model.predict(X) == y))
        else:
            acc = 0.0

        # Incremental model update
        model.partial_fit(X, y)
        print(f"Step {step:02d} | Ingested: {model.samples_seen_:3d} samples | Accuracy: {acc * 100:.1f}%")

    print("-" * 70)
    print(f"Total Drifts Detected: {model.drift_count_}")
    print(f"Final Model Predictions on New Sample:\n  {model.predict(np.zeros((1, 4)))}")
    print("=" * 70)
    print("Quickstart Completed Successfully!")


if __name__ == "__main__":
    main()
