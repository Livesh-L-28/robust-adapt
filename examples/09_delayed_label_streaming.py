"""Example 09: Asynchronous Delayed Label Streaming.

Problem Description:
-------------------
Demonstrates asynchronous streaming learning where inference occurs in real-time at time t,
but ground truth supervisory labels arrive with non-deterministic arrival delays (Delta t).
ROBUST-ADAPT's DelayedLabelQueue caches unlabelled feature vectors, matches incoming labels
by sample_id, and emits verified batches ready for model partial_fit updates without
label leakage or unbounded memory growth.

Dataset:
--------
Synthetic 6-dimensional streaming data where labels arrive with Poisson-distributed delays
(mean delay Delta t = 5 steps) across 100 streaming steps of 6 samples each (600 samples total).

Expected Output:
----------------
Queue matches all enqueued labels; model trains on extracted matched batches; test accuracy > 60%.

Limitations:
------------
Queue size must be sized to accommodate max_delay * throughput to prevent premature timeouts.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_batch(n_samples: int, n_features: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    weights = np.array([2.0, -1.8, 1.2, -1.0, 0.5, -0.4][:n_features], dtype=np.float64)
    logits = np.dot(X, weights)
    y = (logits > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 09: Asynchronous Delayed Label Streaming")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    total_steps = 100
    samples_per_step = 6
    mean_delay = 5

    # 1. Initialize AdaptiveClassifier and DelayedLabelQueue
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=15,
        delta=1e-3,
        random_state=42
    )

    label_queue = aml.DelayedLabelQueue(max_queue_size=2000)

    # Store delayed arrival events: dict of arrival_time -> list of (sample_id, label)
    pending_arrivals: dict[int, list[tuple[str, int]]] = {}

    rng = np.random.RandomState(42)
    start_time = time.perf_counter()

    print(f"[Config] Stream Steps: {total_steps} | Samples/Step: {samples_per_step} | Mean Delay: {mean_delay} steps")
    print("-" * 70)

    for current_t in range(1, total_steps + 1):
        # 1. New unlabelled samples arrive at current_t
        X_step, y_step = generate_batch(samples_per_step, n_features, seed=current_t * 17)

        for i in range(samples_per_step):
            sample_id = f"s_{current_t:03d}_{i}"
            feats = X_step[i]
            true_label = int(y_step[i])

            # Immediate model inference
            pred = classifier.predict(feats.reshape(1, -1))[0]

            # Cache in queue
            label_queue.enqueue(sample_id=sample_id, X=feats, prediction=pred, timestamp=float(current_t))

            # Schedule delayed arrival
            delay = int(rng.poisson(mean_delay))
            arrival_t = current_t + max(1, delay)
            pending_arrivals.setdefault(arrival_t, []).append((sample_id, true_label))

        # 2. Check if any delayed labels arrived at current_t
        if current_t in pending_arrivals:
            for s_id, s_label in pending_arrivals[current_t]:
                label_queue.provide_label(sample_id=s_id, label=s_label, arrival_timestamp=float(current_t))

        # 3. Extract ready matched batch and train model
        if label_queue.ready_count >= 20:
            X_batch, y_batch, weights, delays = label_queue.extract_ready_batch(max_batch_size=30)
            classifier.partial_fit(X_batch, y_batch, sample_weight=weights)

        if current_t % 25 == 0:
            print(
                f"Time t={current_t:03d} | Pending Queue: {label_queue.pending_count:3d} | "
                f"Ready: {label_queue.ready_count:2d} | "
                f"Mean Delay: {label_queue.mean_observed_delay:4.1f} steps | "
                f"Trained: {classifier.samples_seen_:3d}"
            )

    # Drain remaining delayed labels arriving after total_steps
    for arr_t in sorted(k for k in pending_arrivals.keys() if k > total_steps):
        for s_id, s_label in pending_arrivals[arr_t]:
            label_queue.provide_label(sample_id=s_id, label=s_label, arrival_timestamp=float(arr_t))

    if label_queue.ready_count > 0:
        X_batch, y_batch, weights, delays = label_queue.extract_ready_batch()
        classifier.partial_fit(X_batch, y_batch, sample_weight=weights)

    elapsed = time.perf_counter() - start_time

    # Evaluate on held-out test set
    X_test, y_test = generate_batch(300, n_features, seed=999)
    test_acc = classifier.score(X_test, y_test)

    print("-" * 70)
    print(f"Final Trained Samples:       {classifier.samples_seen_}")
    print(f"Total Enqueued Samples:      {label_queue._total_enqueued}")
    print(f"Total Matched Labels:        {label_queue._total_matched}")
    print(f"Observed Average Delay:      {label_queue.mean_observed_delay:.2f} steps")
    print(f"Final Held-Out Test Accuracy:{test_acc:.2%}")
    print(f"Execution Time:              {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert test_acc >= 0.60, f"Expected final test accuracy >= 60%, got {test_acc:.2%}"
    print("STATUS: SUCCESS - Asynchronous delayed label streaming verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
