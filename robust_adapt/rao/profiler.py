"""Execution Profiling and Resource Telemetry Engine.

Tracks step-level latency profiles, resident memory spikes, and exponential moving averages
to provide predictive early-warning breach alerts before hard budget limits are violated.
"""

from contextlib import contextmanager
import time
from typing import Any, Dict, Generator, Optional
import numpy as np

from robust_adapt.core.telemetry import get_process_memory_bytes


class ExecutionProfiler:
    """Profiles step-level execution time and memory delta with predictive breach warnings.

    Parameters
    ----------
    alpha : float, default=0.10
        Smoothing factor for exponential moving average latency and memory tracking.
    """

    def __init__(self, alpha: float = 0.10) -> None:
        self.alpha = float(alpha)
        self.step_count: int = 0

        self.last_latency_ms: float = 0.0
        self.ema_latency_ms: float = 0.0
        self.min_latency_ms: float = float("inf")
        self.max_latency_ms: float = 0.0

        self.initial_memory_bytes: int = get_process_memory_bytes()
        self.peak_memory_bytes: int = self.initial_memory_bytes
        self.last_memory_bytes: int = self.initial_memory_bytes

    @contextmanager
    def measure_step(self) -> Generator[Dict[str, float], None, None]:
        """Context manager measuring execution latency and peak memory of an operation."""
        t_start = time.perf_counter()
        mem_start = get_process_memory_bytes()
        info: Dict[str, float] = {"step": float(self.step_count + 1)}

        try:
            yield info
        finally:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            mem_end = get_process_memory_bytes()

            self.step_count += 1
            self.last_latency_ms = elapsed_ms
            self.last_memory_bytes = mem_end
            if mem_end > self.peak_memory_bytes:
                self.peak_memory_bytes = mem_end

            if elapsed_ms < self.min_latency_ms:
                self.min_latency_ms = elapsed_ms
            if elapsed_ms > self.max_latency_ms:
                self.max_latency_ms = elapsed_ms

            if self.step_count == 1:
                self.ema_latency_ms = elapsed_ms
            else:
                self.ema_latency_ms = (1.0 - self.alpha) * self.ema_latency_ms + self.alpha * elapsed_ms

            info["elapsed_ms"] = elapsed_ms
            info["ema_latency_ms"] = self.ema_latency_ms
            info["memory_mb"] = mem_end / (1024.0 ** 2)

    def is_breach_predicted(self, target_latency_ms: float, safety_margin: float = 1.25) -> bool:
        """Predict whether step latency will breach target ceiling within the next few steps."""
        if self.step_count < 3:
            return False
        projected = self.ema_latency_ms * safety_margin
        return projected >= target_latency_ms

    def summary(self) -> Dict[str, Any]:
        """Return structured execution summary."""
        return {
            "total_steps": self.step_count,
            "last_latency_ms": round(self.last_latency_ms, 3),
            "ema_latency_ms": round(self.ema_latency_ms, 3),
            "min_latency_ms": round(self.min_latency_ms, 3) if self.min_latency_ms != float("inf") else 0.0,
            "max_latency_ms": round(self.max_latency_ms, 3),
            "peak_memory_mb": round(self.peak_memory_bytes / (1024.0 ** 2), 2),
            "current_memory_mb": round(self.last_memory_bytes / (1024.0 ** 2), 2),
        }
