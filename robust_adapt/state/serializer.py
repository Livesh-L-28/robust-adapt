"""
AdaptiveML Safe State Serialization.

Guarantees zero Python pickle deserialization for security against arbitrary code execution.
Persists binary parameter weights via Safetensors and structural metadata via JSON.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from robust_adapt.core.exceptions import SerializationError, ValidationError

try:
    import safetensors.numpy as sn
    _SAFETENSORS_AVAILABLE = True
except ImportError:
    sn = None
    _SAFETENSORS_AVAILABLE = False


def is_safetensors_available() -> bool:
    """Check whether the optional Safetensors dependency is installed."""
    return _SAFETENSORS_AVAILABLE


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Compute SHA-256 cryptographic digest of a binary file in chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_file_hmac(filepath: Union[str, Path], key: bytes) -> str:
    """Compute HMAC-SHA256 cryptographic signature of a binary file in chunks."""
    h = hmac.new(key, digestmod=hashlib.sha256)
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def save_state(
    filepath: Union[str, Path],
    tensors: Dict[str, np.ndarray],
    metadata: Optional[Dict[str, Any]] = None,
    auth_key: Optional[bytes] = None,
) -> None:
    """Safely persist tensor dictionary and metadata without pickle.

    Executes atomic persistence and computes cryptographic SHA-256 integrity hash
    and optional HMAC-SHA256 signature.

    Args:
        filepath: Base path to target file (appends .safetensors and .meta.json if absent).
        tensors: Dictionary mapping string tensor keys to NumPy arrays.
        metadata: Optional dictionary of serializable metadata.
        auth_key: Optional secret bytes key for HMAC-SHA256 authentication against tampering.

    Raises:
        SerializationError: If 'safetensors' is not installed or state cannot be written.
        TypeError: If auth_key is not bytes or bytearray.
    """
    if auth_key is not None and not isinstance(auth_key, (bytes, bytearray)):
        raise TypeError(f"auth_key must be bytes or bytearray, got {type(auth_key).__name__}")
    if auth_key is not None and len(auth_key) < 16:
        raise ValueError("auth_key must be at least 16 bytes for cryptographic security.")

    if not _SAFETENSORS_AVAILABLE or sn is None:
        raise SerializationError(
            "State serialization requires the optional 'safetensors' dependency. "
            "Install it via: pip install 'robust-adapt[safetensors]'"
        )

    path = Path(filepath)
    if path.suffix == ".safetensors":
        tensor_path = path
        meta_path = path.with_suffix(".meta.json")
    else:
        tensor_path = path.with_suffix(".safetensors")
        meta_path = path.with_suffix(".meta.json")

    # Ensure parent directory exists
    tensor_path.parent.mkdir(parents=True, exist_ok=True)

    # Temporary paths for atomic write
    tmp_tensor_path = tensor_path.with_name(f".{tensor_path.name}.tmp")
    tmp_meta_path = meta_path.with_name(f".{meta_path.name}.tmp")

    # Validate and ensure C-contiguous arrays for safetensors
    contiguous_tensors: Dict[str, np.ndarray] = {}
    for k, v in tensors.items():
        if not isinstance(v, np.ndarray):
            v = np.asarray(v)
        contiguous_tensors[str(k)] = np.ascontiguousarray(v)

    # 1. Save tensors to temporary file
    try:
        sn.save_file(contiguous_tensors, str(tmp_tensor_path))
    except Exception as exc:
        if tmp_tensor_path.exists():
            tmp_tensor_path.unlink()
        raise SerializationError(f"Failed to save safetensors file at {tensor_path}: {exc}") from exc

    # 2. Compute cryptographic SHA-256 checksum and file size
    sha256_hash = compute_file_sha256(tmp_tensor_path)
    file_size_bytes = tmp_tensor_path.stat().st_size

    # 3. Construct enriched metadata
    meta = dict(metadata or {})
    meta["_format_version"] = "1.0"
    meta["_sha256"] = sha256_hash
    meta["_file_size_bytes"] = file_size_bytes

    if auth_key is not None:
        meta["_hmac_sha256"] = compute_file_hmac(tmp_tensor_path, auth_key)

    # 4. Save metadata to temporary JSON file
    try:
        with open(tmp_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
    except Exception as exc:
        if tmp_tensor_path.exists():
            tmp_tensor_path.unlink()
        if tmp_meta_path.exists():
            tmp_meta_path.unlink()
        raise SerializationError(f"Failed to save metadata JSON at {meta_path}: {exc}") from exc

    # 5. Atomic replacement to prevent half-written files
    try:
        tmp_tensor_path.replace(tensor_path)
        tmp_meta_path.replace(meta_path)
    except Exception as exc:
        raise SerializationError(f"Atomic state commit failed at {filepath}: {exc}") from exc


def load_state(
    filepath: Union[str, Path],
    verify_integrity: bool = True,
    max_file_size_bytes: int = 5 * 1024 * 1024 * 1024,
    auth_key: Optional[bytes] = None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """Safely load tensor dictionary and metadata.

    Verifies file size limits, cryptographic SHA-256 checksum, and optional HMAC authentication.

    Args:
        filepath: Base path to state files.
        verify_integrity: Whether to verify cryptographic SHA-256 checksum against metadata.
        max_file_size_bytes: Maximum allowable file size in bytes (default 5 GB).
        auth_key: Optional secret bytes key for HMAC-SHA256 signature verification.

    Returns:
        Tuple of (tensors_dict, metadata_dict).

    Raises:
        FileNotFoundError: If the tensor state file does not exist.
        SerializationError: If 'safetensors' is not installed, file is corrupted, or integrity check fails.
        TypeError: If auth_key is not bytes or bytearray.
    """
    if auth_key is not None and not isinstance(auth_key, (bytes, bytearray)):
        raise TypeError(f"auth_key must be bytes or bytearray, got {type(auth_key).__name__}")

    if not _SAFETENSORS_AVAILABLE or sn is None:
        raise SerializationError(
            "State deserialization requires the optional 'safetensors' dependency. "
            "Install it via: pip install 'robust-adapt[safetensors]'"
        )

    path = Path(filepath)
    if path.suffix == ".safetensors":
        tensor_path = path
        meta_path = path.with_suffix(".meta.json")
    else:
        tensor_path = path.with_suffix(".safetensors")
        meta_path = path.with_suffix(".meta.json")

    if not tensor_path.exists():
        raise FileNotFoundError(f"Tensor state file not found at: {tensor_path}")

    # File size validation to prevent DoS via massive allocations
    file_size = tensor_path.stat().st_size
    if file_size > max_file_size_bytes:
        raise SerializationError(
            f"Checkpoint file exceeds size ceiling ({file_size} > {max_file_size_bytes} bytes): {tensor_path}"
        )

    # Load metadata if present
    metadata: Dict[str, Any] = {}
    if meta_path.exists():
        meta_size = meta_path.stat().st_size
        max_meta_size = 64 * 1024 * 1024  # 64 MB ceiling on JSON metadata to prevent memory exhaustion
        if meta_size > max_meta_size:
            raise SerializationError(
                f"Metadata file exceeds size limit ({meta_size} > {max_meta_size} bytes): {meta_path}"
            )
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as exc:
            raise SerializationError(f"Failed to parse metadata JSON at {meta_path}: {exc}") from exc

    # Cryptographic integrity verification (SHA-256)
    if verify_integrity and "_sha256" in metadata:
        expected_hash = metadata["_sha256"]
        actual_hash = compute_file_sha256(tensor_path)
        if actual_hash != expected_hash:
            raise SerializationError(
                f"Integrity check failed for checkpoint at {tensor_path}: "
                f"expected SHA-256 '{expected_hash}', got '{actual_hash}'. "
                f"File may be corrupted, truncated, or tampered with."
            )

    # Authenticated HMAC integrity verification
    if auth_key is not None:
        if "_hmac_sha256" not in metadata:
            raise SerializationError(
                f"Checkpoint at {tensor_path} does not contain an HMAC signature, "
                f"but auth_key was provided for verified loading."
            )
        expected_hmac = metadata["_hmac_sha256"]
        actual_hmac = compute_file_hmac(tensor_path, auth_key)
        if not hmac.compare_digest(actual_hmac, expected_hmac):
            raise SerializationError(
                f"HMAC authentication failed for checkpoint at {tensor_path}. "
                f"File signature mismatch: checkpoint may be tampered with or auth_key is invalid."
            )

    try:
        tensors = sn.load_file(str(tensor_path))
    except Exception as exc:
        raise SerializationError(f"Failed to load safetensors file at {tensor_path}: {exc}") from exc

    return tensors, metadata
