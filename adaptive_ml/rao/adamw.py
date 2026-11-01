"""LowMemoryAdamW: CPU Block-Quantized AdamW Optimizer.

Mathematical formulation specified in DOC-DES-P6-005 and DOC-DES-P6-009 (Algorithm 7).
Achieves 74.6% optimizer state RAM reduction via pure vector block quantization (int8/uint8).
Zero mandatory C++ compiler or CUDA dependencies.
"""

import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
import numpy as np
from adaptive_ml.core.constants import DEFAULT_BLOCK_SIZE, EPS_QUANT, INT8_MAX, UINT8_MAX
from adaptive_ml.core.exceptions import ConfigurationError, ValidationError
from adaptive_ml.rao.quantizer import BlockQuantizer

try:
    import torch
    from torch.optim import Optimizer as TorchOptimizer
    _TORCH_AVAILABLE = True
except ImportError:
    class TorchOptimizer:  # type: ignore[no-redef]
        def __init__(self, params: Any, defaults: Dict[str, Any]) -> None:
            self.param_groups = [{"params": list(params), **defaults}]
            self.state: Dict[Any, Any] = {}
            self.defaults = defaults
    _TORCH_AVAILABLE = False


class LowMemoryAdamW(TorchOptimizer):
    """CPU-first block-quantized AdamW optimizer achieving 74.6% state memory reduction.

    Quantizes first-order moments into signed 8-bit integers (int8) and second-order
    moments into unsigned 8-bit integers (uint8) over 256-element blocks.

    Parameters
    ----------
    params : Iterable[Any]
        Iterable of parameters (PyTorch Tensors or NumPy ndarrays) to optimize.
    lr : float, default=1e-3
        Learning rate.
    betas : Tuple[float, float], default=(0.9, 0.999)
        Coefficients for computing running averages of gradient and its square.
    eps : float, default=1e-8
        Numerical stability epsilon.
    weight_decay : float, default=1e-2
        Decoupled weight decay coefficient.
    block_size : int, default=256
        Block size for dynamic quantization. Must be a power of 2.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 1e-3,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 1e-2,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> None:
        if lr <= 0.0:
            raise ConfigurationError(f"lr must be positive, got {lr}")
        if not 0.0 <= betas[0] < 1.0 or not 0.0 <= betas[1] < 1.0:
            raise ConfigurationError(f"betas must be in [0, 1), got {betas}")
        if eps <= 0.0:
            raise ConfigurationError(f"eps must be positive, got {eps}")
        if weight_decay < 0.0:
            raise ConfigurationError(f"weight_decay must be non-negative, got {weight_decay}")
        if block_size <= 0 or (block_size & (block_size - 1)) != 0:
            raise ConfigurationError(f"block_size must be a power of 2, got {block_size}")

        defaults = dict(
            lr=float(lr),
            betas=betas,
            eps=float(eps),
            weight_decay=float(weight_decay),
            block_size=int(block_size),
        )

        self.block_size = int(block_size)
        self.quantizer = BlockQuantizer(block_size=self.block_size)

        # Inspect if params contains PyTorch tensors or NumPy arrays
        param_list = list(params)
        has_torch_tensors = False
        if _TORCH_AVAILABLE and len(param_list) > 0:
            first = param_list[0]
            if isinstance(first, dict) and "params" in first:
                first = list(first["params"])[0] if len(first["params"]) > 0 else None
            if isinstance(first, torch.Tensor):
                has_torch_tensors = True

        if has_torch_tensors:
            super().__init__(param_list, defaults)
        else:
            # Standalone NumPy optimizer initialization
            if _TORCH_AVAILABLE:
                from collections import OrderedDict
                self._optimizer_step_pre_hooks = OrderedDict()
                self._optimizer_step_post_hooks = OrderedDict()
                self._optimizer_state_dict_pre_hooks = OrderedDict()
                self._optimizer_state_dict_post_hooks = OrderedDict()
                self._optimizer_load_state_dict_pre_hooks = OrderedDict()
                self._optimizer_load_state_dict_post_hooks = OrderedDict()
            self.param_groups = [{"params": param_list, **defaults}]
            self.state = {}
            self.defaults = defaults

    def step(self, closure: Optional[Callable[[], float]] = None) -> Optional[float]:
        """Perform a single optimization step using block-quantized updates."""
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            lr = group["lr"]
            beta1, beta2 = group["betas"]
            eps = group["eps"]
            wd = group["weight_decay"]
            B_q = group["block_size"]

            for p in group["params"]:
                # Check gradient presence
                grad = getattr(p, "grad", None)
                if grad is None:
                    continue

                if _TORCH_AVAILABLE and isinstance(p, torch.Tensor):
                    self._step_torch(p, grad, lr, beta1, beta2, eps, wd, B_q)
                elif isinstance(p, np.ndarray):
                    self._step_numpy(p, grad, lr, beta1, beta2, eps, wd, B_q)
                elif hasattr(p, "data") and isinstance(p.data, np.ndarray):
                    self._step_numpy(p.data, grad, lr, beta1, beta2, eps, wd, B_q)
                else:
                    # Fallback for generic objects
                    pass

        return loss

    def _step_numpy(
        self,
        param: np.ndarray,
        grad: np.ndarray,
        lr: float,
        beta1: float,
        beta2: float,
        eps: float,
        wd: float,
        B_q: int,
    ) -> None:
        """Execute block-quantized step on NumPy array."""
        state = self.state.setdefault(id(param), {})

        p_flat = param.ravel()
        g_flat = grad.ravel()
        numel = p_flat.size
        n_blocks = int(np.ceil(numel / B_q))

        if "step" not in state:
            state["step"] = 0
            state["q_m"] = np.zeros(numel, dtype=np.int8)
            state["q_v"] = np.zeros(numel, dtype=np.uint8)
            state["scale_m"] = np.zeros(n_blocks, dtype=np.float32)
            state["scale_v"] = np.zeros(n_blocks, dtype=np.float32)

        state["step"] += 1
        t = state["step"]
        bias_correction1 = 1.0 - (beta1 ** t)
        bias_correction2 = 1.0 - (beta2 ** t)

        q_m = state["q_m"]
        q_v = state["q_v"]
        scale_m = state["scale_m"]
        scale_v = state["scale_v"]

        for b in range(n_blocks):
            start = b * B_q
            end = min(start + B_q, numel)

            # Dequantize moments for current block b
            s_m = scale_m[b]
            s_v = scale_v[b]
            m_slice = q_m[start:end].astype(np.float32) * s_m
            v_slice = q_v[start:end].astype(np.float32) * s_v
            g_slice = g_flat[start:end].astype(np.float32)

            # Standard AdamW update equations
            m_new = beta1 * m_slice + (1.0 - beta1) * g_slice
            v_new = beta2 * v_slice + (1.0 - beta2) * (g_slice ** 2)

            # Bias-corrected estimates
            m_hat = m_new / bias_correction1
            v_hat = v_new / bias_correction2

            # Parameter update with decoupled weight decay
            p_slice = p_flat[start:end]
            if wd > 0.0:
                p_slice -= lr * wd * p_slice
            p_slice -= lr * (m_hat / (np.sqrt(v_hat) + eps))
            p_flat[start:end] = p_slice

            # Re-quantize moments back to int8 / uint8
            max_abs_m = float(np.max(np.abs(m_new)))
            new_s_m = (max_abs_m / float(INT8_MAX)) + EPS_QUANT
            q_m[start:end] = np.clip(np.round(m_new / new_s_m), -INT8_MAX, INT8_MAX).astype(np.int8)
            scale_m[b] = new_s_m

            max_v = float(np.max(v_new))
            new_s_v = (max_v / float(UINT8_MAX)) + EPS_QUANT
            q_v[start:end] = np.clip(np.round(v_new / new_s_v), 0, UINT8_MAX).astype(np.uint8)
            scale_v[b] = new_s_v

    def _step_torch(
        self,
        param: "torch.Tensor",
        grad: "torch.Tensor",
        lr: float,
        beta1: float,
        beta2: float,
        eps: float,
        wd: float,
        B_q: int,
    ) -> None:
        """Execute block-quantized step on PyTorch Tensor with zero host transfers."""
        state = self.state.setdefault(param, {})

        p_flat = param.data.view(-1)
        g_flat = grad.data.view(-1)
        numel = p_flat.numel()
        n_blocks = int(math.ceil(numel / B_q))

        if "step" not in state:
            state["step"] = 0
            state["q_m"] = torch.zeros(numel, dtype=torch.int8, device=param.device)
            state["q_v"] = torch.zeros(numel, dtype=torch.uint8, device=param.device)
            state["scale_m"] = torch.zeros(n_blocks, dtype=torch.float32, device=param.device)
            state["scale_v"] = torch.zeros(n_blocks, dtype=torch.float32, device=param.device)

        state["step"] += 1
        t = state["step"]
        bias_correction1 = 1.0 - (beta1 ** t)
        bias_correction2 = 1.0 - (beta2 ** t)

        q_m = state["q_m"]
        q_v = state["q_v"]
        scale_m = state["scale_m"]
        scale_v = state["scale_v"]

        for b in range(n_blocks):
            start = b * B_q
            end = min(start + B_q, numel)

            s_m = scale_m[b]
            s_v = scale_v[b]
            m_slice = q_m[start:end].to(torch.float32) * s_m
            v_slice = q_v[start:end].to(torch.float32) * s_v
            g_slice = g_flat[start:end].to(torch.float32)

            m_new = beta1 * m_slice + (1.0 - beta1) * g_slice
            v_new = beta2 * v_slice + (1.0 - beta2) * (g_slice ** 2)

            m_hat = m_new / bias_correction1
            v_hat = v_new / bias_correction2

            p_slice = p_flat[start:end]
            if wd > 0.0:
                p_slice.mul_(1.0 - lr * wd)
            p_slice.addcdiv_(m_hat, torch.sqrt(v_hat).add_(eps), value=-lr)

            # Re-quantize in-place
            max_abs_m = torch.max(torch.abs(m_new))
            new_s_m = (max_abs_m / float(INT8_MAX)) + EPS_QUANT
            q_m[start:end] = torch.clamp(torch.round(m_new / new_s_m), -INT8_MAX, INT8_MAX).to(torch.int8)
            scale_m[b] = new_s_m

            max_v = torch.max(v_new)
            new_s_v = (max_v / float(UINT8_MAX)) + EPS_QUANT
            q_v[start:end] = torch.clamp(torch.round(v_new / new_s_v), 0, UINT8_MAX).to(torch.uint8)
            scale_v[b] = new_s_v

    def get_state_memory_bytes(self) -> int:
        """Compute the exact memory footprint of all quantized optimizer states."""
        total_bytes = 0
        for p, s in self.state.items():
            if "q_m" in s:
                q_m = s["q_m"]
                q_v = s["q_v"]
                s_m = s["scale_m"]
                s_v = s["scale_v"]
                if hasattr(q_m, "nbytes"):
                    total_bytes += q_m.nbytes + q_v.nbytes + s_m.nbytes + s_v.nbytes
                elif hasattr(q_m, "element_size"):
                    total_bytes += (
                        q_m.element_size() * q_m.numel()
                        + q_v.element_size() * q_v.numel()
                        + s_m.element_size() * s_m.numel()
                        + s_v.element_size() * s_v.numel()
                    )
        return total_bytes
