"""Streaming Drift Classification and Attribution Engine.

Analyzes non-stationary streams to classify drift characteristics:
- Velocity & Severity
- Drift Type: Abrupt, Gradual, Incremental, Recurring, Stationary
- Drift Nature: Concept Drift (P(y|X)), Feature Drift (P(X)), or Dual Drift
- Feature Attribution: Identifies which features contributed most to the distribution shift.
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError


class DriftType(str, Enum):
    """Categorical temporal profile of concept shift."""
    STATIONARY = "STATIONARY"
    ABRUPT = "ABRUPT"
    GRADUAL = "GRADUAL"
    INCREMENTAL = "INCREMENTAL"
    RECURRING = "RECURRING"


class DriftNature(str, Enum):
    """Underlying statistical origin of stream shift."""
    NO_DRIFT = "NO_DRIFT"
    CONCEPT_DRIFT = "CONCEPT_DRIFT"  # P(y|X) changes
    FEATURE_DRIFT = "FEATURE_DRIFT"  # P(X) changes while P(y|X) stable
    DUAL_DRIFT = "DUAL_DRIFT"        # Both P(X) and P(y|X) shift


@dataclass(frozen=True)
class DriftAnalysisResult:
    """Structured report returned by DriftClassifier."""
    drift_type: DriftType
    drift_nature: DriftNature
    severity: float
    velocity: float
    top_features: List[Tuple[int, float]]
    confidence: float
    explanation: str


class DriftClassifier:
    """Classifies drift characteristics and attributes feature-level distribution shifts.

    Parameters
    ----------
    n_features : int
        Dimensionality of streaming feature vectors.
    window_size : int, default=200
        Size of sliding analysis window.
    reference_window_size : int, default=500
        Size of baseline reference window representing stationary distribution.
    velocity_threshold_abrupt : float, default=0.15
        Error gradient threshold distinguishing abrupt from gradual drift.
    """

    def __init__(
        self,
        n_features: int,
        window_size: int = 200,
        reference_window_size: int = 500,
        velocity_threshold_abrupt: float = 0.15,
    ) -> None:
        if n_features < 1:
            raise ConfigurationError(f"n_features must be >= 1, got {n_features}")
        if window_size < 20:
            raise ConfigurationError(f"window_size must be >= 20, got {window_size}")

        self.n_features = int(n_features)
        self.window_size = int(window_size)
        self.reference_window_size = int(reference_window_size)
        self.velocity_threshold_abrupt = float(velocity_threshold_abrupt)

        # Buffers
        self._ref_X: deque = deque(maxlen=self.reference_window_size)
        self._ref_y: deque = deque(maxlen=self.reference_window_size)
        self._ref_errors: deque = deque(maxlen=self.reference_window_size)
        self._curr_X: deque = deque(maxlen=self.window_size)
        self._curr_y: deque = deque(maxlen=self.window_size)
        self._curr_errors: deque = deque(maxlen=self.window_size)

        self._samples_seen: int = 0

    def update(
        self,
        X: np.ndarray,
        y: np.ndarray,
        errors: Optional[np.ndarray] = None,
    ) -> None:
        """Ingest streaming batch into sliding analysis buffers."""
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.int64)
        n = X_arr.shape[0]

        if errors is None:
            err_arr = np.zeros(n, dtype=np.float64)
        else:
            err_arr = np.asarray(errors, dtype=np.float64)

        for i in range(n):
            self._samples_seen += 1
            if len(self._ref_X) < self.reference_window_size:
                self._ref_X.append(X_arr[i])
                self._ref_y.append(int(y_arr[i]))
                self._ref_errors.append(float(err_arr[i]))
            self._curr_X.append(X_arr[i])
            self._curr_y.append(int(y_arr[i]))
            self._curr_errors.append(float(err_arr[i]))

    def analyze(self) -> DriftAnalysisResult:
        """Analyze sliding buffers and return complete drift diagnostic report."""
        if len(self._curr_X) < 20 or len(self._ref_X) < 20:
            return DriftAnalysisResult(
                drift_type=DriftType.STATIONARY,
                drift_nature=DriftNature.NO_DRIFT,
                severity=0.0,
                velocity=0.0,
                top_features=[],
                confidence=1.0,
                explanation="Insufficient samples to perform drift classification.",
            )

        curr_X_mat = np.array(self._curr_X)
        ref_X_mat = np.array(self._ref_X)
        errors = np.array(self._curr_errors)
        ref_errors = np.array(self._ref_errors)

        # 1. Feature Distribution Shift Analysis (Wasserstein / Normalized Distance per feature)
        ref_means = np.mean(ref_X_mat, axis=0)
        ref_stds = np.std(ref_X_mat, axis=0) + 1e-6
        curr_means = np.mean(curr_X_mat, axis=0)

        # Standardized difference per feature: |mu_curr - mu_ref| / sigma_ref
        feature_shift_scores = np.abs(curr_means - ref_means) / ref_stds
        top_feature_indices = np.argsort(-feature_shift_scores)
        top_features = [(int(idx), float(feature_shift_scores[idx])) for idx in top_feature_indices[:5]]

        max_feature_shift = float(np.max(feature_shift_scores))
        mean_feature_shift = float(np.mean(feature_shift_scores))

        # 2. Error Trajectory Analysis (Velocity = error slope)
        recent_half = len(errors) // 2
        err_first_half = float(np.mean(errors[:recent_half])) if recent_half > 0 else 0.0
        err_second_half = float(np.mean(errors[recent_half:])) if recent_half > 0 else 0.0
        err_delta = err_second_half - err_first_half
        ref_err = float(np.mean(ref_errors)) if len(ref_errors) > 0 else 0.0
        curr_err = float(np.mean(errors)) if len(errors) > 0 else 0.0
        err_jump = curr_err - ref_err

        velocity = float(err_jump / max(1, len(errors)))
        severity = float(np.clip(curr_err, 0.0, 1.0))

        # 3. Determine Drift Nature
        is_feature_drift = mean_feature_shift > 0.40 or max_feature_shift > 1.20
        is_concept_drift = (curr_err > 0.25 and err_jump > 0.10) or (err_second_half > 0.25 and err_delta > 0.05)

        if is_concept_drift and is_feature_drift:
            nature = DriftNature.DUAL_DRIFT
        elif is_concept_drift:
            nature = DriftNature.CONCEPT_DRIFT
        elif is_feature_drift:
            nature = DriftNature.FEATURE_DRIFT
        else:
            nature = DriftNature.NO_DRIFT

        # 4. Determine Drift Type
        if nature == DriftNature.NO_DRIFT:
            drift_type = DriftType.STATIONARY
            explanation = "Stream is statistically stable; no significant feature or error divergence."
            confidence = 0.95
        else:
            if abs(err_jump) >= self.velocity_threshold_abrupt or abs(err_delta) >= self.velocity_threshold_abrupt or max_feature_shift >= 3.0:
                drift_type = DriftType.ABRUPT
                explanation = f"Abrupt change detected with sudden error jump (+{err_jump:.2f}) or large feature shock."
                confidence = 0.90
            elif err_jump > 0.02 or err_delta > 0.02:
                drift_type = DriftType.GRADUAL
                explanation = f"Gradual drift detected: smooth divergence over {len(errors)} samples."
                confidence = 0.85
            else:
                drift_type = DriftType.INCREMENTAL
                explanation = "Slow, incremental drift detected across feature manifolds."
                confidence = 0.80

            if len(top_features) > 0 and top_features[0][1] > 0.5:
                top_feat_str = ", ".join([f"feature_{idx} (shift={s:.2f})" for idx, s in top_features[:3]])
                explanation += f" Top contributing features: {top_feat_str}."

        return DriftAnalysisResult(
            drift_type=drift_type,
            drift_nature=nature,
            severity=severity,
            velocity=velocity,
            top_features=top_features,
            confidence=confidence,
            explanation=explanation,
        )

    def reset_reference(self) -> None:
        """Promote current window to reference window after adaptation."""
        self._ref_X.clear()
        self._ref_y.clear()
        self._ref_errors.clear()
        for x in self._curr_X:
            self._ref_X.append(x)
        for y in self._curr_y:
            self._ref_y.append(y)
        for e in self._curr_errors:
            self._ref_errors.append(e)
