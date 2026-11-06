# RAO 2.0: Configuration Reference

This guide details configuration parameters for `VectorizedLowMemoryAdamW` and `LowMemoryAdamW`.

---

## `VectorizedLowMemoryAdamW` Parameters (PyTorch)

```python
from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW

optimizer = VectorizedLowMemoryAdamW(
    params=model.parameters(),
    lr=1e-3,
    betas=(0.9, 0.999),
    eps=1e-4,
    weight_decay=1e-2,
    block_size=64,
    max_grad_norm=1.0,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`params`** | `Iterable[Tensor] \| List[dict]` | *Required* | Parameters or parameter groups to optimize. |
| **`lr`** | `float` | `1e-3` | Learning rate ($\eta > 0$). |
| **`betas`** | `Tuple[float, float]` | `(0.9, 0.999)` | Coefficients for computing running averages of gradient and square ($0 \le \beta < 1$). |
| **`eps`** | `float` | `1e-4` | Numerical stability epsilon added to denominator. |
| **`weight_decay`** | `float` | `1e-2` | Decoupled weight decay coefficient ($\lambda \ge 0$). |
| **`block_size`** | `int` | `64` | Block size for tensor quantization ($B_q$, must be a power of 2). |
| **`max_grad_norm`** | `Optional[float]` | `1.0` | Maximum gradient norm for built-in gradient clipping (set to `None` to disable). |

---

## `LowMemoryAdamW` Parameters (NumPy)

```python
from robust_adapt.rao.adamw import LowMemoryAdamW

optimizer = LowMemoryAdamW(
    params=[weight_array, bias_array],
    lr=1e-3,
    betas=(0.9, 0.999),
    eps=1e-8,
    weight_decay=1e-2,
    block_size=256,
)
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`block_size`** | `int` | `256` | Block size for CPU NumPy vector quantization. |
| **`eps`** | `float` | `1e-8` | Float64 numerical stability term. |
