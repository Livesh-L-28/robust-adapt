"""Hardware Device and Acceleration Capability Detection.

Safely detects CPU SIMD acceleration features and GPU hardware (CUDA, MPS)
without external binary crashes or mandatory driver dependencies.
"""

from dataclasses import dataclass
import platform
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DeviceProfile:
    """Hardware capability and accelerator profile."""
    platform: str
    machine: str
    processor: str
    has_cuda: bool
    cuda_device_name: Optional[str]
    has_mps: bool
    recommended_backend: str
    cpu_cores: int


class DeviceCapabilityDetector:
    """Detects system compute capabilities and hardware accelerators."""

    @staticmethod
    def detect() -> DeviceProfile:
        """Inspect host execution environment and construct DeviceProfile."""
        plat_system = platform.system()
        plat_machine = platform.machine()
        plat_processor = platform.processor()

        import os
        cpu_cores = os.cpu_count() or 1

        has_cuda = False
        cuda_name = None
        has_mps = False

        # Safe PyTorch accelerator query
        try:
            import torch
            if torch.cuda.is_available():
                has_cuda = True
                cuda_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "CUDA Device"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                has_mps = True
        except Exception:
            pass

        if has_cuda:
            recommended = "cuda"
        elif has_mps:
            recommended = "mps"
        else:
            recommended = "numpy_cpu"

        return DeviceProfile(
            platform=plat_system,
            machine=plat_machine,
            processor=plat_processor,
            has_cuda=has_cuda,
            cuda_device_name=cuda_name,
            has_mps=has_mps,
            recommended_backend=recommended,
            cpu_cores=cpu_cores,
        )
