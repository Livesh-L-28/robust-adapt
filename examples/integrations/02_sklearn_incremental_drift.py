"""
Example 02: Incremental Streaming and Drift Detection in scikit-learn.

Demonstrates streaming data updates with partial_fit(), utilizing
SklearnDriftDetectorTransformer to track distribution drift and
SklearnAdaptiveClassifier to adapt to non-stationary environments.
"""

from __future__ import annotations

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from robust_adapt.integrations.sklearn import (
    SklearnAdaptiveClassifier,
    SklearnDriftDetectorTransformer,
)


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 02: Incremental Streaming & Drift Adaptation")
    print("=====================================================================")

    rng = np.random.default_rng(123)
    n_batches = 20
    batch_size = 200
    n_features = 6

    # Build streaming pipeline with drift monitor and adaptive classifier
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("drift_monitor", SklearnDriftDetectorTransformer(delta=0.005, monitored_feature_index=0)),
        ("classifier", SklearnAdaptiveClassifier(
            n_features=n_features,
            n_classes=2,
            grace_period=20,
            delta=1e-3,
            random_state=123,
        )),
    ])

    print(f"Streaming Simulation: {n_batches} batches of {batch_size} samples ({n_batches * batch_size} total).")
    print("Concept Drift injected at Batch 10 (mean shift on feature 0 & label inversion).\n")

    pre_drift_accs = []
    post_drift_accs = []

    for b in range(1, n_batches + 1):
        # Generate batch
        if b <= 10:
            # Concept 1
            X_batch = rng.normal(loc=0.0, scale=1.0, size=(batch_size, n_features))
            y_batch = (X_batch[:, 0] + X_batch[:, 1] > 0).astype(np.int64)
        else:
            # Concept 2 (Abrupt Drift: inverted decision boundary + feature shift)
            X_batch = rng.normal(loc=3.0, scale=1.0, size=(batch_size, n_features))
            y_batch = (X_batch[:, 0] + X_batch[:, 1] < 3.0).astype(np.int64)

        # Pre-update test evaluation (Prequential / Test-Then-Train)
        if b > 1:
            preds = pipeline.predict(X_batch)
            acc = accuracy_score(y_batch, preds)
            if b <= 10:
                pre_drift_accs.append(acc)
            else:
                post_drift_accs.append(acc)
            acc_str = f"{acc * 100:.1f}%"
        else:
            acc_str = "N/A (warm-up)"

        # Incremental pipeline training
        # We manually step through pipeline components to mimic streaming partial_fit
        scaled_X = pipeline.named_steps["scaler"].partial_fit(X_batch).transform(X_batch)
        monitored_X = pipeline.named_steps["drift_monitor"].transform(scaled_X)
        pipeline.named_steps["classifier"].partial_fit(monitored_X, y_batch, classes=[0, 1])

        drift_flag = "[DRIFT DETECTED]" if pipeline.named_steps["drift_monitor"].last_drift_detected_ else ""
        print(f"Batch {b:02d} | Test-Then-Train Accuracy: {acc_str:>12} | Cumulative Drifts: {pipeline.named_steps['drift_monitor'].drift_count_} {drift_flag}")

    print("\nSummary Results:")
    print(f"  Pre-drift Mean Accuracy (Batches 2-10):  {np.mean(pre_drift_accs) * 100:.2f}%")
    print(f"  Post-drift Mean Accuracy (Batches 11-20): {np.mean(post_drift_accs) * 100:.2f}%")
    print(f"  Total Drifts Flagged by Transformer:    {pipeline.named_steps['drift_monitor'].drift_count_}")
    print(f"  Total Tree Adaptations:                 {pipeline.named_steps['classifier'].drift_count_}")


if __name__ == "__main__":
    main()
