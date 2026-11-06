"""Example 07: Minority-Aware Learning with Adaptive Thresholds.

Problem Description:
-------------------
Demonstrates how to preserve detection recall on rare minority classes (5% prevalence)
under continuous streaming distribution shifts. In severe imbalance, standard 0.50 argmax
decision thresholds suppress minority predictions. ROBUST-ADAPT integrates OnlineClassPriorTracker
with ClassBalancedWeights, AdaptiveThresholdManager, and Reservoir Replay to dynamically tune
decision thresholds and protect minority instances.

Dataset:
--------
Synthetic 6-dimensional streaming data where Class 1 is a rare minority (5% prevalence).

Expected Output:
----------------
Prior tracker detects 5% minority prior; adaptive threshold manager lowers decision threshold
to preserve minority recall > 50% without massive false positive explosion.

Limitations:
------------
Requires sufficient minority instances to accumulate in replay buffer before tree split.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_imbalanced_stream_batch(
    n_samples: int, n_features: int, minority_ratio: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    n_min = int(n_samples * minority_ratio)
    n_maj = n_samples - n_min

    # Majority class (0): mean at -0.5
    X_maj = rng.randn(n_maj, n_features).astype(np.float64) - 0.5
    y_maj = np.zeros(n_maj, dtype=np.int64)

    # Minority class (1): mean at +1.2
    X_min = rng.randn(n_min, n_features).astype(np.float64) + 1.2
    y_min = np.ones(n_min, dtype=np.int64)

    X = np.vstack([X_maj, X_min])
    y = np.concatenate([y_maj, y_min])

    indices = rng.permutation(len(y))
    return X[indices], y[indices]


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 07: Minority-Aware Learning & Adaptive Thresholds")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    n_batches = 8
    batch_size = 200
    minority_rate = 0.05  # 5% minority

    print(f"[Config] Extreme Imbalance: 95% Majority / 5% Minority | Batches: {n_batches} x {batch_size}")
    print("-" * 70)

    # 1. Initialize AdaptiveClassifier with Replay
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=15,
        delta=1e-3,
        replay_capacity=1000,
        replay_ratio=0.3,
        random_state=42
    )

    # 2. Initialize OnlineClassPriorTracker with responsive alpha
    prior_tracker = aml.OnlineClassPriorTracker(
        n_classes=n_classes,
        alpha=0.30,
        window_size=400,
        imbalance_threshold=0.15
    )

    # 3. Initialize AdaptiveThresholdManager
    threshold_mgr = aml.AdaptiveThresholdManager(
        n_classes=n_classes,
        mode="dynamic",
        base_threshold=0.50,
        gamma=0.6,
        tau_min=0.10,
        tau_max=0.90
    )

    cb_weighter = aml.ClassBalancedWeights(beta=0.99)
    running_counts = np.array([10.0, 10.0], dtype=np.float64)

    start_time = time.perf_counter()

    for batch_idx in range(1, n_batches + 1):
        X_batch, y_batch = generate_imbalanced_stream_batch(
            batch_size, n_features, minority_ratio=minority_rate, seed=700 + batch_idx
        )

        # Update prior tracker with newly arrived labels
        prior_tracker.update(y_batch)
        priors = prior_tracker.priors
        imbalance_ratio = prior_tracker.imbalance_ratio

        # Update adaptive decision thresholds based on current priors
        threshold_mgr.update_from_priors(priors)
        current_thresholds = threshold_mgr.thresholds

        # Compute sample weights from running counts
        running_counts[0] += np.sum(y_batch == 0)
        running_counts[1] += np.sum(y_batch == 1)
        class_weights = cb_weighter.compute_weights(running_counts)
        sample_weights = class_weights[y_batch]

        # Train classifier
        classifier.partial_fit(X_batch, y_batch, sample_weight=sample_weights)

        print(
            f"Batch {batch_idx:02d} | Priors: [{priors[0]:.2f}, {priors[1]:.2f}] | "
            f"Imbalance: {imbalance_ratio:4.1f}:1 | "
            f"Minority Threshold: {current_thresholds[1]:.3f}"
        )

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out test set
    X_test, y_test = generate_imbalanced_stream_batch(400, n_features, minority_ratio=minority_rate, seed=999)
    test_probs = classifier.predict_proba(X_test)

    # Predict using standard static threshold (0.50) vs dynamic adaptive threshold
    preds_standard = (test_probs[:, 1] >= 0.50).astype(np.int64)
    preds_adaptive = threshold_mgr.predict(test_probs)

    min_mask = (y_test == 1)
    recall_standard = float(np.mean(preds_standard[min_mask] == 1))
    recall_adaptive = float(np.mean(preds_adaptive[min_mask] == 1))

    print("-" * 70)
    print(f"Standard Threshold (0.50) Minority Recall: {recall_standard:.2%}")
    print(f"Adaptive Threshold ({current_thresholds[1]:.3f}) Minority Recall: {recall_adaptive:.2%}")
    print(f"Total Execution Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert recall_adaptive >= 0.50, f"Expected adaptive minority recall >= 50%, got {recall_adaptive:.2%}"
    print("STATUS: SUCCESS - Minority intelligence and adaptive thresholding verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
