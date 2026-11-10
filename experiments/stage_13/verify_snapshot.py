import hashlib
import json
from pathlib import Path

backup_dir = Path(".stage_13_pre_integration_snapshot")
manifest_file = backup_dir / "snapshot_manifest.json"

with open(manifest_file, "r", encoding="utf-8") as f:
    data = json.load(f)

files = data["files"]
verified = 0
errors = []

for rel_path, meta in files.items():
    file_path = backup_dir / rel_path
    if not file_path.exists():
        errors.append(f"Missing: {rel_path}")
        continue
    h = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if h != meta["sha256"]:
        errors.append(f"Hash mismatch: {rel_path}")
    else:
        verified += 1

print(f"Snapshot Verification: {verified}/{len(files)} files matched exact SHA-256 digests.")
if errors:
    print(f"FAILED: {len(errors)} errors found.")
    for e in errors[:5]:
        print(" ", e)
else:
    print("SUCCESS: Pre-integration snapshot is 100% verified and intact.")

