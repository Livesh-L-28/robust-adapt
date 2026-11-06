# Observability, Diagnostics & Telemetry Guide

AdaptiveML includes a built-in observability and diagnostics architecture designed for real-time monitoring of streaming pipelines, controller arbitration decisions, memory consumption, and error traces.

---

## 1. Zero-PII Observability Guarantees

AdaptiveML adheres to a strict **zero Personally Identifiable Information (PII)** and zero data-leakage design contract:
- **No Raw Feature Values:** Observability hooks never log raw input matrices, target values, or feature coordinates.
- **Statistical Aggregates Only:** Telemetry records only non-invertible aggregate metrics: mean loss, batch sizes, latency in milliseconds, parameter norms, and discrete intervention states.
- **Air-Gapped & Offline Ready:** Built-in diagnostics emit structured Python dictionaries and standard Python logging events with zero external telemetry networks or unconsented outbound sockets.

---

## 2. Using `DiagnosticRegistry`

The `DiagnosticRegistry` provides a thread-safe, bounded in-memory diagnostic event sink for tracking pipeline health and logging operational events:

```python
from robust_adapt.core import DiagnosticRegistry, DiagnosticEvent

# 1. Initialize registry with bounded memory capacity (e.g. 1,000 events)
registry = DiagnosticRegistry(max_events=1000)

# 2. Record structured diagnostic events
registry.record(
    component="DRIFT_DETECTOR",
    event_type="ADWIN_CUT",
    details={"delta": 0.002, "window_length": 320},
    level="INFO",
    step=1420
)

registry.record(
    component="RESOURCE_BUDGET",
    event_type="LATENCY_PRESSURE",
    details={"step_time_ms": 125.4, "action": "throttle_batch_size"},
    level="WARNING",
    step=1421
)

# 3. Query historical events for auditing or debugging
recent_events = registry.get_events(component="DRIFT_DETECTOR", limit=10)
for ev in recent_events:
    print(f"[{ev.level}] step {ev.step} - {ev.component}: {ev.event_type} ({ev.details})")
```

---

## 3. Real-Time Memory Probing (`get_process_memory_bytes`)

AdaptiveML includes a cross-platform memory probe function `get_process_memory_bytes()` that queries the operating system kernel for current process resident memory (RSS):

```python
from robust_adapt.core import get_process_memory_bytes

initial_mem = get_process_memory_bytes()
print(f"Initial Resident Memory: {initial_mem / (1024 * 1024):.2f} MB")

# Perform memory-intensive streaming or optimizer step
# ...

current_mem = get_process_memory_bytes()
delta_mb = (current_mem - initial_mem) / (1024 * 1024)
print(f"Current Memory: {current_mem / (1024 * 1024):.2f} MB (Delta: {delta_mb:+.2f} MB)")
```

---

## 4. Controller Telemetry & Explainability

When using the `UnifiedLearningControllerV4_1` or `UnifiedLearningControllerV5`, every arbitration step emits rich, structured telemetry:

```python
import numpy as np
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config

controller = UnifiedLearningControllerV5(n_features=8, n_classes=2)

X = np.random.randn(32, 8)
y = (X[:, 0] > 0.0).astype(int)

directive, telemetry = controller.step(X, y)

print("Arbitration Directive:", directive.action)
print("Telemetry Keys:", list(telemetry.keys()))
print(f"Step Loss: {telemetry['loss']:.4f}")
print(f"Utility Score: {telemetry['utility_score']:.4f}")
print(f"Active Concept ID: {telemetry['active_concept_id']}")
```

---

## 5. Integrating with Prometheus or CloudWatch

Because AdaptiveML telemetry dictionaries contain standard scalar types (float, int, str), they can be forwarded directly to third-party metric collectors:

```python
def export_to_metrics_exporter(telemetry: dict):
    # Example adapter for Prometheus / CloudWatch / OpenTelemetry
    metric_payload = {
        "stream_loss": float(telemetry.get("loss", 0.0)),
        "stream_accuracy": float(telemetry.get("accuracy", 0.0)),
        "intervention_tier": str(telemetry.get("tier", "TIER_0")),
        "step_latency_ms": float(telemetry.get("latency_ms", 0.0)),
    }
    # send_to_collector(metric_payload)
```
