"""AdaptiveML Core primitives, types, configuration, and exception hierarchy."""

from robust_adapt.core.constants import (
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
from robust_adapt.core.types import (
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
from robust_adapt.core.exceptions import (
    AdaptiveMLError,
    ConfigurationError,
    ValidationError,
    DriftStateError,
    QuantizationError,
    ResourceBudgetExceededError,
    NumericalInstabilityError,
    SerializationError,
)
from robust_adapt.core.config import (
    TreeConfig,
    ADWINConfig,
    ReplayConfig,
    ScorerConfig,
    AdamWConfig,
    ULCConfig,
)
from robust_adapt.core.validation import (
    check_array_2d,
    check_labels_1d,
    check_probabilities,
    check_sample_weights,
)
from robust_adapt.core.telemetry import (
    get_process_memory_bytes,
    MemoryBudgetTracker,
)
from robust_adapt.core.diagnostics import (
    DiagnosticEvent,
    DiagnosticRegistry,
    clear_diagnostic_events,
    configure_logging,
    get_diagnostic_events,
    record_diagnostic_event,
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
    # Telemetry & Diagnostics
    "get_process_memory_bytes",
    "MemoryBudgetTracker",
    "DiagnosticEvent",
    "DiagnosticRegistry",
    "record_diagnostic_event",
    "get_diagnostic_events",
    "clear_diagnostic_events",
    "configure_logging",
]
