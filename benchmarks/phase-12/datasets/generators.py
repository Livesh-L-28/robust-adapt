"""
Benchmark synthetic dataset and stream generators.

Generates standard concept-drift, noisy-label, and resource-constrained
evaluation streams for Phase 12 experiments.
"""

from __future__ import annotations

from typing import Iterator, Optional, Tuple
import numpy as np


class SEAGenerator:
    """Streaming generator for SEA Concept Drift benchmark.

    Instances have 3 continuous features x_0, x_1, x_2 in [0, 10].
    Target label is 1 if (x_0 + x_1) <= theta, else 0.
    Feature x_2 is irrelevant Gaussian noise.
    Concept drift occurs by abruptly or gradually altering threshold theta.
    """

    def __init__(
        self,
        thetas: list[float] = [8.0, 9.0, 7.0, 9.5],
        concept_length: int = 1000,
        noise_ratio: float = 0.05,
        random_state: Optional[int] = None,
    ) -> None:
        self.thetas = thetas
        self.concept_length = concept_length
        self.noise_ratio = noise_ratio
        self.rng = np.random.default_rng(random_state)
        self.sample_idx = 0

    def generate_stream(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate n_samples from the non-stationary SEA stream."""
        X = self.rng.uniform(0.0, 10.0, size=(n_samples, 3))
        y = np.zeros(n_samples, dtype=np.int64)

        for i in range(n_samples):
            concept_idx = (self.sample_idx // self.concept_length) % len(self.thetas)
            theta = self.thetas[concept_idx]
            y[i] = 1 if (X[i, 0] + X[i, 1]) <= theta else 0

            # Noise injection
            if self.noise_ratio > 0.0 and self.rng.random() < self.noise_ratio:
                y[i] = 1 - y[i]

            self.sample_idx += 1

        return X, y


class RotatingHyperplaneGenerator:
    """Rotating Hyperplane stream generator for continuous gradual concept drift."""

    def __init__(
        self,
        n_features: int = 4,
        mag_change: float = 0.005,
        noise_ratio: float = 0.05,
        random_state: Optional[int] = None,
    ) -> None:
        self.n_features = n_features
        self.mag_change = mag_change
        self.noise_ratio = noise_ratio
        self.rng = np.random.default_rng(random_state)
        self.weights = self.rng.uniform(0.0, 1.0, size=n_features)
        self.weights /= np.sum(self.weights)

    def generate_stream(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate rotating hyperplane stream."""
        X = self.rng.uniform(0.0, 1.0, size=(n_samples, self.n_features))
        y = np.zeros(n_samples, dtype=np.int64)

        for i in range(n_samples):
            # Rotate weights smoothly
            self.weights += self.rng.normal(0.0, self.mag_change, size=self.n_features)
            self.weights = np.maximum(0.0, self.weights)
            self.weights /= np.sum(self.weights)

            threshold = 0.5 * np.sum(self.weights)
            y[i] = 1 if np.dot(X[i], self.weights) >= threshold else 0

            if self.noise_ratio > 0.0 and self.rng.random() < self.noise_ratio:
                y[i] = 1 - y[i]

        return X, y


def inject_label_noise(
    y: np.ndarray,
    noise_type: str = "symmetric",
    noise_rate: float = 0.2,
    n_classes: int = 2,
    X: Optional[np.ndarray] = None,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """Inject controlled label noise into a ground truth label vector."""
    rng = np.random.default_rng(random_state)
    y_corrupt = y.copy()
    n_samples = len(y)

    if noise_type == "symmetric":
        # Random uniform label flipping
        mask = rng.random(size=n_samples) < noise_rate
        random_labels = rng.integers(0, n_classes, size=n_samples)
        y_corrupt[mask] = random_labels[mask]

    elif noise_type == "asymmetric":
        # Class-conditional flip (e.g., class 0 -> class 1)
        mask = (y == 0) & (rng.random(size=n_samples) < noise_rate)
        y_corrupt[mask] = 1

    elif noise_type == "instance_dependent":
        # Probability of flip increases near decision boundary or dense core
        if X is None:
            raise ValueError("X must be provided for instance-dependent noise.")
        norms = np.linalg.norm(X, axis=1)
        norm_std = np.std(norms) + 1e-8
        prob = noise_rate / (1.0 + np.exp(-(norms - np.mean(norms)) / norm_std))
        mask = rng.random(size=n_samples) < prob
        y_corrupt[mask] = 1 - y_corrupt[mask]

    else:
        raise ValueError(f"Unknown noise_type: {noise_type}")

    return y_corrupt


def generate_imbalanced_multiclass_stream(
    n_samples: int = 1000,
    n_features: int = 4,
    n_classes: int = 3,
    imbalance_ratio: float = 0.02,  # 2% minority class
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate multi-class stream with extreme minority class."""
    rng = np.random.default_rng(random_state)
    X = []
    y = []

    # Class 0: Majority (60%)
    # Class 1: Moderate (38%)
    # Class 2: Extreme minority (2%)
    p0 = 1.0 - imbalance_ratio - 0.38
    p1 = 0.38
    p2 = imbalance_ratio

    centers = {
        0: np.array([-2.0] * n_features),
        1: np.array([2.0] * n_features),
        2: np.array([6.0] * n_features),
    }

    for _ in range(n_samples):
        c = rng.choice([0, 1, 2], p=[p0, p1, p2])
        x_i = rng.normal(loc=centers[c], scale=0.5, size=n_features)
        X.append(x_i)
        y.append(c)

    return np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)
