"""AdaptiveML Core primitives, types, configuration, and exception hierarchy."""

from adaptive_ml.core.constants import (
    EPS_DIV,
    EPS_VAR,
    EPS_SOFTMAX,
    EPS_LOG,
    EPS_CLIP_RCE,
    EPS_RELIABILITY,
    EPS_QUANT,
    DEFAULT_BLOCK_SIZE,
    INT8_MAX,
    UINT8_MAX,
    DEFAULT_TAU_R,
    DEFAULT_DELTA_HYST,
    DEFAULT_RECOVERY_STEPS,
)
from adaptive_ml.core.types import (
    FloatArray1D,
    FloatArray2D,
    IntArray1D,
    IntArray2D,
    ByteArray1D,
    UByteArray1D,
    ArrayLike,
    EstimatorProtocol,
    StatefulProtocol,
)
from adaptive_ml.core.exceptions import (
    AdaptiveMLError,
    ConfigurationError,
    ValidationError,
    DriftStateError,
    QuantizationError,
    ResourceBudgetExceededError,
    NumericalInstabilityError,
    SerializationError,
)
from adaptive_ml.core.config import (
    TreeConfig,
    ADWINConfig,
    ReplayConfig,
    ScorerConfig,
    AdamWConfig,
    ULCConfig,
)
from adaptive_ml.core.validation import (
    check_array_2d,
    check_labels_1d,
    check_probabilities,
    check_sample_weights,
)
from adaptive_ml.core.telemetry import (
    get_process_memory_bytes,
    MemoryBudgetTracker,
)

__all__ = [
    # Constants
    "EPS_DIV",
    "EPS_VAR",
    "EPS_SOFTMAX",
    "EPS_LOG",
    "EPS_CLIP_RCE",
    "EPS_RELIABILITY",
    "EPS_QUANT",
    "DEFAULT_BLOCK_SIZE",
    "INT8_MAX",
    "UINT8_MAX",
    "DEFAULT_TAU_R",
    "DEFAULT_DELTA_HYST",
    "DEFAULT_RECOVERY_STEPS",
    # Types
    "FloatArray1D",
    "FloatArray2D",
    "IntArray1D",
    "IntArray2D",
    "ByteArray1D",
    "UByteArray1D",
    "ArrayLike",
    "EstimatorProtocol",
    "StatefulProtocol",
    # Exceptions
    "AdaptiveMLError",
    "ConfigurationError",
    "ValidationError",
    "DriftStateError",
    "QuantizationError",
    "ResourceBudgetExceededError",
    "NumericalInstabilityError",
    "SerializationError",
    # Config
    "TreeConfig",
    "ADWINConfig",
    "ReplayConfig",
    "ScorerConfig",
    "AdamWConfig",
    "ULCConfig",
    # Validation
    "check_array_2d",
    "check_labels_1d",
    "check_probabilities",
    "check_sample_weights",
    # Telemetry
    "get_process_memory_bytes",
    "MemoryBudgetTracker",
]
