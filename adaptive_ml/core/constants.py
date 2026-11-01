"""Numerical constants, epsilon guards, and stability bounds for AdaptiveML.

Certified in Phase 6 Mathematical Verification Report (DOC-DES-P6-010).
"""

from typing import Final

# Denominator and division safety guards
EPS_DIV: Final[float] = 1e-12
EPS_VAR: Final[float] = 1e-8
EPS_SOFTMAX: Final[float] = 1e-12
EPS_LOG: Final[float] = 1e-12

# RLA Robust Loss Constants
EPS_CLIP_RCE: Final[float] = 1e-4
EPS_RELIABILITY: Final[float] = 1e-4

# RAO Quantization Constants
EPS_QUANT: Final[float] = 1e-12
DEFAULT_BLOCK_SIZE: Final[int] = 256
INT8_MAX: Final[int] = 127
UINT8_MAX: Final[int] = 255

# ULC Arbitration Constants
DEFAULT_TAU_R: Final[float] = 0.65
DEFAULT_DELTA_HYST: Final[float] = 0.15
DEFAULT_RECOVERY_STEPS: Final[int] = 100
