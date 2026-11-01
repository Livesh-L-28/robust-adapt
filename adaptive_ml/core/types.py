"""Type annotations, protocols, and standard aliases for AdaptiveML."""

from typing import (
    Any,
    Dict,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)
import numpy as np
import numpy.typing as npt

# Floating point and integer array aliases
FloatArray2D = npt.NDArray[np.float64]
FloatArray1D = npt.NDArray[np.float64]
IntArray1D = npt.NDArray[np.int64]
IntArray2D = npt.NDArray[np.int64]
ByteArray1D = npt.NDArray[np.int8]
UByteArray1D = npt.NDArray[np.uint8]

ArrayLike = Union[FloatArray2D, FloatArray1D, Sequence[float], Sequence[int]]

T = TypeVar("T")


@runtime_checkable
class EstimatorProtocol(Protocol):
    """Protocol for streaming classifiers."""

    def fit(self, X: FloatArray2D, y: IntArray1D) -> Any:
        ...

    def partial_fit(
        self,
        X: FloatArray2D,
        y: IntArray1D,
        sample_weight: Optional[FloatArray1D] = None,
    ) -> Any:
        ...

    def predict(self, X: FloatArray2D) -> IntArray1D:
        ...

    def predict_proba(self, X: FloatArray2D) -> FloatArray2D:
        ...


@runtime_checkable
class StatefulProtocol(Protocol):
    """Protocol for stateful and serializable modules."""

    def state_dict(self) -> Dict[str, Any]:
        ...

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        ...

