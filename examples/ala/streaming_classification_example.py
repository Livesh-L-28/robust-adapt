"""Executable example for Phase 8: Adaptive Learning Algorithms (ALA).

Demonstrates:
1. Streaming classification with AdaptiveClassifier.
2. Concept drift adaptation via Reliability-Weighted ADWIN.
3. Class-balanced reservoir replay.
"""

import numpy as np
from robust_adapt.ala import AdaptiveClassifier


def run_ala_demo() -> None:
    print("=" * 60)
    print("ROBUST-ADAPT — Phase 8 ALA Streaming Demo")
    print("=" * 60)

    rng = np.random.default_rng(42)
    n_features = 4
    n_classes = 2

    clf = AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=50,
        enable_drift_detection=True,
        replay_capacity=200,
        replay_ratio=0.2,
        random_state=42,
    )

    # Concept 1: First 500 samples (mean [-1, -1, 0, 0] vs [1, 1, 0, 0])
    print("\nPhase 1: Ingesting Concept 1 (500 samples)...")
    for step in range(10):
        X0 = rng.normal(loc=[-1.0, -1.0, 0.0, 0.0], scale=0.6, size=(25, n_features))
        y0 = np.zeros(25, dtype=np.int64)
        X1 = rng.normal(loc=[1.0, 1.0, 0.0, 0.0], scale=0.6, size=(25, n_features))
        y1 = np.ones(25, dtype=np.int64)

        X_batch = np.vstack([X0, X1])
        y_batch = np.concatenate([y0, y1])
        perm = rng.permutation(50)

        clf.partial_fit(X_batch[perm], y_batch[perm])

    print(f"Samples processed: {clf.samples_seen_}, Drift events: {clf.drift_count_}")
    acc1 = clf.score(X_batch, y_batch)
    print(f"Concept 1 Final Batch Accuracy: {acc1:.2%}")

    # Concept 2: Sudden drift (labels invert!)
    print("\nPhase 2: Ingesting Concept 2 with Inverted Labels (500 samples)...")
    for step in range(10):
        X0 = rng.normal(loc=[-1.0, -1.0, 0.0, 0.0], scale=0.6, size=(25, n_features))
        y0 = np.ones(25, dtype=np.int64)  # INVERTED!
        X1 = rng.normal(loc=[1.0, 1.0, 0.0, 0.0], scale=0.6, size=(25, n_features))
        y1 = np.zeros(25, dtype=np.int64)  # INVERTED!

        X_batch = np.vstack([X0, X1])
        y_batch = np.concatenate([y0, y1])
        perm = rng.permutation(50)

        clf.partial_fit(X_batch[perm], y_batch[perm])

    print(f"Samples processed: {clf.samples_seen_}, Drift events: {clf.drift_count_}")
    acc2 = clf.score(X_batch, y_batch)
    print(f"Concept 2 Post-Adaptation Batch Accuracy: {acc2:.2%}")
    print("\nALA Demonstration successfully completed.")


if __name__ == "__main__":
    run_ala_demo()

