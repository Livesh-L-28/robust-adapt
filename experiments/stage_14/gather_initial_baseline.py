"""Gather Initial Production Baseline Metrics for Stage 14."""

import json
import os
import psutil
import subprocess
import sys
import time

def measure_cold_import_and_memory():
    # Run subprocess measuring cold import time and memory
    code = """
import time, os, psutil
p = psutil.Process(os.getpid())
m0 = p.memory_info().rss / (1024 * 1024)
t0 = time.perf_counter()
import adaptive_ml
t1 = time.perf_counter()
m1 = p.memory_info().rss / (1024 * 1024)
print(f"IMPORT_TIME_MS:{(t1 - t0)*1000.0:.2f}")
print(f"INIT_MEM_MB:{m0:.2f}")
print(f"CORE_MEM_MB:{m1:.2f}")
print(f"MEM_DELTA_MB:{m1 - m0:.2f}")
"""
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    out = {}
    for line in res.stdout.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k] = float(v)
    return out

def get_public_api_inventory():
    import adaptive_ml
    exports = sorted(adaptive_ml.__all__)
    submodules = ["ala", "rla", "minority", "rao", "ulc", "core", "state", "integrations"]
    sub_exports = {}
    for s in submodules:
        try:
            mod = __import__(f"adaptive_ml.{s}", fromlist=[s])
            sub_exports[s] = getattr(mod, "__all__", [x for x in dir(mod) if not x.startswith("_")])
        except Exception as e:
            sub_exports[s] = f"Error: {e}"
    return {
        "top_level_count": len(exports),
        "top_level_exports": exports,
        "submodule_exports": sub_exports,
    }

def main():
    print("=== Gathering Stage 14 Baseline Metrics ===")
    import_mem = measure_cold_import_and_memory()
    print("Import and Memory Metrics:", import_mem)

    api_inv = get_public_api_inventory()
    print(f"Public API Inventory: {api_inv['top_level_count']} top-level symbols.")

    results = {
        "import_and_memory": import_mem,
        "api_inventory": api_inv,
        "python_version": sys.version,
        "platform": sys.platform,
    }

    out_file = os.path.join("experiments", "stage_14", "initial_baseline_metrics.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved baseline metrics to {out_file}")

if __name__ == "__main__":
    main()

