"""Resource-Aware Optimization (RAO) module.

Provides block-quantized AdamW optimizers, dynamic resource budgeting,
step execution profiling, device capability detection, and resilient checkpointing.
"""

from robust_adapt.rao.accumulator import AdaptiveGradientAccumulator
from robust_adapt.rao.budget import BudgetState, DynamicResourceBudgetManager
from robust_adapt.rao.device import DeviceCapabilityDetector, DeviceProfile
from robust_adapt.rao.memory import ResourceBudget
from robust_adapt.rao.profiler import ExecutionProfiler
from robust_adapt.rao.quantizer import BlockQuantizer
from robust_adapt.rao.recovery import ResilientCheckpointManager

__all__ = [
    "BlockQuantizer",
    "LowMemoryAdamW",
    "AdaptiveGradientAccumulator",
    "ResourceBudget",
    "DynamicResourceBudgetManager",
    "BudgetState",
    "ExecutionProfiler",
    "DeviceCapabilityDetector",
    "DeviceProfile",
    "ResilientCheckpointManager",
    "VectorizedLowMemoryAdamW",
]


def __getattr__(name: str):
    if name == "LowMemoryAdamW":
        from robust_adapt.rao.adamw import LowMemoryAdamW
        return LowMemoryAdamW
    if name == "VectorizedLowMemoryAdamW":
        try:
            from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW
            return VectorizedLowMemoryAdamW
        except (ImportError, Exception) as e:
            raise AttributeError(f"VectorizedLowMemoryAdamW requires PyTorch optional integration: {e}") from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
