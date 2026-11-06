"""Custom exception hierarchy for ROBUST-ADAPT.

Certified in Phase 7 Configuration and Error Handling Architecture (DOC-DES-P7-007).
"""


class RobustAdaptError(Exception):
    """Base exception for all errors raised by ROBUST-ADAPT."""

    pass


# Backward-compatibility alias
AdaptiveMLError = RobustAdaptError


class ConfigurationError(RobustAdaptError):
    """Raised when an invalid hyperparameter configuration is provided."""

    pass


class ValidationError(RobustAdaptError):
    """Raised when input tensors violate shape, dtype, or value constraints."""

    pass


class DriftStateError(RobustAdaptError):
    """Raised when an invalid drift detector state transition or window partition occurs."""

    pass


class QuantizationError(RobustAdaptError):
    """Raised when tensor dimensions or block alignments violate quantization rules."""

    pass


class ResourceBudgetExceededError(RobustAdaptError):
    """Raised when allocated memory or compute exceeds the user-configured ceiling."""

    pass


class NumericalInstabilityError(RobustAdaptError):
    """Raised when NaN, Inf, or unrecoverable numerical degeneracy is encountered."""

    pass


class SerializationError(RobustAdaptError):
    """Raised when state serialization or deserialization fails or encounters invalid payloads."""

    pass
