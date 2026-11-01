"""Unit tests for Phase 10 RAO (Resource-Aware Optimization)."""

import pytest
import numpy as np
from adaptive_ml.rao.quantizer import BlockQuantizer
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rao.accumulator import AdaptiveGradientAccumulator
from adaptive_ml.rao.memory import ResourceBudget
from adaptive_ml.core.exceptions import ConfigurationError, QuantizationError, ResourceBudgetExceededError

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


class TestBlockQuantizer:
    """Tests for BlockQuantizer."""

    def test_signed_quantization_roundtrip_bound(self) -> None:
        """Verify quantization error is bounded by scale / 2."""
        quantizer = BlockQuantizer(block_size=256)
        rng = np.random.default_rng(42)

        # Vector with 1024 elements (4 blocks)
        vec = rng.normal(loc=0.0, scale=1.5, size=1024).astype(np.float32)
        q_vec, scales = quantizer.quantize_signed(vec)

        assert q_vec.dtype == np.int8
        assert q_vec.shape == (1024,)
        assert scales.shape == (4,)

        dequant = quantizer.dequantize_signed(q_vec, scales).astype(np.float32)

        # Max error in block b must be <= scales[b] / 2
        for b in range(4):
            start = b * 256
            end = start + 256
            block_err = np.max(np.abs(vec[start:end] - dequant[start:end]))
            assert block_err <= (scales[b] / 2.0) + 1e-6

    def test_unsigned_quantization(self) -> None:
        quantizer = BlockQuantizer(block_size=128)
        rng = np.random.default_rng(42)

        # Variance vector >= 0
        vec = np.abs(rng.normal(loc=2.0, scale=1.0, size=512)).astype(np.float32)
        q_vec, scales = quantizer.quantize_unsigned(vec)

        assert q_vec.dtype == np.uint8
        assert np.all(q_vec >= 0)
        assert np.all(q_vec <= 255)

        dequant = quantizer.dequantize_unsigned(q_vec, scales).astype(np.float32)
        max_err = np.max(np.abs(vec - dequant))
        assert max_err < 0.10

    def test_invalid_block_size(self) -> None:
        with pytest.raises(QuantizationError):
            BlockQuantizer(block_size=100)  # Not a power of 2


class TestLowMemoryAdamW:
    """Tests for LowMemoryAdamW."""

    def test_numpy_convergence_on_quadratic_bowl(self) -> None:
        """Verify convergence on f(w) = ||w - w*||^2 in pure NumPy."""
        w_star = np.array([3.0, -2.0, 1.5], dtype=np.float32)
        w = np.zeros(3, dtype=np.float32)

        class ParamWrapper:
            def __init__(self, arr: np.ndarray) -> None:
                self.arr = arr
                self.grad = np.zeros_like(arr)

            @property
            def data(self) -> np.ndarray:
                return self.arr

        p = ParamWrapper(w)
        optimizer = LowMemoryAdamW([p], lr=0.1, weight_decay=0.0, block_size=32)

        for step in range(100):
            # Gradient: 2 * (w - w*)
            p.grad = 2.0 * (p.arr - w_star)
            optimizer.step()

        # Should converge close to w_star
        err = np.linalg.norm(p.arr - w_star)
        assert err < 0.05, f"Convergence error too large: {err}"

    def test_state_memory_savings(self) -> None:
        """Verify that optimizer states consume only ~2.031 bytes per parameter vs 8.0 bytes standard."""
        num_params = 10240  # 10k parameters
        param = np.zeros(num_params, dtype=np.float32)
        grad = np.ones(num_params, dtype=np.float32)

        optimizer = LowMemoryAdamW([param], lr=1e-3, block_size=256)
        # Execute 1 step to allocate state
        optimizer._step_numpy(param, grad, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, wd=0.01, B_q=256)

        actual_bytes = optimizer.get_state_memory_bytes()
        # In float32 AdamW, states (m + v) take: 10240 * 8 = 81,920 bytes
        standard_bytes = num_params * 8
        # In LowMemoryAdamW, states take: 10240 (int8) + 10240 (uint8) + 40*4 (scales_m) + 40*4 (scales_v) = 20,800 bytes
        expected_quant_bytes = num_params * 2 + int(np.ceil(num_params / 256)) * 8

        assert actual_bytes == expected_quant_bytes
        savings = (standard_bytes - actual_bytes) / standard_bytes
        # Savings must be >= 74%
        assert savings > 0.74, f"Memory savings {savings:.2%} must exceed 74%"

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch not available")
    def test_torch_optimizer_integration(self) -> None:
        """Verify seamless integration as a standard torch.optim.Optimizer."""
        model = nn.Linear(4, 1)
        optimizer = LowMemoryAdamW(model.parameters(), lr=0.05, block_size=32)

        # Synthetic regression
        x = torch.randn(20, 4)
        target = torch.randn(20, 1)
        criterion = nn.MSELoss()

        initial_loss = criterion(model(x), target).item()

        for _ in range(30):
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, target)
            loss.backward()
            optimizer.step()

        final_loss = criterion(model(x), target).item()
        assert final_loss < initial_loss, f"Loss did not decrease: {initial_loss} -> {final_loss}"


class TestAdaptiveGradientAccumulator:
    """Tests for AdaptiveGradientAccumulator."""

    def test_gradient_accumulation_equivalence(self) -> None:
        """Verify that accumulating 4 micro-batches yields exact target batch gradient."""
        accum = AdaptiveGradientAccumulator(target_batch_size=40, initial_phys_batch_size=10)
        assert accum.accumulation_steps == 4

        # 4 micro-batches of gradients
        rng = np.random.default_rng(42)
        micro_grads = [rng.normal(size=10) for _ in range(4)]

        # Direct mathematical average of all 4 micro-batches
        direct_avg = np.mean(micro_grads, axis=0)

        # Simulated accumulation
        ready = False
        for g in micro_grads:
            accum.accumulate_numpy(param_id=0, grad=g)
            ready = accum.step_completed()

        assert ready is True
        accum_avg = accum.accumulated_gradients[0]
        assert np.allclose(accum_avg, direct_avg, atol=1e-6)


class TestResourceBudget:
    """Tests for ResourceBudget."""

    def test_step_budget_exceeded(self) -> None:
        budget = ResourceBudget(max_steps=5)
        for _ in range(5):
            budget.check_and_increment_step()

        with pytest.raises(ResourceBudgetExceededError):
            budget.check_and_increment_step()
