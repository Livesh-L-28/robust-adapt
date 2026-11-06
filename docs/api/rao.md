# API Reference: Resource-Aware Optimization (`adaptive_ml.rao`)

The `adaptive_ml.rao` module provides 8-bit dynamic block quantization, budget enforcement, and resource telemetry profiling.

---

## 1. Class: `LowMemoryAdamW`

```python
class LowMemoryAdamW(
    params: Iterable[Any],
    lr: float = 1e-3,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    weight_decay: float = 1e-2,
    block_size: int = 256,
)
```

CPU-first block-quantized AdamW optimizer achieving 74.6% state RAM reduction via int8 momentum and uint8 second moments across blocks of 256 parameters. Fully compatible with PyTorch `torch.optim.Optimizer` and standalone NumPy arrays.

### Methods
- **`step(closure=None) -> Optional[float]`**: Executes a single block-quantized parameter update.
- **`get_state_memory_bytes() -> int`**: Returns the exact memory footprint of all quantized optimizer states in bytes.
- **`state_dict() -> dict`**: Serializes quantized optimizer state tables.

---

## 2. Class: `BlockQuantizer`

```python
class BlockQuantizer(block_size: int = 256)
```

Block-wise dynamic quantizer converting continuous float vectors into signed 8-bit and unsigned 8-bit representations.

### Methods
- **`quantize_signed(vector: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`**: Quantizes signed values (e.g. momentum) into int8 array and block float32 scale factors.
- **`dequantize_signed(q_vector: np.ndarray, scales: np.ndarray) -> np.ndarray`**: Reconstructs float32 array from int8 and scale factors.
- **`quantize_unsigned(vector: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`**: Quantizes non-negative values (e.g. variance) into uint8 array and block scales.
- **`dequantize_unsigned(q_vector: np.ndarray, scales: np.ndarray) -> np.ndarray`**: Reconstructs float32 array from uint8 and scale factors.

---

## 3. Class: `DynamicResourceBudgetManager`

```python
class DynamicResourceBudgetManager(
    max_step_time_ms: float = 100.0,
    max_memory_mb: float = 2048.0,
    min_batch_size: int = 16,
    max_batch_size: int = 512,
    warning_threshold: float = 0.80,
)
```

Multi-dimensional budget manager tracking CPU execution time (ms/step) and resident memory (MB), dynamically throttling micro-batch sizes under resource pressure.

### Properties
- **`current_batch_size`** (`int`): Active recommended micro-batch size.
- **`state`** (`BudgetState`): Current operational state (`NORMAL`, `PRESSURE_WARNING`, `THROTTLED`, `CRITICAL`).

### Methods
- **`evaluate_step(step_time_ms: float) -> BudgetState`**: Updates metrics and adjusts batch size.

---

## 4. Class: `VectorizedLowMemoryAdamW`

```python
class VectorizedLowMemoryAdamW(
    params: Iterable[torch.nn.Parameter],
    lr: float = 1e-3,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    weight_decay: float = 1e-2,
    block_size: int = 256,
)
```

Vectorized PyTorch implementation of block-quantized 8-bit AdamW optimizer. Achieves up to $22\times$ speedup over serial block-by-block quantization loops while maintaining 74.6% memory state compression on CPU.

### Features
- **Vectorized Reshaping**: Quantizes 2D+ weight matrices across flattened contiguous views without serial Python loops.
- **Selective 1D Float32 Preservation**: Keeps 1D vectors (biases, normalization scales) in unquantized float32 to prevent catastrophic scale collapse.
- **Clamped Denominators**: Implements `.clamp_min(1e-4)` before division to eliminate numerical division-by-zero instability.
- **Sparse Gradient Guard**: Validates dense gradient format before clipping, preventing unhandled `NotImplementedError` crashes.
