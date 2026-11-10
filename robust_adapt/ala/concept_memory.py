"""Concept Memory and Knowledge Retention for Recurring Concept Drift.

Stores historical model states alongside statistical concept signatures (centroids,
feature covariances, class priors). Enables instantaneous restoration of previously learned
models upon detecting recurring drift, eliminating costly retraining from scratch.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError


@dataclass
class ConceptSignature:
    """Statistical summary representing a learned concept distribution."""
    concept_id: str
    centroid: np.ndarray
    variances: np.ndarray
    class_priors: np.ndarray
    sample_count: int

    def similarity(self, candidate_centroid: np.ndarray, candidate_variances: np.ndarray) -> float:
        """Compute Gaussian feature similarity in [0, 1] against a candidate batch."""
        # Normalized Euclidean distance weighted by inverse variance
        denom = np.sqrt(self.variances + candidate_variances + 1e-6)
        normalized_diff = np.abs(self.centroid - candidate_centroid) / denom
        dist = float(np.mean(normalized_diff))
        # Gaussian kernel similarity
        return float(np.exp(-0.5 * (dist ** 2)))


class ConceptMemory:
    """Bounded repository of historical concept signatures and model checkpoints.

    Parameters
    ----------
    max_concepts : int, default=10
        Maximum distinct concept models retained in memory.
    similarity_threshold : float, default=0.75
        Minimum similarity required to declare a recurring concept match.
    """

    def __init__(
        self,
        max_concepts: int = 10,
        similarity_threshold: float = 0.75,
    ) -> None:
        if max_concepts < 1:
            raise ConfigurationError(f"max_concepts must be >= 1, got {max_concepts}")
        if not 0.0 < similarity_threshold <= 1.0:
            raise ConfigurationError(f"similarity_threshold must be in (0, 1], got {similarity_threshold}")

        self.max_concepts = int(max_concepts)
        self.similarity_threshold = float(similarity_threshold)

        # Storage
        self._signatures: Dict[str, ConceptSignature] = {}
        self._models: Dict[str, Dict[str, Any]] = {}
        self._access_history: List[str] = []

    @property
    def stored_concept_ids(self) -> List[str]:
        """List of concept IDs currently held in memory."""
        return list(self._signatures.keys())

    @property
    def n_stored(self) -> int:
        """Total number of stored concepts."""
        return len(self._signatures)

    def extract_signature(
        self,
        concept_id: str,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        n_classes: int = 2,
    ) -> ConceptSignature:
        """Extract statistical centroid, variance, and prior vectors from a sample batch."""
        X_arr = np.asarray(X, dtype=np.float64)
        n_samples = X_arr.shape[0]

        centroid = np.mean(X_arr, axis=0)
        variances = np.var(X_arr, axis=0) + 1e-6

        if y is not None:
            y_arr = np.asarray(y, dtype=np.int64)
            counts = np.bincount(y_arr, minlength=n_classes)
            priors = (counts + 1.0) / (n_samples + n_classes)
        else:
            priors = np.full(n_classes, 1.0 / n_classes)

        return ConceptSignature(
            concept_id=concept_id,
            centroid=centroid,
            variances=variances,
            class_priors=priors,
            sample_count=n_samples,
        )

    def store_concept(
        self,
        concept_id: str,
        arg2: Any = None,
        arg3: Any = None,
        arg4: Any = None,
        n_classes: int = 2,
        *,
        model_state: Optional[Any] = None,
        X: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None,
    ) -> ConceptSignature:
        """Store a model state dict along with its statistical concept signature.

        Supports both positional conventions and keyword arguments:
        - Legacy: (concept_id, model_state, X, y=None, n_classes=2)
        - Intuitive: (concept_id, X, y=None, model_state=None, n_classes=2)
        - Keyword arguments: (concept_id=..., X=..., y=..., model_state=..., n_classes=...)
        """
        resolved_model_state = model_state
        resolved_X = X
        resolved_y = y

        # Resolve positional arguments if provided
        if arg2 is not None:
            is_arg2_data = isinstance(arg2, np.ndarray) or hasattr(arg2, "__array__")
            if is_arg2_data:
                # Intuitive ordering: (concept_id, X, [y or model_state], [model_state])
                if resolved_X is None:
                    resolved_X = arg2
                if arg3 is not None:
                    is_arg3_data = isinstance(arg3, np.ndarray) or hasattr(arg3, "__array__")
                    if is_arg3_data:
                        if resolved_y is None:
                            resolved_y = arg3
                        if arg4 is not None and resolved_model_state is None:
                            resolved_model_state = arg4
                    else:
                        # arg3 is model_state
                        if resolved_model_state is None:
                            resolved_model_state = arg3
                        if arg4 is not None and resolved_y is None:
                            resolved_y = arg4
            else:
                # Legacy ordering: (concept_id, model_state, X, [y])
                if resolved_model_state is None:
                    resolved_model_state = arg2
                if arg3 is not None and resolved_X is None:
                    resolved_X = arg3
                if arg4 is not None and resolved_y is None:
                    resolved_y = arg4

        if resolved_X is None:
            raise ValueError("store_concept requires feature data 'X' (as positional or keyword argument).")
        if resolved_model_state is None:
            resolved_model_state = {}

        sig = self.extract_signature(concept_id, resolved_X, y=resolved_y, n_classes=n_classes)

        # Enforce LRU eviction if capacity reached
        if len(self._signatures) >= self.max_concepts and concept_id not in self._signatures:
            lru_id = self._access_history[0] if self._access_history else next(iter(self._signatures))
            self.remove_concept(lru_id)

        self._signatures[concept_id] = sig
        self._models[concept_id] = resolved_model_state
        if concept_id in self._access_history:
            self._access_history.remove(concept_id)
        self._access_history.append(concept_id)
        return sig

    def query_recurring(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
    ) -> Optional[Tuple[str, Dict[str, Any], float]]:
        """Query memory for a recurring concept matching the candidate data batch.

        Parameters
        ----------
        X : np.ndarray
            Incoming candidate feature batch.
        y : Optional[np.ndarray], default=None
            Optional labels.

        Returns
        -------
        Optional[Tuple[str, Dict[str, Any], float]]
            If match found: (best_concept_id, restored_model_state, similarity_score).
            If no match exceeds similarity_threshold: returns None.
        """
        if not self._signatures or X.shape[0] < 5:
            return None

        X_arr = np.asarray(X, dtype=np.float64)
        cand_centroid = np.mean(X_arr, axis=0)
        cand_var = np.var(X_arr, axis=0) + 1e-6

        best_id: Optional[str] = None
        best_sim = -1.0

        for c_id, sig in self._signatures.items():
            sim = sig.similarity(cand_centroid, cand_var)
            if sim > best_sim:
                best_sim = sim
                best_id = c_id

        if best_id is not None and best_sim >= self.similarity_threshold:
            # Update access history for LRU
            if best_id in self._access_history:
                self._access_history.remove(best_id)
            self._access_history.append(best_id)
            return best_id, self._models[best_id], best_sim

        return None

    def get_model(self, concept_id: str) -> Optional[Any]:
        """Retrieve stored model state for a concept ID."""
        return self._models.get(concept_id)

    def get_signature(self, concept_id: str) -> Optional[ConceptSignature]:
        """Retrieve stored concept signature for a concept ID."""
        return self._signatures.get(concept_id)

    def remove_concept(self, concept_id: str) -> None:
        """Remove a stored concept."""
        self._signatures.pop(concept_id, None)
        self._models.pop(concept_id, None)
        if concept_id in self._access_history:
            self._access_history.remove(concept_id)

    def clear(self) -> None:
        """Clear all stored concepts."""
        self._signatures.clear()
        self._models.clear()
        self._access_history.clear()


@dataclass
class ConceptSnapshot:
    """Represents a stored historical concept and its associated model state."""
    concept_id: str
    fingerprint: np.ndarray
    model_state: Any
    creation_step: int
    last_used_step: int
    usage_count: int = 1
    metadata: Dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class ConceptFingerprinter:
    """Extracts compact statistical fingerprints from data windows for recurring drift matching."""

    def __init__(self, n_features: int, n_classes: int = 2) -> None:
        if n_features < 1:
            raise ConfigurationError(f"n_features must be >= 1, got {n_features}")
        if n_classes < 1:
            raise ConfigurationError(f"n_classes must be >= 1, got {n_classes}")
        self.n_features = int(n_features)
        self.n_classes = int(n_classes)

    def compute_fingerprint(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Computes a fixed-dimensional normalized summary vector [mean, std, class_priors]."""
        X_arr = np.asarray(X, dtype=np.float64)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        if X_arr.shape[0] == 0:
            raise ValidationError("Cannot compute fingerprint from an empty array.")

        mu = np.mean(X_arr, axis=0)
        sigma = np.std(X_arr, axis=0) + 1e-6

        if y is not None:
            y_arr = np.asarray(y, dtype=np.int64).ravel()
            counts = np.bincount(y_arr, minlength=self.n_classes)
            priors = counts[:self.n_classes] / max(1, len(y_arr))
        else:
            priors = np.ones(self.n_classes) / self.n_classes

        raw_fp = np.concatenate([mu, sigma, priors])
        norm = np.linalg.norm(raw_fp)
        return raw_fp / max(float(norm), 1e-8)


class RecurringConceptMemory:
    """Bounded concept repository with cosine similarity matching and LRU/LFU eviction.

    Parameters
    ----------
    max_concepts : int, default=5
        Maximum number of distinct concept snapshots retained in memory.
    similarity_threshold : float, default=0.82
        Minimum cosine similarity required to declare a recurring concept match.
    """

    def __init__(
        self,
        max_concepts: int = 5,
        similarity_threshold: float = 0.82,
    ) -> None:
        if max_concepts < 0:
            raise ConfigurationError(f"max_concepts must be >= 0, got {max_concepts}")
        if not 0.0 < similarity_threshold <= 1.0:
            raise ConfigurationError(f"similarity_threshold must be in (0, 1], got {similarity_threshold}")

        self.max_concepts = int(max_concepts)
        self.similarity_threshold = float(similarity_threshold)
        self.concepts: Dict[str, ConceptSnapshot] = {}
        self._next_id = 0

    @property
    def n_stored(self) -> int:
        """Total number of currently stored concept snapshots."""
        return len(self.concepts)

    def find_matching_concept(
        self,
        fingerprint: np.ndarray,
    ) -> Tuple[Optional[ConceptSnapshot], float]:
        """Finds the most similar stored concept snapshot via cosine similarity."""
        if not self.concepts or self.max_concepts <= 0:
            return None, 0.0

        fp = np.asarray(fingerprint, dtype=np.float64).ravel()
        best_concept: Optional[ConceptSnapshot] = None
        best_sim = -1.0

        for snap in self.concepts.values():
            sim = float(np.dot(fp, snap.fingerprint))
            if sim > best_sim:
                best_sim = sim
                best_concept = snap

        if best_sim >= self.similarity_threshold and best_concept is not None:
            return best_concept, best_sim
        return None, max(0.0, best_sim)

    def store_concept(
        self,
        fingerprint: np.ndarray,
        model_state: Any,
        step: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConceptSnapshot]:
        """Stores a new concept snapshot, evicting the least valuable if at capacity."""
        if self.max_concepts <= 0:
            return None

        import copy

        if len(self.concepts) >= self.max_concepts:
            # Evict least-frequently / least-recently used concept
            evict_id = min(
                self.concepts.keys(),
                key=lambda cid: (self.concepts[cid].usage_count, self.concepts[cid].last_used_step),
            )
            del self.concepts[evict_id]

        cid = f"concept_{self._next_id}"
        self._next_id += 1
        snap = ConceptSnapshot(
            concept_id=cid,
            fingerprint=np.asarray(fingerprint, dtype=np.float64).copy(),
            model_state=copy.deepcopy(model_state),
            creation_step=int(step),
            last_used_step=int(step),
            usage_count=1,
            metadata=copy.deepcopy(metadata) if metadata else {},
        )
        self.concepts[cid] = snap
        return snap

    def update_concept(
        self,
        concept_id: str,
        fingerprint: np.ndarray,
        model_state: Any,
        step: int,
    ) -> bool:
        """Updates an existing concept snapshot upon reactivation."""
        if concept_id not in self.concepts:
            return False

        import copy

        snap = self.concepts[concept_id]
        snap.fingerprint = np.asarray(fingerprint, dtype=np.float64).copy()
        snap.model_state = copy.deepcopy(model_state)
        snap.last_used_step = int(step)
        snap.usage_count += 1
        return True

    def get_concept(self, concept_id: str) -> Optional[ConceptSnapshot]:
        """Retrieve concept snapshot by ID."""
        return self.concepts.get(concept_id)

    def remove_concept(self, concept_id: str) -> bool:
        """Remove a stored concept by ID."""
        if concept_id in self.concepts:
            del self.concepts[concept_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored concept snapshots."""
        self.concepts.clear()
        self._next_id = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes memory configuration and snapshots to a dictionary."""
        return {
            "max_concepts": self.max_concepts,
            "similarity_threshold": self.similarity_threshold,
            "next_id": self._next_id,
            "concepts": {
                cid: {
                    "concept_id": snap.concept_id,
                    "fingerprint": snap.fingerprint.tolist(),
                    "creation_step": snap.creation_step,
                    "last_used_step": snap.last_used_step,
                    "usage_count": snap.usage_count,
                    "metadata": snap.metadata,
                }
                for cid, snap in self.concepts.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurringConceptMemory":
        """Reconstructs memory state from a serialized dictionary."""
        mem = cls(
            max_concepts=data.get("max_concepts", 5),
            similarity_threshold=data.get("similarity_threshold", 0.82),
        )
        mem._next_id = data.get("next_id", 0)
        for cid, snap_data in data.get("concepts", {}).items():
            mem.concepts[cid] = ConceptSnapshot(
                concept_id=snap_data["concept_id"],
                fingerprint=np.array(snap_data["fingerprint"], dtype=np.float64),
                model_state=None,
                creation_step=snap_data["creation_step"],
                last_used_step=snap_data["last_used_step"],
                usage_count=snap_data["usage_count"],
                metadata=snap_data.get("metadata", {}),
            )
        return mem
