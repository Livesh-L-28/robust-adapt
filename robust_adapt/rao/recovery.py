"""Resilient Checkpoint Management and Recovery for Streaming Optimizers.

Provides atomic checkpointing, integrity hashing (SHA-256), automated corruption recovery,
and rollback to the most recent intact state upon crash or power interruption.
"""

import hashlib
import hmac
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from robust_adapt.core.exceptions import SerializationError


class ResilientCheckpointManager:
    """Manages persistent atomic checkpoints with integrity checksums and recovery rollback.

    Parameters
    ----------
    checkpoint_dir : str
        Directory path where checkpoints are saved.
    max_to_keep : int, default=3
        Maximum historical checkpoints retained before pruning.
    auth_key : Optional[bytes], default=None
        Optional cryptographic secret key for HMAC-SHA256 authenticated verification.
    max_file_size_bytes : int, default=104857600 (100 MB)
        Maximum allowable file size for a single checkpoint JSON file to guard against DoS.
    """

    def __init__(
        self,
        checkpoint_dir: str,
        max_to_keep: int = 3,
        auth_key: Optional[bytes] = None,
        max_file_size_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        if max_to_keep < 1:
            raise SerializationError(f"max_to_keep must be >= 1, got {max_to_keep}")
        if auth_key is not None:
            if not isinstance(auth_key, (bytes, bytearray)):
                raise TypeError(f"auth_key must be bytes or bytearray, got {type(auth_key).__name__}")
            if len(auth_key) < 16:
                raise ValueError("auth_key must be at least 16 bytes for cryptographic security.")

        self.checkpoint_dir = os.path.abspath(checkpoint_dir)
        self.max_to_keep = int(max_to_keep)
        self.auth_key = bytes(auth_key) if auth_key is not None else None
        self.max_file_size_bytes = int(max_file_size_bytes)
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _compute_checksum(self, payload: bytes) -> str:
        """Compute SHA-256 hex digest of payload."""
        return hashlib.sha256(payload).hexdigest()

    def _compute_hmac(self, payload: bytes) -> str:
        """Compute HMAC-SHA256 hex digest of payload using configured auth_key."""
        if self.auth_key is None:
            return ""
        return hmac.new(self.auth_key, payload, hashlib.sha256).hexdigest()

    def save_checkpoint(self, step: int, state_dict: Dict[str, Any]) -> str:
        """Atomically persist a verified checkpoint file with embedded SHA-256 checksum.

        Parameters
        ----------
        step : int
            Current streaming optimization step.
        state_dict : Dict[str, Any]
            Serializable state dictionary.

        Returns
        -------
        str
            Path to the saved checkpoint file.
        """
        raw_state_json = json.dumps(state_dict, sort_keys=True).encode("utf-8")
        checksum = self._compute_checksum(raw_state_json)

        bundle: Dict[str, Any] = {
            "step": int(step),
            "checksum": checksum,
            "state_dict": state_dict,
        }
        if self.auth_key is not None:
            bundle["hmac"] = self._compute_hmac(raw_state_json)

        bundle_bytes = json.dumps(bundle, indent=2).encode("utf-8")

        target_file = os.path.join(self.checkpoint_dir, f"checkpoint_step_{step:08d}.json")
        temp_file = target_file + ".tmp"

        # Atomic write: write to temp file then rename
        with open(temp_file, "wb") as f:
            f.write(bundle_bytes)
            f.flush()
            os.fsync(f.fileno())

        shutil.move(temp_file, target_file)
        self._prune_old_checkpoints()
        return target_file

    def load_latest_checkpoint(self) -> Optional[Tuple[int, Dict[str, Any]]]:
        """Scan checkpoint directory and restore the most recent uncorrupted checkpoint.

        If the newest checkpoint is corrupted, truncated, or tampered with, rolls back
        to the prior intact checkpoint.

        Returns
        -------
        Optional[Tuple[int, Dict[str, Any]]]
            (step, state_dict) if valid checkpoint found; None if directory is empty or all corrupted.
        """
        ckpts = self._list_checkpoints_descending()
        if not ckpts:
            return None

        for path in ckpts:
            try:
                # Security size check to prevent memory exhaustion attacks
                if os.path.getsize(path) > self.max_file_size_bytes:
                    continue

                with open(path, "rb") as f:
                    bundle_bytes = f.read()

                bundle = json.loads(bundle_bytes.decode("utf-8"))
                expected_sum = bundle.get("checksum")
                expected_hmac = bundle.get("hmac")
                state_dict = bundle.get("state_dict")
                step = bundle.get("step")

                # Verify payload integrity
                raw_state_json = json.dumps(state_dict, sort_keys=True).encode("utf-8")
                actual_sum = self._compute_checksum(raw_state_json)

                if actual_sum != expected_sum:
                    # Corrupted payload detected; attempt next older checkpoint
                    continue

                # Verify HMAC authentication if auth_key configured
                if self.auth_key is not None:
                    if not expected_hmac:
                        # Missing HMAC signature on authenticated manager
                        continue
                    actual_hmac = self._compute_hmac(raw_state_json)
                    if not hmac.compare_digest(actual_hmac, expected_hmac):
                        # Tampered payload detected; attempt next older checkpoint
                        continue

                return int(step), dict(state_dict)
            except Exception:
                # Corrupted or truncated JSON; fall back to older checkpoint
                continue

        return None

    def _list_checkpoints_descending(self) -> List[str]:
        """List checkpoint files sorted from newest to oldest."""
        files = [
            os.path.join(self.checkpoint_dir, f)
            for f in os.listdir(self.checkpoint_dir)
            if f.startswith("checkpoint_step_") and f.endswith(".json")
        ]
        files.sort(reverse=True)
        return files

    def _prune_old_checkpoints(self) -> None:
        """Prune excess checkpoints exceeding max_to_keep."""
        ckpts = self._list_checkpoints_descending()
        if len(ckpts) > self.max_to_keep:
            for old_path in ckpts[self.max_to_keep:]:
                try:
                    os.remove(old_path)
                except OSError:
                    pass
