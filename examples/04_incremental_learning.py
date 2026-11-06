"""Example 04: Micro-Batch Incremental Learning.

Problem Description:
-------------------
Demonstrates pure incremental learning on high-frequency streaming micro-batches (25 samples
per step). Unlike batch algorithms that require retaining past data in memory, ROBUST-ADAPT's
incremental learning algorithms update internal tree leaves on-the-fly with constant memory
consumption and sub-millisecond per-step update times.

Dataset:
--------
Synthetic 6-dimensional stream ingested across 25 sequential micro-batches (625 samples total).

Expected Output:
----------------
Model continuously improves accuracy from initial cold-start (~50%) to >70%; constant memory.

Limitations:
------------
Micro-batches require setting grace_period appropriately low (e.g. 15-25) to allow splits.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_micro_batch(n_samples: int, n_features: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    weights = np.array([1.8, -1.4, 1.0, -0.8, 0.4, -0.3][:n_features], dtype=np.float64)
    logits = np.dot(X, weights)
    y = (logits > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 04: Micro-Batch Incremental Learning")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    batch_size = 25
    n_steps = 25

    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=20,
        delta=1e-3,
        random_state=42
    )

    print(f"[Config] Micro-batches: {n_steps} steps of {batch_size} samples (Total: {n_steps * batch_size})")
    print("-" * 70)

    start_time = time.perf_counter()
    recent_accs = []

    for step in range(1, n_steps + 1):
        X_batch, y_batch = generate_micro_batch(batch_size, n_features, seed=400 + step)

        if classifier.samples_seen_ > 0:
            step_acc = classifier.score(X_batch, y_batch)
        else:
            step_acc = 0.50

        classifier.partial_fit(X_batch, y_batch)
        recent_accs.append(step_acc)

        if step % 5 == 0 or step == 1:
            rolling_acc = np.mean(recent_accs[-5:])
            print(
                f"Step {step:02d} / {n_steps:02d} | Total Seen: {classifier.samples_seen_:3d} | "
                f"Current Batch Acc: {step_acc:6.1%} | Rolling 5-Step Acc: {rolling_acc:6.1%}"
            )

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out test set
    X_test, y_test = generate_micro_batch(250, n_features, seed=999)
    final_test_acc = classifier.score(X_test, y_test)

    print("-" * 70)
    print(f"Final Held-Out Test Accuracy: {final_test_acc:.2%}")
    print(f"Average Step Duration: {(elapsed / n_steps) * 1000:.3f} ms")
    print(f"Total Elapsed Time: {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert final_test_acc >= 0.70, f"Expected final test accuracy >= 70%, got {final_test_acc:.2%}"
    print("STATUS: SUCCESS - Micro-batch incremental learning verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
