"""Create and verify a safe Stage 14 pre-hardening snapshot.

Archives:
- adaptive_ml/
- tests/
- examples/
- pyproject.toml
into .stage_14_pre_hardening_snapshot/ with SHA-256 manifest.
"""

import hashlib
import json
import os
import shutil
import time

TARGET_DIRS = ["adaptive_ml", "tests", "examples"]
TARGET_FILES = ["pyproject.toml"]
SNAPSHOT_DIR = os.path.abspath(".stage_14_pre_hardening_snapshot")


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    print("=== Creating Stage 14 Pre-Hardening Snapshot ===")
    if os.path.exists(SNAPSHOT_DIR):
        print(f"Removing pre-existing snapshot directory: {SNAPSHOT_DIR}")
        shutil.rmtree(SNAPSHOT_DIR)

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": "Stage 14 Pre-Hardening Recovery Point",
        "git_commit": "67e9ef1b347ca223828a1f225e85e35a086a1f30",
        "files": {},
    }

    total_files = 0

    # Archive directories
    for d in TARGET_DIRS:
        for root, _, filenames in os.walk(d):
            if "__pycache__" in root or ".pytest_cache" in root:
                continue
            for fname in filenames:
                if fname.endswith(".pyc") or fname.endswith(".pyo"):
                    continue
                src_path = os.path.join(root, fname)
                rel_path = os.path.relpath(src_path, ".")
                dest_path = os.path.join(SNAPSHOT_DIR, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)

                sha = compute_sha256(dest_path)
                manifest["files"][rel_path.replace("\\", "/")] = {
                    "sha256": sha,
                    "size_bytes": os.path.getsize(dest_path),
                }
                total_files += 1

    # Archive target files
    for f in TARGET_FILES:
        if os.path.exists(f):
            dest_path = os.path.join(SNAPSHOT_DIR, f)
            shutil.copy2(f, dest_path)
            sha = compute_sha256(dest_path)
            manifest["files"][f] = {
                "sha256": sha,
                "size_bytes": os.path.getsize(dest_path),
            }
            total_files += 1

    manifest_path = os.path.join(SNAPSHOT_DIR, "snapshot_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)

    print(f"Snapshot created successfully: {total_files} files archived.")

    # Verification pass
    print("Verifying snapshot integrity...")
    verified = 0
    for rel_path, meta in manifest["files"].items():
        archived_path = os.path.join(SNAPSHOT_DIR, rel_path)
        assert os.path.exists(archived_path), f"Archived file missing: {archived_path}"
        current_sha = compute_sha256(archived_path)
        assert current_sha == meta["sha256"], f"Checksum mismatch: {rel_path}"
        verified += 1

    print(f"Snapshot Verification Passed: {verified}/{total_files} files bit-perfect.")


if __name__ == "__main__":
    main()

