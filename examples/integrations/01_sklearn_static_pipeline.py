"""
Example 01: Standard scikit-learn Pipeline Integration.

Demonstrates wrapping ROBUST-ADAPT's streaming classifier inside a classical
scikit-learn Pipeline alongside standard transformers (StandardScaler, SimpleImputer).
"""

from __future__ import annotations

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 01: Standard scikit-learn Pipeline Integration")
    print("=====================================================================")

    # 1. Generate synthetic static dataset
    rng = np.random.default_rng(42)
    n_samples = 2000
    n_features = 8

    X = rng.standard_normal((n_samples, n_features))
    # Latent linear decision boundary with noise
    logits = X[:, 0] * 1.5 - X[:, 1] * 2.0 + X[:, 2] * 0.8
    y = (logits > 0).astype(np.int64)

    # Train / Test split
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Dataset: {n_samples} samples, {n_features} features, 2 classes.")
    print(f"Train split: {len(X_train)} samples | Test split: {len(X_test)} samples")

    # 2. Build standard scikit-learn Pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", SklearnAdaptiveClassifier(
            n_features=n_features,
            n_classes=2,
            grace_period=50,
            delta=1e-4,
            random_state=42,
        )),
    ])

    # 3. Fit pipeline
    print("\nFitting scikit-learn Pipeline (StandardScaler -> SklearnAdaptiveClassifier)...")
    pipeline.fit(X_train, y_train)

    # 4. Predict and evaluate
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)
    acc = accuracy_score(y_test, preds)

    print(f"\nEvaluation Results:")
    print(f"  Test Accuracy: {acc * 100:.2f}%")
    print(f"  Mean Confidence: {np.max(probs, axis=1).mean() * 100:.2f}%")
    print(f"  Underlying Drift Resets: {pipeline.named_steps['classifier'].drift_count_}")
    print(f"  Total Stream Samples Processed: {pipeline.named_steps['classifier'].samples_seen_}")

    print("\nClassification Report:")
    print(classification_report(y_test, preds, digits=4))


if __name__ == "__main__":
    main()
