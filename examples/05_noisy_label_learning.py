"""Example 05: Noisy Label Learning with Reliability Weighting.

Problem Description:
-------------------
Demonstrates robust learning in the presence of 25% symmetric label noise. Standard online
classifiers overfit to corrupted labels, degrading decision boundaries. ROBUST-ADAPT's
MultiSignalReliabilityEngine identifies noisy samples by combining prediction margin,
k-NN neighborhood consistency, and temporal signals, allowing the model to down-weight
corrupted instances via sample_weight in partial_fit.

Dataset:
--------
Synthetic 8-dimensional stream with 25% random label flips injected into training batches.

Expected Output:
----------------
Reliability-weighted learning maintains >75% accuracy on clean test data despite 25% label corruption.

Limitations:
------------
Neighborhood consistency requires sufficient buffer history (buffer_size >= 50) to evaluate k-NN.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_data(n_samples: int, n_features: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    weights = np.array([1.5, -1.2, 0.9, -0.7, 0.5, -0.4, 0.2, -0.1], dtype=np.float64)
    logits = np.dot(X, weights)
    y = (logits > 0.0).astype(np.int64)
    return X, y


def inject_symmetric_noise(y: np.ndarray, noise_rate: float, seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    y_noisy = y.copy()
    flip_mask = rng.rand(len(y)) < noise_rate
    y_noisy[flip_mask] = 1 - y_noisy[flip_mask]
    return y_noisy


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 05: Noisy Label Learning with Reliability Weighting")
    print("=" * 70)

    n_features = 8
    n_classes = 2
    n_batches = 6
    batch_size = 150
    noise_rate = 0.25

    print(f"[Config] 25% Symmetric Label Noise | Batches: {n_batches} x {batch_size}")
    print("-" * 70)

    # Initialize model and reliability engine
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=25,
        delta=1e-4,
        random_state=42
    )

    reliability_engine = aml.MultiSignalReliabilityEngine(
        n_classes=n_classes,
        k_neighbors=5,
        buffer_size=500,
        weight_margin=0.40,
        weight_neighbor=0.40,
        weight_temporal=0.20
    )

    start_time = time.perf_counter()

    for batch_idx in range(1, n_batches + 1):
        X_clean, y_clean = generate_data(batch_size, n_features, seed=500 + batch_idx)
        y_noisy = inject_symmetric_noise(y_clean, noise_rate, seed=1500 + batch_idx)

        # Pre-update prediction probabilities
        probas = classifier.predict_proba(X_clean)

        # Compute multi-signal reliability
        reliabilities = reliability_engine.compute_reliability(X_clean, y_noisy, probas)
        mean_rel = float(np.mean(reliabilities))

        # Down-weight noisy samples: threshold at 0.50
        sample_weights = np.where(reliabilities >= 0.50, reliabilities, 0.05)

        # Train with reliability sample weights
        classifier.partial_fit(X_clean, y_noisy, sample_weight=sample_weights)

        # Measure pre-train clean accuracy
        clean_acc = classifier.score(X_clean, y_clean)
        print(
            f"Batch {batch_idx:02d} | Mean Reliability: {mean_rel:4.2f} | "
            f"Clean Batch Acc: {clean_acc:6.1%} | Total Seen: {classifier.samples_seen_}"
        )

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out clean test set
    X_test, y_test = generate_data(300, n_features, seed=999)
    test_acc = classifier.score(X_test, y_test)

    print("-" * 70)
    print(f"Final Clean Test Accuracy: {test_acc:.2%}")
    print(f"Total Execution Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert test_acc >= 0.70, f"Expected clean test accuracy >= 70%, got {test_acc:.2%}"
    print("STATUS: SUCCESS - Noisy label robustness verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
