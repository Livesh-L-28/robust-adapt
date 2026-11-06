"""PyTorch Training Callbacks, Budget Hooks, and Checkpoint Utilities.

Provides seamless integration between PyTorch training loops, RAO resource budgeting,
and safe multi-component state serialization.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore[assignment]
    nn = object  # type: ignore[assignment,misc]

from robust_adapt.core.exceptions import SerializationError
from robust_adapt.rao.budget import BudgetState, DynamicResourceBudgetManager
from robust_adapt.state.serializer import is_safetensors_available, load_state, save_state


class TorchTrainingBudgetHook:
    """Monitors per-step latency and process RAM during PyTorch training loops.

    Automatically invokes DynamicResourceBudgetManager to detect resource pressure
    and adjust recommended micro-batch sizes.

    Parameters
    ----------
    budget_manager : DynamicResourceBudgetManager
        Active budget manager instance.
    """

    def __init__(
        self,
        budget_manager: DynamicResourceBudgetManager,
        max_history_len: int = 10000,
    ) -> None:
        self.budget_manager = budget_manager
        self.max_history_len = int(max_history_len)
        self._step_start_time: float = 0.0
        self.step_latencies: list[float] = []

    def on_step_begin(self) -> None:
        """Mark the beginning of a training forward-backward-optimizer step."""
        self._step_start_time = time.perf_counter()

    def on_step_end(self) -> BudgetState:
        """Record step duration and evaluate current resource status.

        Returns
        -------
        BudgetState
            Updated operational budget state (NORMAL, PRESSURE_WARNING, THROTTLED, CRITICAL).
        """
        elapsed_ms = (time.perf_counter() - self._step_start_time) * 1000.0
        if len(self.step_latencies) >= self.max_history_len:
            self.step_latencies.pop(0)
        self.step_latencies.append(elapsed_ms)
        return self.budget_manager.evaluate_step(elapsed_ms)

    @property
    def recommended_batch_size(self) -> int:
        """Current recommended micro-batch size from budget manager."""
        return self.budget_manager.current_batch_size


class TorchCheckpointAdapter:
    """Safe state-dict serialization utility for hybrid PyTorch and AdaptiveML systems.

    Avoids unsafe Python pickle loading by separating neural model weights
    from AdaptiveML controller metadata.
    """

    @staticmethod
    def save_hybrid_checkpoint(
        model: Any,
        optimizer: Any,
        controller: Optional[Any],
        filepath: Union[str, Path],
    ) -> Path:
        """Save PyTorch model weights and AdaptiveML optimizer/controller states safely."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_tensors: Dict[str, Any] = {}
        if hasattr(model, "state_dict"):
            for k, v in model.state_dict().items():
                if hasattr(v, "cpu"):
                    model_tensors[str(k)] = v.cpu().numpy()
                else:
                    model_tensors[str(k)] = v

        metadata: Dict[str, Any] = {
            "format": "robust_adapt_hybrid_v1",
            "optimizer_state": optimizer.state_dict() if hasattr(optimizer, "state_dict") else {},
            "controller_state": controller.state_dict() if (controller is not None and hasattr(controller, "state_dict")) else {},
        }

        if is_safetensors_available() and model_tensors:
            save_state(filepath=path, tensors=model_tensors, metadata=metadata)
            return path.with_suffix(".safetensors") if path.suffix != ".safetensors" else path

        # Fallback to JSON metadata when no model tensors or safetensors absent
        meta_path = path.with_suffix(".meta.json") if path.suffix != ".meta.json" else path
        try:
            meta_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize hybrid metadata: {e}") from e

        return meta_path

    @staticmethod
    def load_hybrid_checkpoint(
        model: Any,
        optimizer: Any,
        controller: Optional[Any],
        filepath: Union[str, Path],
    ) -> None:
        """Restore PyTorch model and AdaptiveML optimizer/controller state from checkpoint."""
        path = Path(filepath)

        if is_safetensors_available():
            base_path = path
            if base_path.suffix in (".safetensors", ".json"):
                base_path = base_path.with_suffix("")
            tensor_file = Path(f"{base_path}.safetensors")

            if tensor_file.exists():
                tensors, metadata = load_state(base_path)
                if hasattr(model, "load_state_dict") and _TORCH_AVAILABLE:
                    torch_state = {k: torch.from_numpy(v) for k, v in tensors.items()}
                    model.load_state_dict(torch_state)
                if controller is not None and hasattr(controller, "load_state_dict") and "controller_state" in metadata:
                    controller.load_state_dict(metadata["controller_state"])
                return

        meta_path = path.with_suffix(".meta.json") if not path.name.endswith(".meta.json") else path
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception as e:
                raise SerializationError(f"Failed to parse checkpoint JSON: {e}") from e

            if controller is not None and hasattr(controller, "load_state_dict") and "controller_state" in data:
                controller.load_state_dict(data["controller_state"])
        else:
            raise SerializationError(f"Checkpoint file not found: {filepath}")
