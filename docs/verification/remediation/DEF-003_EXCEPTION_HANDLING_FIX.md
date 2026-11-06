# AdaptiveML — DEF-003 Remediation Report
## Scoped Platform Exception Handling and Win32 Ctypes 64-bit Handle Fix

**Defect Identifier:** `DEF-003`<br>
**Severity:** `LOW`<br>
**Category:** Code Quality, Exception Handling & Platform Portability<br>
**Affected File:** [`adaptive_ml/core/telemetry.py`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py)<br>
**Status:** `RESOLVED & VERIFIED`

---

## 1. Problem Description & Root Cause Analysis

Automated static security analysis via Bandit 1.9.4 flagged three occurrences of rule `B110: try_except_pass` in [`adaptive_ml/core/telemetry.py`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py):
- Line 15: `try: import psutil ... except Exception: pass`
- Line 43: Windows ctypes memory lookup catch-all `except Exception: pass`
- Line 52: Linux `/proc/self/statm` memory lookup catch-all `except Exception: pass`

### The Architectural & Defensive Risk
Broad exception suppression (`except Exception: pass`):
1. **Masks Programming Bugs:** Critical internal programming bugs (such as `TypeError`, `NameError`, `UnboundLocalError`, or memory allocation errors) are silently swallowed rather than exposed.
2. **Obscures Platform Invariants:** It hides genuine platform-specific failure modes, preventing developers from understanding why a fallback failed.

### The Win32 64-bit Truncation Defect Discovery
During investigation of the Windows ctypes fallback on Python 3.11 when `psutil` was absent, [`get_process_memory_bytes()`](file:///c:/projects/AdaptiveML/adaptive_ml/core/telemetry.py#L8) was returning `0` despite executing on Windows.

**Root Cause:**<br>
On 64-bit Windows, `kernel32.GetCurrentProcess()` returns the pseudo-handle `(HANDLE)-1` (`0xFFFFFFFFFFFFFFFF`). Because `restype` was not explicitly configured on `ctypes.windll.kernel32.GetCurrentProcess`, ctypes defaulted to a 32-bit `c_int`, returning `0x00000000FFFFFFFF`. When passed to `psapi.GetProcessMemoryInfo`, the Windows kernel rejected the truncated pointer with `ERROR_INVALID_HANDLE` (Win32 Error 6), causing the fallback to fail silently.

---

## 2. Technical Remediation Implementation

### 2.1 Narrowed Exception Scopes
Broad exception handling was replaced with explicit, narrow exception tuples corresponding strictly to expected OS and file-system failure modes:

```python
def get_process_memory_bytes() -> int:
    """Return the current resident set size (RSS) memory in bytes without mandatory external deps."""
    # 1. psutil lookup
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return int(process.memory_info().rss)
    except (ImportError, AttributeError, OSError):
        pass

    # 2. Windows fallback via ctypes
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            kernel32 = ctypes.windll.kernel32
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            handle = kernel32.GetCurrentProcess()

            psapi = ctypes.windll.psapi
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        except (ImportError, AttributeError, OSError, ValueError):
            pass

    # 3. Linux / Unix /proc fallback
    try:
        with open("/proc/self/statm", "r", encoding="utf-8") as f:
            fields = f.read().split()
            if len(fields) >= 2:
                page_size = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
                return int(fields[1]) * page_size
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError, ValueError, IndexError):
        pass

    return 0
```

### 2.2 Win32 Ctypes 64-bit Handle Configuration
By configuring:
```python
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
```
the full 64-bit pseudo-handle `0xFFFFFFFFFFFFFFFF` is passed to `psapi.GetProcessMemoryInfo`, which now succeeds and returns the exact resident working set size without requiring `psutil`.

---

## 3. Verification Test Evidence

Automated regression tests were added in [`tests/unit/test_defect_remediation.py::TestDEF003TelemetryExceptionHandling`](file:///c:/projects/AdaptiveML/tests/unit/test_defect_remediation.py):

### 3.1 Host Memory Query Verification
```python
def test_get_process_memory_bytes_returns_positive_int(self) -> None:
    mem = get_process_memory_bytes()
    assert isinstance(mem, int)
    assert mem > 0, f"Expected positive RSS memory bytes, got {mem}"
```
- **Result:** **PASSED** (returned $15,253,504\text{ bytes} \approx 15.25\text{ MB}$ RSS on Python 3.11 with zero psutil).

### 3.2 Graceful Fallback on Missing `psutil`
```python
def test_psutil_import_error_falls_back_gracefully(self) -> None:
    with patch.dict(sys.modules, {"psutil": None}):
        mem = get_process_memory_bytes()
        assert isinstance(mem, int)
        assert mem >= 0
```
- **Result:** **PASSED**

### 3.3 Unexpected Programming Exception Propagation
```python
def test_unexpected_exception_is_not_silently_suppressed(self) -> None:
    class MaliciousPsutil:
        @staticmethod
        def Process(*args, **kwargs):
            raise TypeError("Simulated programming bug: invalid type")

    with patch.dict(sys.modules, {"psutil": MaliciousPsutil}):
        with pytest.raises(TypeError) as exc_info:
            get_process_memory_bytes()
        assert "Simulated programming bug" in str(exc_info.value)
```
- **Result:** **PASSED** (unexpected programming errors are surfaced).

### 3.4 Static Security Scan (Bandit 1.9.4)
Re-running Bandit over `adaptive_ml` confirmed:
```text
Run metrics:
    Total issues (by severity):
        Low: 0
        Medium: 0
        High: 0
```
- **Result:** All B110 findings have been **100% eliminated**.

---

## 4. Conclusion & Acceptance Status

**Acceptance Criterion:** *PASS only if expected platform failures are handled, unexpected programming errors are not silently swallowed, and supported platform fallback behavior is preserved.*

**Verdict:** **`PASS`**
