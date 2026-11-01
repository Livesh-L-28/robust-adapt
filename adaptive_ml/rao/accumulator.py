"""Adaptive Dynamic Gradient Accumulator.

Mathematical formulation specified in DOC-DES-P6-005.
Preserves exact mathematical gradient equivalence while dynamically scheduling micro-batches under memory constraints.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from adaptive_ml.core.exceptions import ValidationError
from adaptive_ml.core.telemetry import MemoryBudgetTracker


class AdaptiveGradientAccumulator:
    """Dynamically schedules gradient accumulation micro-batches to respect host RAM ceilings.

    Parameters
    ----------
    target_batch_size : int
        Target effective batch size required for mathematical training stability.
    initial_phys_batch_size : int, default=32
        Initial physical mini-batch size executed per forward-backward step.
    memory_tracker : Optional[MemoryBudgetTracker], default=None
        Tracker for monitoring host RAM pressure.
    """

    def __init__(
        self,
        target_batch_size: int,
        initial_phys_batch_size: int = 32,
        memory_tracker: Optional[MemoryBudgetTracker] = None,
    ) -> None:
        if target_batch_size <= 0:
            raise ValidationError(f"target_batch_size must be positive, got {target_batch_size}")
        if initial_phys_batch_size <= 0:
            raise ValidationError(f"initial_phys_batch_size must be positive, got {initial_phys_batch_size}")

        self.target_batch_size = int(target_batch_size)
        self.phys_batch_size = min(int(initial_phys_batch_size), self.target_batch_size)
        self.memory_tracker = memory_tracker or MemoryBudgetTracker()

        self._recompute_steps()
        self.current_micro_step: int = 0
        self.accumulated_gradients: Dict[int, np.ndarray] = {}

    def _recompute_steps(self) -> None:
        """Compute accumulation steps K = ceil(target / phys)."""
        self.accumulation_steps = int(np.ceil(self.target_batch_size / self.phys_batch_size))
        self.effective_batch_size = self.accumulation_steps * self.phys_batch_size

    def check_memory_and_adapt(self) -> bool:
        """Check host RAM and dynamically halve physical batch size if memory pressure is active."""
        if self.memory_tracker.is_pressure_active() and self.phys_batch_size > 1:
            self.phys_batch_size = max(1, self.phys_batch_size // 2)
            self._recompute_steps()
            return True
        return False

    def accumulate_numpy(self, param_id: int, grad: np.ndarray) -> None:
        """Accumulate gradient into running sum for given parameter."""
        scale = 1.0 / float(self.accumulation_steps)
        scaled_g = grad * scale

        if param_id not in self.accumulated_gradients:
            self.accumulated_gradients[param_id] = scaled_g.copy()
        else:
            self.accumulated_gradients[param_id] += scaled_g

    def step_completed(self) -> bool:
        """Advance micro-step counter and return True if target batch is ready for optimizer step."""
        self.current_micro_step += 1
        if self.current_micro_step >= self.accumulation_steps:
            self.current_micro_step = 0
            return True
        return False

    def reset_accumulated(self) -> None:
        """Clear accumulated gradient buffers."""
        self.accumulated_gradients.clear()
        self.current_micro_step = 0

