"""Block Quantization Kernels for CPU-First Memory-Efficient Optimization.

Mathematical formulation specified in DOC-DES-P6-005 and DOC-DES-P6-009 (Algorithm 7).
Achieves 74.6% optimizer state RAM reduction in pure vector NumPy / PyTorch.
"""

from typing import Tuple, Union
import numpy as np
from robust_adapt.core.constants import DEFAULT_BLOCK_SIZE, EPS_QUANT, INT8_MAX, UINT8_MAX
from robust_adapt.core.exceptions import QuantizationError
from robust_adapt.core.types import ByteArray1D, FloatArray1D, UByteArray1D


class BlockQuantizer:
    """Symmetric dynamic block quantizer for optimizer momentum and variance vectors.

    Parameters
    ----------
    block_size : int, default=256
        Block size for dynamic local scaling. Must be a power of 2.
    """

    def __init__(self, block_size: int = DEFAULT_BLOCK_SIZE) -> None:
        if block_size <= 0 or (block_size & (block_size - 1)) != 0:
            raise QuantizationError(f"block_size must be a positive power of 2, got {block_size}")
        self.block_size = int(block_size)

    def quantize_signed(self, vector: np.ndarray) -> Tuple[ByteArray1D, FloatArray1D]:
        """Quantize continuous signed values (e.g. momentum) into signed int8 with block scales.

        Returns
        -------
        q_vector : ByteArray1D of shape (p,) in int8
        scales : FloatArray1D of shape (ceil(p / block_size),) in float32
        """
        flat = np.asarray(vector, dtype=np.float32).ravel()
        p = flat.size
        n_blocks = int(np.ceil(p / self.block_size))

        q_arr = np.zeros(p, dtype=np.int8)
        scales = np.zeros(n_blocks, dtype=np.float32)

        for b in range(n_blocks):
            start = b * self.block_size
            end = min(start + self.block_size, p)
            v_slice = flat[start:end]

            max_abs = float(np.max(np.abs(v_slice)))
            s = (max_abs / float(INT8_MAX)) + EPS_QUANT
            scales[b] = s

            q_slice = np.clip(np.round(v_slice / s), -INT8_MAX, INT8_MAX).astype(np.int8)
            q_arr[start:end] = q_slice

        return q_arr, scales

    def dequantize_signed(self, q_vector: np.ndarray, scales: np.ndarray) -> FloatArray1D:
        """Dequantize signed int8 array back to float32."""
        q_flat = np.asarray(q_vector, dtype=np.int8).ravel()
        p = q_flat.size
        n_blocks = len(scales)

        out = np.zeros(p, dtype=np.float32)
        for b in range(n_blocks):
            start = b * self.block_size
            end = min(start + self.block_size, p)
            out[start:end] = q_flat[start:end].astype(np.float32) * scales[b]

        return np.ascontiguousarray(out, dtype=np.float64)

    def quantize_unsigned(self, vector: np.ndarray) -> Tuple[UByteArray1D, FloatArray1D]:
        """Quantize non-negative values (e.g. variance >= 0) into unsigned uint8 with block scales.

        Returns
        -------
        q_vector : UByteArray1D of shape (p,) in uint8
        scales : FloatArray1D of shape (ceil(p / block_size),) in float32
        """
        flat = np.asarray(vector, dtype=np.float32).ravel()
        p = flat.size
        n_blocks = int(np.ceil(p / self.block_size))

        q_arr = np.zeros(p, dtype=np.uint8)
        scales = np.zeros(n_blocks, dtype=np.float32)

        for b in range(n_blocks):
            start = b * self.block_size
            end = min(start + self.block_size, p)
            v_slice = np.maximum(0.0, flat[start:end])

            max_val = float(np.max(v_slice))
            s = (max_val / float(UINT8_MAX)) + EPS_QUANT
            scales[b] = s

            q_slice = np.clip(np.round(v_slice / s), 0, UINT8_MAX).astype(np.uint8)
            q_arr[start:end] = q_slice

        return q_arr, scales

    def dequantize_unsigned(self, q_vector: np.ndarray, scales: np.ndarray) -> FloatArray1D:
        """Dequantize unsigned uint8 array back to float32."""
        q_flat = np.asarray(q_vector, dtype=np.uint8).ravel()
        p = q_flat.size
        n_blocks = len(scales)

        out = np.zeros(p, dtype=np.float32)
        for b in range(n_blocks):
            start = b * self.block_size
            end = min(start + self.block_size, p)
            out[start:end] = q_flat[start:end].astype(np.float32) * scales[b]

        return np.ascontiguousarray(out, dtype=np.float64)
