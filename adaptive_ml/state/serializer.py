"""
AdaptiveML Safe State Serialization.

Guarantees zero Python pickle deserialization for security against arbitrary code execution.
Persists binary parameter weights via Safetensors and structural metadata via JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import numpy as np
import safetensors.numpy as sn


def save_state(
    filepath: Union[str, Path],
    tensors: Dict[str, np.ndarray],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Safely persist tensor dictionary and metadata without pickle.

    Args:
        filepath: Base path to target file (appends .safetensors and .meta.json if absent).
        tensors: Dictionary mapping string tensor keys to NumPy arrays.
        metadata: Optional dictionary of serializable metadata.
    """
    path = Path(filepath)
    if path.suffix == ".safetensors":
        tensor_path = path
        meta_path = path.with_suffix(".meta.json")
    else:
        tensor_path = path.with_suffix(".safetensors")
        meta_path = path.with_suffix(".meta.json")

    # Ensure parent directory exists
    tensor_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate and ensure C-contiguous arrays for safetensors
    contiguous_tensors: Dict[str, np.ndarray] = {}
    for k, v in tensors.items():
        if not isinstance(v, np.ndarray):
            v = np.asarray(v)
        contiguous_tensors[str(k)] = np.ascontiguousarray(v)

    # Save tensors safely
    sn.save_file(contiguous_tensors, str(tensor_path))

    # Save metadata
    meta = metadata or {}
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)


def load_state(filepath: Union[str, Path]) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """Safely load tensor dictionary and metadata.

    Args:
        filepath: Base path to state files.

    Returns:
        Tuple of (tensors_dict, metadata_dict).
    """
    path = Path(filepath)
    if path.suffix == ".safetensors":
        tensor_path = path
        meta_path = path.with_suffix(".meta.json")
    else:
        tensor_path = path.with_suffix(".safetensors")
        meta_path = path.with_suffix(".meta.json")

    if not tensor_path.exists():
        raise FileNotFoundError(f"Tensor state file not found at: {tensor_path}")

    tensors = sn.load_file(str(tensor_path))

    metadata: Dict[str, Any] = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return tensors, metadata

