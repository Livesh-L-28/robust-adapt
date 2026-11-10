# ROBUST-ADAPT — Phase 17.4: Platform & Operating System Validation Report

**Document ID:** REPORT-PLATFORM-VAL-PHASE17-4-001<br>
**Version:** 0.1.0-alpha.0<br>
**Committed Baseline:** `4103b87abe1744fbd4e7449a4932b09b5d3b78d4` (`4103b87`)<br>
**Evaluation Date:** November 2026<br>
**Status:** **AUDITED / PLATFORM BOUNDED**<br>

---

## 1. Executive Summary

This report establishes the operating system platform audit for **ROBUST-ADAPT** (`robust-adapt` version `0.1.0.dev0`).

Testing was executed on Microsoft Windows 11 (AMD64). Linux (Ubuntu/Debian) and macOS (Darwin) were not locally available and are formally categorized as **NOT TESTED** in compliance with governance non-extrapolation rules.

---

## 2. Windows 11 Platform Validation (Empirically Confirmed)

### 2.1 Host Specifications
* **Operating System:** Microsoft Windows 11 Home Single Language
* **OS Build:** `10.0.26200.5050`
* **Architecture:** AMD64 (x86_64)
* **Shell Environment:** PowerShell 5.1 / Windows Terminal
* **File System:** NTFS (Case-preserving, case-insensitive)

### 2.2 Windows-Specific Operating Characteristics Evaluated
1. **Path Handling & Separators:**
   - Evaluated cross-platform path resolution using `pathlib.Path` across checkpoint managers, serializers, and datasets.
   - Zero hardcoded POSIX `/` or Windows `\` assumptions found in production source files.
   - Checkpoint paths verified using `Path.resolve()`.
2. **Atomic State Swapping & File Locking:**
   - Tested atomic checkpoint swapping in `robust_adapt.state.checkpoint.ResilientCheckpointManager`.
   - Windows NTFS enforces strict file locking on open file handles. The checkpoint manager utilizes temporary atomic file replacement (`os.replace`) which completed cleanly under both Python 3.11 and 3.14.
3. **Memory Telemetry on Windows:**
   - Evaluated `get_process_memory_bytes` in `robust_adapt.core.telemetry`.
   - Uses `psutil.Process().memory_info().rss` with graceful fallback to `0` when `psutil` is uninstalled. Verified on Windows 11 without memory access violations.
4. **Windows Application Control (Host Policy Consideration):**
   - In locked-down corporate Windows environments, executing newly generated `.exe` files copied into `%TEMP%` (such as `pip.exe` in temporary virtual environments) may be blocked by Windows Application Control policies.
   - **Remediation Standard:** Always invoke tooling via the signed Python executable:
     ```powershell
     <venv>\Scripts\python.exe -m pip install <wheel>
     ```
     This pattern was verified 100% operational across all test runs.

---

## 3. Linux (Ubuntu/Debian) Platform Status

* **Architecture Target:** x86_64 / aarch64
* **Local Workspace Status:** **NOT TESTED** (No local Linux kernel, container runtime, or WSL instance configured in current session).
* **CI Target:** `ubuntu-latest` configured in `.github/workflows/ci.yml`.

### Architectural Expectations for Linux
- Case-sensitive filesystem (`ext4`): Canonical module imports use strictly lowercase naming (`robust_adapt.ala`, `robust_adapt.rla`), preventing case-sensitivity collisions.
- Memory telemetry uses `/proc/self/statm` or `psutil`. Fallbacks verified compliant.

---

## 4. macOS (Darwin) Platform Status

* **Architecture Target:** ARM64 (Apple Silicon M1-M4) / x86_64
* **Local Workspace Status:** **NOT TESTED** (No Apple Darwin host locally available).
* **CI Target:** `macos-latest` configured in `.github/workflows/ci.yml`.

### Architectural Expectations for macOS
- macOS uses case-insensitive APFS by default.
- PyTorch acceleration on Darwin utilizes `mps` (Metal Performance Shaders) rather than `cuda`. Core `robust_adapt` falls back cleanly to CPU/NumPy when accelerator devices are absent.

---

## 5. Summary Platform Assessment

| Platform | Local Status | CI Automated Status | Overall Readiness |
| :--- | :---: | :---: | :--- |
| **Windows 11 (AMD64)** | **PASSED** | Active | Fully verified and operational |
| **Linux (Ubuntu)** | **NOT TESTED** | Configured | Pending CI pipeline execution |
| **macOS (Darwin)** | **NOT TESTED** | Configured | Pending CI pipeline execution |

