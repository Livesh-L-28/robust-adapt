"""
Integration tests for scikit-learn framework compatibility.
"""

from __future__ import annotations

import numpy as np
import pytest

try:
    from sklearn.base import clone
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from adaptive_ml.integrations.sklearn import SklearnAdaptiveClassifier


@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn is required")
class TestSklearnIntegration:
    def test_estimator_cloning(self) -> None:
        """Verify sklearn.base.clone() compatibility."""
        clf = SklearnAdaptiveClassifier(
            n_features=5,
            n_classes=3,
            grace_period=50,
            delta=1e-4,
            random_state=42,
        )
        cloned_clf = clone(clf)

        assert cloned_clf.n_features == 5
        assert cloned_clf.n_classes == 3
        assert cloned_clf.grace_period == 50
        assert cloned_clf.delta == 1e-4
        assert cloned_clf.random_state == 42
        assert cloned_clf._estimator is None

    def test_pipeline_integration(self) -> None:
        """Verify execution inside a scikit-learn Pipeline."""
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SklearnAdaptiveClassifier(n_features=4, n_classes=2, grace_period=20)),
        ])

        rng = np.random.default_rng(42)
        X = rng.normal(size=(100, 4))
        y = (X[:, 0] + X[:, 1] > 0).astype(np.int64)

        pipe.fit(X, y)
        preds = pipe.predict(X)
        probs = pipe.predict_proba(X)

        assert len(preds) == 100
        assert probs.shape == (100, 2)
        score = pipe.score(X, y)
        assert 0.0 <= score <= 1.0

    def test_partial_fit_streaming_compatibility(self) -> None:
        """Verify incremental learning via partial_fit()."""
        clf = SklearnAdaptiveClassifier(n_features=3, n_classes=2, grace_period=10)

        rng = np.random.default_rng(123)
        for _ in range(5):
            X_batch = rng.normal(size=(20, 3))
            y_batch = (X_batch[:, 0] > 0).astype(np.int64)
            clf.partial_fit(X_batch, y_batch)

        assert hasattr(clf, "classes_")
        assert len(clf.classes_) == 2

