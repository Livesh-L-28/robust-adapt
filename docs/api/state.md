# API Reference: State, Checkpoints & Serialization (`adaptive_ml.state`)

The `adaptive_ml.state` module provides state saving, loading, atomic checkpointing, cryptographic integrity verification, and zero-copy SafeTensors serialization for AdaptiveML models, optimizers, and controllers.

---

## 1. Top-Level Functions

### `save_state`
```python
def save_state(
    filepath: Union[str, Path],
    tensors: Dict[str, np.ndarray],
    metadata: Optional[Dict[str, Any]] = None,
    auth_key: Optional[bytes] = None,
) -> None
```

Safely persists a dictionary of tensors and metadata to disk using the HuggingFace SafeTensors binary format.

- **Atomic Writes**: Writes first to temporary hidden files (`.filename.tmp`) before atomic replacement via `os.replace`, preventing half-written or corrupted states on sudden shutdown.
- **Integrity Checksums**: Automatically calculates and attaches SHA-256 integrity checksums to the companion `.meta.json` file.
- **Tamper Protection**: If `auth_key` ($\ge 16$ bytes) is provided, calculates and records an HMAC-SHA256 signature to prevent unauthorized tampering or injection.

#### Parameters
- **`filepath`** (`Union[str, Path]`): Target file path. Appends `.safetensors` and `.meta.json` if absent.
- **`tensors`** (`Dict[str, np.ndarray]`): Mapping from parameter/buffer names to NumPy arrays.
- **`metadata`** (`Optional[Dict[str, Any]]`): Optional JSON-serializable metadata dictionary.
- **`auth_key`** (`Optional[bytes]`): Secret bytes key for HMAC-SHA256 signature authentication.

#### Raises
- **`SerializationError`**: If `safetensors` is not installed or atomic write fails.
- **`TypeError` / `ValueError`**: If `auth_key` is invalid or shorter than 16 bytes.

---

### `load_state`
```python
def load_state(
    filepath: Union[str, Path],
    verify_integrity: bool = True,
    max_file_size_bytes: int = 5 * 1024 * 1024 * 1024,
    auth_key: Optional[bytes] = None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]
```

Safely deserializes tensors and companion metadata from disk.

- **Integrity Verification**: When `verify_integrity=True`, validates the SHA-256 checksum of the tensor file against the recorded metadata before reading.
- **HMAC Authentication**: If `auth_key` is provided, verifies the HMAC-SHA256 signature using constant-time comparison (`hmac.compare_digest`).
- **DoS Protection**: Enforces strict file size ceilings (default $5\text{ GB}$ for tensors, $64\text{ MB}$ for metadata) to protect against decompression bombs and memory exhaustion attacks.

#### Parameters
- **`filepath`** (`Union[str, Path]`): Base path to state files.
- **`verify_integrity`** (`bool`, default `True`): Whether to verify SHA-256 checksum against metadata.
- **`max_file_size_bytes`** (`int`, default $5\text{ GB}$): Maximum allowable file size in bytes.
- **`auth_key`** (`Optional[bytes]`): Secret bytes key for HMAC authentication.

#### Returns
- **`Tuple[Dict[str, np.ndarray], Dict[str, Any]]`**: Reconstructed tensors dictionary and metadata dictionary.

#### Raises
- **`FileNotFoundError`**: If tensor file does not exist.
- **`SerializationError`**: If integrity verification fails, HMAC fails, file size exceeds ceiling, or parsing fails.

---

### `is_safetensors_available`
```python
def is_safetensors_available() -> bool
```
Returns `True` if the underlying `safetensors` optional dependency is installed and operational.

---

## 2. Class: `CheckpointManager`

```python
class CheckpointManager(
    checkpoint_dir: Union[str, Path],
    max_checkpoints: int = 5,
    prefix: str = "checkpoint",
)
```

Manages atomic checkpoint snapshotting, rolling retention, and automated rollback history for streaming models and controllers.

### Parameters
- **`checkpoint_dir`** (`Union[str, Path]`): Directory where checkpoints and companion metadata are saved.
- **`max_checkpoints`** (`int`, default `5`): Maximum number of recent checkpoints to retain before automatic pruning.
- **`prefix`** (`str`, default `"checkpoint"`): File naming prefix.

### Methods

#### `save_checkpoint`
```python
def save_checkpoint(
    step: int,
    tensors: Dict[str, np.ndarray],
    metadata: Optional[Dict[str, Any]] = None,
) -> Path
```
Atomically persists a checkpoint snapshot for step `step`. Enforces FIFO pruning when retained checkpoints exceed `max_checkpoints`.

#### `list_checkpoints`
```python
def list_checkpoints() -> List[int]
```
Returns sorted list of all available step indices currently stored in `checkpoint_dir`.

#### `load_latest`
```python
def load_latest() -> Optional[Tuple[Dict[str, np.ndarray], Dict[str, Any]]]
```
Loads the most recent checkpoint snapshot. Returns `None` if no checkpoints exist.

#### `load_step`
```python
def load_step(step: int) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]
```
Restores state corresponding to a specific historical step index.
