"""Local Observability and Structured Diagnostic Event Registry.

Provides lightweight, opt-in Python logging and in-memory bounded diagnostic event tracking
without requiring external daemons, network endpoints, or cloud services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from collections import deque
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("robust_adapt")
logger.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class DiagnosticEvent:
    """Structured diagnostic telemetry event."""

    timestamp: float
    component: str
    event_type: str
    level: str = "INFO"
    step: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dictionary."""
        return asdict(self)


class DiagnosticRegistry:
    """Thread-safe, bounded in-memory diagnostic event registry.

    Parameters
    ----------
    max_events : int, default=1000
        Maximum historical diagnostic events retained in memory.
    """

    def __init__(self, max_events: int = 1000) -> None:
        self.max_events = int(max_events)
        self._lock = threading.Lock()
        self._events: deque[DiagnosticEvent] = deque(maxlen=self.max_events)

    def record(
        self,
        component: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "INFO",
        step: Optional[int] = None,
    ) -> DiagnosticEvent:
        """Record a structured diagnostic event and emit to standard Python logging."""
        event = DiagnosticEvent(
            timestamp=time.time(),
            component=str(component),
            event_type=str(event_type),
            level=str(level).upper(),
            step=step,
            details=details or {},
        )

        with self._lock:
            self._events.append(event)

        # Emit to standard Python logger
        log_msg = f"[{component}] {event_type}"
        if step is not None:
            log_msg += f" (step={step})"
        if details:
            log_msg += f" - {details}"

        if level.upper() == "DEBUG":
            logger.debug(log_msg)
        elif level.upper() == "WARNING":
            logger.warning(log_msg)
        elif level.upper() == "ERROR":
            logger.error(log_msg)
        else:
            logger.info(log_msg)

        return event

    def get_events(
        self,
        component: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[DiagnosticEvent]:
        """Query recent diagnostic events with optional component filtering."""
        with self._lock:
            matching = [
                e
                for e in self._events
                if (component is None or e.component == component)
                and (event_type is None or e.event_type == event_type)
            ]
            return matching[-limit:]

    def clear(self) -> None:
        """Clear all retained diagnostic events."""
        with self._lock:
            self._events.clear()

    @property
    def event_count(self) -> int:
        """Total active events currently held in memory."""
        with self._lock:
            return len(self._events)


# Global default registry instance
_GLOBAL_REGISTRY = DiagnosticRegistry(max_events=1000)


def record_diagnostic_event(
    component: str,
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
    step: Optional[int] = None,
) -> DiagnosticEvent:
    """Record a global diagnostic event."""
    return _GLOBAL_REGISTRY.record(
        component=component,
        event_type=event_type,
        details=details,
        level=level,
        step=step,
    )


def get_diagnostic_events(
    component: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> List[DiagnosticEvent]:
    """Retrieve recent diagnostic events from the global registry."""
    return _GLOBAL_REGISTRY.get_events(component=component, event_type=event_type, limit=limit)


def clear_diagnostic_events() -> None:
    """Clear all diagnostic events from the global registry."""
    _GLOBAL_REGISTRY.clear()


def configure_logging(level: int = logging.INFO, stream: Any = None) -> None:
    """Configure standard Python logging handler for robust_adapt.

    Parameters
    ----------
    level : int, default=logging.INFO
        Logging verbosity level.
    stream : Any, default=None
        Target output stream. If None, defaults to sys.stderr.
    """
    logger.setLevel(level)
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
