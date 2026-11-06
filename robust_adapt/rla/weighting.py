"""Class-Balanced Loss Reweighting based on the effective number of samples.

Mathematical formulation specified in DOC-DES-P6-004 and DOC-DES-P6-009 (Algorithm 7).
"""

from typing import Union
import numpy as np
from robust_adapt.core.constants import EPS_DIV
from robust_adapt.core.exceptions import ValidationError
from robust_adapt.core.types import FloatArray1D, IntArray1D
from robust_adapt.core.validation import check_labels_1d


class ClassBalancedWeights:
    """Computes class weights based on the effective number of samples: (1 - beta) / (1 - beta^n).

    Parameters
    ----------
    beta : float, default=0.999
        Hyperparameter governing the volume overlap of samples in (0.0, 1.0).
    """

    def __init__(self, beta: float = 0.999) -> None:
        if beta <= 0.0 or beta >= 1.0:
            raise ValidationError(f"beta must be in (0, 1), got {beta}")
        self.beta = float(beta)

    def compute_weights(self, class_counts: np.ndarray) -> FloatArray1D:
        """Compute normalized class weight vector from observed class frequencies.

        Parameters
        ----------
        class_counts : np.ndarray of shape (n_classes,)
            Integer or float counts of samples observed for each class.

        Returns
        -------
        class_weights : FloatArray1D of shape (n_classes,)
            Normalized weights whose mean equals 1.0.
        """
        counts = np.asarray(class_counts, dtype=np.float64)
        if counts.ndim != 1 or counts.shape[0] < 2:
            raise ValidationError(f"class_counts must be 1D array with >= 2 classes, got {counts.shape}")
        if np.any(counts < 0.0):
            raise ValidationError("class_counts cannot contain negative values")

        n_classes = counts.shape[0]
        # Effective number of samples: E_n = (1 - beta^n) / (1 - beta)
        effective_num = 1.0 - (self.beta ** counts)
        # Avoid division by zero for classes with 0 samples
        raw_weights = np.where(counts > 0.0, (1.0 - self.beta) / (effective_num + EPS_DIV), 1.0)

        # Normalize weights so mean is 1.0
        total_raw = float(np.sum(raw_weights)) + EPS_DIV
        norm_weights = n_classes * (raw_weights / total_raw)

        return np.ascontiguousarray(norm_weights, dtype=np.float64)

    def compute_sample_weights(self, y: np.ndarray, class_counts: np.ndarray) -> FloatArray1D:
        """Map class weights to individual sample weights."""
        y_val = check_labels_1d(y, name="y")
        class_weights = self.compute_weights(class_counts)
        sample_weights = class_weights[y_val]
        return np.ascontiguousarray(sample_weights, dtype=np.float64)
