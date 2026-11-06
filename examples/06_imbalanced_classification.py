"""Example 06: Imbalanced Streaming Classification.

Problem Description:
-------------------
Demonstrates continual classification under severe class imbalance (90% majority class, 10%
minority class). Standard streaming models predict the majority class exclusively to minimize
cross-entropy loss. ROBUST-ADAPT uses ClassBalancedWeights (based on effective sample volume)
and Class-Balanced Reservoir Replay to preserve minority class recall.

Dataset:
--------
Synthetic 6-dimensional stream with 90:10 imbalance ratio (Class 0: 90%, Class 1: 10%).

Expected Output:
----------------
Balanced accuracy > 65% and minority recall > 50% without collapsing to majority predictions.

Limitations:
------------
Extreme imbalance (>99:1) requires larger replay capacity to maintain sufficient minority exemplars.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_imbalanced_batch(
    n_samples: int, n_features: int, minority_ratio: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    n_minority = int(n_samples * minority_ratio)
    n_majority = n_samples - n_minority

    # Majority class (0): centered at -0.5
    X_maj = rng.randn(n_majority, n_features).astype(np.float64) - 0.5
    y_maj = np.zeros(n_majority, dtype=np.int64)

    # Minority class (1): centered at +1.0
    X_min = rng.randn(n_minority, n_features).astype(np.float64) + 1.0
    y_min = np.ones(n_minority, dtype=np.int64)

    X = np.vstack([X_maj, X_min])
    y = np.concatenate([y_maj, y_min])

    # Shuffle
    indices = rng.permutation(len(y))
    return X[indices], y[indices]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    acc = float(np.mean(y_true == y_pred))
    min_mask = (y_true == 1)
    maj_mask = (y_true == 0)

    recall_min = float(np.mean(y_pred[min_mask] == 1)) if np.any(min_mask) else 0.0
    recall_maj = float(np.mean(y_pred[maj_mask] == 0)) if np.any(maj_mask) else 0.0
    balanced_acc = (recall_min + recall_maj) / 2.0
    return {"acc": acc, "recall_min": recall_min, "recall_maj": recall_maj, "balanced_acc": balanced_acc}


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 06: Imbalanced Streaming Classification")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    n_batches = 6
    batch_size = 200
    minority_ratio = 0.10

    print(f"[Config] Imbalance: 90% Class 0 / 10% Class 1 | Batches: {n_batches} x {batch_size}")
    print("-" * 70)

    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=20,
        delta=1e-3,
        replay_capacity=1000,
        replay_ratio=0.3,
        random_state=42
    )

    cb_weighter = aml.ClassBalancedWeights(beta=0.99)
    running_counts = np.array([10.0, 10.0], dtype=np.float64)

    start_time = time.perf_counter()

    for batch_idx in range(1, n_batches + 1):
        X_batch, y_batch = generate_imbalanced_batch(batch_size, n_features, minority_ratio, seed=600 + batch_idx)

        # Update running class frequencies
        running_counts[0] += np.sum(y_batch == 0)
        running_counts[1] += np.sum(y_batch == 1)

        # Compute dynamic class weights
        class_weights = cb_weighter.compute_weights(running_counts)
        sample_weights = class_weights[y_batch]

        # Interleaved evaluation
        if classifier.samples_seen_ > 0:
            preds = classifier.predict(X_batch)
            m = compute_metrics(y_batch, preds)
        else:
            m = {"acc": 0.5, "recall_min": 0.5, "recall_maj": 0.5, "balanced_acc": 0.5}

        classifier.partial_fit(X_batch, y_batch, sample_weight=sample_weights)

        print(
            f"Batch {batch_idx:02d} | Seen: {classifier.samples_seen_:4d} | "
            f"Bal Acc: {m['balanced_acc']:5.1%} | Min Recall: {m['recall_min']:5.1%} | "
            f"Maj Recall: {m['recall_maj']:5.1%}"
        )

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out test set
    X_test, y_test = generate_imbalanced_batch(400, n_features, minority_ratio, seed=999)
    y_pred = classifier.predict(X_test)
    test_metrics = compute_metrics(y_test, y_pred)

    print("-" * 70)
    print(f"Final Test Accuracy:         {test_metrics['acc']:.2%}")
    print(f"Final Balanced Accuracy:     {test_metrics['balanced_acc']:.2%}")
    print(f"Final Minority Class Recall: {test_metrics['recall_min']:.2%}")
    print(f"Final Majority Class Recall: {test_metrics['recall_maj']:.2%}")
    print(f"Execution Time:              {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert test_metrics["balanced_acc"] >= 0.65, f"Expected balanced acc >= 65%, got {test_metrics['balanced_acc']:.2%}"
    assert test_metrics["recall_min"] >= 0.45, f"Expected minority recall >= 45%, got {test_metrics['recall_min']:.2%}"
    print("STATUS: SUCCESS - Imbalanced streaming classification verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
