"""Resource Budget and Execution Constraints Management for RAO."""

from typing import Optional
from adaptive_ml.core.exceptions import ResourceBudgetExceededError
from adaptive_ml.core.telemetry import MemoryBudgetTracker, get_process_memory_bytes


class ResourceBudget:
    """Manages memory and computation budgets, enforcing hard ceilings and soft warnings.

    Parameters
    ----------
    max_memory_bytes : Optional[int], default=None
        Hard ceiling on process RAM in bytes.
    max_steps : Optional[int], default=None
        Maximum total optimization steps allowed.
    """

    def __init__(
        self,
        max_memory_bytes: Optional[int] = None,
        max_steps: Optional[int] = None,
    ) -> None:
        self.max_memory_bytes = max_memory_bytes
        self.max_steps = max_steps
        self.tracker = MemoryBudgetTracker(max_memory_bytes=max_memory_bytes)
        self.step_count: int = 0

    def check_and_increment_step(self) -> None:
        """Increment step counter and assert resource constraints."""
        self.step_count += 1
        if self.max_steps is not None and self.step_count > self.max_steps:
            raise ResourceBudgetExceededError(
                f"Step budget exceeded: {self.step_count} > max_steps ({self.max_steps})"
            )

        if self.max_memory_bytes is not None:
            current = get_process_memory_bytes()
            if current >= self.max_memory_bytes:
                raise ResourceBudgetExceededError(
                    f"Memory ceiling exceeded: current RSS {current / (1024**2):.2f} MB "
                    f"exceeds ceiling {self.max_memory_bytes / (1024**2):.2f} MB"
                )

    def is_pressure_active(self) -> bool:
        """Returns True if memory pressure is active."""
        return self.tracker.is_pressure_active()

