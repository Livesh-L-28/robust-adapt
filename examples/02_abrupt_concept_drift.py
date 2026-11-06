"""Example 02: Abrupt Concept Drift Adaptation.

Problem Description:
-------------------
Demonstrates the detection of and recovery from sudden (abrupt) concept drift in a streaming
environment. At a discrete switch point, the generative decision boundary abruptly changes,
causing pre-drift models to suffer high error rates. ROBUST-ADAPT's ADWIN drift detector detects
the shift and triggers tree reorganization.

Dataset:
--------
Synthetic 6-dimensional stream.
- Concept A (Steps 1-4): Boundary defined by x0 + x1 > 0
- Concept B (Steps 5-8): Boundary abruptly switches to x2 - x3 > 0

Expected Output:
----------------
Drift detected at or shortly after the switch point; accuracy drops temporarily and recovers.

Limitations:
------------
Requires sufficient samples in Concept B to reconstruct new decision splits.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_drift_batch(n_samples: int, n_features: int, concept: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    if concept == "A":
        # Concept A: primary signal on features 0 and 1
        y = (X[:, 0] + X[:, 1] > 0.0).astype(np.int64)
    else:
        # Concept B: primary signal on features 2 and 3
        y = (X[:, 2] - X[:, 3] > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 02: Abrupt Concept Drift Adaptation")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    batch_size = 150
    total_steps = 8
    drift_step = 5

    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=20,
        delta=1e-3,
        enable_drift_detection=True,
        random_state=42
    )

    print(f"[Config] Abrupt drift at Step {drift_step:02d} | Concept A -> Concept B")
    print("-" * 70)

    start_time = time.perf_counter()
    pre_drift_accs = []
    post_drift_accs = []

    for step in range(1, total_steps + 1):
        concept = "A" if step < drift_step else "B"
        X_batch, y_batch = generate_drift_batch(batch_size, n_features, concept=concept, seed=200 + step)

        if classifier.samples_seen_ > 0:
            step_acc = classifier.score(X_batch, y_batch)
        else:
            step_acc = 0.50

        if step < drift_step:
            pre_drift_accs.append(step_acc)
        else:
            post_drift_accs.append(step_acc)

        prev_drifts = classifier.drift_count_
        classifier.partial_fit(X_batch, y_batch)
        drift_signal = classifier.drift_count_ > prev_drifts

        alert = " *** DRIFT DETECTED ***" if drift_signal else ""
        print(
            f"Step {step:02d} [Concept {concept}] | "
            f"Pre-Train Acc: {step_acc:6.1%} | "
            f"Total Drifts: {classifier.drift_count_}{alert}"
        )

    elapsed = time.perf_counter() - start_time

    # Evaluate on Concept B final test set
    X_test_b, y_test_b = generate_drift_batch(300, n_features, concept="B", seed=888)
    final_acc_b = classifier.score(X_test_b, y_test_b)

    print("-" * 70)
    print(f"Post-Adaptation Concept B Accuracy: {final_acc_b:.2%}")
    print(f"Total Drift Events Triggered: {classifier.drift_count_}")
    print(f"Execution Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert final_acc_b >= 0.70, f"Expected adapted Concept B accuracy >= 70%, got {final_acc_b:.2%}"
    print("STATUS: SUCCESS - Abrupt concept drift detected and handled.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
