"""
AdaptiveML Checkpoint Management.

Provides atomic checkpoint snapshotting, rolling retention, and safe rollback.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from adaptive_ml.state.serializer import load_state, save_state


class CheckpointManager:
    """Manages atomic checkpoint snapshotting and rollback retention."""

    def __init__(
        self,
        checkpoint_dir: Union[str, Path],
        max_checkpoints: int = 5,
        prefix: str = "checkpoint",
    ) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max(1, int(max_checkpoints))
        self.prefix = prefix
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        step: int,
        tensors: Dict[str, np.ndarray],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Atomically persist a checkpoint snapshot for a given step.

        Args:
            step: Monotonic execution step index.
            tensors: Dictionary of state arrays.
            metadata: Additional state metadata.

        Returns:
            Path to the saved safetensors checkpoint.
        """
        stem = f"{self.prefix}_{step:08d}"
        target_path = self.checkpoint_dir / stem
        tmp_target_path = self.checkpoint_dir / f"{stem}.tmp"

        meta = dict(metadata or {})
        meta["step"] = int(step)

        # 1. Save to temporary target
        save_state(tmp_target_path, tensors, metadata=meta)

        # 2. Atomic rename
        tmp_tensor = tmp_target_path.with_suffix(".safetensors")
        tmp_meta = tmp_target_path.with_suffix(".meta.json")
        final_tensor = target_path.with_suffix(".safetensors")
        final_meta = target_path.with_suffix(".meta.json")

        if tmp_tensor.exists():
            os.replace(tmp_tensor, final_tensor)
        if tmp_meta.exists():
            os.replace(tmp_meta, final_meta)

        # 3. Clean up older checkpoints exceeding max_checkpoints
        self._prune_checkpoints()

        return final_tensor

    def list_checkpoints(self) -> List[int]:
        """List all available checkpoint steps in chronological order."""
        steps: List[int] = []
        for p in self.checkpoint_dir.glob(f"{self.prefix}_*.safetensors"):
            try:
                parts = p.stem.split("_")
                step_idx = int(parts[-1])
                steps.append(step_idx)
            except (ValueError, IndexError):
                continue
        return sorted(steps)

    def load_latest(self) -> Optional[Tuple[Dict[str, np.ndarray], Dict[str, Any]]]:
        """Load the most recent checkpoint snapshot."""
        steps = self.list_checkpoints()
        if not steps:
            return None
        return self.load_step(steps[-1])

    def load_step(self, step: int) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """Load state corresponding to a specific step."""
        target_path = self.checkpoint_dir / f"{self.prefix}_{step:08d}.safetensors"
        return load_state(target_path)

    def _prune_checkpoints(self) -> None:
        """Prune excess checkpoints exceeding max_checkpoints limit."""
        steps = self.list_checkpoints()
        if len(steps) > self.max_checkpoints:
            excess = steps[: -self.max_checkpoints]
            for step in excess:
                tensor_p = self.checkpoint_dir / f"{self.prefix}_{step:08d}.safetensors"
                meta_p = self.checkpoint_dir / f"{self.prefix}_{step:08d}.meta.json"
                if tensor_p.exists():
                    tensor_p.unlink()
                if meta_p.exists():
                    meta_p.unlink()

