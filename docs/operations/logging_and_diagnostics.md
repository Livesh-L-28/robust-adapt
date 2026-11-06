# AdaptiveML Production Operations — Logging and Diagnostics Guide

## 1. Observability Architecture

AdaptiveML provides comprehensive zero-overhead observability for production streaming machine learning pipelines. Observability in AdaptiveML adheres to the following production principles:

1. **Local-Only by Default:** Zero mandatory telemetry, zero network sockets opened, zero outbound phone-home analytics.
2. **Deterministic Bounded Ring Buffers:** Diagnostic events are stored in a fixed-size ring buffer ($O(N)$ with default capacity $N=1,000$), guaranteeing that event logging cannot cause memory leaks or OOM crashes.
3. **Structured Event Data:** All diagnostic records are emitted as structured JSON-serializable dictionaries containing timestamp, component, level, message, and contextual metadata.
4. **Integration with Standard Python Logging:** Emits events to Python's standard `logging` library hierarchy (`adaptive_ml.*`), enabling seamless ingestion into OpenTelemetry, Prometheus, Datadog, or Grafana Loki.

---

## 2. Configuring Production Logging

To configure structured logging with customized log levels and handlers, use `configure_logging`:

```python
import logging
from robust_adapt.core.diagnostics import configure_logging

# Enable INFO logging for AdaptiveML with custom format
configure_logging(
    level=logging.INFO,
    format_string="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

---

## 3. Using the Diagnostic Event Registry

The [`DiagnosticRegistry`](file:///c:/projects/AdaptiveML/adaptive_ml/core/diagnostics.py) singleton records anomalies, budget breaches, concept drift events, and automaton state transitions:

```python
from robust_adapt.core.diagnostics import (
    record_diagnostic_event,
    get_diagnostic_events,
    clear_diagnostic_events,
)

# Ingest or query events
events = get_diagnostic_events(component="ulc", min_level="WARNING")
for event in events:
    print(f"[{event['timestamp']}] {event['message']} (data: {event['metadata']})")
```

### Filtering Events Programmatically
`get_diagnostic_events()` supports filtering by:
- `component`: e.g. `"ulc"`, `"ala"`, `"rla"`, `"rao"`, `"state"`
- `min_level`: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

---

## 4. Monitoring Streaming Controller Telemetry

On every batch step, [`UnifiedLearningControllerV4_1.step()`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) returns a real-time `telemetry` dictionary:

```python
directive, telemetry = controller.step(X, y)

print(f"Step: {telemetry['step']}")
print(f"Automaton State: {telemetry['state']}")
print(f"Active Scenario: {telemetry['scenario']}")
print(f"Mean Sample Reliability: {telemetry['mean_reliability']:.3f}")
print(f"Retained Training Samples: {telemetry['n_retained_samples']}/{telemetry['n_input_samples']}")
```

### Recommended Alerting Rules

| Metric | Trigger Condition | Severity | Recommended Action |
| :--- | :--- | :--- | :--- |
| `mean_reliability` | $< 0.35$ for $> 5$ steps | **WARNING** | Investigate data stream for sensor corruption or adversarial injection. |
| `n_retained_samples` | $0$ for $> 10$ steps | **ERROR** | Pipeline is discarding all data. Check filter threshold or recalibrate reliability scorer. |
| `state == NOISE_BURST` | $> 12$ consecutive steps | **WARNING** | Dwell timeout will trigger escape to `STABLE` at step 15. Check upstream label quality. |
| `step_time_ms` | $> \text{max\_step\_time\_ms}$ | **WARNING** | Budget manager will throttle tree split evaluations. Inspect CPU load. |
