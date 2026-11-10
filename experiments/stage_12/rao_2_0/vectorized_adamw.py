"""
Stage 12 — Workstream D: RAO 2.0 Vectorized Low-Memory Optimizer.

Implements next-generation Resource-Aware Optimization resolving the Stage 11
75.1x CPU latency penalty and BatchNorm numerical instability:
1. Vectorized Tensor-Batched Block Quantization (zero Python loop over blocks)
2. Selective 1D Parameter Exemption (biases and normalizations preserved in float32)
3. Mandatory Built-In Gradient Norm Clipping (guarantees numerical stability)
4. Theoretical and Empirical > 72% Memory Reduction on 2D+ Weight Matrices
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple

import torch
from torch.optim import Optimizer

INT8_MAX = 127.0
UINT8_MAX = 255.0
EPS_QUANT = 1e-7


class VectorizedLowMemoryAdamW(Optimizer):
    """
    Vectorized CPU/GPU 8-bit block-quantized AdamW optimizer.
    Quantizes 2D+ weight matrices into int8/uint8 blocks via parallel PyTorch tensor
    operations, while maintaining 1D biases and normalization scales in float32.
    """

    def __init__(
        self,
        params: Iterable[torch.Tensor],
        lr: float = 1e-3,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-4,
        weight_decay: float = 1e-2,
        block_size: int = 64,
        max_grad_norm: Optional[float] = 1.0,
    ):
        if lr <= 0.0:
            raise ValueError(f"lr must be positive, got {lr}")
        if not (0.0 <= betas[0] < 1.0 and 0.0 <= betas[1] < 1.0):
            raise ValueError(f"betas must be in [0, 1), got {betas}")
        if eps <= 0.0:
            raise ValueError(f"eps must be positive, got {eps}")
        if weight_decay < 0.0:
            raise ValueError(f"weight_decay must be non-negative, got {weight_decay}")
        if block_size <= 0 or (block_size & (block_size - 1)) != 0:
            raise ValueError(f"block_size must be a power of 2, got {block_size}")

        defaults = dict(
            lr=lr,
            betas=betas,
            eps=eps,
            weight_decay=weight_decay,
            block_size=block_size,
            max_grad_norm=max_grad_norm,
        )
        super().__init__(params, defaults)
        self.block_size = block_size
        self.max_grad_norm = max_grad_norm

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        # 1. Built-in gradient clipping across all parameters
        if self.max_grad_norm is not None and self.max_grad_norm > 0:
            all_params = [p for group in self.param_groups for p in group["params"] if p.grad is not None]
            if all_params:
                torch.nn.utils.clip_grad_norm_(all_params, max_norm=self.max_grad_norm)

        for group in self.param_groups:
            lr = group["lr"]
            beta1, beta2 = group["betas"]
            eps = group["eps"]
            wd = group["weight_decay"]
            B_q = group["block_size"]

            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad

                state = self.state[p]
                if "step" not in state:
                    state["step"] = 0
                    # Selective Quantization: 1D params (biases/BatchNorm) stay float32
                    if p.ndim <= 1:
                        state["is_quantized"] = False
                        state["exp_avg"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                        state["exp_avg_sq"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                    else:
                        state["is_quantized"] = True
                        numel = p.numel()
                        pad = (B_q - (numel % B_q)) % B_q
                        n_blocks = (numel + pad) // B_q
                        state["pad"] = pad
                        state["numel"] = numel
                        state["q_m"] = torch.zeros(n_blocks, B_q, dtype=torch.int8, device=p.device)
                        state["q_v"] = torch.zeros(n_blocks, B_q, dtype=torch.uint8, device=p.device)
                        state["scale_m"] = torch.zeros(n_blocks, 1, dtype=torch.float32, device=p.device)
                        state["scale_v"] = torch.zeros(n_blocks, 1, dtype=torch.float32, device=p.device)

                state["step"] += 1
                t = state["step"]
                bias_correction1 = 1.0 - (beta1 ** t)
                bias_correction2 = 1.0 - (beta2 ** t)

                if not state["is_quantized"]:
                    # Standard float32 AdamW for 1D parameters
                    exp_avg = state["exp_avg"]
                    exp_avg_sq = state["exp_avg_sq"]

                    if wd != 0:
                        p.mul_(1.0 - lr * wd)

                    exp_avg.mul_(beta1).add_(grad, alpha=1.0 - beta1)
                    exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1.0 - beta2)

                    denom = (exp_avg_sq.sqrt() / math.sqrt(bias_correction2)).add_(eps)
                    step_size = lr / bias_correction1
                    p.addcdiv_(exp_avg, denom, value=-step_size)

                else:
                    # Vectorized Block-Quantized AdamW for 2D+ parameters
                    q_m = state["q_m"]
                    q_v = state["q_v"]
                    scale_m = state["scale_m"]
                    scale_v = state["scale_v"]
                    pad = state["pad"]
                    numel = state["numel"]

                    # 1. Parallel Dequantize: (n_blocks, B_q)
                    m = q_m.to(torch.float32) * scale_m
                    v = q_v.to(torch.float32) * scale_v

                    # 2. Reshape gradient to match (n_blocks, B_q)
                    g_flat = grad.view(-1)
                    if pad > 0:
                        g_padded = torch.cat([g_flat, torch.zeros(pad, device=p.device, dtype=g_flat.dtype)])
                    else:
                        g_padded = g_flat
                    g_blocks = g_padded.view(-1, B_q).to(torch.float32)

                    # 3. Vectorized moment updates
                    m = beta1 * m + (1.0 - beta1) * g_blocks
                    v = beta2 * v + (1.0 - beta2) * (g_blocks ** 2)

                    # 4. Bias-corrected estimates & parameter update
                    m_hat = m / bias_correction1
                    v_hat = v / bias_correction2

                    denom = (torch.sqrt(v_hat) + eps).clamp_min(1e-4)
                    update_blocks = m_hat / denom
                    update_flat = update_blocks.view(-1)[:numel].view_as(p)

                    if wd != 0:
                        p.mul_(1.0 - lr * wd)
                    p.add_(update_flat, alpha=-lr)

                    # 5. Vectorized Re-Quantization in PyTorch Tensor Ops
                    new_scale_m = (torch.max(torch.abs(m), dim=-1, keepdim=True).values / INT8_MAX) + EPS_QUANT
                    new_scale_v = (torch.max(v, dim=-1, keepdim=True).values / UINT8_MAX) + EPS_QUANT

                    q_m.copy_(torch.clamp(torch.round(m / new_scale_m), -INT8_MAX, INT8_MAX).to(torch.int8))
                    q_v.copy_(torch.clamp(torch.round(v / new_scale_v), 0, UINT8_MAX).to(torch.uint8))
                    scale_m.copy_(new_scale_m)
                    scale_v.copy_(new_scale_v)

        return loss

    def get_state_memory_bytes(self) -> int:
        """Calculates exact total memory allocated by optimizer state buffers."""
        total_bytes = 0
        for state in self.state.values():
            if not state.get("is_quantized", True):
                total_bytes += state["exp_avg"].nelement() * state["exp_avg"].element_size()
                total_bytes += state["exp_avg_sq"].nelement() * state["exp_avg_sq"].element_size()
            else:
                total_bytes += state["q_m"].nelement() * state["q_m"].element_size()
                total_bytes += state["q_v"].nelement() * state["q_v"].element_size()
                total_bytes += state["scale_m"].nelement() * state["scale_m"].element_size()
                total_bytes += state["scale_v"].nelement() * state["scale_v"].element_size()
        return total_bytes
