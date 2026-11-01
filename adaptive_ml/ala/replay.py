"""Class-Balanced Reservoir Replay Buffer.

Mathematical formulation specified in DOC-DES-P6-003 and DOC-DES-P6-009 (Algorithm 4).
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.types import FloatArray2D, IntArray1D
from adaptive_ml.core.validation import check_array_2d, check_labels_1d


class ClassBalancedReservoirReplay:
    """Bounded-memory experience replay buffer executing class-stratified reservoir retention.

    Prevents catastrophic forgetting on streaming long-tailed data by guaranteeing that
    rare classes retain proportional capacity in memory regardless of arrival frequency.

    Parameters
    ----------
    capacity : int, default=5000
        Maximum total instances stored in the replay buffer across all classes.
    n_classes : int
        Total number of target classes.
    random_state : Optional[int], default=None
        Seed for reproducible random sampling and replacement.
    """

    def __init__(
        self,
        capacity: int = 5000,
        n_classes: int = 2,
        random_state: Optional[int] = None,
    ) -> None:
        if capacity <= 0:
            raise ValidationError(f"capacity must be positive, got {capacity}")
        if n_classes < 2:
            raise ValidationError(f"n_classes must be >= 2, got {n_classes}")

        self.capacity = int(capacity)
        self.n_classes = int(n_classes)
        self.bucket_capacity = max(1, self.capacity // self.n_classes)

        self._rng = np.random.default_rng(random_state)
        self.random_state = random_state

        # Storage buffers per class
        self._buffers_X: List[List[np.ndarray]] = [[] for _ in range(self.n_classes)]
        self._buffers_y: List[List[int]] = [[] for _ in range(self.n_classes)]
        self._class_seen_counts: np.ndarray = np.zeros(self.n_classes, dtype=np.int64)

    @property
    def total_stored(self) -> int:
        """Total instances currently stored in the buffer."""
        return sum(len(b) for b in self._buffers_y)

    @property
    def class_counts(self) -> Dict[int, int]:
        """Dictionary of current sample counts stored per class."""
        return {c: len(self._buffers_y[c]) for c in range(self.n_classes)}

    def add(self, X: np.ndarray, y: np.ndarray) -> None:
        """Insert a batch of instances into the class-partitioned reservoir buffer."""
        X_val = check_array_2d(X, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")

        n_samples = X_val.shape[0]
        for i in range(n_samples):
            c = int(y_val[i])
            self._class_seen_counts[c] += 1
            n_seen = self._class_seen_counts[c]

            buf_X = self._buffers_X[c]
            buf_y = self._buffers_y[c]

            if len(buf_X) < self.bucket_capacity:
                buf_X.append(X_val[i].copy())
                buf_y.append(c)
            else:
                # Vitter's reservoir replacement
                idx = int(self._rng.integers(0, n_seen))
                if idx < self.bucket_capacity:
                    buf_X[idx] = X_val[i].copy()
                    buf_y[idx] = c

    def sample(self, n_samples: int) -> Tuple[FloatArray2D, IntArray1D]:
        """Extract a stratified balanced replay batch from memory.

        Parameters
        ----------
        n_samples : int
            Total number of replay samples requested.

        Returns
        -------
        X_rep : FloatArray2D of shape (n_actual_samples, n_features)
        y_rep : IntArray1D of shape (n_actual_samples,)
        """
        if n_samples <= 0 or self.total_stored == 0:
            return np.empty((0, 0), dtype=np.float64), np.empty(0, dtype=np.int64)

        per_class = max(1, n_samples // self.n_classes)
        sampled_X: List[np.ndarray] = []
        sampled_y: List[int] = []

        for c in range(self.n_classes):
            buf_X = self._buffers_X[c]
            buf_y = self._buffers_y[c]
            size = len(buf_y)
            if size == 0:
                continue

            k = min(per_class, size)
            chosen_indices = self._rng.choice(size, size=k, replace=False)
            for idx in chosen_indices:
                sampled_X.append(buf_X[idx])
                sampled_y.append(buf_y[idx])

        if len(sampled_X) == 0:
            return np.empty((0, 0), dtype=np.float64), np.empty(0, dtype=np.int64)

        return (
            np.ascontiguousarray(np.stack(sampled_X, axis=0), dtype=np.float64),
            np.ascontiguousarray(np.array(sampled_y, dtype=np.int64)),
        )

    def update_and_sample(
        self,
        X: np.ndarray,
        y: np.ndarray,
        replay_ratio: float = 0.2,
    ) -> Tuple[FloatArray2D, IntArray1D]:
        """Insert incoming stream instances and return combined (stream + replay) batch."""
        X_val = check_array_2d(X, name="X")
        y_val = check_labels_1d(y, expected_len=X_val.shape[0], n_classes=self.n_classes, name="y")

        # Ingest stream instances
        self.add(X_val, y_val)

        n_replay = int(round(X_val.shape[0] * replay_ratio))
        if n_replay <= 0:
            return X_val, y_val

        X_rep, y_rep = self.sample(n_replay)
        if X_rep.shape[0] == 0:
            return X_val, y_val

        X_combined = np.concatenate([X_val, X_rep], axis=0)
        y_combined = np.concatenate([y_val, y_rep], axis=0)
        return np.ascontiguousarray(X_combined), np.ascontiguousarray(y_combined)

    def clear(self) -> None:
        """Reset replay memory completely."""
        for c in range(self.n_classes):
            self._buffers_X[c].clear()
            self._buffers_y[c].clear()
        self._class_seen_counts.fill(0)

    def state_dict(self) -> Dict[str, Any]:
        """Serialize replay buffer state."""
        return {
            "capacity": self.capacity,
            "n_classes": self.n_classes,
            "bucket_capacity": self.bucket_capacity,
            "class_seen_counts": self._class_seen_counts.tolist(),
            "stored_X": [
                [x.tolist() for x in self._buffers_X[c]] for c in range(self.n_classes)
            ],
            "stored_y": [list(self._buffers_y[c]) for c in range(self.n_classes)],
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore replay buffer state."""
        self.capacity = int(state["capacity"])
        self.n_classes = int(state["n_classes"])
        self.bucket_capacity = int(state["bucket_capacity"])
        self._class_seen_counts = np.array(state["class_seen_counts"], dtype=np.int64)

        for c in range(self.n_classes):
            self._buffers_X[c] = [np.array(x, dtype=np.float64) for x in state["stored_X"][c]]
            self._buffers_y[c] = list(state["stored_y"][c])
