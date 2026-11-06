"""
ROBUST-ADAPT Example: Scikit-learn Pipeline Integration.

Demonstrates using SklearnAdaptiveClassifier within a standard scikit-learn
Pipeline with feature scaling and cross-validation metrics.
"""

from __future__ import annotations

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier


def main() -> None:
    print("=" * 80)
    print("ROBUST-ADAPT: Scikit-learn Pipeline Integration Example")
    print("=" * 80)

    # 1. Generate Synthetic Classification Data
    rng = np.random.default_rng(42)
    X = rng.normal(loc=1.0, scale=2.0, size=(200, 4))
    y = ((X[:, 0] * 1.5 - X[:, 1] * 0.8) > 0.0).astype(np.int64)

    # 2. Build Pipeline
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", SklearnAdaptiveClassifier(
            n_features=4,
            n_classes=2,
            grace_period=20,
            delta=1e-4,
            random_state=42,
        )),
    ])

    print("Fitting scikit-learn Pipeline on 200 samples...")
    pipe.fit(X, y)

    # 3. Predict & Evaluate
    preds = pipe.predict(X)
    probs = pipe.predict_proba(X)
    accuracy = pipe.score(X, y)

    print(f"Accuracy: {accuracy * 100:.2f}%")
    print(f"Predicted class distribution: Class 0 = {np.sum(preds == 0)}, Class 1 = {np.sum(preds == 1)}")
    print(f"Sample predicted probabilities (first 3 rows):\n{probs[:3]}")
    print("=" * 80)
    print("Scikit-learn Pipeline Example Completed Successfully!")


if __name__ == "__main__":
    main()

