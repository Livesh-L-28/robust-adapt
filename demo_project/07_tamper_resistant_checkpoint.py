"""
Demo 07: Zero-Pickle Tamper-Resistant Model Checkpoints
=======================================================
Demonstrates ROBUST-ADAPT's safe serialization system:
- Strict zero-pickle SafeTensors binary format (protects against RCE exploits)
- Cryptographic SHA-256 file hashing
- HMAC-SHA256 signature authentication
- Tamper detection rejecting corrupted checkpoint payloads

Key Components:
- robust_adapt.state.save_state
- robust_adapt.state.load_state
- robust_adapt.core.exceptions.SerializationError
"""

import tempfile
from pathlib import Path
import numpy as np

import robust_adapt
from robust_adapt.state import save_state, load_state
from robust_adapt.core.exceptions import SerializationError


def main():
    print("=" * 70)
    print("DEMO 07: ZERO-PICKLE SAFE CHECKPOINTING & TAMPER RESISTANCE")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    # 1. Create realistic model parameter tensors
    tensors = {
        "encoder.weight": np.random.randn(64, 128).astype(np.float32),
        "encoder.bias": np.zeros(64, dtype=np.float32),
        "classifier.weight": np.random.randn(2, 64).astype(np.float32),
        "classifier.bias": np.zeros(2, dtype=np.float32),
    }
    metadata = {
        "model_name": "RobustStreamingEnsemble",
        "training_step": 25_000,
        "validation_accuracy": 0.942,
        "author": "ROBUST-ADAPT Maintainer",
    }
    auth_key = b"super_secret_hmac_key_2026_xyz"

    with tempfile.TemporaryDirectory() as tmp_dir:
        checkpoint_path = Path(tmp_dir) / "model_checkpoint"

        # 2. Save state safely without pickle
        print("\nSaving checkpoint with SafeTensors and HMAC-SHA256...")
        save_state(checkpoint_path, tensors=tensors, metadata=metadata, auth_key=auth_key)

        tensor_file = Path(f"{checkpoint_path}.safetensors")
        meta_file = Path(f"{checkpoint_path}.meta.json")
        print(f"  [OK] Saved tensor payload: {tensor_file.name} ({tensor_file.stat().st_size} bytes)")
        print(f"  [OK] Saved metadata file:   {meta_file.name} ({meta_file.stat().st_size} bytes)")

        # 3. Load and verify state with secret key
        print("\nLoading and validating genuine checkpoint...")
        loaded_tensors, loaded_meta = load_state(checkpoint_path, auth_key=auth_key)
        print(f"  [OK] Successfully authenticated {len(loaded_tensors)} tensor layers.")
        print(f"  [OK] Model step: {loaded_meta['training_step']}, Val Acc: {loaded_meta['validation_accuracy']}")
        print(f"  [OK] SHA-256 Digest: {loaded_meta['_sha256'][:16]}...")
        print(f"  [OK] HMAC-SHA256 Signature: {loaded_meta['_hmac_sha256'][:16]}...")

        # 4. Tamper Injection Test: Corrupting 1 byte in the safetensors binary file
        print("\n--- TAMPER INJECTION TEST ---")
        print("Adversary modifies 1 byte in the safetensors model file...")
        with open(tensor_file, "r+b") as f:
            f.seek(50) # Seek to byte 50
            original_byte = f.read(1)
            f.seek(50)
            f.write(bytes([original_byte[0] ^ 0xFF])) # Bitwise flip!

        # Attempt to load the tampered file
        try:
            load_state(checkpoint_path, auth_key=auth_key)
            print("  [FAIL] Tampered checkpoint was unexpectedly accepted!")
        except SerializationError as err:
            print("  [SUCCESS] Tamper detected! ROBUST-ADAPT rejected the compromised file:")
            print(f"            Reason: {err}")

    print("-" * 70)
    print("Conclusion: Zero pickle dependencies eliminate arbitrary code execution vulnerabilities.")
    print("            HMAC-SHA256 signing guarantees tamper-evident state integrity.")


if __name__ == "__main__":
    main()

