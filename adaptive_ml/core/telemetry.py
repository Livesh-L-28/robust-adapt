"""Local performance and process memory monitoring."""

import os
import sys
from typing import Optional


def get_process_memory_bytes() -> int:
    """Return the current resident set size (RSS) memory in bytes without mandatory external deps."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return int(process.memory_info().rss)
    except Exception:
        pass

    # Windows fallback via ctypes
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
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        except Exception:
            pass

    # Linux / Unix fallback
    try:
        with open("/proc/self/statm", "r") as f:
            fields = f.read().split()
            # resident pages * page size
            return int(fields[1]) * os.sysconf("SC_PAGE_SIZE")
    except Exception:
        pass

    return 0


class MemoryBudgetTracker:
    """Monitors process memory and signals pressure when approaching max budget."""

    def __init__(self, max_memory_bytes: Optional[int] = None, pressure_threshold: float = 0.85) -> None:
        self.max_memory_bytes = max_memory_bytes
        self.pressure_threshold = pressure_threshold

    @property
    def current_memory_bytes(self) -> int:
        return get_process_memory_bytes()

    def is_pressure_active(self) -> bool:
        """Returns True if current RAM usage exceeds the safety threshold."""
        if self.max_memory_bytes is None or self.max_memory_bytes <= 0:
            return False
        current = self.current_memory_bytes
        return current >= (self.max_memory_bytes * self.pressure_threshold)

    def is_budget_exceeded(self) -> bool:
        """Returns True if memory usage strictly exceeds max budget."""
        if self.max_memory_bytes is None or self.max_memory_bytes <= 0:
            return False
        return self.current_memory_bytes >= self.max_memory_bytes
