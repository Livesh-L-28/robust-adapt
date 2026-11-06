"""Minority-Aware Experience Replay Buffer.

Guarantees retention of rare and minority-class instances under extreme stream imbalance
(e.g., 90:10, 99:1, 1000:1) by reserving dedicated memory quotas that cannot be
cannibalized by arriving majority instances.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.types import FloatArray2D, IntArray1D
from robust_adapt.core.validation import check_array_2d, check_labels_1d


class MinorityAwareReplayBuffer:
    """Experience replay buffer with dedicated minority quotas and reliability filtering.

    Parameters
    ----------
    capacity : int, default=2000
        Maximum total instances stored across all classes.
    n_classes : int, default=2
        Number of target classes.
    min_minority_fraction : float, default=0.35
        Minimum fraction of buffer capacity strictly reserved for minority classes.
    min_reliability : float, default=0.20
        Reliability threshold below which samples are filtered out to prevent noise poisoning.
    random_state : Optional[int], default=None
        Random seed for sampling and reservoir replacement.
    """

    def __init__(
        self,
        capacity: int = 2000,
        n_classes: int = 2,
        min_minority_fraction: float = 0.35,
        min_reliability: float = 0.20,
        random_state: Optional[int] = None,
    ) -> None:
        if capacity < 10:
            raise ConfigurationError(f"capacity must be >= 10, got {capacity}")
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if not 0.0 < min_minority_fraction < 1.0:
            raise ConfigurationError(f"min_minority_fraction must be in (0, 1), got {min_minority_fraction}")

        self.capacity = int(capacity)
        self.n_classes = int(n_classes)
        self.min_minority_fraction = float(min_minority_fraction)
        self.min_reliability = float(min_reliability)
        self.random_state = random_state
        self._rng = np.random.default_rng(random_state)

        # Storage buffers per class
        self._buffers_X: List[List[np.ndarray]] = [[] for _ in range(self.n_classes)]
        self._buffers_y: List[List[int]] = [[] for _ in range(self.n_classes)]
        self._buffers_w: List[List[float]] = [[] for _ in range(self.n_classes)]
        self._class_seen_counts: np.ndarray = np.zeros(self.n_classes, dtype=np.int64)

    @property
    def total_stored(self) -> int:
        """Total instances currently stored in memory."""
        return sum(len(b) for b in self._buffers_y)

    @property
    def class_counts(self) -> Dict[int, int]:
        """Dictionary of current sample counts stored per class."""
        return {c: len(self._buffers_y[c]) for c in range(self.n_classes)}

    def _get_minority_classes(self) -> List[int]:
        """Dynamically identify minority classes based on cumulative stream frequency."""
        counts = self._class_seen_counts
        total = max(1, np.sum(counts))
        freqs = counts / total
        cutoff = 1.0 / (2.0 * self.n_classes)
        minorities = [int(c) for c in range(self.n_classes) if freqs[c] <= cutoff]
        if not minorities:
            # If perfectly balanced, smallest count is minority
            minorities = [int(np.argmin(counts))]
        return minorities

    def add(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> int:
        """Ingest incoming stream instances into memory subject to minority quota reservations.

        Parameters
        ----------
        X : np.ndarray
            2D array of instance features.
        y : np.ndarray
            1D array of instance class labels.
        sample_weight : Optional[np.ndarray], default=None
            Sample-level reliability scores in [0, 1].

        Returns
        -------
        int
            Number of instances successfully ingested into replay memory.
        """
        X_val = check_array_2d(X, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")

        n_samples = X_val.shape[0]
        if sample_weight is not None:
            w_val = np.asarray(sample_weight, dtype=np.float64)
            if w_val.shape[0] != n_samples:
                raise ValidationError(f"sample_weight shape {w_val.shape} != n_samples {n_samples}")
        else:
            w_val = np.ones(n_samples, dtype=np.float64)

        minority_quota = int(round(self.capacity * self.min_minority_fraction))
        majority_capacity = self.capacity - minority_quota

        ingested = 0
        for i in range(n_samples):
            c = int(y_val[i])
            rel = float(w_val[i])
            self._class_seen_counts[c] += 1
            n_seen = self._class_seen_counts[c]

            # Reliability filter (avoids polluting buffer with severe noise)
            if rel < self.min_reliability:
                continue

            minorities = self._get_minority_classes()
            is_minority = c in minorities

            buf_X = self._buffers_X[c]
            buf_y = self._buffers_y[c]
            buf_w = self._buffers_w[c]

            # Dedicated capacity bounds
            if is_minority:
                class_quota = max(1, minority_quota // max(1, len(minorities)))
            else:
                n_maj = max(1, self.n_classes - len(minorities))
                class_quota = max(1, majority_capacity // n_maj)

            if len(buf_X) < class_quota:
                buf_X.append(X_val[i].copy())
                buf_y.append(c)
                buf_w.append(rel)
                ingested += 1
            else:
                # Reservoir replacement strictly within its own class bucket
                idx = int(self._rng.integers(0, n_seen))
                if idx < class_quota:
                    buf_X[idx] = X_val[i].copy()
                    buf_y[idx] = c
                    buf_w[idx] = rel
                    ingested += 1

        return ingested

    def sample_balanced(
        self,
        n_samples: int,
        target_minority_ratio: float = 0.5,
    ) -> Tuple[FloatArray2D, IntArray1D]:
        """Extract a stratified replay batch ensuring target representation of minority classes.

        Parameters
        ----------
        n_samples : int
            Total batch size requested.
        target_minority_ratio : float, default=0.5
            Target fraction of the extracted batch dedicated to minority instances.

        Returns
        -------
        Tuple[FloatArray2D, IntArray1D]
            Stratified replay feature matrix and label vector.
        """
        if n_samples <= 0 or self.total_stored == 0:
            return np.empty((0, 0), dtype=np.float64), np.empty(0, dtype=np.int64)

        minorities = self._get_minority_classes()
        majorities = [c for c in range(self.n_classes) if c not in minorities]

        n_min_target = int(round(n_samples * target_minority_ratio))
        n_maj_target = n_samples - n_min_target

        sampled_X: List[np.ndarray] = []
        sampled_y: List[int] = []

        # 1. Sample from minority classes
        min_stored = sum(len(self._buffers_y[c]) for c in minorities)
        if min_stored > 0 and len(minorities) > 0:
            per_min_class = max(1, n_min_target // len(minorities))
            for c in minorities:
                buf_X = self._buffers_X[c]
                buf_y = self._buffers_y[c]
                k = min(per_min_class, len(buf_y))
                if k > 0:
                    chosen = self._rng.choice(len(buf_y), size=k, replace=(k > len(buf_y)))
                    for idx in chosen:
                        sampled_X.append(buf_X[idx])
                        sampled_y.append(buf_y[idx])

        # 2. Sample from majority classes
        maj_stored = sum(len(self._buffers_y[c]) for c in majorities)
        if maj_stored > 0 and len(majorities) > 0:
            per_maj_class = max(1, n_maj_target // len(majorities))
            for c in majorities:
                buf_X = self._buffers_X[c]
                buf_y = self._buffers_y[c]
                k = min(per_maj_class, len(buf_y))
                if k > 0:
                    chosen = self._rng.choice(len(buf_y), size=k, replace=(k > len(buf_y)))
                    for idx in chosen:
                        sampled_X.append(buf_X[idx])
                        sampled_y.append(buf_y[idx])

        if len(sampled_X) == 0:
            return np.empty((0, 0), dtype=np.float64), np.empty(0, dtype=np.int64)

        return (
            np.ascontiguousarray(np.stack(sampled_X, axis=0), dtype=np.float64),
            np.ascontiguousarray(np.array(sampled_y, dtype=np.int64)),
        )

    def purge(
        self,
        policy: str = "selective",
        min_reliability: float = 0.5,
        keep_minority: bool = True,
    ) -> int:
        """Purge stale majority instances while protecting minority memories."""
        valid_policies = {"full", "selective", "partial"}
        if policy not in valid_policies:
            raise ValidationError(f"policy must be one of {valid_policies}, got '{policy}'")

        if policy == "full":
            initial_count = self.total_stored
            self.clear()
            return initial_count

        minorities = set(self._get_minority_classes())
        total_purged = 0

        for c in range(self.n_classes):
            if keep_minority and c in minorities:
                continue

            buf_X = self._buffers_X[c]
            buf_y = self._buffers_y[c]
            buf_w = self._buffers_w[c]
            initial_len = len(buf_y)
            if initial_len == 0:
                continue

            if policy == "selective":
                kept_indices = [idx for idx, w in enumerate(buf_w) if w >= min_reliability]
                self._buffers_X[c] = [buf_X[i] for i in kept_indices]
                self._buffers_y[c] = [buf_y[i] for i in kept_indices]
                self._buffers_w[c] = [buf_w[i] for i in kept_indices]
                total_purged += initial_len - len(kept_indices)
            elif policy == "partial":
                half = initial_len // 2
                self._buffers_X[c] = buf_X[half:]
                self._buffers_y[c] = buf_y[half:]
                self._buffers_w[c] = buf_w[half:]
                total_purged += half

        return total_purged

    def clear(self) -> None:
        """Reset all storage buffers."""
        for c in range(self.n_classes):
            self._buffers_X[c].clear()
            self._buffers_y[c].clear()
            self._buffers_w[c].clear()
        self._class_seen_counts.fill(0)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize buffer state."""
        return {
            "capacity": self.capacity,
            "n_classes": self.n_classes,
            "min_minority_fraction": self.min_minority_fraction,
            "min_reliability": self.min_reliability,
            "class_seen_counts": self._class_seen_counts.tolist(),
            "stored_X": [[x.tolist() for x in self._buffers_X[c]] for c in range(self.n_classes)],
            "stored_y": [list(self._buffers_y[c]) for c in range(self.n_classes)],
            "stored_w": [list(self._buffers_w[c]) for c in range(self.n_classes)],
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore buffer state."""
        self.capacity = int(state["capacity"])
        self.n_classes = int(state["n_classes"])
        self.min_minority_fraction = float(state["min_minority_fraction"])
        self.min_reliability = float(state["min_reliability"])
        self._class_seen_counts = np.array(state["class_seen_counts"], dtype=np.int64)
        for c in range(self.n_classes):
            self._buffers_X[c] = [np.array(x, dtype=np.float64) for x in state["stored_X"][c]]
            self._buffers_y[c] = list(state["stored_y"][c])
            self._buffers_w[c] = [float(w) for w in state["stored_w"][c]]
