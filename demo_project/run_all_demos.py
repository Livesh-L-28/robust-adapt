"""
===============================================================================
ROBUST-ADAPT: Master Demo Runner
===============================================================================
Executes all 7 interactive demonstrations validating the 5 pillars of 
robust-adapt (v1.0.0):
  1. Concept Drift Adaptation (ALA)
  2. Robust Label Noise Defense (RLA)
  3. Extreme Class Imbalance Mitigation (Minority)
  4. Resource-Aware Budget Optimization (RAO)
  5. Multi-Tier Arbitration Controller (ULC-v5)
  6. Scikit-Learn Ecosystem Integration (Sklearn Pipeline)
  7. Tamper-Resistant Zero-Pickle Checkpointing (SafeTensors + HMAC)

Usage:
    python run_all_demos.py
===============================================================================
"""

import sys
import os
import subprocess
import time

DEMO_SCRIPTS = [
    {
        "id": "01",
        "name": "Concept Drift Adaptation (ALA)",
        "file": "01_concept_drift_stream.py",
        "pillar": "Adaptive Learning Architecture",
    },
    {
        "id": "02",
        "name": "Noisy Labels Defense (RLA)",
        "file": "02_noisy_labels_defense.py",
        "pillar": "Robust Loss & Correction",
    },
    {
        "id": "03",
        "name": "Extreme Class Imbalance (Minority)",
        "file": "03_imbalanced_fraud_detection.py",
        "pillar": "Online Prior & Threshold",
    },
    {
        "id": "04",
        "name": "Resource Budget Optimization (RAO)",
        "file": "04_resource_budget_optimization.py",
        "pillar": "Block Quant & Dynamic Latency",
    },
    {
        "id": "05",
        "name": "ULC-v5 Noise vs. Drift Arbitration",
        "file": "05_ulc_drift_vs_noise_burst.py",
        "pillar": "Unified Learning Controller",
    },
    {
        "id": "06",
        "name": "Scikit-Learn Pipeline Integration",
        "file": "06_sklearn_pipeline_integration.py",
        "pillar": "Ecosystem Compatibility",
    },
    {
        "id": "07",
        "name": "Tamper-Resistant Checkpointing",
        "file": "07_tamper_resistant_checkpoint.py",
        "pillar": "Zero-Pickle SafeTensors + HMAC",
    },
]

def run_all():
    print("=" * 80)
    print(" ROBUST-ADAPT (v1.0.0) — INTERACTIVE DEMONSTRATION SUITE")
    print(f" Python Interpreter: {sys.executable}")
    print(f" Working Directory:  {os.path.abspath(os.path.dirname(__file__))}")
    print("=" * 80)
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    results = []
    total_start = time.time()

    for idx, demo in enumerate(DEMO_SCRIPTS, 1):
        file_path = os.path.join(script_dir, demo["file"])
        print(f"\n[{idx}/{len(DEMO_SCRIPTS)}] RUNNING: {demo['name']} ({demo['file']})")
        print("-" * 80)

        t0 = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, file_path],
                cwd=script_dir,
                capture_output=True,
                text=True,
                check=False
            )
            elapsed = time.time() - t0
            passed = (proc.returncode == 0)

            # Print standard output indented
            for line in proc.stdout.strip().splitlines():
                print(f"   {line}")
            
            if not passed:
                print(f"   [ERROR] Exit Code: {proc.returncode}")
                for err_line in proc.stderr.strip().splitlines():
                    print(f"   ! {err_line}")

            results.append({
                **demo,
                "passed": passed,
                "elapsed": elapsed,
                "code": proc.returncode
            })

        except Exception as e:
            elapsed = time.time() - t0
            print(f"   [EXCEPTION] Failed to execute {demo['file']}: {e}")
            results.append({
                **demo,
                "passed": False,
                "elapsed": elapsed,
                "code": -1
            })

    total_time = time.time() - total_start

    print("\n" + "=" * 80)
    print(" MASTER DEMONSTRATION SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"{'#':<3} | {'Demo Script':<34} | {'Pillar / Module':<30} | {'Time':<7} | {'Status'}")
    print("-" * 80)

    all_passed = True
    for idx, res in enumerate(results, 1):
        status = "PASSED [OK]" if res["passed"] else f"FAILED [E:{res['code']}]"
        if not res["passed"]:
            all_passed = False
        print(f"{idx:<3} | {res['file']:<34} | {res['pillar']:<30} | {res['elapsed']:5.2f}s | {status}")

    print("-" * 80)
    print(f"Total Demonstrations: {len(results)} | Passed: {sum(1 for r in results if r['passed'])} | Failed: {sum(1 for r in results if not r['passed'])}")
    print(f"Cumulative Execution Time: {total_time:.2f} seconds")
    print("=" * 80)

    if all_passed:
        print("[SUCCESS] All 7 robust-adapt demonstrations executed with zero errors!")
        sys.exit(0)
    else:
        print("[FAILURE] One or more demonstrations failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_all()

