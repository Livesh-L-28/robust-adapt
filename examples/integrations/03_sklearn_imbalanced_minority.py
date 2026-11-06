"""
Example 03: Severe Class Imbalance with scikit-learn and ROBUST-ADAPT.

Demonstrates handling extreme stream imbalance (95% Class 0 vs 5% Class 1)
using SklearnReliabilityFilter and SklearnAdaptiveClassifier with minority tracking.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from robust_adapt.integrations.sklearn import (
    SklearnAdaptiveClassifier,
    SklearnReliabilityFilter,
)


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 03: Imbalanced Stream & Minority Intelligence")
    print("=====================================================================")

    rng = np.random.default_rng(42)
    n_samples = 3000
    n_features = 6

    # 1. Generate imbalanced synthetic stream (95% majority, 5% minority)
    is_minority = rng.random(n_samples) < 0.05
    y = is_minority.astype(np.int64)

    X = np.zeros((n_samples, n_features), dtype=np.float64)
    # Majority class: standard Gaussian distribution centered at 0
    X[~is_minority] = rng.normal(loc=0.0, scale=1.0, size=(np.sum(~is_minority), n_features))
    # Minority class: shifted Gaussian centered at +2.0
    X[is_minority] = rng.normal(loc=2.0, scale=1.0, size=(np.sum(is_minority), n_features))

    print(f"Total Stream Samples: {n_samples}")
    print(f"  Majority Class 0: {np.sum(y == 0)} ({np.mean(y == 0)*100:.1f}%)")
    print(f"  Minority Class 1: {np.sum(y == 1)} ({np.mean(y == 1)*100:.1f}%)")

    # Split train/test
    split = 2000
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    # 2. Build Pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", SklearnAdaptiveClassifier(
            n_features=n_features,
            n_classes=2,
            grace_period=25,
            delta=1e-4,
            random_state=42,
        )),
    ])

    print("\nFitting pipeline on initial imbalanced train split...")
    pipeline.fit(X_train, y_train)

    # 3. Predict on test set
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)

    # 4. Filter test set with SklearnReliabilityFilter to examine noisy instances
    rel_filter = SklearnReliabilityFilter(n_classes=2, min_reliability=0.30)
    filtered_X, filtered_y, filtered_w = rel_filter.filter_batch(X_test, y_test, probs)

    print("\nEvaluation Results on Test Split:")
    f1_min = f1_score(y_test, preds, pos_label=1)
    f1_macro = f1_score(y_test, preds, average="macro")
    print(f"  Minority Class F1-Score: {f1_min:.4f}")
    print(f"  Macro F1-Score:          {f1_macro:.4f}")
    print(f"  Samples Filtered for Low Reliability: {rel_filter.filtered_count_} / {len(X_test)}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, preds))

    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["Majority (0)", "Minority (1)"], digits=4))


if __name__ == "__main__":
    main()
