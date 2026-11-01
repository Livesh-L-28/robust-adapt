"""Input validation, dimension checks, and boundary guards."""

from typing import Optional, Sequence
import numpy as np
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray1D, FloatArray2D, IntArray1D


def check_array_2d(
    X: np.ndarray,
    expected_dim: Optional[int] = None,
    name: str = "X",
) -> FloatArray2D:
    """Validate that X is a non-empty 2D array of floats with finite values."""
    if not isinstance(X, np.ndarray):
        try:
            X = np.asarray(X, dtype=np.float64)
        except Exception as e:
            raise ValidationError(f"{name} must be a numpy ndarray, got {type(X).__name__}: {e}") from e

    if X.ndim != 2:
        raise ValidationError(f"{name} must be a 2D array, but got shape {X.shape} (ndim={X.ndim})")

    if X.shape[0] == 0:
        raise ValidationError(f"{name} cannot be empty (0 rows)")

    if expected_dim is not None and X.shape[1] != expected_dim:
        raise ValidationError(
            f"{name} feature dimension mismatch: expected {expected_dim} columns, but received {X.shape[1]}"
        )

    if not np.all(np.isfinite(X)):
        raise ValidationError(f"{name} contains NaN or Infinite values")

    return np.ascontiguousarray(X, dtype=np.float64)


def check_labels_1d(
    y: np.ndarray,
    expected_len: Optional[int] = None,
    n_classes: Optional[int] = None,
    name: str = "y",
) -> IntArray1D:
    """Validate that y is a 1D array of non-negative integer class labels."""
    if not isinstance(y, np.ndarray):
        try:
            y = np.asarray(y, dtype=np.int64)
        except Exception as e:
            raise ValidationError(f"{name} must be a numpy ndarray, got {type(y).__name__}: {e}") from e

    if y.ndim != 1:
        raise ValidationError(f"{name} must be a 1D array, but got shape {y.shape}")

    if expected_len is not None and y.shape[0] != expected_len:
        raise ValidationError(
            f"Length mismatch: {name} length ({y.shape[0]}) does not match expected length ({expected_len})"
        )

    if not np.issubdtype(y.dtype, np.integer):
        # Check if float values are exact integers
        if np.all(np.equal(np.mod(y, 1), 0)):
            y = y.astype(np.int64)
        else:
            raise ValidationError(f"{name} must contain integer labels, got {y.dtype}")

    if np.any(y < 0):
        raise ValidationError(f"{name} contains negative class labels")

    if n_classes is not None and np.any(y >= n_classes):
        max_val = int(np.max(y))
        raise ValidationError(
            f"{name} contains class label {max_val} which exceeds valid range for {n_classes} classes [0..{n_classes - 1}]"
        )

    return np.ascontiguousarray(y, dtype=np.int64)


def check_probabilities(probs: np.ndarray, name: str = "probabilities") -> FloatArray2D:
    """Validate that probs is a 2D array on the probability simplex."""
    P = check_array_2d(probs, name=name)
    if np.any(P < 0.0) or np.any(P > 1.0 + 1e-6):
        raise ValidationError(f"{name} must contain valid probabilities in [0, 1]")

    row_sums = np.sum(P, axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-5):
        raise ValidationError(f"{name} rows must sum to 1.0 on probability simplex, got sums {row_sums[:3]}")

    return P


def check_sample_weights(
    weights: Optional[np.ndarray],
    expected_len: int,
    name: str = "sample_weight",
) -> Optional[FloatArray1D]:
    """Validate optional 1D sample weights."""
    if weights is None:
        return None

    if not isinstance(weights, np.ndarray):
        weights = np.asarray(weights, dtype=np.float64)

    if weights.ndim != 1 or weights.shape[0] != expected_len:
        raise ValidationError(
            f"{name} must be 1D array matching sample count {expected_len}, got shape {weights.shape}"
        )

    if not np.all(np.isfinite(weights)):
        raise ValidationError(f"{name} contains NaN or Infinite values")

    if np.any(weights < 0.0):
        raise ValidationError(f"{name} contains negative values")

    return np.ascontiguousarray(weights, dtype=np.float64)

