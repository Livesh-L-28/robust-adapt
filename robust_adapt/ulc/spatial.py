"""Spatial Discordance and Neighborhood Coherence Engine.

Computes nearest-neighbor label agreement in feature space to distinguish
genuine, spatially coherent concept drift from random label noise.
"""

from __future__ import annotations

import numpy as np

from robust_adapt.core.validation import check_array_2d, check_labels_1d


def compute_spatial_discordance(
    X: np.ndarray,
    y: np.ndarray,
    k: int = 5,
    metric: str = "euclidean",
) -> float:
    """Calculate mean nearest-neighbor label discordance in feature space.

    Measures the average fraction of $k$-nearest spatial neighbors whose class
    label differs from the query point. When genuine concept drift occurs, new
    samples form spatially coherent clusters, yielding low discordance ($d \\le 0.25$).
    Conversely, random or adversarial label noise corrupts individual labels within
    existing feature clusters, yielding high discordance ($d > 0.25$).

    Parameters
    ----------
    X : np.ndarray
        Feature matrix of shape ``(n_samples, n_features)``.
    y : np.ndarray
        Class labels of shape ``(n_samples,)``.
    k : int, default=5
        Number of nearest neighbors to inspect.
    metric : str, default="euclidean"
        Distance metric. Currently supports ``"euclidean"``.

    Returns
    -------
    float
        Mean spatial discordance in $[0.0, 1.0]$.
        - 0.0: Perfectly coherent (all $k$ neighbors share the same label).
        - 1.0: Completely discordant (all $k$ neighbors have different labels).

    Raises
    ------
    ValueError
        If inputs fail shape or type validation, or if $k < 1$.
    """
    if k < 1:
        raise ValueError(f"k must be a positive integer >= 1, got {k}")

    X_arr = check_array_2d(X, name="X")
    n_samples = X_arr.shape[0]
    y_arr = check_labels_1d(y, expected_len=n_samples, name="y")

    # If insufficient samples to form k neighbors, default to 0.0 (coherent)
    if n_samples <= k:
        return 0.0

    if metric != "euclidean":
        raise ValueError(f"Unsupported metric '{metric}'. Only 'euclidean' is supported.")

    # Vectorized pairwise squared Euclidean distances
    # Shape: (n_samples, n_samples)
    diff = X_arr[:, np.newaxis, :] - X_arr[np.newaxis, :, :]
    dist_sq = np.sum(diff ** 2, axis=-1)

    # Exclude self-distance by setting diagonal to infinity
    np.fill_diagonal(dist_sq, np.inf)

    # Partition indices to obtain the k nearest neighbors
    nn_idx = np.argpartition(dist_sq, k, axis=1)[:, :k]

    # Compute discordance: fraction of k-neighbors with discordant labels
    neighbor_labels = y_arr[nn_idx]
    discordances = np.mean(neighbor_labels != y_arr[:, np.newaxis], axis=1)

    return float(np.clip(np.mean(discordances), 0.0, 1.0))
