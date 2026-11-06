"""Example 03: Gradual Concept Drift Adaptation.

Problem Description:
-------------------
Demonstrates handling of gradual (smooth) concept drift where the data distribution transitions
continuously over a multi-step window rather than changing instantaneously. Incremental tree
splits continuously update leaf statistics to follow the moving decision boundary.

Dataset:
--------
Synthetic 6-dimensional stream of 10 steps.
- Steps 1-3: Pure Concept A (alpha = 0.0)
- Steps 4-7: Transition window where alpha interpolates linearly from 0.0 to 1.0
- Steps 8-10: Pure Concept B (alpha = 1.0)

Expected Output:
----------------
Continuous learning accommodates the sliding boundary; final accuracy on Concept B exceeds 70%.

Limitations:
------------
Very slow gradual drift may not cross statistical cut-point thresholds for abrupt drift detectors,
relying primarily on continuous Hoeffding tree leaf adaptations.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_gradual_drift_batch(
    n_samples: int, n_features: int, alpha: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)

    # Weights interpolate between Concept A and Concept B
    w_a = np.array([1.5, -1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    w_b = np.array([0.0, 0.0, 1.5, -1.0, 0.0, 0.0], dtype=np.float64)
    w_current = (1.0 - alpha) * w_a + alpha * w_b

    logits = np.dot(X, w_current)
    y = (logits > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 03: Gradual Concept Drift Adaptation")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    batch_size = 120
    total_steps = 10

    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=20,
        delta=1e-3,
        random_state=42
    )

    print("[Config] Gradual transition between Step 4 and Step 7 (alpha: 0.0 -> 1.0)")
    print("-" * 70)

    start_time = time.perf_counter()

    for step in range(1, total_steps + 1):
        if step <= 3:
            alpha = 0.0
        elif step >= 8:
            alpha = 1.0
        else:
            alpha = (step - 3) / 4.0

        X_batch, y_batch = generate_gradual_drift_batch(batch_size, n_features, alpha, seed=300 + step)

        if classifier.samples_seen_ > 0:
            step_acc = classifier.score(X_batch, y_batch)
        else:
            step_acc = 0.50

        classifier.partial_fit(X_batch, y_batch)
        print(f"Step {step:02d} | Transition alpha: {alpha:4.2f} | Pre-Train Acc: {step_acc:6.1%} | Seen: {classifier.samples_seen_}")

    elapsed = time.perf_counter() - start_time

    # Evaluate on final Concept B test set
    X_test_b, y_test_b = generate_gradual_drift_batch(300, n_features, alpha=1.0, seed=777)
    final_acc_b = classifier.score(X_test_b, y_test_b)

    print("-" * 70)
    print(f"Final Concept B Test Accuracy: {final_acc_b:.2%}")
    print(f"Execution Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert final_acc_b >= 0.70, f"Expected final Concept B accuracy >= 70%, got {final_acc_b:.2%}"
    print("STATUS: SUCCESS - Gradual concept drift adapted successfully.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
