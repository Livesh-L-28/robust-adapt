"""
Advanced scikit-learn pipeline and adapter integration test suite.

Verifies:
- SklearnAdaptiveClassifier full protocol compliance (fit, predict, predict_proba, score, partial_fit).
- Estimator cloning, get_params, set_params.
- Integration inside standard scikit-learn Pipeline and cross_val_score.
- SklearnDriftDetectorTransformer concept drift detection.
- SklearnReliabilityFilter instance filtering.
"""

from __future__ import annotations

import numpy as np
import pytest

try:
    from sklearn.base import clone
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

from robust_adapt.integrations.sklearn import (
    SklearnAdaptiveClassifier,
    SklearnDriftDetectorTransformer,
    SklearnReliabilityFilter,
)


@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn is required")
class TestSklearnPipelineAdvanced:
    """Test suite for advanced scikit-learn integration."""

    def test_classifier_fit_predict_score(self) -> None:
        """Verify standard fit, predict, predict_proba, and score methods."""
        rng = np.random.default_rng(42)
        X = rng.standard_normal((100, 4))
        y = (X[:, 0] + X[:, 1] > 0).astype(np.int64)

        clf = SklearnAdaptiveClassifier(
            n_features=4,
            n_classes=2,
            grace_period=20,
            random_state=42,
        )

        clf.fit(X, y)
        assert hasattr(clf, "classes_")
        assert np.array_equal(clf.classes_, [0, 1])
        assert clf.n_features_in_ == 4

        preds = clf.predict(X)
        assert preds.shape == (100,)
        assert set(np.unique(preds)).issubset({0, 1})

        probs = clf.predict_proba(X)
        assert probs.shape == (100, 2)
        assert np.allclose(probs.sum(axis=1), 1.0)

        score = clf.score(X, y)
        assert 0.0 <= score <= 1.0

    def test_classifier_partial_fit_streaming(self) -> None:
        """Verify incremental streaming updates via partial_fit()."""
        rng = np.random.default_rng(123)
        clf = SklearnAdaptiveClassifier(
            n_features=3,
            n_classes=2,
            grace_period=10,
            random_state=123,
        )

        for b in range(5):
            X_batch = rng.standard_normal((30, 3))
            y_batch = (X_batch[:, 0] > 0).astype(np.int64)
            clf.partial_fit(X_batch, y_batch, classes=[0, 1])

        assert clf.samples_seen_ == 150
        assert clf.n_features_in_ == 3

    def test_classifier_cloning_and_params(self) -> None:
        """Verify get_params, set_params, and scikit-learn clone() equivalence."""
        clf = SklearnAdaptiveClassifier(
            n_features=8,
            n_classes=3,
            grace_period=40,
            delta=1e-5,
            random_state=999,
        )
        params = clf.get_params()
        assert params["n_features"] == 8
        assert params["n_classes"] == 3
        assert params["grace_period"] == 40
        assert params["delta"] == 1e-5
        assert params["random_state"] == 999

        cloned = clone(clf)
        assert cloned.n_features == 8
        assert cloned._estimator is None

        clf.set_params(grace_period=100)
        assert clf.grace_period == 100

    def test_pipeline_with_preprocessing_and_cv(self) -> None:
        """Verify execution in a scikit-learn Pipeline with cross-validation."""
        rng = np.random.default_rng(42)
        X = rng.standard_normal((120, 5))
        y = (X[:, 0] > 0).astype(np.int64)

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SklearnAdaptiveClassifier(n_features=5, n_classes=2, grace_period=20, random_state=42)),
        ])

        scores = cross_val_score(pipe, X, y, cv=3)
        assert len(scores) == 3
        assert all(0.0 <= s <= 1.0 for s in scores)

    @pytest.mark.skipif(not _PANDAS_AVAILABLE, reason="pandas is required")
    def test_dataframe_feature_names_retention(self) -> None:
        """Verify feature_names_in_ attribute is properly set when input is a DataFrame."""
        df_X = pd.DataFrame({"age": [25.0, 30.0, 45.0], "income": [50.0, 60.0, 80.0]})
        y = np.array([0, 1, 1], dtype=np.int64)

        clf = SklearnAdaptiveClassifier(n_features=2, n_classes=2, grace_period=10)
        clf.fit(df_X, y)

        assert hasattr(clf, "feature_names_in_")
        assert list(clf.feature_names_in_) == ["age", "income"]

    def test_drift_detector_transformer(self) -> None:
        """Verify SklearnDriftDetectorTransformer detects concept drift in a pipeline."""
        rng = np.random.default_rng(42)
        # Stationary pre-drift data: constant stream with minor perturbation
        X1 = np.ones((50, 4)) * 0.5 + rng.normal(loc=0.0, scale=0.01, size=(50, 4))
        # Drifted post-drift data: sudden large shift
        X2 = np.ones((50, 4)) * 5.0 + rng.normal(loc=0.0, scale=0.01, size=(50, 4))

        transformer = SklearnDriftDetectorTransformer(delta=0.001, monitored_feature_index=0)
        transformer.fit(X1)

        # First batch: no drift detected
        out1 = transformer.transform(X1)
        assert out1.shape == X1.shape
        assert transformer.drift_count_ == 0

        # Second batch: abrupt drift should be triggered
        out2 = transformer.transform(X2)
        assert out2.shape == X2.shape
        assert transformer.drift_count_ > 0
        assert transformer.last_drift_detected_ is True

    def test_reliability_filter(self) -> None:
        """Verify SklearnReliabilityFilter filters low-weight instances."""
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
        y = np.array([0, 1, 0, 1], dtype=np.int64)
        probas = np.array([[0.9, 0.1], [0.1, 0.9], [0.8, 0.2], [0.2, 0.8]])

        flt = SklearnReliabilityFilter(n_classes=2, min_reliability=0.35)
        flt.fit(X, y)
        filtered_X, filtered_y, filtered_w = flt.filter_batch(X, y, probas)

        assert isinstance(filtered_X, np.ndarray)
        assert len(filtered_X) > 0
        assert len(filtered_X) == len(filtered_y) == len(filtered_w)
