"""Dynamic Multi-Dimensional Resource Budget Manager.

Provides dynamic budget management across CPU execution time (ms/step),
process RAM memory footprint (MB), micro-batch sizing, and adaptive operation shedding
(e.g., skipping expensive tree split scans or scaling replay ratios under memory pressure).
"""

from enum import Enum
from typing import Any, Dict, Optional
import numpy as np

from robust_adapt.core.exceptions import (
    ConfigurationError,
    ResourceBudgetExceededError,
    ValidationError,
)
from robust_adapt.core.telemetry import get_process_memory_bytes


class BudgetState(str, Enum):
    """Discrete state of resource constraints."""
    NORMAL = "NORMAL"
    PRESSURE_WARNING = "PRESSURE_WARNING"
    THROTTLED = "THROTTLED"
    CRITICAL = "CRITICAL"


class DynamicResourceBudgetManager:
    """Manages multi-dimensional execution constraints and dynamic operation shedding.

    Parameters
    ----------
    max_step_time_ms : float, default=100.0
        Target execution latency ceiling per training step in milliseconds.
    max_memory_mb : float, default=2048.0
        Maximum allowable process RSS memory footprint in megabytes.
    min_batch_size : int, default=16
        Minimum allowable micro-batch size under throttling.
    max_batch_size : int, default=512
        Maximum allowable micro-batch size under unconstrained execution.
    warning_threshold : float, default=0.80
        Budget utilization fraction triggering PRESSURE_WARNING.
    """

    def __init__(
        self,
        max_step_time_ms: float = 100.0,
        max_memory_mb: float = 2048.0,
        min_batch_size: int = 16,
        max_batch_size: int = 512,
        warning_threshold: float = 0.80,
    ) -> None:
        if max_step_time_ms <= 0.0:
            raise ConfigurationError(f"max_step_time_ms must be positive, got {max_step_time_ms}")
        if max_memory_mb <= 0.0:
            raise ConfigurationError(f"max_memory_mb must be positive, got {max_memory_mb}")
        if min_batch_size < 1 or min_batch_size > max_batch_size:
            raise ConfigurationError(f"Invalid batch size bounds: [{min_batch_size}, {max_batch_size}]")

        self.max_step_time_ms = float(max_step_time_ms)
        self.max_memory_bytes = int(max_memory_mb * (1024 ** 2))
        self.min_batch_size = int(min_batch_size)
        self.max_batch_size = int(max_batch_size)
        self.warning_threshold = float(warning_threshold)

        # Operational state
        self.state: BudgetState = BudgetState.NORMAL
        self.current_batch_size: int = self.max_batch_size
        self._last_step_time_ms: float = 0.0
        self._last_memory_bytes: int = 0
        self.total_steps: int = 0
        self.throttled_steps: int = 0

    @property
    def current_memory_mb(self) -> float:
        """Current process resident memory in megabytes."""
        return float(get_process_memory_bytes() / (1024 ** 2))

    def evaluate_step(self, step_time_ms: float) -> BudgetState:
        """Evaluate resource utilization following an execution step.

        Parameters
        ----------
        step_time_ms : float
            Elapsed execution time of the step in milliseconds.

        Returns
        -------
        BudgetState
            Updated budget operational state.
        """
        step_time_float = float(step_time_ms)
        if step_time_float < 0.0 or not np.isfinite(step_time_float):
            raise ValidationError(
                f"step_time_ms must be a non-negative finite float, got {step_time_ms}"
            )

        self.total_steps += 1
        self._last_step_time_ms = step_time_float
        current_mem = get_process_memory_bytes()
        self._last_memory_bytes = current_mem

        time_ratio = step_time_float / self.max_step_time_ms
        mem_ratio = current_mem / max(1, self.max_memory_bytes)
        max_utilization = max(time_ratio, mem_ratio)

        if max_utilization >= 1.0:
            self.state = BudgetState.CRITICAL
            self.throttled_steps += 1
            # Shrink batch size by 50%
            self.current_batch_size = max(self.min_batch_size, self.current_batch_size // 2)
        elif max_utilization >= self.warning_threshold:
            self.state = BudgetState.PRESSURE_WARNING
            # Slightly scale down batch size
            self.current_batch_size = max(self.min_batch_size, int(self.current_batch_size * 0.85))
        else:
            self.state = BudgetState.NORMAL
            # Gradually recover batch size towards max
            if self.current_batch_size < self.max_batch_size:
                self.current_batch_size = min(self.max_batch_size, int(self.current_batch_size * 1.10))

        return self.state

    def should_skip_expensive_ops(self) -> bool:
        """Predicate checking whether non-critical operations should be shed."""
        return self.state in (BudgetState.PRESSURE_WARNING, BudgetState.CRITICAL)

    def recommended_replay_ratio(self, base_ratio: float = 0.20) -> float:
        """Recommend adjusted replay ratio based on current memory pressure."""
        if self.state == BudgetState.CRITICAL:
            return 0.05  # Minimal retention replay
        elif self.state == BudgetState.PRESSURE_WARNING:
            return max(0.05, base_ratio * 0.50)
        return base_ratio

    def state_dict(self) -> Dict[str, Any]:
        """Serialize budget manager state."""
        return {
            "max_step_time_ms": self.max_step_time_ms,
            "max_memory_bytes": self.max_memory_bytes,
            "min_batch_size": self.min_batch_size,
            "max_batch_size": self.max_batch_size,
            "warning_threshold": self.warning_threshold,
            "state": str(self.state),
            "current_batch_size": self.current_batch_size,
            "total_steps": self.total_steps,
            "throttled_steps": self.throttled_steps,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore budget manager state."""
        self.max_step_time_ms = float(state["max_step_time_ms"])
        self.max_memory_bytes = int(state["max_memory_bytes"])
        self.min_batch_size = int(state["min_batch_size"])
        self.max_batch_size = int(state["max_batch_size"])
        self.warning_threshold = float(state["warning_threshold"])
        self.state = BudgetState(state["state"].split(".")[-1])
        self.current_batch_size = int(state["current_batch_size"])
        self.total_steps = int(state["total_steps"])
        self.throttled_steps = int(state["throttled_steps"])
