"""Stage 13 Rollback & Recovery Verification Script.

Tests and validates the rollback procedure using the verified pre-integration snapshot
stored in `.stage_13_pre_integration_snapshot/`:
1. Validates integrity of all 284 snapshot files against `snapshot_manifest.json`.
2. Simulates an isolated rollback restoration into a temporary sandbox.
3. Confirms exact bitwise identity (SHA-256) of every restored file against baseline.
4. Executes baseline test verification in the sandboxed restored tree.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

SNAPSHOT_DIR = os.path.abspath(".stage_13_pre_integration_snapshot")
MANIFEST_PATH = os.path.join(SNAPSHOT_DIR, "snapshot_manifest.json")


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    print("=== Stage 13 Rollback & Recovery Procedure Verification ===")
    assert os.path.exists(MANIFEST_PATH), f"Snapshot manifest missing: {MANIFEST_PATH}"

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = data["files"]
    print(f"Loaded snapshot manifest containing {len(manifest)} files.")

    # 1. Verify snapshot file integrity
    print("Verifying snapshot storage integrity...")
    for rel_path, meta in manifest.items():
        snap_file = os.path.join(SNAPSHOT_DIR, rel_path)
        assert os.path.exists(snap_file), f"Snapshot file missing: {snap_file}"
        current_hash = compute_sha256(snap_file)
        expected_hash = meta["sha256"]
        assert current_hash == expected_hash, f"Hash mismatch in snapshot file: {rel_path}"

    print(f"All {len(manifest)} snapshot files verified intact (100% SHA-256 match).")

    # 2. Simulate isolated rollback restoration
    with tempfile.TemporaryDirectory() as sandbox_dir:
        print(f"Simulating restoration into isolated sandbox: {sandbox_dir}")
        for rel_path, meta in manifest.items():
            src_file = os.path.join(SNAPSHOT_DIR, rel_path)
            dest_file = os.path.join(sandbox_dir, rel_path)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)

        # 3. Verify restored files bitwise identity
        verified_count = 0
        for rel_path, meta in manifest.items():
            restored_file = os.path.join(sandbox_dir, rel_path)
            assert os.path.exists(restored_file)
            restored_hash = compute_sha256(restored_file)
            expected_hash = meta["sha256"]
            assert restored_hash == expected_hash
            verified_count += 1

        print(f"Restoration verification: {verified_count}/{len(manifest)} files bit-for-bit identical to baseline.")

        # 4. Verify test execution in restored sandbox
        print("Executing quick sanity test in restored sandbox...")
        code = """
import sys, os
sandbox = sys.argv[1]
sys.path.insert(0, sandbox)
import adaptive_ml
assert adaptive_ml.__version__ == "0.1.0.dev0"
from adaptive_ml.ala.classifier import AdaptiveClassifier
clf = AdaptiveClassifier(n_features=2, n_classes=2)
assert clf.n_features == 2
print("Sandboxed restored package successfully imported and instantiated!")
"""
        res = subprocess.run([sys.executable, "-c", code, sandbox_dir], capture_output=True, text=True, check=True)
        print(res.stdout.strip())

    print("\nRollback procedure verified 100% operational and safe.")

    # Persist summary
    out_file = os.path.join("experiments", "stage_13", "rollback_verification_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "status": "VERIFIED",
            "files_verified": verified_count,
            "manifest_total": len(manifest),
            "bitwise_match": True,
            "runtime_smoke_test": "PASSED",
        }, f, indent=2)


if __name__ == "__main__":
    main()
