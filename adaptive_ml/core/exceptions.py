"""Custom exception hierarchy for AdaptiveML.

Certified in Phase 7 Configuration and Error Handling Architecture (DOC-DES-P7-007).
"""


class AdaptiveMLError(Exception):
    """Base exception for all errors raised by AdaptiveML."""

    pass


class ConfigurationError(AdaptiveMLError):
    """Raised when an invalid hyperparameter configuration is provided."""

    pass


class ValidationError(AdaptiveMLError):
    """Raised when input tensors violate shape, dtype, or value constraints."""

    pass


class DriftStateError(AdaptiveMLError):
    """Raised when an invalid drift detector state transition or window partition occurs."""

    pass


class QuantizationError(AdaptiveMLError):
    """Raised when tensor dimensions or block alignments violate quantization rules."""

    pass


class ResourceBudgetExceededError(AdaptiveMLError):
    """Raised when allocated memory or compute exceeds the user-configured ceiling."""

    pass


class NumericalInstabilityError(AdaptiveMLError):
    """Raised when NaN, Inf, or unrecoverable numerical degeneracy is encountered."""

    pass


class SerializationError(AdaptiveMLError):
    """Raised when state serialization or deserialization fails or encounters invalid payloads."""

    pass

