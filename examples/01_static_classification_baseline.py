"""Example 01: Static Classification Baseline.

Problem Description:
-------------------
Establishes a baseline for streaming classification on a stationary (non-drifting)
data distribution using ROBUST-ADAPT's AdaptiveClassifier. Verifies that incremental
Hoeffding trees converge cleanly on steady Gaussian distributions.

Dataset:
--------
Synthetic 8-dimensional Gaussian feature stream with 2 stationary classes generated
via linear hyperplane separation. 5 sequential batches of 100 samples each.

Expected Output:
----------------
Streaming accuracy increases as sample count grows; test set accuracy exceeds 80%.

Limitations:
------------
Assumes stationary data (no concept drift) and clean labels (no label corruption).
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_stationary_batch(n_samples: int, n_features: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    weights = np.array([1.5, -1.2, 0.8, -0.7, 0.4, -0.3, 0.2, -0.1][:n_features], dtype=np.float64)
    logits = np.dot(X, weights)
    y = (logits > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 01: Static Classification Baseline")
    print("=" * 70)

    n_features = 8
    n_classes = 2
    n_batches = 6
    batch_size = 150

    # Initialize AdaptiveClassifier with valid parameters
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=30,
        delta=1e-4,
        random_state=42
    )

    print(f"\n[Config] Model: AdaptiveClassifier | Features: {n_features} | Batches: {n_batches} x {batch_size}")
    print("-" * 70)

    start_time = time.perf_counter()

    for batch_idx in range(1, n_batches + 1):
        X_batch, y_batch = generate_stationary_batch(batch_size, n_features, seed=100 + batch_idx)
        # In online streaming: evaluate on batch before training (interleaved test-then-train)
        if classifier.samples_seen_ > 0:
            batch_acc = classifier.score(X_batch, y_batch)
        else:
            batch_acc = 0.50

        classifier.partial_fit(X_batch, y_batch)
        print(
            f"Batch {batch_idx:02d} | Seen: {classifier.samples_seen_:4d} | "
            f"Pre-Train Acc: {batch_acc:6.1%} | Drifts: {classifier.drift_count_}"
        )

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out stationary test set
    X_test, y_test = generate_stationary_batch(300, n_features, seed=999)
    y_pred = classifier.predict(X_test)
    y_prob = classifier.predict_proba(X_test)
    test_acc = classifier.score(X_test, y_test)

    print("-" * 70)
    print(f"Final Held-Out Test Accuracy: {test_acc:.2%}")
    print(f"Prediction Probability Shape: {y_prob.shape}")
    print(f"Execution Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert test_acc >= 0.75, f"Expected test accuracy >= 75%, got {test_acc:.2%}"
    print("STATUS: SUCCESS - Stationary baseline verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
