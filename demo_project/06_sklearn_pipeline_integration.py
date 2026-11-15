"""
Demo 06: Scikit-Learn Ecosystem Integration
============================================
Demonstrates using ROBUST-ADAPT as a native, drop-in estimator
inside standard scikit-learn Pipelines and streaming partial_fit workflows.

Key Components:
- robust_adapt.integrations.sklearn.SklearnAdaptiveClassifier: Full scikit-learn BaseEstimator & ClassifierMixin
- sklearn.pipeline.Pipeline
- sklearn.preprocessing.StandardScaler
"""

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

import robust_adapt
from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier


def main():
    print("=" * 70)
    print("DEMO 06: SCIKIT-LEARN PIPELINE & STREAMING INTEGRATION")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    # 1. Generate synthetic feature stream
    rng = np.random.default_rng(42)
    X = rng.normal(loc=5.0, scale=3.0, size=(600, 4))
    y = ((X[:, 0] + X[:, 1]) > 10.0).astype(int)

    # Split train stream and test stream
    X_train, y_train = X[:400], y[:400]
    X_test, y_test = X[400:], y[400:]

    # 2. Build standard scikit-learn Pipeline
    print("\nConstructing scikit-learn Pipeline with StandardScaler and SklearnAdaptiveClassifier...")
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("adaptive_clf", SklearnAdaptiveClassifier(
            n_features=4,
            n_classes=2,
            enable_drift_detection=True,
            grace_period=20,
            random_state=42,
        ))
    ])

    # 3. Simulate incremental streaming fit via mini-batches
    batch_size = 50
    n_batches = len(X_train) // batch_size
    print(f"Streaming {len(X_train)} training events in batches of {batch_size}...")

    # First batch fits the scaler and initializes the classifier
    pipeline.fit(X_train[:batch_size], y_train[:batch_size])

    # Subsequent batches update the classifier incrementally
    for b in range(1, n_batches):
        start = b * batch_size
        end = start + batch_size
        X_b, y_b = X_train[start:end], y_train[start:end]
        
        # Transform features through pipeline scaler and partial_fit the adaptive classifier
        X_scaled = pipeline.named_steps["scaler"].transform(X_b)
        pipeline.named_steps["adaptive_clf"].partial_fit(X_scaled, y_b)

    # 4. Evaluation on unseen holdout test set
    preds = pipeline.predict(X_test)
    probas = pipeline.predict_proba(X_test)

    print("\nHoldout Test Set Evaluation (200 unseen samples):")
    report = classification_report(y_test, preds, digits=3)
    print(report)

    drift_count = pipeline.named_steps["adaptive_clf"].drift_count_
    print(f"Drift Events Handled: {drift_count}")
    print("Conclusion: ROBUST-ADAPT estimators plug directly into existing scikit-learn pipelines.")


if __name__ == "__main__":
    main()
